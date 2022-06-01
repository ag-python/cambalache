#
# Cambalache Application
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
import sys
import gi

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio

from cambalache import *

from .cmb_window import CmbWindow

basedir = os.path.dirname(__file__) or '.'


class CmbApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='ar.xjuan.Cambalache',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

        self.add_main_option('version', b'v',
                             GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE,
                             _("Print version"),
                             None)

        self.add_main_option('export-all', b'E',
                             GLib.OptionFlags.NONE,
                             GLib.OptionArg.FILENAME,
                             _("Export project"),
                             None)

    def __add_window(self):
        window = CmbWindow(application=self)
        window.connect('open-project', self.__on_open_project)
        self.add_window(window)
        return window

    def open(self, path, target_tk=None, uiname=None):
        window = None

        for win in self.get_windows():
            if win.project is not None and win.project.filename == path:
                window = win

        if window is None:
            window = self.__add_window()
            if path is not None:
                window.open_project(path, target_tk=target_tk, uiname=uiname)

        window.present()

    def import_file(self, path):
        window = self.__add_window() if self.props.active_window is None else self.props.active_window
        window.import_file(path)
        window.present()

    def do_open(self, files, nfiles, hint):
        for file in files:
            path = file.get_path()

            content_type, uncertain = Gio.content_type_guess(path, None)
            if uncertain:
                with open(path, 'rb') as fd:
                    data = fd.read(1024)
                content_type, uncertain = Gio.content_type_guess(path, data)

            if content_type == 'application/x-cambalache-project':
                self.open(path)
            elif content_type in ['application/x-gtk-builder', 'application/x-glade']:
                self.import_file(path)

    def do_startup(self):
        Gtk.Application.do_startup(self)

        for action in ['quit']:
            gaction= Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self.add_action(gaction)

        provider = Gtk.CssProvider()
        provider.load_from_resource('/ar/xjuan/Cambalache/app/cambalache.css')
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_activate(self):
        if self.props.active_window is None:
            self.open(None)

    def __on_open_project(self, window, filename, target_tk, uiname):
        if window.project is None:
            window.open_project(filename, target_tk, uiname)
        else:
            self.open(filename, target_tk, uiname)

    def _on_quit_activate(self, action, data):
        self.quit()

    def do_handle_local_options(self, options):
        if options.contains('version'):
            print(VERSION)
            return 0

        if options.contains('export-all'):
            filename = options.lookup_value('export-all')
            filename = ''.join([ chr(c) for c in filename.unpack()])
            project = CmbProject(filename=filename)
            project.export()
            return 0

        return -1

if __name__ == '__main__':
    app = CmbApplication()
    app.run(sys.argv)
