#
# Cambalache Type Info wrapper
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
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_objects_base import CmbBaseTypeInfo, CmbBaseTypeDataInfo, CmbBaseTypeDataArgInfo, CmbTypeChildInfo


class CmbTypeDataArgInfo(CmbBaseTypeDataArgInfo):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CmbTypeDataInfo(CmbBaseTypeDataInfo):
    def __init__(self, **kwargs):
        self.args = {}
        self.children = {}
        super().__init__(**kwargs)


class CmbTypeInfo(CmbBaseTypeInfo):
    parent = GObject.Property(type=GObject.Object, flags = GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self.hierarchy = []
        self.properties = {}
        self.signals = {}
        self.data = {}
        super().__init__(**kwargs)

        if self.parent_id == 'enum':
            self.enum = self.__init_enum_flags('enum')
        elif self.parent_id == 'flags':
            self.flags = self.__init_enum_flags('flags')

        self.child_types = self.__init_child_type()

    def __init_child_type(self):
        retval = {}

        for row in self.project.db.execute('SELECT * FROM type_child_type WHERE type_id=?',
                                           (self.type_id, )):
            type_id, child_type, max_children, linked_property_id = row
            retval[child_type] = CmbTypeChildInfo(project=self.project,
                                                  type_id=type_id,
                                                  child_type=child_type,
                                                  max_children=max_children if max_children else 0,
                                                  linked_property_id=linked_property_id)

        return retval if len(retval.keys()) else None

    def __init_enum_flags(self, name):
        retval = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_INT)

        for row in self.project.db.execute(f'SELECT name, nick, value FROM type_{name} WHERE type_id=?', (self.type_id,)):
            retval.append(row)

        return retval

    def is_a(self, type_id):
        return self.type_id == type_id or type_id in self.hierarchy

    def get_data_info(self, name):
        parent = self
        while parent:
            if name in parent.data:
                return parent.data[name]

            parent = parent.parent

        return None

    def has_child_types(self):
        parent = self
        while parent:
            if parent.child_types:
                return True
            parent = parent.parent

        return False
