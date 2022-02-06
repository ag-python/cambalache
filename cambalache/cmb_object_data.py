#
# Cambalache Object Data wrapper
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

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_objects_base import CmbBaseObjectData
from .cmb_type_info import CmbTypeDataInfo
from cambalache import getLogger

logger = getLogger(__name__)

class CmbObjectData(CmbBaseObjectData):
    object = GObject.Property(type=GObject.Object, flags = GObject.ParamFlags.READWRITE)
    info = GObject.Property(type=CmbTypeDataInfo, flags = GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self.args = []
        self.children = []

        super().__init__(**kwargs)

        if self.project is None:
            return

        self.__populate_children()

    def __str__(self):
        return f'CmbObjectData<{self.owner_id}> {self.ui_id}:{self.object_id} {self.data_id} {self.id}'

    def get_arg(self, key):
        c = self.project.db.execute("SELECT value FROM object_data_arg WHERE ui_id=? AND object_id=? AND owner_id=? AND data_id=? AND key=?;",
                                    (self.ui_id,
                                     self.object_id,
                                     self.owner_id,
                                     self.data_id,
                                     key))
        row = c.fetchone()
        return row[0] if row is not None else None

    def set_arg(self, key, value):
        c = self.project.db.cursor()

        try:
            if value is None:
                c.execute("DELETE FROM object_data_arg WHERE ui_id=? AND object_id=? AND owner_id=? AND data_id=? AND id=? AND key=?;",
                          (self.ui_id, self.object_id, self.owner_id, self.data_id, self.id, key))
            else:
                c.execute("REPLACE INTO object_data_arg (ui_id, object_id, owner_id, data_id, id, key, value) VALUES (?, ?, ?, ?, ?, ?, ?);",
                          (self.ui_id, self.object_id, self.owner_id, self.data_id, self.id, key, str(value)))
        except Exception as e:
            logger.warning(f'{self} Error setting arg {key}={value}: {e}')

        c.close()

    def __add_child(self, child):
        self.children.append(child)

        # TODO: add necessary signals
        #self.emit('child-added', child)
        #self.project._object_data_child_added(self, )

    def __populate_children(self):
        c = self.project.db.cursor()

        # Populate children
        for row in c.execute('SELECT * FROM object_data WHERE ui_id=? AND object_id=? AND owner_id=? AND parent_id=?;',
                             (self.ui_id,
                              self.object_id,
                              self.owner_id,
                              self.id)):
            obj = CmbObjectData.from_row(self.project, *row)
            obj.object = self.object
            obj.info = self.info.children.get(row[3])
            self.__add_child(obj)

    def add_data(self, data_key, value=None, comment=None):
        try:
            value = str(value) if value is not None else None
            taginfo = self.info.children.get(data_key)
            owner_id = taginfo.owner_id
            data_id = taginfo.data_id
            id = self.project.db.object_add_data(self.ui_id, self.object_id, owner_id, data_id, value, self.id, comment)
        except Exception as e:
            logger.warning(f'{self} Error adding child data {data_key}: {e}')
            return None
        else:
            new_data = CmbObjectData(project=self.project,
                                     object=self.object,
                                     info=taginfo,
                                     ui_id=self.ui_id,
                                     object_id=self.object_id,
                                     owner_id=owner_id,
                                     data_id=data_id,
                                     id=id,
                                     value=value,
                                     parent_id=self.id,
                                     comment=comment)
            self.__add_child(new_data)
            return new_data

    def remove_data(self, data):
        try:
            assert data in self.children
            self.project.db.execute("DELETE FROM object_data WHERE ui_id=? AND object_id=? AND owner_id=? AND data_id=? AND id=?;",
                                    (self.ui_id, self.object_id, data.owner_id, data.data_id, data.id))
            self.project.db.commit()
        except Exception as e:
            logger.warning(f'{self} Error removing data {data}: {e}')
            return False
        else:
            self.children.remove(data)

            # TODO: add necessary signals
            #self.emit('child-removed', child)
            #self.project._object_data_child_removed(self, )
            return True
