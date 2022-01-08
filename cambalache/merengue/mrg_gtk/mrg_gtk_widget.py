# GtkWidget Controller
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

import gi
from gi.repository import GObject, Gdk, Gtk

from .mrg_selection import MrgSelection

from merengue import MrgController, getLogger, utils

logger = getLogger(__name__)


class MrgGtkWidgetController(MrgController):
    object = GObject.Property(type=Gtk.Widget,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self.window = None

        super().__init__(**kwargs)

        # Make sure all widget are always visible
        self.property_ignore_list.add('visible')

        self.child_property_ignore_list = set()

        self.connect("notify::selected", self.__on_selected_changed)
        self.connect("notify::object", self.__on_object_changed)

        # Make sure show_all() always works
        if Gtk.MAJOR_VERSION == 3:
            self.property_ignore_list.add('no-show-all')

        self.__on_object_changed(self.object, None)

    def __on_object_changed(self, obj, pspec):
        self.__on_selected_changed(obj, pspec)

        if self.object is None:
            if self.window:
                self.window.destroy()
                self.window = None
            return

        parent = self.object.get_parent()

        if parent or issubclass(type(self.object), Gtk.Window):
            return

        if self.window is None:
            type_name = GObject.type_name(self.object.__gtype__)
            self.window = Gtk.Window(deletable=False, title=type_name)
            self.selection = MrgSelection(app=self.app, window=self.window)

        if Gtk.MAJOR_VERSION == 4:
            self.window.set_child(self.object)
            self.window.show()
        else:
            child = self.window.get_child()
            if child:
                self.window.remove(child)
            self.window.add(self.object)
            self.window.show_all()

    def __on_selected_changed(self, obj, pspec):
        if self.object is None:
            return

        if self.selected:
            self.object.get_style_context().add_class('merengue_selected')
        else:
            self.object.get_style_context().remove_class('merengue_selected')

        # Update toplevel backdrop state
        if Gtk.MAJOR_VERSION == 4:
            toplevel = self.object.get_root()
        else:
            toplevel = self.object.get_toplevel()

        if toplevel:
            state = Gtk.StateFlags.NORMAL if self.selected else Gtk.StateFlags.BACKDROP
            toplevel.set_state_flags(state, True)

    def get_children(self):
        if self.object is None:
            return []

        if Gtk.MAJOR_VERSION == 4:
            retval = []

            child = self.object.get_first_child()
            while child is not None:
                retval.append(child)
                child = child.get_next_sibling()

            return retval
        else:
            return self.object.get_children() if isinstance(self.object, Gtk.Container) else []

    def child_get(self, child, properties):
        if self.object is None:
            return None

        if Gtk.MAJOR_VERSION == 4:
            layout_child = None
            manager = self.object.get_layout_manager()
            if manager:
                layout_child = manager.get_layout_child(child)

            return [layout_child.get_property(x) for x in properties] if layout_child else None
        else:
            return self.object.child_get(child, *properties)

    def get_child_position(self, child):
        return -1

    def get_child_layout(self, child, layout):
        return layout

    def placeholder_selected(self, placeholder):
        position = self.get_child_position(placeholder)
        layout = self.get_child_layout(placeholder, {})
        utils.write_command('placeholder_selected',
                            args={
                                'ui_id': self.ui_id,
                                'object_id': self.object_id,
                                'position': position,
                                'layout': layout
                            })

    def placeholder_activated(self, placeholder):
        position = self.get_child_position(placeholder)
        layout = self.get_child_layout(placeholder, {})
        utils.write_command('placeholder_activated',
                            args={
                                'ui_id': self.ui_id,
                                'object_id': self.object_id,
                                'position': position,
                                'layout': layout
                            })

    def add_placeholder(self, mod):
        pass

    def remove_placeholder(self, mod):
        pass

    def find_child_property(self, child, property_id):
        if self.object is None:
            return None

        if Gtk.MAJOR_VERSION == 4:
            manager = self.object.get_layout_manager()
            layout_child = manager.get_layout_child(child)
            return layout_child.find_property(property_id) if layout_child else None

        return self.object.find_child_property(property_id)

    def set_object_child_property(self, child, property_id, val):
        if self.object is None or property_id in self.child_property_ignore_list:
            return

        if Gtk.MAJOR_VERSION == 4:
            manager = self.object.get_layout_manager()
            layout_child = manager.get_layout_child(child)
            layout_child.set_property(property_id, val)
        else:
            self.object.child_set_property(child, property_id, val)

