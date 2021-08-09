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
from .cmb_type_info import CmbTypeInfo


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
        self._populate_layout_properties()
        self._populate_signals()

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

    def _populate_layout_properties_from_type(self, name):
        property_info = self.project.get_type_properties(name)
        if property_info is None:
            return

        # parent_id is stored in the DB so its better to cache it
        parent_id = self.parent_id
        for property_name in property_info:
            info = property_info[property_name]

            prop = CmbLayoutProperty(project=self.project,
                                     ui_id=self.ui_id,
                                     object_id=parent_id,
                                     child_id=self.object_id,
                                     owner_id=name,
                                     property_id=info.property_id,
                                     info=info)

            self.layout.append(prop)

    def _add_signal_object(self, signal):
        self.signals.append(signal)
        self.emit('signal-added', signal)
        self.project._object_signal_added(self, signal)

    def _populate_signals(self):
        c = self.project.db.cursor()

        # Populate signals
        for row in c.execute('SELECT * FROM object_signal WHERE ui_id=? AND object_id=?;',
                             (self.ui_id, self.object_id)):
            self._add_signal_object(CmbSignal.from_row(self.project, *row))

    def _populate_layout_properties(self):
        parent_id = self.parent_id

        if parent_id > 0:
            parent = self.project._get_object_by_id(self.ui_id, parent_id)
            self._populate_layout_properties_from_type(f"{parent.type_id}LayoutChild")
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

        self._populate_layout_properties()

    def _add_signal(self, signal_pk, owner_id, signal_id, handler, detail=None, user_data=0, swap=False, after=False):
        signal = CmbSignal(project=self.project,
                           signal_pk=signal_pk,
                           ui_id=self.ui_id,
                           object_id=self.object_id,
                           owner_id=owner_id,
                           signal_id=signal_id,
                           handler=handler,
                           detail=detail,
                           user_data=user_data,
                           swap=swap,
                           after=after)

        self._add_signal_object(signal)

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
            print('add_signal', e)
            return None
        else:
            return self._add_signal(signal_pk,
                                    owner_id,
                                    signal_id,
                                    handler,
                                    detail=detail,
                                    user_data=user_data,
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
            print('remove_signal', e)
            return False
        else:
            self._remove_signal(signal)
            return True
