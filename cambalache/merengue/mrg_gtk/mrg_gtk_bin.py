# GtkBin Controller
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
from merengue import MrgPlaceholder


class MrgGtkBinController(MrgGtkWidgetController):
    object = GObject.Property(type=Gtk.Bin if Gtk.MAJOR_VERSION == 3 else Gtk.Widget,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect("notify::object", self.__on_object_changed)
        self.__on_object_changed(self.object, None)

    def add(self, child):
        if self.object is None:
            return

        if Gtk.MAJOR_VERSION == 3:
            self.object.add(child)
        else:
            self.object.set_child(child)

    def __update_placeholder(self):
        if self.object is None:
            return

        child = self.object.get_child()

        if child is None:
            self.add(MrgPlaceholder(visible=True, controller=self))

    def __on_object_changed(self, obj, pspec):
        self.__update_placeholder()

