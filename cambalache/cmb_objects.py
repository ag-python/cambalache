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
    info = GObject.Property(type=CmbPropertyInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

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
        return row[0] if row is not None else self.info.default_value

    @value.setter
    def _set_value(self, value):
        c = self.project.conn.cursor()

        if value is None or value == self.info.default_value:
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
                                         self.object_id,
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
                                                         self.property_id)

        c.close()


class CmbTypeInfo(CmbBaseTypeInfo):
    def __init__(self, **kwargs):
        self.hierarchy = []
        super().__init__(**kwargs)


class CmbObject(CmbBaseObject):
    info = GObject.Property(type=CmbTypeInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        self.properties = []
        self.layout = []
        self.signals = []

        super().__init__(**kwargs)

        if self.project is None:
            return

        self._populate_properties()

    def _populate_type_properties(self, name):
        property_info = self.project.get_type_properties(name)
        if property_info is None:
            return

        for property_name in property_info:
            info = property_info[property_name]

            prop = CmbProperty(project=self.project,
                               ui_id=self.ui_id,
                               object_id=self.object_id,
                               owner_id=name,
                               property_id=info.property_id,
                               info=info)

            self.properties.append(prop)

    def _populate_properties(self):
        self._populate_type_properties(self.type_id)
        for parent_id in self.info.hierarchy:
            self._populate_type_properties(parent_id)

    def _populate_layout_properties(self, name):
        property_info = self.project.get_type_properties(name)
        if property_info is None:
            return

        for property_name in property_info:
            info = property_info[property_name]

            prop = CmbLayoutProperty(project=self.project,
                                     ui_id=self.ui_id,
                                     object_id=self.parent_id,
                                     child_id=self.object_id,
                                     owner_id=name,
                                     property_id=info.property_id,
                                     info=info)

            self.layout.append(prop)

    @GObject.Property(type=int)
    def parent_id(self):
        return self._parent_id

    @parent_id.setter
    def _set_parent_id(self, parent_id):
        self._parent_id = parent_id

        if parent_id > 0:
            parent = self.project._get_object_by_id(self.ui_id, parent_id)
            self._populate_layout_properties(f'{parent.type_id}LayoutChild')
        else:
            self.layout = []

