# GtkGrid Controller
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
from gi.repository import GObject, Gtk

from .mrg_gtk_widget import MrgGtkWidget
from merengue import MrgPlaceholder, getLogger, utils

logger = getLogger(__name__)


class MrgGtkGrid(MrgGtkWidget):
    object = GObject.Property(type=Gtk.Grid, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if Gtk.MAJOR_VERSION == 4:
            self._packing = ['column', 'row', 'column-span', 'row-span']
        else:
            self._packing = ['left-attach', 'top-attach', 'width', 'height']

        self.width = None
        self.height = None

        self.connect("notify::object", self.__on_object_changed)
        self.__on_object_changed(None, None)

    def __get_size(self, ignore_placeholders=False):
        w = 0
        h = 0

        for child in self.get_children():
            if ignore_placeholders and isinstance(child, MrgPlaceholder):
                continue
            x, y, width, height = self.child_get(child, self._packing)
            w = max(x + width, w)
            h = max(y + height, h)

        return (w, h)

    def __cleanup_placeholders(self):
        # Remove all placeholders
        children = self.get_children()
        for child in children:
            if isinstance(child, MrgPlaceholder):
                self.object.remove(child)

    def __ensure_placeholders(self, width, height):
        if self.object is None:
            return

        self.__cleanup_placeholders()

        for x in range(width):
            for y in range(height):
                if self.object.get_child_at(x, y) is None:
                    placeholder = MrgPlaceholder(visible=True, controller=self)
                    self.object.attach(placeholder, x, y, 1, 1)

        # Save size for rebuild
        self.width = width
        self.height = height

    def __on_object_changed(self, obj, pspec):
        width, height = self.__get_size()

        if self.width is None:
            self.width = width if width else 3
            self.height = height if width else 3

        self.__ensure_placeholders(max(width, self.width), max(height, self.height))

    def get_child_position(self, child):
        x, y, w, h = self.child_get(child, self._packing)
        return x * y

    def get_child_layout(self, child, layout):
        for prop in self._packing:
            layout[prop] = self.child_get(child, [prop])[0]

        return super().get_child_layout(child, layout)

    def add_placeholder(self, mod):
        width, height = self.__get_size()

        if mod:
            height += 1
        else:
            width += 1

        self.__ensure_placeholders(max(width, 1), max(height, 1))

    def remove_placeholder(self, mod):
        width, height = self.__get_size()
        width_np, height_np = self.__get_size(ignore_placeholders=True)

        if mod:
            height = max(height-1, height_np)
        else:
            width = max(width-1, width_np)

        self.__ensure_placeholders(max(width, 1), max(height, 1))
