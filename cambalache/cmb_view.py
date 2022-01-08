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

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import GObject, GLib, Gio, Gdk, Gtk, WebKit2

from . import config
from .cmb_object import CmbObject
from .cmb_project import CmbProject
from .cmb_context_menu import CmbContextMenu
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
                              self.__on_stdout)

        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE,
                             pid,
                             self.__on_exit,
                             None)

    def __on_exit(self, pid, status, data):
        self.stop()
        self.emit('exit')

    def __on_stdout(self, channel, condition):
        return self.emit('stdout', condition)


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_view.ui')
class CmbView(Gtk.Stack):
    __gtype_name__ = 'CmbView'

    __gsignals__ = {
        'placeholder-selected': (GObject.SignalFlags.RUN_LAST, None, (int, int, int, object)),
        'placeholder-activated': (GObject.SignalFlags.RUN_LAST, None, (int, int, int, object))
    }

    webview = Gtk.Template.Child()
    buffer = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self.__project = None
        self.__restart_project = None
        self.__ui_id = 0
        self.__theme = None

        self.menu = self.__create_context_menu()

        super().__init__(**kwargs)

        self.__merengue_bin = os.path.join(config.merenguedir, 'merengue', 'merengue')
        self.__broadwayd_bin = GLib.find_program_in_path('broadwayd')
        self.__gtk4_broadwayd_bin = GLib.find_program_in_path('gtk4-broadwayd')

        self.webview.connect('load-changed', self.__on_load_changed)

        self.__merengue = None
        self.__broadwayd = None
        self.__port = None

        context = self.get_style_context()
        context.connect('changed', lambda ctx: self.__update_webview_bg())

        if self.__broadwayd_bin is None:
            logger.warning("broadwayd not found, Gtk 3 workspace wont work.")

        if self.__gtk4_broadwayd_bin is None:
            logger.warning("gtk4-broadwayd not found, Gtk 4 workspace wont work.")

        GObject.Object.bind_property(self, 'gtk-theme',
                                     self.menu, 'gtk-theme',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)

    def do_destroy(self):
        if self.__merengue:
            self.__merengue.stop()

        if self.__broadwayd:
            self.__broadwayd.stop()

    def __update_webview_bg(self):
        context = self.get_style_context()
        bg = context.get_background_color(Gtk.StateFlags.NORMAL)
        self.webview.run_javascript(f"document.body.style.background = '{bg.to_string()}';")

    def __on_load_changed(self, webview, event):
        if event != WebKit2.LoadEvent.FINISHED:
            return

        self.__update_webview_bg()

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

    def __merengue_command(self, command, payload=None, args=None):
        if self.__merengue is None or self.__merengue.stdin is None:
            return

        cmd = {
            'command': command,
            'payload': payload is not None
        }

        if args is not None:
            cmd['args'] = args

        # Send command in one line as json
        self.__merengue.stdin.write(json.dumps(cmd))
        self.__merengue.stdin.write('\n')

        if payload is not None:
            self.__merengue.stdin.write(GLib.strescape(payload))
            self.__merengue.stdin.write('\n')

        # Flush
        self.__merengue.stdin.flush()

    def __get_ui_xml(self, ui_id, merengue=False):
        return self.__project.db.tostring(ui_id, merengue=merengue)

    def __update_view(self):
        if self.__project is not None and self.__ui_id > 0:
            if self.props.visible_child_name == 'ui_xml':
                ui = self.__get_ui_xml(self.__ui_id, merengue=True)
                self.buffer.set_text(ui)
            return

        self.buffer.set_text('')
        self.__ui_id = 0

    def __merengue_update_ui(self, ui_id):
        ui = self.__get_ui_xml(ui_id, merengue=True)
        toplevels = self.__project.db.get_toplevels(ui_id)

        self.__merengue_command('update_ui',
                                payload=ui,
                                args={
                                    'ui_id': ui_id,
                                    'toplevels': toplevels
                                })

    def __on_object_added(self, project, obj):
        self.__update_view()
        self.__merengue_update_ui(obj.ui_id)

    def __on_object_removed(self, project, obj):
        self.__update_view()
        self.__merengue_update_ui(obj.ui_id)

    def __on_object_property_changed(self, project, obj, prop):
        self.__update_view()
        self.__merengue_command('object_property_changed', args={
            'ui_id': obj.ui_id,
            'object_id': obj.object_id,
            'property_id': prop.property_id,
            'is_object': prop.info.is_object,
            'value': prop.value
        })

    def __on_object_layout_property_changed(self, project, obj, child, prop):
        self.__update_view()
        self.__merengue_command('object_layout_property_changed', args={
            'ui_id': obj.ui_id,
            'object_id': obj.object_id,
            'child_id': child.object_id,
            'property_id': prop.property_id,
            'value': prop.value
        })

    def __on_project_selection_changed(self, project):
        selection = project.get_selection()

        if len(selection) > 0:
            ui_id = selection[0].ui_id

            if self.__ui_id != ui_id:
                self.__ui_id = ui_id
                self.__update_view()
                self.__merengue_update_ui(ui_id)

            objects = []
            for obj in selection:
                if type(obj) == CmbObject and obj.ui_id == ui_id:
                    objects.append(obj.object_id)

            self.__merengue_command('selection_changed', args={ 'ui_id': ui_id, 'selection': objects })

        elif self.__ui_id > 0:
            self.__ui_id = 0
            self.__update_view()
            self.__merengue_command('selection_changed', args={ 'ui_id': 0, 'selection': [] })

    @GObject.Property(type=GObject.GObject)
    def project(self):
        return self.__project

    @project.setter
    def _set_project(self, project):
        if self.__project is not None:
            self.__project.disconnect_by_func(self.__on_object_added)
            self.__project.disconnect_by_func(self.__on_object_removed)
            self.__project.disconnect_by_func(self.__on_object_property_changed)
            self.__project.disconnect_by_func(self.__on_object_layout_property_changed)
            self.__project.disconnect_by_func(self.__on_project_selection_changed)
            self.__merengue.disconnect_by_func(self.__on_merengue_stdout)
            self.__merengue.stop()
            self.__broadwayd.stop()

        self.__project = project

        self.__update_view()

        if project is not None:
            project.connect('object-added', self.__on_object_added)
            project.connect('object-removed', self.__on_object_removed)
            project.connect('object-property-changed', self.__on_object_property_changed)
            project.connect('object-layout-property-changed', self.__on_object_layout_property_changed)
            project.connect('selection-changed', self.__on_project_selection_changed)

            self.__merengue = CmbProcess(file=self.__merengue_bin)
            self.__merengue.connect('stdout', self.__on_merengue_stdout)
            self.__merengue.connect('exit', self.__on_process_exit)

            self.__broadwayd_check(self.__project.target_tk)

            broadwayd = self.__gtk4_broadwayd_bin if self.__project.target_tk == 'gtk-4.0' else self.__broadwayd_bin
            self.__broadwayd = CmbProcess(file=broadwayd)
            self.__broadwayd.connect('stdout', self.__on_broadwayd_stdout)
            self.__broadwayd.connect('exit', self.__on_process_exit)

            self.__port = self.__find_free_port()
            display = self.__port - 8080
            self.__broadwayd.run([f':{display}'])

            # Update css themes
            self.menu.target_tk = self.__project.target_tk

    @GObject.Property(type=str)
    def gtk_theme(self):
        return self.__theme

    @gtk_theme.setter
    def _set_theme(self, theme):
        self.__theme = theme
        self.__merengue_command('gtk_settings_set',
                               args={
                                   'property': 'gtk-theme-name',
                                   'value': theme
                               })

    @Gtk.Template.Callback('on_context_menu')
    def __on_context_menu(self, webview, menu, e, hit_test_result):
        self.menu.popup_at(e.x, e.y)
        return True

    def __webview_set_msg(self, msg):
        self.webview.load_html(f'<html><body><h3 style="white-space: pre; text-align: center; margin-top: 45vh; opacity: 50%">{msg}</h3></body></html>')

    def __broadwayd_check(self, target_tk):
        bin = None

        if target_tk == 'gtk-4.0' and self.__gtk4_broadwayd_bin is None:
            bin = 'gtk4-broadwayd'
        if target_tk == 'gtk+-3.0' and self.__broadwayd_bin is None:
            bin = 'broadwayd'

        if bin is not None:
            self.__webview_set_msg(_('Workspace not available\n{bin} executable not found').format(bin=bin))

    def __on_inspect_button_clicked(self, button):
        self.props.visible_child_name = 'ui_xml'
        self.__update_view()

    def __on_restart_button_clicked(self, button):
        self.__restart_project = self.__project
        self.project = None

    def __create_context_menu(self):
        retval = CmbContextMenu(relative_to=self)

        restart = Gtk.ModelButton(text=_('Restart workspace'),
                                  visible=True)
        restart.connect('clicked', self.__on_restart_button_clicked)

        inspect = Gtk.ModelButton(text=_('Inspect UI definition'),
                                  visible=True)
        inspect.connect('clicked', self.__on_inspect_button_clicked)

        retval.main_box.add(restart)
        retval.main_box.add(inspect)

        return retval

    def __on_process_exit(self, process):
        if self.__broadwayd.pid == 0 and self.__merengue.pid == 0:
            self.project = self.__restart_project
            self.__restart_project = None
            self.__ui_id = 0

    def __command_selection_changed(self, selection):
        objects = []

        for key in selection:
            obj = self.__project.get_object_by_key(key)
            objects.append(obj)

        self.__project.set_selection(objects)

    def __on_merengue_stdout(self, process, condition):
        if condition == GLib.IOCondition.HUP:
            self.__merengue.stop()
            return GLib.SOURCE_REMOVE

        if self.__merengue.stdout is None:
            return GLib.SOURCE_REMOVE

        retval = self.__merengue.stdout.readline()
        cmd = None

        try:
            cmd = json.loads(retval)
            command = cmd.get('command', None)
            args = cmd.get('args', {})

            if command == 'selection_changed':
                self.__command_selection_changed(**args)
            elif command == 'started':
                self.__on_project_selection_changed(self.__project)

                self.__merengue_command('gtk_settings_get',
                                       args={ 'property': 'gtk-theme-name' })
            elif command == 'placeholder_selected':
                self.emit('placeholder-selected', args['ui_id'], args['object_id'], args['position'], args['layout'])
            elif command == 'placeholder_activated':
                self.emit('placeholder-activated', args['ui_id'], args['object_id'], args['position'], args['layout'])
            elif command == 'gtk_settings_get':
                if args['property'] == 'gtk-theme-name':
                    self.__theme = args['value']
                    self.notify('gtk_theme')

        except Exception as e:
            logger.warning(f'Merenge output error: {e}')

        return GLib.SOURCE_CONTINUE

    def __on_broadwayd_stdout(self, process, condition):
        if condition == GLib.IOCondition.HUP:
            self.__broadwayd.stop()
            return GLib.SOURCE_REMOVE

        if self.__broadwayd.stdout is None:
            return GLib.SOURCE_REMOVE

        status, retval, length, terminator = self.__broadwayd.stdout.read_line()
        path = retval.replace('Listening on ', '').strip()

        # Run view process
        if self.__project.target_tk == 'gtk+-3.0':
            version = '3.0'
        elif self.__project.target_tk == 'gtk-4.0':
            version = '4.0'

        display = self.__port - 8080
        self.__merengue.run([version], [
            'GDK_BACKEND=broadway',
            #'GTK_DEBUG=interactive',
            f'BROADWAY_DISPLAY=:{display}'
        ])

        # Load broadway desktop
        self.webview.load_uri(f'http://127.0.0.1:{self.__port}')

        self.__broadwayd.stdout.shutdown(False)
        self.__broadwayd.stdout = None
        return GLib.SOURCE_REMOVE

    def __find_free_port(self):
        for port in range(8080, 8180):
            s = socket.socket()
            retval = s.connect_ex(('127.0.0.1', port))
            s.close()

            if retval != 0:
                return port

        return 0

    def __add_remove_placeholder(self, command, modifier):
        if self.project is None:
            return

        selection = self.project.get_selection()
        if len(selection) < 0:
            return

        obj = selection[0]
        self.__merengue_command(command,
                               args={
                                   'ui_id': obj.ui_id,
                                   'object_id': obj.object_id,
                                   'modifier': modifier
                               })

    def add_placeholder(self, modifier=False):
        self.__add_remove_placeholder('add_placeholder', modifier)

    def remove_placeholder(self, modifier=False):
        self.__add_remove_placeholder('remove_placeholder', modifier)


Gtk.WidgetClass.set_css_name(CmbView, 'CmbView')
