# GtkNotebook Controller
#
# Copyright (C) 2022  Juan Pablo Ugarte
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

from .mrg_gtk_widget import MrgGtkWidget
from merengue import MrgPlaceholder

from merengue import getLogger

logger = getLogger(__name__)


class MrgGtkNotebook(MrgGtkWidget):
    object = GObject.Property(type=Gtk.Notebook,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("notify::object", self.__on_object_changed)
        self.__ensure_placeholders()

    def get_children(self):
        if Gtk.MAJOR_VERSION == 4:
            return list(self.object.get_pages() if self.object else [])

        return super().get_children()

    def __get_placeholder(self):
        for child in self.get_children():
            if Gtk.MAJOR_VERSION == 4 and isinstance(child, Gtk.NotebookPage):
                child = child.get_child()

            if isinstance(child, MrgPlaceholder):
                return child
        return None

    def __ensure_placeholders(self):
        if self.object is None:
            return

        if len(self.get_children()) == 0:
            self.add(MrgPlaceholder(visible=True, controller=self))

    def __on_object_changed(self, obj, pspec):
        self.__ensure_placeholders()

    def show_child(self, child):
        if Gtk.MAJOR_VERSION == 4:
            if isinstance(child, Gtk.NotebookPage):
                position = child.props.position
            else:
                position = self.object.page_num(child)
        else:
            position = self.object.page_num(child)

        if position >= 0:
            self.object.set_current_page(position)

    def add(self, child):
        if self.object is None:
            return

        if Gtk.MAJOR_VERSION == 3:
            self.object.add(child)
        else:
            self.object.append_page(child, None)

    def remove_child(self, child):
        if self.object is None:
            return

        if Gtk.MAJOR_VERSION == 4:
            self.object.detach_tab(child)
        else:
            super().remove_child(child)

    def add_placeholder(self, mod):
        placeholder = self.__get_placeholder()

        if placeholder is None:
            placeholder = MrgPlaceholder(visible=True, controller=self)
            self.add(placeholder)

        self.show_child(placeholder)

    def remove_placeholder(self, mod):
        placeholder = self.__get_placeholder()
        if placeholder:
            self.remove_child(placeholder)
