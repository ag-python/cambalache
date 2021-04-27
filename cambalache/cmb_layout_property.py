#
# Cambalache Layout Property wrapper
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject

from .cmb_objects_base import CmbBaseLayoutProperty, CmbPropertyInfo


class CmbLayoutProperty(CmbBaseLayoutProperty):
    info = GObject.Property(type=CmbPropertyInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        self._init = True
        super().__init__(**kwargs)
        self._init = False

    @GObject.property(type=str)
    def value(self):
        c = self.project.conn.execute("SELECT value FROM object_layout_property WHERE ui_id=? AND object_id=? AND child_id=? AND owner_id=? AND property_id=?;",
                                        (self.ui_id,
                                         self.object_id,
                                         self.child_id,
                                         self.owner_id,
                                         self.property_id))
        row = c.fetchone()
        return row[0] if row is not None else self.info.default_value

    @value.setter
    def _set_value(self, value):
        c = self.project.conn.cursor()

        if value is None or value == self.info.default_value:
            c.execute("DELETE FROM object_layout_property WHERE ui_id=? AND object_id=? AND child_id=? AND owner_id=? AND property_id=?;",
                      (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id))
        else:
            c.execute("SELECT count(ui_id) FROM object_layout_property WHERE ui_id=? AND object_id=? AND child_id=? AND  owner_id=? AND property_id=?;",
                      (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id))
            count = c.fetchone()[0]

            if count > 0:
               c.execute("UPDATE object_layout_property SET value=? WHERE ui_id=? AND object_id=? AND child_id=? AND  owner_id=? AND property_id=?;",
                          (value, self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id))
            else:
               c.execute("INSERT INTO object_layout_property (ui_id, object_id, child_id, owner_id, property_id, value) VALUES (?, ?, ?, ?, ?, ?);",
                          (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id, value))

        if self._init == False:
            self.project._object_layout_property_changed(self.ui_id,
                                                         self.object_id,
                                                         self.child_id,
                                                         self)

        c.close()

