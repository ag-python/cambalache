# GtkWindow Controller
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

from .mrg_gtk_bin import MrgGtkBin
from .mrg_selection import MrgSelection


class MrgGtkWindow(MrgGtkBin):
    object = GObject.Property(type=Gtk.Window,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self._object = None
        self._position = None
        self._size = None
        self._is_maximized = None
        self._is_fullscreen = None
        self.selection = None

        super().__init__(**kwargs)

        self.connect("notify::object", self.__on_object_changed)

        self.selection = MrgSelection(app=self.app, window=self.object)

        self.property_ignore_list.add('modal')

    def __on_object_changed(self, obj, pspec):
        if self._object:
            self._object.destroy()

        self._object = self.object

        # Handle widget selection
        if self.selection:
            self.selection.window = self.object

        if self.object:
            self._update_name()

            # Make sure the user can not close the window
            if Gtk.MAJOR_VERSION == 4:
                self.object.connect('close-request', lambda o: True)
            else:
                self.object.connect('delete-event', lambda o, e: True)

            # Restore size
            if self._size and not self._is_maximized:
                self.object.set_default_size(*self._size)
            else:
                self.object.set_default_size(320, 240)

            # Disable modal at runtime
            self.object.props.modal = False

            # Always show toplevels windows
            if Gtk.MAJOR_VERSION == 4:
                self.object.show()
            else:
                self.object.show_all()

            # Add gtk version CSS class
            gtkversion = 'gtk4' if Gtk.MAJOR_VERSION == 4 else 'gtk3'
            self.object.get_style_context().add_class(gtkversion)

            self._restore_state()

        # keep track of size, position, and window state (maximized)
        self._save_state()

    def _update_name(self):
        if self.object is None:
            return

        # TODO: find a way to get object name instead of ID
        type_name = GObject.type_name(self.object.__gtype__)
        self.object.props.title = type_name

    def _save_state(self):
        if self.object is None:
            return

        self._is_maximized = self.object.is_maximized()

        if self._is_maximized:
            return

        if Gtk.MAJOR_VERSION == 4:
            # FIXME: this does not work, find a way to get the size of the window try map event
            self._size = [self.object.get_width(), self.object.get_height()]
        else:
            self._position = self.object.get_position()
            self._size = self.object.get_size()

    def _restore_state(self):
        if self._is_maximized:
            self.object.maximize()
            return

        if Gtk.MAJOR_VERSION == 4:
            # TODO: find a way to store position on gtk4
            pass
        else:
            if self._position:
                self.object.move(*self._position)

