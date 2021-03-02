#
# Cambalache UI Maker
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from cambalache import *

from .cmb_window import CmbWindow


class CmbApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='ar.xjuan.Cambalache',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.windows = []

    def do_open(self, files, nfiles, hint):
        open_files = {}

        for win in self.windows:
            if win.project is not None and win.project.filename is not None:
                open_files[win.project.filename] = win

        for file in files:
            path = file.get_path()

            if path in open_files.keys():
                open_files[path].present()
            else:
                window = CmbWindow(application=self)
                window.present()
                window.open_project(path)
                self.windows.append(window)
                open_files[path] = window

    def do_startup(self):
        Gtk.Application.do_startup(self)

        for action in ['quit']:
            gaction= Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self.add_action(gaction)

    def do_activate(self):
        if len(self.windows) > 0:
            return

        window = CmbWindow(application=self)
        window.present()
        self.windows.append(window)

    def _on_quit_activate(self, action, data):
        for win in self.windows:
            win.destroy()
        self.quit()


if __name__ == "__main__":
    # FIXME: we need this to load template resources
    os.chdir(os.path.dirname(__file__))
    app = CmbApplication()
    app.run(sys.argv)
