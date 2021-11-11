# GtkLabel Controller
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
from merengue import getLogger, utils

logger = getLogger(__name__)


class MrgGtkLabelController(MrgGtkWidgetController):
    object = GObject.Property(type=Gtk.Label, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect("notify::object", self.__on_object_changed)
        self.__init_label()

    def __init_label(self):
        if self.object is None:
            return

        # Ensure a label so that it can be selected in the workspace
        self.object.set_label('<label>')

    def __on_object_changed(self, obj, pspec):
        self.__init_label()

    def set_object_property(self, name, value):
        if name == 'label' and value == '':
            self.__init_label()
            return

        super().set_object_property(name, value)
