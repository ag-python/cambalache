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
from gi.repository import GObject, Gdk, Gtk, CambalachePrivate

from .mrg_selection import MrgSelection

from merengue import MrgController, getLogger, utils

logger = getLogger(__name__)


class MrgGtkWidget(MrgController):
    object = GObject.Property(type=Gtk.Widget,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self.window = None
        self.selection = None

        super().__init__(**kwargs)

        # Make sure all widget are always visible
        self.property_ignore_list.add('visible')

        self.child_property_ignore_list = set()

        self.connect("notify::selected", self.__on_selected_changed)

        # Make sure show_all() always works
        if Gtk.MAJOR_VERSION == 3:
            self.property_ignore_list.add('no-show-all')

    def on_object_changed(self):
        def window_remove_child(window):
            if window is None:
                return

            if Gtk.MAJOR_VERSION == 4:
                window.set_child(None)
            else:
                child = window.get_child()
                if child:
                    window.remove(child)

        super().on_object_changed()

        self.on_selected_changed()

        if self.object is None:
            window_remove_child(self.window)
            return

        if not self.toplevel or issubclass(type(self.object), Gtk.Window):
            return

        if self.window is None:
            self.window = Gtk.Window(deletable=False)
            self.selection = MrgSelection(app=self.app, container=self.window)

        # Update title
        self.window.set_title(GObject.type_name(self.object.__gtype__))

        window_remove_child(self.window)

        if Gtk.MAJOR_VERSION == 4:
            self.window.set_child(self.object)
            self.window.show()
        else:
            self.window.add(self.object)
            self.window.show_all()

    def on_selected_changed(self):
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

    def __on_selected_changed(self, obj, pspec):
        self.on_selected_changed()

    def __get_children(self, obj):
        if obj is None:
            return []

        if Gtk.MAJOR_VERSION == 4:
            retval = []

            child = obj.get_first_child()
            while child is not None:
                retval.append(child)
                child = child.get_next_sibling()

            return retval
        else:
            return obj.get_children() if isinstance(obj, Gtk.Container) else []

    def get_children(self):
        return self.__get_children(self.object)

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

    def get_child_type(self, child):
        return None

    def get_child_layout(self, child, layout):
        return layout

    def remove_child(self, child):
        if self.object is None:
            return

        if Gtk.MAJOR_VERSION == 3:
            self.object.remove(child)
        else:
            logger.warning('Not implemented')

    def placeholder_selected(self, placeholder):
        position = self.get_child_position(placeholder)
        child_type = self.get_child_type(placeholder)
        layout = self.get_child_layout(placeholder, {})
        utils.write_command('placeholder_selected',
                            args={
                                'ui_id': self.ui_id,
                                'object_id': self.object_id,
                                'position': position,
                                'child_type': child_type,
                                'layout': layout
                            })

    def placeholder_activated(self, placeholder):
        position = self.get_child_position(placeholder)
        child_type = self.get_child_type(placeholder)
        layout = self.get_child_layout(placeholder, {})
        utils.write_command('placeholder_activated',
                            args={
                                'ui_id': self.ui_id,
                                'object_id': self.object_id,
                                'position': position,
                                'child_type': child_type,
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
            CambalachePrivate.object_set_property_from_string(layout_child, property_id, val)
        else:
            CambalachePrivate.container_child_set_property_from_string(self.object, child, property_id, val)

    def show_child(self, child):
        pass

    def find_child(self, *args):
        retval = self.object

        for name in args:
            for child in self.__get_children(retval):
                if utils.object_get_builder_id(child) == name:
                    retval = child
                    break

            if utils.object_get_builder_id(retval) != name:
                return None

        return retval
        
