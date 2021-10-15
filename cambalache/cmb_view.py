#
# CmbView - Cambalache View
#
# Copyright (C) 2021  Juan Pablo Ugarte
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation;
# version 2.1 of the License.
#
# library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors:
#   Juan Pablo Ugarte <juanpablougarte@gmail.com>
#

import os
import gi
import json
import socket

from time import sleep
from lxml import etree

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import GObject, GLib, Gio, Gdk, Gtk, WebKit2

from . import config
from .cmb_object import CmbObject
from .cmb_project import CmbProject
from cambalache import getLogger

logger = getLogger(__name__)

basedir = os.path.dirname(__file__) or '.'

GObject.type_ensure(WebKit2.Settings.__gtype__)
GObject.type_ensure(WebKit2.WebView.__gtype__)


class CmbProcess(GObject.Object):
    __gsignals__ = {
        'stdout': (GObject.SignalFlags.RUN_LAST, bool, (GLib.IOCondition, )),

        'exit': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    file = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pid = 0
        self.stdin = None
        self.stdout = None

    def stop(self):
        if self.stdin:
            self.stdin.shutdown(False)
            self.stdin = None

        if self.stdout:
            self.stdout.shutdown(False)
            self.stdout = None

        if self.pid:
            try:
                GLib.spawn_close_pid(self.pid)
                os.kill(self.pid, 9)
                self.pid = 0
            except Exception as e:
                logger.warning(f'Error stoping {self.file} {e}')

    def run(self, args, env=[]):
        if self.file is None or self.pid > 0:
            return

        envp = []
        for var in os.environ:
            val = os.environ.get(var)
            envp.append(f"{var}={val}")

        pid, stdin, stdout, stderr = GLib.spawn_async([self.file] + args,
                                                      envp=envp+env,
                                                      flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_input=True,
                                                      standard_output=True)
        self.pid = pid

        self.stdin = GLib.IOChannel.unix_new(stdin)
        self.stdout = GLib.IOChannel.unix_new(stdout)

        self.stdout.add_watch(GLib.IOCondition.IN | GLib.IOCondition.HUP,
                              self._on_stdout)

        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE,
                             pid,
                             self._on_exit,
                             None)

    def _on_exit(self, pid, status, data):
        self.stop()
        self.emit('exit')

    def _on_stdout(self, channel, condition):
        return self.emit('stdout', condition)


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_view.ui')
class CmbView(Gtk.Stack):
    __gtype_name__ = 'CmbView'

    webview = Gtk.Template.Child()
    buffer = Gtk.Template.Child()
    menu = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self._project = None
        self._restart_project = None
        self._ui_id = 0

        super().__init__(**kwargs)

        self._merengue_bin = os.path.join(config.merenguedir, 'merengue', 'merengue')
        self._broadwayd_bin = GLib.find_program_in_path('broadwayd')
        self._gtk4_broadwayd_bin = GLib.find_program_in_path('gtk4-broadwayd')

        self.webview.connect('load-changed', self._on_load_changed)

        self._merengue = None
        self._broadwayd = None
        self._port = None

        context = self.get_style_context()
        context.connect('changed', self._on_style_context_changed)

        if self._broadwayd_bin is None:
            logger.warning("broadwayd not found, Gtk 3 workspace wont work.")

        if self._gtk4_broadwayd_bin is None:
            logger.warning("gtk4-broadwayd not found, Gtk 4 workspace wont work.")

    def do_destroy(self):
        if self._merengue:
            self._merengue.stop()

        if self._broadwayd:
            self._broadwayd.stop()

    def _on_style_context_changed(self, ctx):
        self._update_webview_bg()

    def _update_webview_bg(self):
        context = self.get_style_context()
        bg = context.get_background_color(Gtk.StateFlags.NORMAL)
        self.webview.run_javascript(f"document.body.style.background = '{bg.to_string()}';")

    def _on_load_changed(self, webview, event):
        if event != WebKit2.LoadEvent.FINISHED:
            return

        self._update_webview_bg()

        # Disable aler() function used when broadwayd get disconnected
        # Monkey patch setupDocument() to avoid disabling document.oncontextmenu
        webview.run_javascript('''
window.alert = function (message) {
    console.log (message);
}

window.merengueSetupDocument = setupDocument;

window.setupDocument = function (document) {
    var cb = oncontextmenu
    merengueSetupDocument(document);
    document.oncontextmenu = cb;
}
''', None, None)

    def _merengue_command(self, command, payload=None, args=None):
        if self._merengue is None or self._merengue.stdin is None:
            return

        cmd = {
            'command': command,
            'payload_length': len(payload) if payload is not None else 0
        }

        if args is not None:
            cmd['args'] = args

        # Send command in one line as json
        self._merengue.stdin.write(json.dumps(cmd))
        self._merengue.stdin.write('\n')

        # Send payload if any
        if payload is not None:
            self._merengue.stdin.write(payload)

        # Flush
        self._merengue.stdin.flush()

    def _get_ui_xml(self, ui_id, use_id=False):
        ui = self._project.db.export_ui(ui_id, use_id=use_id)
        return etree.tostring(ui,
                              pretty_print=True,
                              xml_declaration=True,
                              encoding='UTF-8').decode('UTF-8')

    def _update_view(self):
        if self._project is not None and self._ui_id > 0:
            if self.props.visible_child_name == 'ui_xml':
                ui = self._get_ui_xml(self._ui_id)
                self.buffer.set_text(ui)
            return

        self.buffer.set_text('')
        self._ui_id = 0

    def _merengue_update_ui(self, ui_id):
        ui = self._get_ui_xml(ui_id, use_id=True)

        self._merengue_command('update_ui',
                               payload=ui,
                               args={ 'ui_id': ui_id })

    def _on_object_added(self, project, obj):
        self._update_view()
        self._merengue_update_ui(obj.ui_id)

    def _on_object_removed(self, project, obj):
        self._update_view()
        self._merengue_command('object_removed', args={
            'ui_id': obj.ui_id,
            'object_id': obj.object_id
        })

    def _on_object_property_changed(self, project, obj, prop):
        self._update_view()
        self._merengue_command('object_property_changed', args={
            'ui_id': obj.ui_id,
            'object_id': obj.object_id,
            'property_id': prop.property_id,
            'is_object': prop.info.is_object,
            'value': prop.value
        })

    def _on_object_layout_property_changed(self, project, obj, child, prop):
        self._update_view()
        self._merengue_command('object_layout_property_changed', args={
            'ui_id': obj.ui_id,
            'object_id': obj.object_id,
            'child_id': child.object_id,
            'property_id': prop.property_id,
            'value': prop.value
        })

    def _on_project_selection_changed(self, project):
        selection = project.get_selection()

        if len(selection) > 0:
            ui_id = selection[0].ui_id

            if self._ui_id != ui_id:
                self._ui_id = ui_id
                self._update_view()
                self._merengue_update_ui(ui_id)

            objects = []
            for obj in selection:
                if type(obj) == CmbObject and obj.ui_id == ui_id:
                    objects.append(obj.object_id)

            self._merengue_command('selection_changed', args={ 'ui_id': ui_id, 'selection': objects })

        elif self._ui_id > 0:
            self._ui_id = 0
            self._update_view()
            self._merengue_command('selection_changed', args={ 'ui_id': 0, 'selection': [] })

    @GObject.Property(type=GObject.GObject)
    def project(self):
        return self._project

    @project.setter
    def _set_project(self, project):
        if self._project is not None:
            self._project.disconnect_by_func(self._on_object_added)
            self._project.disconnect_by_func(self._on_object_removed)
            self._project.disconnect_by_func(self._on_object_property_changed)
            self._project.disconnect_by_func(self._on_object_layout_property_changed)
            self._project.disconnect_by_func(self._on_project_selection_changed)
            self._merengue.disconnect_by_func(self._on_merengue_stdout)
            self._merengue.stop()
            self._broadwayd.stop()

        self._project = project

        self._update_view()

        if project is not None:
            project.connect('object-added', self._on_object_added)
            project.connect('object-removed', self._on_object_removed)
            project.connect('object-property-changed', self._on_object_property_changed)
            project.connect('object-layout-property-changed', self._on_object_layout_property_changed)
            project.connect('selection-changed', self._on_project_selection_changed)

            self._merengue = CmbProcess(file=self._merengue_bin)
            self._merengue.connect('stdout', self._on_merengue_stdout)
            self._merengue.connect('exit', self._on_process_exit)

            broadwayd = self._gtk4_broadwayd_bin if self._project.target_tk == 'gtk-4.0' else self._broadwayd_bin
            self._broadwayd = CmbProcess(file=broadwayd)
            self._broadwayd.connect('stdout', self._on_broadwayd_stdout)
            self._broadwayd.connect('exit', self._on_process_exit)

            self._port = self._find_free_port()
            display = self._port - 8080
            self._broadwayd.run([f':{display}'])

    @GObject.Property(type=str)
    def gtk_theme(self):
        return self._theme

    @gtk_theme.setter
    def _set_theme(self, theme):
        self._theme = theme
        self._merengue_command('gtk_settings_set',
                               args={
                                   'property': 'gtk-theme-name',
                                   'value': theme
                               })

    @Gtk.Template.Callback('on_context_menu')
    def _on_context_menu(self, webview, menu, e, hit_test_result):
        r = Gdk.Rectangle()
        r.x, r.y, r.width, r.height = (e.x, e.y, 10, 10)
        self.menu.set_pointing_to(r)
        self.menu.popup()
        return True

    @Gtk.Template.Callback('on_inspect_button_clicked')
    def _on_inspect_button_clicked(self, button):
        self.props.visible_child_name = 'ui_xml'
        self._update_view()

    @Gtk.Template.Callback('on_restart_button_clicked')
    def _on_restart_button_clicked(self, button):
        self._restart_project = self._project
        self.project = None

    def _on_process_exit(self, process):
        if self._broadwayd.pid == 0 and self._merengue.pid == 0:
            self.project = self._restart_project
            self._restart_project = None
            self._ui_id = 0

    def _command_selection_changed(self, selection):
        objects = []

        for key in selection:
            obj = self._project._get_object_by_key(key)
            objects.append(obj)

        self._project.set_selection(objects)

    def _on_merengue_stdout(self, process, condition):
        if condition == GLib.IOCondition.HUP:
            self._merengue.stop()
            return GLib.SOURCE_REMOVE

        if self._merengue.stdout is None:
            return GLib.SOURCE_REMOVE

        retval = self._merengue.stdout.readline()
        cmd = None

        try:
            cmd = json.loads(retval)
            command = cmd.get('command', None)
            args = cmd.get('args', {})

            if command == 'selection_changed':
                self._command_selection_changed(**args)
            elif command == 'started':
                self._on_project_selection_changed(self._project)

                self._merengue_command('gtk_settings_get',
                                       args={ 'property': 'gtk-theme-name' })
            elif command == 'gtk_settings_get':
                if args['property'] == 'gtk-theme-name':
                    self._theme = args['value']
                    self.notify('gtk_theme')

        except Exception as e:
            logger.warning('Merenge output error: {e}')

        return GLib.SOURCE_CONTINUE

    def _on_broadwayd_stdout(self, process, condition):
        if condition == GLib.IOCondition.HUP:
            self._broadwayd.stop()
            return GLib.SOURCE_REMOVE

        if self._broadwayd.stdout is None:
            return GLib.SOURCE_REMOVE

        status, retval, length, terminator = self._broadwayd.stdout.read_line()
        path = retval.replace('Listening on ', '').strip()

        # Run view process
        if self._project.target_tk == 'gtk+-3.0':
            version = '3.0'
        elif self._project.target_tk == 'gtk-4.0':
            version = '4.0'

        display = self._port - 8080
        self._merengue.run([version], [
            'GDK_BACKEND=broadway',
            #'GTK_DEBUG=interactive',
            f'BROADWAY_DISPLAY=:{display}'
        ])

        # Load broadway desktop
        self.webview.load_uri(f'http://127.0.0.1:{self._port}')

        self._broadwayd.stdout.shutdown(False)
        self._broadwayd.stdout = None
        return GLib.SOURCE_REMOVE

    def _find_free_port(self):
        for port in range(8080, 8180):
            s = socket.socket()
            retval = s.connect_ex(('127.0.0.1', port))
            s.close()

            if retval != 0:
                return port

        return 0


Gtk.WidgetClass.set_css_name(CmbView, 'CmbView')
