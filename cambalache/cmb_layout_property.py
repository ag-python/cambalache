#
# Cambalache Layout Property wrapper
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
from gi.repository import GObject

from .cmb_objects_base import CmbBaseLayoutProperty, CmbPropertyInfo


class CmbLayoutProperty(CmbBaseLayoutProperty):
    object = GObject.Property(type=GObject.GObject, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    info = GObject.Property(type=CmbPropertyInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        self._init = True
        super().__init__(**kwargs)
        self._init = False

    @GObject.property(type=str)
    def value(self):
        c = self.project.db.execute("SELECT value FROM object_layout_property WHERE ui_id=? AND object_id=? AND child_id=? AND owner_id=? AND property_id=?;",
                                    (self.ui_id,
                                     self.object_id,
                                     self.child_id,
                                     self.owner_id,
                                     self.property_id))
        row = c.fetchone()
        return row[0] if row is not None else self.info.default_value

    @value.setter
    def _set_value(self, value):
        c = self.project.db.cursor()

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
            self.object._layout_property_changed(self)

        c.close()

