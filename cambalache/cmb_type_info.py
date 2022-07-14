#
# Cambalache Type Info wrapper
#
# Copyright (C) 2021-2022  Juan Pablo Ugarte
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

from .cmb_objects_base import CmbBaseTypeInfo, CmbBaseTypeDataInfo, CmbBaseTypeDataArgInfo, CmbTypeChildInfo, CmbPropertyInfo, CmbSignalInfo


class CmbTypeDataArgInfo(CmbBaseTypeDataArgInfo):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CmbTypeDataInfo(CmbBaseTypeDataInfo):
    def __init__(self, **kwargs):
        self.args = {}
        self.children = {}
        super().__init__(**kwargs)


class CmbTypeInfo(CmbBaseTypeInfo):
    type_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)
    parent_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)
    parent = GObject.Property(type=GObject.Object, flags = GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.hierarchy = self.__init_hierarchy()
        self.interfaces = self.__init_interfaces()
        self.properties = self.__init_properties_signals(CmbPropertyInfo, 'property')
        self.signals = self.__init_properties_signals(CmbSignalInfo, 'signal')
        self.data = self.__init_data()

        if self.parent_id == 'enum':
            self.enum = self.__init_enum_flags('enum')
        elif self.parent_id == 'flags':
            self.flags = self.__init_enum_flags('flags')

        self.child_types = self.__init_child_type()

        self.instantiable = self.is_a('GObject') and not self.abstract

    def __init_hierarchy(self):
        retval = []

        c = self.project.db.cursor()
        for row in c.execute('''
                    WITH RECURSIVE ancestor(type_id, generation, parent_id) AS (
                      SELECT type_id, 1, parent_id FROM type
                        WHERE parent_id IS NOT NULL AND
                              parent_id != 'interface' AND
                              parent_id != 'enum' AND
                              parent_id != 'flags' AND
                              type_id=?
                      UNION ALL
                      SELECT ancestor.type_id, generation + 1, type.parent_id
                        FROM type
                        JOIN ancestor ON type.type_id = ancestor.parent_id
                        WHERE type.parent_id IS NOT NULL AND
                            type.parent_id != 'object' AND
                            ancestor.type_id=?
                    )
                    SELECT parent_id, generation FROM ancestor
                    UNION
                    SELECT type_iface.iface_id, 0
                      FROM ancestor JOIN type_iface
                      WHERE ancestor.type_id = type_iface.type_id
                    ORDER BY generation;''',
                             (self.type_id, self.type_id)):
            retval.append(row[0])

        c.close()

        return retval

    def __init_interfaces(self):
        retval = []

        c = self.project.db.cursor()
        for row in c.execute(f'SELECT iface_id FROM type_iface WHERE type_id=? ORDER BY iface_id;',
                             (self.type_id, )):
            retval.append(row[0])

        c.close()
        return retval

    def __init_properties_signals(self, Klass, table):
        retval = {}

        c = self.project.db.cursor()
        for row in c.execute(f'SELECT * FROM {table} WHERE owner_id=? ORDER BY {table}_id;',
                             (self.type_id, )):
            retval[row[1]] = Klass.from_row(self, *row)

        c.close()
        return retval

    def __type_get_data(self, owner_id, data_id, parent_id, key, type_id):
        args = {}
        children = {}
        parent_id = parent_id if parent_id is not None else 0
        retval = CmbTypeDataInfo.from_row(self, owner_id, data_id, parent_id, key, type_id)

        c = self.project.db.cursor()

        # Collect Arguments
        for row in c.execute('SELECT * FROM type_data_arg WHERE owner_id=? AND data_id=?;',
                             (owner_id, data_id)):
            _key = row[2]
            args[_key] = CmbTypeDataArgInfo.from_row(self, *row)

        # Recurse children
        for row in c.execute('SELECT * FROM type_data WHERE owner_id=? AND parent_id=?;',
                             (owner_id, data_id)):
            _key = row[3]
            children[_key] = self.__type_get_data(*row)

        c.close()

        retval.args = args
        retval.children = children

        return retval

    def __init_data(self):
        retval = {}

        c = self.project.db.cursor()
        for row in c.execute('SELECT * FROM type_data WHERE parent_id IS NULL AND owner_id=? ORDER BY data_id;',
                             (self.type_id, )):
            key = row[3]
            retval[key] = self.__type_get_data(*row)

        c.close()
        return retval

    def __init_child_type(self):
        retval = {}

        c = self.project.db.cursor()
        for row in c.execute('SELECT * FROM type_child_type WHERE type_id=?;',
                             (self.type_id, )):
            type_id, child_type, max_children, linked_property_id = row
            retval[child_type] = CmbTypeChildInfo(project=self.project,
                                                  type_id=type_id,
                                                  child_type=child_type,
                                                  max_children=max_children if max_children else 0,
                                                  linked_property_id=linked_property_id)

        c.close()
        return retval

    def __init_enum_flags(self, name):
        retval = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_INT)

        c = self.project.db.cursor()
        for row in c.execute(f'SELECT name, nick, value FROM type_{name} WHERE type_id=?', (self.type_id,)):
            retval.append(row)

        c.close()
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
