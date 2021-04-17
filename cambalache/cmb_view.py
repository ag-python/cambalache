#
# CmbView - Cambalache View
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import gi
import json
import socket

from time import sleep

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import GObject, GLib, Gio, Gdk, Gtk, WebKit2

from .cmb_objects import CmbObject
from .cmb_project import CmbProject

basedir = os.path.dirname(__file__) or '.'

GObject.type_ensure(WebKit2.Settings.__gtype__)
GObject.type_ensure(WebKit2.WebView.__gtype__)


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_view.ui')
class CmbView(Gtk.Stack):
    __gtype_name__ = 'CmbView'

    webview = Gtk.Template.Child()
    buffer = Gtk.Template.Child()
    menu = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self._project = None
        self._ui_id = 0

        super().__init__(**kwargs)

        self.webview.connect('load-changed', self._on_load_changed)

        self._merengue = GLib.find_program_in_path('merengue')

        self._merengue_pid = -1
        self._merengue_stdin = None

        self._broadwayd = None
        self._broadwayd_pid = -1
        self._port = None

    def _on_load_changed(self, webview, event):
        if event != WebKit2.LoadEvent.FINISHED:
            return

        webview.run_javascript('document.oncontextmenu = document.createElement("div").oncontextmenu;', None, None)

    def _merengue_command(self, command, payload=None, args=None):
        if self._merengue_stdin is None:
            return

        cmd = {
            'command': command,
            'payload_length': len(payload) if payload is not None else 0
        }

        if args is not None:
            cmd['args'] = args

        # Send command in one line as json
        self._merengue_stdin.write(json.dumps(cmd))
        self._merengue_stdin.write('\n')

        # Send payload if any
        if payload is not None:
            self._merengue_stdin.write(payload)

        # Flush
        self._merengue_stdin.flush()

    def _update_view(self):
        if self._project is not None and self._ui_id > 0:
            ui = self._project.export_ui(self._ui_id, use_id=True)
            self.buffer.set_text(ui.decode('unicode_escape'))

            return

        self.buffer.set_text('')
        self._ui_id = 0

    def _on_object_added(self, project, obj):
        self._update_view()
        self._merengue_command('update_ui',
                               payload=self.buffer.props.text,
                               args={ 'ui_id': obj.ui_id })

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
                self._merengue_command('update_ui',
                                       payload=self.buffer.props.text,
                                       args={ 'ui_id': ui_id })
            objects = []
            for obj in selection:
                if type(obj) == CmbObject and obj.ui_id == ui_id:
                    objects.append(obj.object_id)

            self._merengue_command('selection_changed', args={ 'ui_id': ui_id, 'selection': objects })

        elif self._ui_id > 0:
            self._ui_id = 0
            self._update_view()
            self._merengue_command('clear_all')

    @GObject.property(type=GObject.GObject)
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
            if self._merengue_pid > 0:
                os.kill(self._merengue_pid, 9)
            if self._broadwayd_pid > 0:
                os.kill(self._broadwayd_pid, 9)

        self._project = project

        self._update_view()

        if project is not None:
            project.connect('object-added', self._on_object_added)
            project.connect('object-removed', self._on_object_removed)
            project.connect('object-property-changed', self._on_object_property_changed)
            project.connect('object-layout-property-changed', self._on_object_layout_property_changed)
            project.connect('selection-changed', self._on_project_selection_changed)

            broadwayd = 'gtk4-broadwayd' if self._project.target_tk == 'gtk-4.0' else 'broadwayd'
            self._broadwayd = GLib.find_program_in_path(broadwayd)
            self._port = self._find_free_port()
            self._run_broadway()

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

    def _on_merengue_exit(self, pid, status, data):
        GLib.spawn_close_pid(self._merengue_pid)
        self._merengue_pid = None
        print('_on_merengue_exit')

    def _on_broadwayd_exit(self, pid, status, data):
        GLib.spawn_close_pid(self._broadwayd_pid)
        self._broadwayd_pid = None
        print('_on_broadwayd_exit')

    def _on_merengue_stdout(self, channel, condition):
        retval = self._merengue_stdout.readline()

        try:
            cmd = json.loads(retval)
        except:
            pass

        return GLib.SOURCE_CONTINUE

    def _run_merengue(self):
        display = self._port - 8080

        env = []
        for var in os.environ:
            val = os.environ.get(var)
            env.append(f"{var}={val}")

        env.append('GDK_BACKEND=broadway')
        env.append(f'BROADWAY_DISPLAY=:{display}')
        #env.append('GTK_DEBUG=interactive')

        print([self._merengue, self._project.target_tk], display)
        pid, stdin, stdout, stderr = GLib.spawn_async([self._merengue,
                                                       self._project.target_tk],
                                                      envp=env,
                                                      flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_input=True,
                                                      standard_output=True)

        self._merengue_stdin = os.fdopen(stdin, 'w')
        self._merengue_stdout = os.fdopen(stdout, 'r')

        stdout_channel = GLib.IOChannel.unix_new(stdout)
        stdout_channel.add_watch(GLib.IOCondition.IN, self._on_merengue_stdout)

        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid,
                             self._on_merengue_exit, None)

        return GLib.SOURCE_REMOVE

    def _on_broadway_stdout(self, channel, condition):
        status, retval, length, terminator = channel.read_line()
        path = retval.replace('Listening on ', '').strip()
        print('_on_broadway_stdout', path)

        # Run view process
        GLib.timeout_add(1000, self._run_merengue)
        #self._run_merengue()

        # Load broadway desktop
        self.webview.load_uri(f'http://127.0.0.1:{self._port}')

        #channel.close()
        return GLib.SOURCE_REMOVE

    def _find_free_port(self):
        for port in range(8080, 8180):
            s = socket.socket()
            retval = s.connect_ex(('127.0.0.1', port))
            s.close()

            if retval != 0:
                return port

        return 0

    def _run_broadway(self):
        if self._broadwayd is None or self._broadwayd_pid > 0:
            return

        print([self._broadwayd, f'--port={self._port}'])
        pid, stdin, stdout, stderr = GLib.spawn_async([self._broadwayd, f'--port={self._port}'],
                                                      flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True)
        self._broadwayd_pid = pid
        stdout_channel = GLib.IOChannel.unix_new(stdout)
        stdout_channel.add_watch(GLib.IOCondition.IN, self._on_broadway_stdout)

        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid,
                             self._on_broadwayd_exit, None)
