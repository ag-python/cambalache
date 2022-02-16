# GtkCenterBox Controller
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

from .mrg_gtk_widget import MrgGtkWidgetController
from merengue import MrgPlaceholder, getLogger, utils

logger = getLogger(__name__)


class MrgGtkCenterBoxController(MrgGtkWidgetController):
    object = GObject.Property(type=Gtk.CenterBox, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size = None

        self.connect("notify::object", self.__on_object_changed)
        self.__ensure_placeholders()

    def __get_children(self):
        return [
            self.object.get_start_widget(),
            self.object.get_center_widget(),
            self.object.get_end_widget()
        ]

    def add(self, child):
        if self.object is None:
            return

    def get_child_type(self, child):
        start, center, end = self.__get_children()

        if start == child:
            return 'start'
        elif center == child:
            return 'center'
        elif end == child:
            return 'end'

    def __ensure_placeholders(self):
        if self.object is None:
            return

        start, center, end = self.__get_children()

        if start is None:
            self.object.set_start_widget(MrgPlaceholder(visible=True, controller=self))
        if center is None:
            self.object.set_center_widget(MrgPlaceholder(visible=True, controller=self))
        if end is None:
            self.object.set_end_widget(MrgPlaceholder(visible=True, controller=self))

    def __on_object_changed(self, obj, pspec):
        self.__ensure_placeholders()

    def remove_child(self, child):
        if self.object is None:
            return

        start, center, end = self.__get_children()

        if start == child:
            self.object.set_start_widget(None)
        elif center == child:
            self.object.set_center_widget(None)
        elif end == child:
            self.object.set_end_widget(None)

