#
# Cambalache controller object
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
from gi.repository import GObject, CambalachePrivate
from . import utils


class MrgController(GObject.Object):

    app = GObject.Property(type=GObject.GObject,
                           flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    object = GObject.Property(type=GObject.GObject,
                              flags=GObject.ParamFlags.READWRITE)

    toplevel = GObject.Property(type=bool, default=False,
                                flags=GObject.ParamFlags.READWRITE)

    selected = GObject.Property(type=bool, default=False,
                                flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        # Properties in this will will be ignored by set_object_property()
        self.property_ignore_list = set()

        self.ui_id = 0
        self.object_id = 0

        super().__init__(**kwargs)
        self.connect("notify::object", self.__on_object_changed)
        self.on_object_changed()

    def on_object_changed(self):
        if self.object:
            ui_id, object_id = utils.object_get_id(self.object).split('.')
            self.ui_id = int(ui_id)
            self.object_id = int(object_id)
        else:
            self.ui_id = 0
            self.object_id = 0

    def __on_object_changed(self, obj, pspec):
        self.on_object_changed()

    # Object set property wrapper
    def set_object_property(self, name, value):
        if self.object and name not in self.property_ignore_list:
            if type(value) == str:
                CambalachePrivate.object_set_property_from_string(self.object, name, value)
            else:
                self.object.set_property(name, value)


