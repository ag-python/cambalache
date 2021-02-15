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
        super().__init__(application_id='org.gnome.jpu.Cambalache',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        for action in ['quit']:
            gaction= Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self.add_action(gaction)

    def do_activate(self):
        if not self.window:
            self.window = CmbWindow(application=self)

        self.window.present()

    def _on_quit_activate(self, action, data):
        self.quit()


if __name__ == "__main__":
    # FIXME: we need this to load template resources
    os.chdir(os.path.dirname(__file__))
    app = CmbApplication()
    app.run(sys.argv)
