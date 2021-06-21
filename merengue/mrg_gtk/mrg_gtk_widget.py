# GtkWidget Controller
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject, Gdk, Gtk

from merengue.controller import MrgController


class MrgGtkWidgetController(MrgController):
    object = GObject.Property(type=Gtk.Widget,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Make sure all widget are always visible
        self.property_ignore_list.add('visible')

        self.child_property_ignore_list = set()

        self.connect("notify::selected", self.on_selected_changed)
        self.connect("notify::object", self.on_selected_changed)

        # Make sure show_all() always works
        if Gtk.MAJOR_VERSION == 3:
            self.property_ignore_list.add('no-show-all')

    def on_selected_changed(self, obj, pspec):
        if self.object is None:
            return

        if self.selected:
            self.object.get_style_context().add_class('merengue_selected')
        else:
            self.object.get_style_context().remove_class('merengue_selected')

        # Update toplevel backdrop state
        if Gtk.MAJOR_VERSION == 3:
            toplevel = self.object.get_toplevel()
        else:
            toplevel = self.object.get_root()

        if toplevel:
            state = Gtk.StateFlags.NORMAL if self.selected else Gtk.StateFlags.BACKDROP
            toplevel.set_state_flags(state, True)

    def remove_object(self):
        if self.object is None:
            return

        if self.object.props.parent:
            self.object.props.parent.remove(self.object)

        super().remove_object()

    def find_child_property(self, child, property_id):
        if self.object is None:
            return None

        if Gtk.MAJOR_VERSION == 3:
            return self.object.find_child_property(property_id)
        else:
            manager = self.object.get_layout_manager()
            layout_child = manager.get_layout_child(child)
            return layout_child.find_property(property_id)

    def set_object_child_property(self, child, property_id, val):
        if self.object is None or property_id in self.child_property_ignore_list:
            return

        if Gtk.MAJOR_VERSION == 3:
            self.object.child_set_property(child, property_id, val)
        else:
            manager = self.object.get_layout_manager()
            layout_child = manager.get_layout_child(child)
            layout_child.set_property(property_id, val)

