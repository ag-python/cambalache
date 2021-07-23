#
# Cambalache Application
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import gi

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk, Gio

from cambalache import *

from .cmb_window import CmbWindow

basedir = os.path.dirname(__file__) or '.'


class CmbApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='ar.xjuan.Cambalache',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

    def open(self, path, target_tk=None, uiname=None):
        window = None

        for win in self.get_windows():
            if win.project is not None and win.project.filename == path:
                window = win

        if window is None:
            window = CmbWindow(application=self)
            window.connect('open-project', self._on_open_project)
            if path is not None:
                window.open_project(path, target_tk=target_tk, uiname=uiname)
            self.add_window(window)

        window.present()

    def do_open(self, files, nfiles, hint):
        for file in files:
            path = file.get_path()
            self.open(path)

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

    def _on_open_project(self, window, filename, target_tk, uiname):
        if window.project is None:
            window.open_project(filename, target_tk, uiname)
        else:
            self.open(filename, target_tk, uiname)

    def _on_quit_activate(self, action, data):
        self.quit()


if __name__ == '__main__':
    app = CmbApplication()
    app.run(sys.argv)
