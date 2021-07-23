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

from .mrg_gtk_widget import MrgGtkWidgetController
from .mrg_selection import MrgSelection

from merengue import utils


class MrgGtkWindowController(MrgGtkWidgetController):
    def __init__(self, **kwargs):
        self._object = None
        self._position = None
        self._size = None
        self._is_maximized = None
        self._is_fullscreen = None
        self.selection = None

        super().__init__(**kwargs)

        self.selection = MrgSelection(app=self.app, window=self.object)

        self.property_ignore_list.add('modal')

    @GObject.property(type=Gtk.Window)
    def object(self):
        return self._object

    @object.setter
    def _set_object(self, obj):
        # keep track of size, position, and window state (maximized)
        self._save_state()

        if self._object:
            self._object.destroy()

        self._object = obj

        # Handle widget selection
        if self.selection:
            self.selection.window = obj

        if obj:
            self._update_name()

            # Make sure the user can not close the window
            if Gtk.MAJOR_VERSION == 4:
                obj.connect('close-request', lambda o: True)
            else:
                obj.connect('delete-event', lambda o, e: True)

            # Restore size
            if self._size and not self._is_maximized:
                self.object.set_default_size(*self._size)

            # Disable modal at runtime
            obj.props.modal = False

            # Always show toplevels windows
            if Gtk.MAJOR_VERSION == 4:
                obj.show()
            else:
                obj.show_all()

            # Add gtk version CSS class
            gtkversion = 'gtk4' if Gtk.MAJOR_VERSION == 4 else 'gtk3'
            obj.get_style_context().add_class(gtkversion)

            self._restore_state()

    def _update_name(self):
        if self._object is None:
            return

        # TODO: finx a way to get object name instead of ID
        type_name = GObject.type_name(self._object.__gtype__)
        self._object.props.title = type_name

    def _save_state(self):
        if self._object is None:
            return

        self._is_maximized = self.object.is_maximized()

        if self._is_maximized:
            return

        if Gtk.MAJOR_VERSION == 4:
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

