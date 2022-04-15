#
# Cambalache Object wrapper
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

from .cmb_objects_base import CmbBaseObject, CmbSignal
from .cmb_property import CmbProperty
from .cmb_layout_property import CmbLayoutProperty
from .cmb_object_data import CmbObjectData
from .cmb_type_info import CmbTypeInfo
from .cmb_ui import CmbUI
from cambalache import getLogger

logger = getLogger(__name__)

class CmbObject(CmbBaseObject):
    info = GObject.Property(type=CmbTypeInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    __gsignals__ = {
        'property-changed': (GObject.SignalFlags.RUN_FIRST, None, (CmbProperty, )),

        'layout-property-changed': (GObject.SignalFlags.RUN_FIRST, None, (GObject.GObject, CmbLayoutProperty)),

        'signal-added': (GObject.SignalFlags.RUN_FIRST, None, (CmbSignal, )),

        'signal-removed': (GObject.SignalFlags.RUN_FIRST, None, (CmbSignal, ))
    }

    def __init__(self, **kwargs):
        self.properties = []
        self.properties_dict = {}
        self.layout = []
        self.layout_dict = {}
        self.signals = []
        self.data = []
        self.position_layout_property = None

        super().__init__(**kwargs)

        self.connect('notify', self.__on_notify)

        if self.project is None:
            return

        self.__populate_properties()
        self.__populate_layout_properties()
        self.__populate_signals()

    def __str__(self):
        return f'CmbObject<{self.type_id}> {self.ui_id}:{self.object_id}'

    def __populate_type_properties(self, name):
        property_info = self.project.get_type_properties(name)
        if property_info is None:
            return

        for property_name in property_info:
            info = property_info[property_name]

            prop = CmbProperty(object=self,
                               project=self.project,
                               ui_id=self.ui_id,
                               object_id=self.object_id,
                               owner_id=name,
                               property_id=info.property_id,
                               info=info)

            # List of property
            self.properties.append(prop)

            # Dictionary of properties
            self.properties_dict[property_name] = prop

    def __populate_properties(self):
        self.__populate_type_properties(self.type_id)
        for parent_id in self.info.hierarchy:
            self.__populate_type_properties(parent_id)

    def __populate_layout_properties_from_type(self, name):
        property_info = self.project.get_type_properties(name)
        if property_info is None:
            return

        # parent_id is stored in the DB so its better to cache it
        parent_id = self.parent_id
        for property_name in property_info:
            info = property_info[property_name]

            prop = CmbLayoutProperty(object=self,
                                     project=self.project,
                                     ui_id=self.ui_id,
                                     object_id=parent_id,
                                     child_id=self.object_id,
                                     owner_id=name,
                                     property_id=info.property_id,
                                     info=info)

            # Keep a reference to the position layout property
            if info.is_position:
                self.position_layout_property = prop

            self.layout.append(prop)

            # Dictionary of properties
            self.layout_dict[property_name] = prop

    def _property_changed(self, prop):
        self.emit('property-changed', prop)
        self.project._object_property_changed(self, prop)

    def _layout_property_changed(self, prop):
        parent = self.project.get_object_by_id(self.ui_id, self.parent_id)
        self.emit('layout-property-changed', parent, prop)
        self.project._object_layout_property_changed(parent, self, prop)

    def __add_signal_object(self, signal):
        self.signals.append(signal)
        self.emit('signal-added', signal)
        self.project._object_signal_added(self, signal)

    def __on_notify(self, obj, pspec):
        self.project._object_changed(self, pspec.name)

    def __populate_signals(self):
        c = self.project.db.cursor()

        # Populate signals
        for row in c.execute('SELECT * FROM object_signal WHERE ui_id=? AND object_id=?;',
                             (self.ui_id, self.object_id)):
            self.__add_signal_object(CmbSignal.from_row(self.project, *row))

    def __populate_layout_properties(self):
        parent_id = self.parent_id

        if parent_id > 0:
            parent = self.project.get_object_by_id(self.ui_id, parent_id)
            self.__populate_layout_properties_from_type(f"{parent.type_id}LayoutChild")
        else:
            self.layout = []

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

        self.__populate_layout_properties()

    @GObject.Property(type=CmbUI)
    def ui(self):
        return self.project.get_object_by_id(self.ui_id)

    @GObject.Property(type=GObject.Object)
    def parent(self):
        return self.project.get_object_by_id(self.ui_id, self.parent_id)

    def _add_signal(self, signal_pk, owner_id, signal_id, handler, detail=None, user_data=0, swap=False, after=False):
        signal = CmbSignal(project=self.project,
                           signal_pk=signal_pk,
                           ui_id=self.ui_id,
                           object_id=self.object_id,
                           owner_id=owner_id,
                           signal_id=signal_id,
                           handler=handler,
                           detail=detail,
                           user_data=user_data if user_data is not None else 0,
                           swap=swap,
                           after=after)

        self.__add_signal_object(signal)

        return signal

    def add_signal(self, owner_id, signal_id, handler, detail=None, user_data=0, swap=False, after=False):
        try:
            c = self.project.db.cursor()
            c.execute("INSERT INTO object_signal (ui_id, object_id, owner_id, signal_id, handler, detail, user_data, swap, after) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                      (self.ui_id, self.object_id, owner_id, signal_id, handler, detail, user_data, swap, after))
            signal_pk = c.lastrowid
            c.close()
            self.project.db.commit()
        except Exception as e:
            logger.warning(f'Error adding signal handler {owner_id}:{signal_id} {handler} to object {self.ui_id}.{{self.object_id}} {e}')
            return None
        else:
            return self._add_signal(signal_pk,
                                    owner_id,
                                    signal_id,
                                    handler,
                                    detail=detail,
                                    user_data=user_data if user_data is not None else 0,
                                    swap=swap,
                                    after=after)

    def _remove_signal(self, signal):
        self.signals.remove(signal)
        self.emit('signal-removed', signal)
        self.project._object_signal_removed(self, signal)

    def remove_signal(self, signal):
        try:
            self.project.db.execute("DELETE FROM object_signal WHERE signal_pk=?;",
                                    (signal.signal_pk, ))
            self.project.db.commit()
        except Exception as e:
            logger.warning(f'Error removing signal handler {signal.owner_id}:{signal.signal_id} {signal.handler} from object {self.ui_id}.{{self.object_id}} {e}')
            return False
        else:
            self._remove_signal(signal)
            return True

    def add_data(self, data_key, value=None, comment=None):
        try:
            value = str(value) if value is not None else None
            taginfo = self.info.get_data_info(data_key)
            owner_id = taginfo.owner_id
            data_id = taginfo.data_id
            id = self.project.db.object_add_data(self.ui_id, self.object_id, owner_id, data_id, value, None, comment)
        except Exception as e:
            logger.warning(f'Error adding data {data_key} {e}')
            return None
        else:
            new_data = CmbObjectData(project=self.project,
                                     object=self,
                                     info=taginfo,
                                     ui_id=self.ui_id,
                                     object_id=self.object_id,
                                     owner_id=owner_id,
                                     data_id=data_id,
                                     id=id,
                                     value=value,
                                     comment=comment)
            self.data.append(new_data)
            return new_data

    def remove_data(self, data):
        try:
            assert data in self.data
            self.project.db.execute("DELETE FROM object_data WHERE ui_id=? AND object_id=? AND owner_id=? AND data_id=? AND id=?;",
                                    (self.ui_id, self.object_id, data.owner_id, data.data_id, data.id))
            self.project.db.commit()
        except Exception as e:
            logger.warning(f'{self} Error removing data {data}: {e}')
            return False
        else:
            self.data.remove(data)
            return True

    def reorder_child(self, child, position):
        if child is None:
            logger.warning(f'child has to be a CmbObject')
            return

        if self.ui_id != child.ui_id or self.object_id != child.parent_id:
            logger.warning(f'{child} is not children of {self}')
            return

        name = child.name if child.name is not None else child.type_id
        self.project.history_push(_('Reorder object {name} from position {old} to {new}').format(name=name, old=child.position, new=position))

        children = []

        # Get children in order
        c = self.project.db.cursor()
        for row in c.execute('''
            SELECT object_id, position
                FROM object
                WHERE ui_id=? AND parent_id=? AND internal IS NULL AND object_id!=?
                    AND object_id NOT IN (SELECT inline_object_id FROM object_property WHERE inline_object_id IS NOT NULL AND ui_id=? AND object_id=?)
                ORDER BY position;''', (self.ui_id, self.object_id, child.object_id, self.ui_id, self.object_id)):
            child_id, child_position = row

            obj = self.project.get_object_by_id(self.ui_id, child_id)
            if obj:
                children.append(obj)

        # Insert child in new position
        children.insert(position, child)

        # Update all positions
        for pos, obj in enumerate(children):
            # Sync layout property
            if obj.position_layout_property:
                obj.position_layout_property.value = pos
            else:
                # Or object position
                obj.position = pos

        c.close()
        self.project.history_pop()
