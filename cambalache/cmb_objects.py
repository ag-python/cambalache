#
# Cambalache Object wrappers
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject

from .cmb_objects_base import *


class CmbUI(CmbBaseUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CmbProperty(CmbBaseProperty):
    def __init__(self, **kwargs):
        self._init = True
        super().__init__(**kwargs)
        self._init = False

    @GObject.property(type=str)
    def value(self):
        c = self.project.conn.execute("SELECT value FROM object_property WHERE ui_id=? AND object_id=? AND owner_id=? AND property_id=?;",
                                        (self.ui_id,
                                         self.object_id,
                                         self.owner_id,
                                         self.property_id))
        row = c.fetchone()
        return row[0] if row is not None else None

    @value.setter
    def _set_value(self, value):
        c = self.project.conn.cursor()

        if value is None:
            c.execute("DELETE FROM object_property WHERE ui_id=? AND object_id=? AND owner_id=? AND property_id=?;",
                      (self.ui_id, self.object_id, self.owner_id, self.property_id))
        else:
            c.execute("SELECT count(ui_id) FROM object_property WHERE ui_id=? AND object_id=? AND owner_id=? AND property_id=?;",
                      (self.ui_id, self.object_id, self.owner_id, self.property_id))
            count = c.fetchone()[0]

            if count > 0:
               c.execute("UPDATE object_property SET value=? WHERE ui_id=? AND object_id=? AND owner_id=? AND property_id=?;",
                          (value, self.ui_id, self.object_id, self.owner_id, self.property_id))
            else:
               c.execute("INSERT INTO object_property (ui_id, object_id, owner_id, property_id, value) VALUES (?, ?, ?, ?, ?);",
                          (self.ui_id, self.object_id, self.owner_id, self.property_id, value))

        if self._init == False:
            self.project._object_property_changed(self.ui_id, self.object_id, self.property_id)

        c.close()


class CmbObject(CmbBaseObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.properties = []
        self.property_info = {}
        self.signals = []

        if self.project is None:
            return

        self._populate_properties()

    def _populate_type_properties(self, name):
        property_info = self.project.get_type_properties(name)
        if property_info is None:
            return

        c = self.project.conn.cursor()

        for property_name in property_info:
            info = property_info[property_name]
            c.execute("SELECT value FROM object_property WHERE ui_id=? AND object_id=? AND owner_id=? AND property_id=?;",
                       (self.ui_id, self.object_id, name, info.property_id))
            val = c.fetchone()
            prop = CmbProperty(project=self.project,
                               ui_id=self.ui_id,
                               object_id=self.object_id,
                               owner_id=name,
                               property_id=info.property_id,
                               value=val[0] if val is not None else None)

            self.properties.append(prop)
            self.property_info[property_name] = info

        c.close()

    def _populate_properties(self):
        c = self.project.conn.cursor()

        self._populate_type_properties(self.type_id)
        for row in c.execute('SELECT parent_id FROM type_tree WHERE type_id=?',
                             (self.type_id, )):
            self._populate_type_properties(row[0])

        c.close()

