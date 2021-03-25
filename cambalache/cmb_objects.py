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

    @GObject.Property(type=int)
    def template_id(self):
        retval = self.db_get('SELECT template_id FROM ui WHERE (ui_id) IS (?);',
                             (self.ui_id, ))
        return retval if retval is not None else 0

    @template_id.setter
    def _set_template_id(self, value):
        self.db_set('UPDATE ui SET template_id=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value if value != 0 else None)


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
                                                         self.property_id)

        c.close()


class CmbTypeInfo(CmbBaseTypeInfo):
    def __init__(self, **kwargs):
        self.hierarchy = []
        self.signals = []
        super().__init__(**kwargs)


class CmbObject(CmbBaseObject):
    info = GObject.Property(type=CmbTypeInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    __gsignals__ = {
        'signal-added': (GObject.SIGNAL_RUN_FIRST, None, (CmbSignal, )),

        'signal-removed': (GObject.SIGNAL_RUN_FIRST, None, (CmbSignal, ))
    }

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
        retval = self.db_get('SELECT parent_id FROM object WHERE (ui_id, object_id) IS (?, ?);',
                             (self.ui_id, self.object_id, ))
        return retval if retval is not None else 0

    @parent_id.setter
    def _set_parent_id(self, value):
        self.db_set('UPDATE object SET parent_id=? WHERE (ui_id, object_id) IS (?, ?);',
                    (self.ui_id, self.object_id, ),
                    value if value != 0 else None)

        if value > 0:
            parent = self.project._get_object_by_id(self.ui_id, value)
            self._populate_layout_properties(f'{parent.type_id}LayoutChild')
        else:
            self.layout = []

    def add_signal(self, owner_id, signal_id, handler, detail=None, user_data=None, swap=None, after=None):
        try:
            c = self.project.conn.cursor()
            c.execute("INSERT INTO object_signal (ui_id, object_id, owner_id, signal_id, handler, detail, user_data, swap, after) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                      (self.ui_id, self.object_id, owner_id, signal_id, handler, detail, user_data, swap, after))
            signal_pk = c.lastrowid
            c.close()
            self.project.conn.commit()
        except Exception as e:
            print('add_signal', e)
            return None
        else:
            signal = CmbSignal(project=self.project,
                               signal_pk=signal_pk,
                               ui_id=self.ui_id,
                               object_id=self.object_id,
                               owner_id=owner_id,
                               signal_id=signal_id,
                               handler=handler,
                               detail=detail,
                               user_data=0,
                               swap=swap,
                               after=after)
            self.signals.append(signal)
            self.emit('signal-added', signal)
            self.project._object_signal_added(self, signal)
            return signal

    def remove_signal(self, signal):
        try:
            self.project.conn.execute("DELETE FROM object_signal WHERE signal_pk=?;",
                                      (signal.signal_pk, ))
            self.project.conn.commit()
        except Exception as e:
            print('remove_signal', e)
            return False
        else:
            self.signals.remove(signal)
            self.emit('signal-removed', signal)
            self.project._object_signal_removed(self, signal)
            return True
