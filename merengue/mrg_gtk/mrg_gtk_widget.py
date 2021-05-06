# GtkWidget Controller
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject, Gdk, Gtk

from controller import MrgController


class MrgGtkWidgetController(MrgController):
    object = GObject.Property(type=Gtk.Widget,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Make sure all widget are always visible
        self.property_ignore_list.add('visible')

        # Make sure show_all() always works
        if Gtk.MAJOR_VERSION == 3:
            self.property_ignore_list.add('no-show-all')

