#
# CmbProject - Cambalache Project
#
# Copyright (C) 2020-2022  Juan Pablo Ugarte
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

import os
import sys
import gi
import time

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, GObject, Gtk

from lxml import etree

from .cmb_db import CmbDB
from .cmb_ui import CmbUI
from .cmb_object import CmbObject
from .cmb_property import CmbProperty
from .cmb_layout_property import CmbLayoutProperty
from .cmb_type_info import CmbTypeInfo
from .cmb_objects_base import CmbSignal
from .cmb_list_store import CmbListStore
from .config import *
from cambalache import getLogger

logger = getLogger(__name__)


class CmbProject(GObject.GObject, Gtk.TreeModel):
    __gtype_name__ = 'CmbProject'

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, None, ()),

        'ui-added': (GObject.SignalFlags.RUN_FIRST, None,
                     (CmbUI,)),

        'ui-removed': (GObject.SignalFlags.RUN_FIRST, None,
                       (CmbUI,)),

        'object-added': (GObject.SignalFlags.RUN_FIRST, None,
                         (CmbObject,)),

        'object-removed': (GObject.SignalFlags.RUN_FIRST, None,
                           (CmbObject,)),

        'object-changed': (GObject.SignalFlags.RUN_FIRST, None,
                           (CmbObject, str)),

        'object-property-changed': (GObject.SignalFlags.RUN_FIRST, None,
                                    (CmbObject, CmbProperty)),

        'object-layout-property-changed': (GObject.SignalFlags.RUN_FIRST, None,
                                           (CmbObject, CmbObject, CmbLayoutProperty)),

        'object-signal-added': (GObject.SignalFlags.RUN_FIRST, None,
                                (CmbObject, CmbSignal)),

        'object-signal-removed': (GObject.SignalFlags.RUN_FIRST, None,
                                  (CmbObject, CmbSignal)),

        'selection-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    target_tk = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)
    filename = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)

    undo_msg = GObject.Property(type=str)
    redo_msg = GObject.Property(type=str)

    def __init__(self, **kwargs):
        # Type Information
        self.type_info = {}

        # Selection
        self.__selection = []

        # Create TreeModel store
        self.__object_id = {}

        super().__init__(**kwargs)

        # Target from file take precedence over target_tk property
        if self.filename and os.path.isfile(self.filename):
            target_tk = CmbDB.get_target_from_file(self.filename)

            if target_tk is not None:
                self.target_tk = target_tk

        if self.target_tk is None or self.target_tk == '':
            raise Exception('Either target_tk or filename are required')

        # Use a TreeStore to hold object tree instead of using SQL for every
        # TreeStore call
        self.__store = Gtk.TreeStore(GObject.GObject)

        # Foward signals to CmbProject, this way the user can not add data to
        # the TreeModel using Gtk API
        self.__store.connect('row-changed', lambda o, p, i: self.row_changed(p, i))
        self.__store.connect('row-inserted', lambda o, p, i: self.row_inserted(p, i))
        self.__store.connect('row-has-child-toggled', lambda o, p, i: self.row_has_child_toggled(p, i))
        self.__store.connect('row-deleted', lambda o, p: self.row_deleted(p))
        self.__store.connect('rows-reordered', lambda o, p, i, n: self.rows_reordered(p, i, n))

        # DataModel is only used internally
        self.db = CmbDB(target_tk=self.target_tk)
        self.db.type_info = self.type_info
        self.__init_data()

        self.__load()

    @GObject.Property(type=bool, default=False)
    def history_enabled(self):
        return bool(self.db.get_data('history_enabled'))

    @history_enabled.setter
    def _set_history_enabled(self, value):
        self.db.set_data('history_enabled', value)

    @GObject.Property(type=int)
    def history_index_max(self):
        c = self.db.execute("SELECT MAX(history_id) FROM history;")
        row = c.fetchone()
        c.close()

        if row is None or row[0] is None:
            return 0

        return int(row[0])

    @GObject.Property(type=int)
    def history_index(self):
        history_index = int(self.db.get_data('history_index'))

        if history_index < 0:
            return self.history_index_max

        return history_index

    @history_index.setter
    def _set_history_index(self, value):
        if value == self.history_index_max:
            value = -1

        self.db.set_data('history_index', value)

    def _get_table_data(self, table):
        c = self.db.cursor()

        columns = []
        types = []
        pks = []

        for row in c.execute(f'PRAGMA table_info({table});'):
            col = row[1]
            col_type =  row[2]
            pk = row[5]

            if col_type == 'INTEGER':
                col_type = GObject.TYPE_INT
            elif col_type == 'TEXT':
                col_type = GObject.TYPE_STRING
            elif col_type == 'BOOLEAN':
                col_type = GObject.TYPE_BOOLEAN
            else:
                logger.warning(f'Unknown column type {col_type}')

            columns.append(col)
            types.append(col_type)

            if pk:
                pks.append(col)

        c.close()

        return {
            'names': columns,
            'types': types,
            'pks': pks
        }

    def __init_type_info(self, c):
        for row in c.execute('''SELECT * FROM type
                                  WHERE
                                    parent_id IS NOT NULL
                                  ORDER BY type_id;'''):
            type_id = row[0]
            self.type_info[type_id] = CmbTypeInfo.from_row(self, *row)

        # Set parent back reference
        for type_id in self.type_info:
            info = self.type_info[type_id]
            info.parent = self.type_info.get(info.parent_id, None)

    def __init_data(self):
        if self.target_tk is None:
            return

        c = self.db.cursor()

        self.__init_type_info(c)

        c.close()

    def __load(self):
        if self.filename is None or not os.path.isfile(self.filename):
            return

        self.history_enabled = False
        self.db.load(self.filename)
        self.history_enabled = True

        self.__populate_objects()

    def __populate_objects(self, ui_id=None):
        c = self.db.cursor()
        cc = self.db.cursor()

        if ui_id:
            rows = c.execute('SELECT * FROM ui WHERE ui_id=?;', (ui_id, ))
        else:
            rows = c.execute('SELECT * FROM ui;')

        # Populate tree view
        for row in rows:
            ui_id = row[0]
            self.__add_ui(False, *row)

            # Update UI objects
            for obj in cc.execute('SELECT * FROM object WHERE ui_id=?;', (ui_id, )):
                self.__add_object(False, *obj)

        c.close()
        cc.close()

    def save(self):
        self.db.save(self.filename)

    def __get_import_errors(self):
        errors = self.db.errors

        if not len(errors):
            return (None, None)

        msgs = []
        detail_msg = []

        msgs_strings = {
            'unknown-type': (_("one unknown class '{detail}'"), _("{n} unknown classes ({detail})")),
            'unknown-property': (_("one unknown property '{detail}'"), _("{n} unknown properties ({detail})")),
            'unknown-signal': (_("one unknown signal '{detail}'"), _("{n} unknown signals ({detail})")),
            'unknown-tag': (_("one unknown tag '{detail}'"), _("{n} unknown tags ({detail})")),
            'unknown-attr': (_("one unknown attribute '{detail}'"), _("{n} unknown attributes ({detail})")),
            'missing-tag': (_("one missing attribute '{detail}'"), _("{n} missing attributes ({detail})"))
        }

        detail_strings = {
            'unknown-type': _("xml:{line} unknown class '{detail}'"),
            'unknown-property': _("xml:{line} unknown property '{detail}'"),
            'unknown-signal': _("xml:{line} unknown signal '{detail}'"),
            'unknown-tag': _("xml:{line} unknown tag '{detail}'"),
            'unknown-attr': _("xml:{line} unknown attribute '{detail}'"),
            'missing-tag': _("xml:{line} missing attribute '{detail}'")
        }

        detail = []

        # Line by line details
        for error_type in errors:
            error = errors[error_type]

            # Error summary
            n = len(error)
            list = ', '.join(error.keys())
            msgs.append(N_(*msgs_strings[error_type], n).format(n=n, detail=list))

            # Error details
            for key in error:
                lines = error[key]
                for line in lines:
                    detail.append((line, error_type, key))

        # Sort errors by line
        detail = sorted(detail, key=lambda x: x[0])

        # Generate errors by line
        for line, error_type, key in detail:
            detail_msg.append(detail_strings[error_type].format(line=line, detail=key))

        return (msgs, detail_msg)

    def import_file(self, filename, overwrite=False):
        start = time.monotonic()

        self.history_push(_('Import file "{filename}"').format(filename=filename))

        # Remove old UI
        if overwrite:
            c.execute("DELETE FROM ui WHERE filename=?;", (filename, ))

        # Import file
        ui_id = self.db.import_file(filename, os.path.dirname(self.filename))

        import_end = time.monotonic()

        # Populate UI
        self.__populate_objects(ui_id)

        self.history_pop()

        logger.info('Import took: {import_end - start}')
        logger.info('UI update: {time.monotonic() - import_end}')

        # Get parsing errors
        msgs, detail_msg = self.__get_import_errors()
        self.db.errors = None

        ui = self.get_object_by_id(ui_id)

        return (ui, msgs, detail_msg)

    def __export(self, ui_id, filename, dirname=None):
        if not os.path.isabs(filename):
            if dirname is None:
                dirname = os.path.dirname(self.filename)
            filename = os.path.join(dirname, filename)

        # Get XML tree
        ui = self.db.export_ui(ui_id)

        # Dump xml to file
        with open(filename, 'wb') as fd:
            ui.write(fd,
                     pretty_print=True,
                     xml_declaration=True,
                     encoding='UTF-8')
            fd.close()

    def export_ui(self, ui):
        self.__export(ui.ui_id, ui.filename)

    def export(self):
        c = self.db.cursor()

        dirname = os.path.dirname(self.filename)

        for row in c.execute('SELECT ui_id, filename FROM ui WHERE filename IS NOT NULL;'):
            ui_id, filename = row
            self.__export(ui_id, filename, dirname=dirname)

        c.close()

    def __selection_remove(self, obj):
        try:
            self.__selection.remove(obj)
        except:
            pass
        else:
            self.emit('selection-changed')

    def __add_ui(self, emit, ui_id, template_id, name, filename, description, copyright, authors, license_id, translation_domain, comment):
        ui = CmbUI(project=self, ui_id=ui_id)

        self.__object_id[ui_id] = self.__store.append(None, [ui])

        if emit:
            self.emit('ui-added', ui)

        return ui

    def add_ui(self, filename=None, requirements={}):

        if filename is None:
            basename = None
            relpath = None
        else:
            basename = os.path.basename(filename)
            dirname = os.path.dirname(self.filename)
            relpath = os.path.relpath(filename, dirname)

        try:
            self.history_push(_("Add UI {basename}").format(basename=basename))
            ui_id = self.db.add_ui(basename, relpath, requirements)
            self.db.commit()
            self.history_pop()
        except:
            return None
        else:
            return self.__add_ui(True, ui_id, None, basename, relpath, None, None, None, None, None, None)

    def __remove_ui(self, ui):
        iter_ = self.__object_id.pop(ui.ui_id, None)

        if iter_ is not None:
            self.__selection_remove(ui)
            self.__store.remove(iter_)
            self.emit('ui-removed', ui)

    def remove_ui(self, ui):
        try:
            self.history_push(_('Remove UI "{name}"').format(name=ui.name))
            self.db.execute("DELETE FROM ui WHERE ui_id=?;", (ui.ui_id, ))
            self.history_pop()
            self.db.commit()
            self.__remove_ui(ui);
        except:
            pass

    def __add_object(self, emit, ui_id, object_id, obj_type, name=None, parent_id=None, internal_child=None, child_type=None, comment=None, position=None):
        obj = CmbObject(project=self,
                        ui_id=ui_id,
                        object_id=object_id,
                        info=self.type_info[obj_type])

        if parent_id:
            parent = self.__object_id.get(f'{ui_id}.{parent_id}', None)
        else:
            parent = self.__object_id.get(ui_id, None)

        self.__object_id[f'{ui_id}.{object_id}'] = self.__store.append(parent, [obj])

        if emit:
            self.emit('object-added', obj)

        return obj

    def _check_can_add(self, obj_type, parent_type):
        obj_info = self.type_info.get(obj_type, None)
        parent_info = self.type_info.get(parent_type, None)

        if obj_info is None or parent_info is None:
            return False

        if parent_info.is_a('GtkWidget'):
            # In Gtk 3 only GtkWidget can be a child on Gtk 4 on the other hand there are types that can have GObjects as children
            if self.target_tk == 'gtk+-3.0' and not obj_info.is_a('GtkWidget'):
                return False

            # GtkWindow can not be a child
            if obj_info.is_a('GtkWindow'):
                return False

            return parent_info.layout == 'container'
        else:
            return True

    def add_object(self, ui_id, obj_type, name=None, parent_id=None, layout=None, position=None, child_type=None, inline_property=None):
        if parent_id:
            parent = self.get_object_by_id(ui_id, parent_id)
            if parent is None:
                return None

            if not self._check_can_add(obj_type, parent.type_id):
                return None

        obj_name = name if name is not None else obj_type

        try:
            self.history_push(_('Add object {name}').format(name=obj_name))
            object_id = self.db.add_object(ui_id,
                                           obj_type,
                                           name,
                                           parent_id,
                                           layout=layout,
                                           position=position,
                                           inline_property=inline_property,
                                           child_type=child_type)
            self.history_pop()
            self.db.commit()
        except Exception as e:
            logger.warning(f'Error adding object {obj_name}: {e}')
            return None
        else:
            return self.__add_object(True, ui_id, object_id, obj_type, name, parent_id)

    def __remove_object(self, obj):
        iter_ = self.__object_id.pop(f'{obj.ui_id}.{obj.object_id}', None)
        if iter_ is not None:
            self.__selection_remove(obj)
            self.__store.remove(iter_)
            self.emit('object-removed', obj)

    def remove_object(self, obj):
        try:
            name = obj.name if obj.name is not None else obj.type_id
            self.history_push(_('Remove object {name}').format(name=name))
            self.db.execute("DELETE FROM object WHERE ui_id=? AND object_id=?;",
                            (obj.ui_id, obj.object_id))
            self.history_pop()
            self.db.commit()
        except Exception as e:
            logger.warning(f'Error removing object {obj}: {e}')
        else:
            self.__remove_object(obj)

    def get_selection(self):
        return self.__selection

    def set_selection(self, selection):
        if type(selection) != list or self.__selection == selection:
            return

        for obj in selection:
            if type(obj) != CmbUI and type(obj) != CmbObject:
                return

        self.__selection = selection
        self.emit('selection-changed')

    def get_iter_from_object(self, obj):
        if type(obj) == CmbObject:
            return self.__object_id.get(f'{obj.ui_id}.{obj.object_id}', None)
        elif type(obj) == CmbUI:
            return self.__object_id.get(obj.ui_id, None)

    def get_object_by_key(self, key):
        _iter = self.__object_id.get(key, None)
        return self.__store.get_value(_iter, 0) if _iter else None

    def get_object_by_id(self, ui_id, object_id = None):
        key = f'{ui_id}.{object_id}' if object_id is not None else ui_id
        return self.get_object_by_key(key)

    def get_object_by_name(self, ui_id, name):
        c = self.db.execute("SELECT object_id FROM object WHERE ui_id=? AND name=?;",
                            (ui_id, name))
        row = c.fetchone()
        return self.get_object_by_key(f'{ui_id}.{row[0]}') if row else None

    def get_ui_by_filename(self, filename):
        dirname = os.path.dirname(self.filename)
        relpath = os.path.relpath(filename, dirname)

        c = self.db.execute("SELECT ui_id FROM ui WHERE filename=?;",
                            (relpath, ))
        row = c.fetchone()
        return self.get_object_by_key(row[0]) if row else None

    def __undo_redo_property_notify(self, obj, layout, prop, owner_id, property_id):
        # FIXME:use a dict instead of walking the array
        properties = obj.layout if layout else obj.properties
        for p in properties:
            if p.owner_id == owner_id and p.property_id == property_id:
                p.notify(prop)
                if layout:
                    obj._layout_property_changed(p)
                else:
                    obj._property_changed(p)

    def __get_history_command(self, history_index):
        c = self.db.cursor()
        c.execute("SELECT command, range_id, table_name, column_name FROM history WHERE history_id=?", (history_index, ))
        retval = c.fetchone()
        c.close()
        return retval

    def __undo_redo_do(self, undo):
        c = self.db.cursor()

        # Get last command
        command, range_id, table, column = self.__get_history_command(self.history_index)

        if table is not None:
            commands = self.db.history_commands[table]

        # Undo or Redo command
        # TODO: catch sqlite errors and do something with it.
        # probably nuke history data
        if command == 'INSERT':
            c.execute(commands['DELETE' if undo else 'INSERT'], (self.history_index, ))
        elif command == 'DELETE':
            c.execute(commands['INSERT' if undo else 'DELETE'], (self.history_index, ))
        elif command == 'UPDATE':
            old_data = 1 if undo else 0
            c.execute(commands['UPDATE'], (self.history_index, old_data, self.history_index, old_data))
        elif command == 'PUSH' or command == 'POP':
            pass
        else:
            logger.warning(f'Error unknown history command {command}')

        c.close()

        # Update project state
        self.__undo_redo_update(command, range_id, table, column)

    def __undo_redo_update(self, command, range_id, table, column):
        c = self.db.cursor()

        if table is None:
            return

        # Update tree model and emit signals
        # We can not easily implement this using triggers because they are called
        # even if the transaction is rollback because of a FK constraint

        commands = self.db.history_commands[table]
        c.execute(commands['PK'], (self.history_index, ))
        pk = c.fetchone()

        if command == 'UPDATE':
            if table == 'object':
                obj = self.get_object_by_id(pk[0], pk[1])
                if obj:
                    obj.notify(column)
            elif table == 'object_property':
                obj = self.get_object_by_id(pk[0], pk[1])
                self.__undo_redo_property_notify(obj, False, column, pk[2], pk[3])
            elif table == 'object_layout_property':
                child = self.get_object_by_id(pk[0], pk[2])
                self.__undo_redo_property_notify(child, True, column, pk[3], pk[4])
            elif table == 'object_signal':
                pass
        elif command == 'INSERT' or command == 'DELETE':
            if table == 'object_property':
                obj = self.get_object_by_id(pk[0], pk[1])
                self.__undo_redo_property_notify(obj, False, 'value', pk[2], pk[3])
            elif table == 'object_layout_property':
                child = self.get_object_by_id(pk[0], pk[2])
                self.__undo_redo_property_notify(child, True, 'value', pk[3], pk[4])
            elif table =='object' or table == 'ui':
                c.execute(commands['COUNT'], (self.history_index, ))
                count = c.fetchone()

                if count[0] == 0:
                    obj = self.get_object_by_id(pk[0], pk[1] if len(pk) > 1 else None)

                    if table =='object':
                        self.__remove_object(obj)
                    elif table == 'ui':
                        self.__remove_ui(obj)
                else:
                    c.execute(commands['DATA'], (self.history_index, ))
                    row = c.fetchone()
                    if table == 'ui':
                        self.__add_ui(True, *row)
                    elif table == 'object':
                        self.__add_object(True, *row)
            elif table == 'object_signal':
                c.execute(commands['COUNT'], (self.history_index, ))
                count = c.fetchone()

                c.execute(commands['DATA'], (self.history_index, ))
                row = c.fetchone()

                obj = self.get_object_by_id(row[1], row[2])

                if count[0] == 0:
                    for signal in obj.signals:
                        if signal.signal_pk == row[0]:
                            obj._remove_signal(signal)
                            break
                else:
                    obj._add_signal(row[0], row[3], row[4], row[5], row[6], row[7], row[8], row[9])

        c.close()

    def __undo_redo(self, undo):
        c = self.db.cursor()

        self.history_enabled = False
        self.db.foreign_keys = False

        command, range_id, table, column = self.__get_history_command(self.history_index)

        if command == 'POP':
            if undo:
                self.history_index -= 1
                while range_id < self.history_index:
                    self.__undo_redo_do(True)
                    self.history_index -= 1
            else:
                logger.warning("Error on undo/redo stack: we should not try to redo a POP command")
        elif command == 'PUSH':
            if not undo:
                while range_id > self.history_index:
                    self.history_index += 1
                    self.__undo_redo_do(undo)
            else:
                logger.warning("Error on undo/redo stack: we should not try to undo a PUSH command")
        else:
            # Undo / Redo in DB
            self.__undo_redo_do(undo)

        self.db.foreign_keys = True
        self.history_enabled = True
        c.close()

    def get_undo_redo_msg(self):
        c = self.db.cursor()

        def get_msg_vars(table, index):
            retval = {
                'ui': '',
                'obj': '',
                'prop': '',
                'value': ''
            }

            commands = self.db.history_commands[table]
            c.execute(commands['DATA'], (index, ))
            data = c.fetchone()

            if data is None:
                return retval

            if table == 'ui':
                retval['ui'] = data[3]
            else:
                if table == 'object_signal':
                    ui_id = data[1]
                    object_id = data[2]
                else:
                    ui_id = data[0]
                    object_id = data[1]

                if table == 'object':
                    retval['obj'] = data[3] if data[3] is not None else data[2]
                else:
                    c.execute('SELECT type_id, name FROM object WHERE ui_id=? AND object_id=?', (ui_id, object_id))
                    row = c.fetchone()
                    if row is not None:
                        type_id, name = row
                        retval['obj'] = name if name is not None else type_id

                if table == 'object_property':
                    retval['prop'] = data[3]
                    retval['value'] = data[4]
                elif table == 'object_layout_property':
                    retval['prop'] = data[4]
                    retval['value'] = data[5]
                elif table == 'object_signal':
                    retval['signal'] = data[4]

            return retval

        def get_msg(index):
            c.execute("SELECT command, range_id, table_name, column_name, message FROM history WHERE history_id=?", (index, ))
            cmd = c.fetchone()
            if cmd is None:
                return None
            command, range_id, table, column, message = cmd

            if message is not None:
                return message

            msg = {
                'ui': {
                    'INSERT': _('Create UI {ui}'),
                    'DELETE': _('Remove UI {ui}'),
                    'UPDATE': _('Update UI {ui}')
                },
                'object': {
                    'INSERT': _('Create object {obj}'),
                    'DELETE': _('Remove object {obj}'),
                    'UPDATE': _('Update object {obj}')
                },
                'object_property': {
                    'INSERT': _('Set property "{prop}" of {obj} to {value}'),
                    'DELETE': _('Unset property "{prop}" of {obj}'),
                    'UPDATE': _('Update property "{prop}" of {obj} to {value}')
                },
                'object_layout_property': {
                    'INSERT': _('Set layout property "{prop}" of {obj} to {value}'),
                    'DELETE': _('Unset layout property "{prop}" of {obj}'),
                    'UPDATE': _('Update layout property "{prop}" of {obj} to {value}')
                },
                'object_signal': {
                    'INSERT': _('Add {signal} signal to {obj}'),
                    'DELETE': _('Remove {signal} signal from {obj}'),
                    'UPDATE': _('Update {signal} signal of {obj}')
                },
            }.get(table, {}).get(command, None)

            if msg is not None:
                msg = msg.format(**get_msg_vars(table, index))

            return msg

        undo_msg = get_msg(self.history_index)
        redo_msg = get_msg(self.history_index + 1)

        c.close()

        return (undo_msg, redo_msg)

    def undo(self):
        if self.history_index == 0:
            return

        self.__undo_redo(True)
        self.history_index -= 1
        self.emit('changed')

    def redo(self):
        if self.history_index >= self.history_index_max:
            return

        self.history_index += 1
        self.__undo_redo(False)

    def get_type_properties(self, name):
        info = self.type_info.get(name, None)
        return info.properties if info else None

    def _object_changed(self, obj, field):
        iter = self.get_iter_from_object(obj)
        path = self.__store.get_path(iter)

        self.__store.row_changed(path, iter)

        self.emit('object-changed', obj, field)

    def _object_property_changed(self, obj, prop):
        self.emit('object-property-changed', obj, prop)

    def _object_layout_property_changed(self, obj, child, prop):
        self.emit('object-layout-property-changed', obj, child, prop)

    def _object_signal_removed(self, obj, signal):
        self.emit('object-signal-removed', obj, signal)

    def _object_signal_added(self, obj, signal):
        self.emit('object-signal-added', obj, signal)

    def db_backup(self, filename):
        self.db.backup(filename)

    def history_push(self, message):
        if not self.history_enabled:
            return

        self.db.execute("INSERT INTO history (history_id, command, message) VALUES (?, 'PUSH', ?)",
                          (self.history_index_max + 1, message))

    def history_pop(self):
        if not self.history_enabled:
            return

        self.db.execute("INSERT INTO history (history_id, command) VALUES (?, 'POP')",
                          (self.history_index_max + 1, ))
        self.emit('changed')

    def copy(self):
        # TODO: filter children out
        selection = [(o.ui_id, o.object_id) for o in self.__selection if isinstance(o, CmbObject)]
        self.db.clipboard_copy(selection)

    def paste(self):
        if len(self.__selection) == 0:
            return

        c = self.db.cursor()

        obj = self.__selection[0]
        ui_id = obj.ui_id
        parent_id = obj.object_id if isinstance(obj, CmbObject) else None
        name = obj.name if obj.name is not None else obj.type_id

        self.history_push(_('Paste clipboard to {name}').format(name=name))

        new_objects = self.db.clipboard_paste(ui_id, parent_id)

        self.history_pop()
        self.db.commit()

        # Update UI objects
        for object_id in new_objects:
            c.execute('SELECT * FROM object WHERE ui_id=? AND object_id=?;',
                      (ui_id, object_id))
            self.__add_object(True, *c.fetchone())

        c.close()

    def cut(self):
        # TODO: filter children out
        selection = [o for o in self.__selection if isinstance(o, CmbObject)]

        # Copy to clipboard
        self.copy()

        # Delete from project
        try:
            n_objects = len(selection)

            if n_objects == 1:
                obj = selection[0]
                name = obj.name if obj.name is not None else obj.type_id
                self.history_push(_('Cut object {name}').format(name=name))
            else:
                self.history_push(_('Cut {n_objects} object').format(n_objects=n_objects))

            for obj in selection:
                self.db.execute("DELETE FROM object WHERE ui_id=? AND object_id=?;",
                                (obj.ui_id, obj.object_id))

            self.history_pop()
            self.db.commit()
        except:
            pass
        else:
            for obj in selection:
                self.__remove_object(obj)

    def clipboard_count(self):
        try:
            c = self.db.execute('SELECT count(ui_id) FROM clipboard_object WHERE parent_id IS NULL;')
            retval = c.fetchone()[0]
            c.close()
        except:
            retval = 0

        return retval

    @staticmethod
    def get_target_from_ui_file(filename):
        tree = etree.parse(filename)
        root = tree.getroot()

        lib, ver, inferred = CmbDB._get_target_from_node(root)

        return f'{lib}-{ver}' if lib is not None else None

    # Default handlers
    def do_ui_added(self, ui):
        self.emit('changed')

    def do_ui_removed(self, ui):
        self.emit('changed')

    def do_object_added(self, obj):
        self.emit('changed')

    def do_object_removed(self, obj):
        self.emit('changed')

    def do_object_changed(self, obj, field):
        self.emit('changed')

    def do_object_property_changed(self, obj, prop):
        self.emit('changed')

    def do_object_layout_property_changed(self, obj, child, prop):
        self.emit('changed')

    def do_object_signal_added(self, obj, signal):
        self.emit('changed')

    def do_object_signal_removed(self, obj, signal):
        self.emit('changed')

    # GtkTreeModel iface

    def do_get_iter(self, path):
        # NOTE: We could implement TreeModel iface directly with sqlite using
        # row_number() function and the object_id as the iter but it would be
        # too intensive just to save some memory
        # "SELECT * FROM (SELECT object_id, row_number() OVER (ORDER BY object_id) AS row_number FROM object WHERE ui_id=1 ORDER BY object_id) WHERE row_number=?;"

        try:
            retval = self.__store.get_iter(path)
            return (retval is not None, retval)
        except:
            return (False, None)

    def do_iter_next(self, iter_):
        retval = self.__store.iter_next(iter_)

        if retval is not None:
            iter_.user_data = retval.user_data
            iter_.user_data2 = retval.user_data2
            iter_.user_data3 = retval.user_data3
            return True
        return False

    def do_iter_previous(self, iter_):
        retval = self.__store.iter_previous(iter_)
        if retval is not None:
            iter_.user_data = retval.user_data
            iter_.user_data2 = retval.user_data2
            iter_.user_data3 = retval.user_data3
            return True
        return False

    def do_iter_has_child(self, iter_):
        return self.__store.iter_has_child(iter_)

    def do_iter_nth_child(self, iter_, n):
        retval = self.__store.iter_nth_child(iter_, n)
        return (retval is not None, retval)

    def do_iter_children(self, parent):
        if parent is None:
            retval = self.__store.get_iter_first()
            return (retval is not None, retval)
        elif self.__store.iter_has_child(parent):
            retval = self.__store.iter_children(parent)
            return (True, retval)

        return (False, None)

    def do_iter_n_children(self, iter_):
        return self.__store.iter_n_children(iter_)

    def do_iter_parent(self, child):
        retval = self.__store.iter_parent(child)
        return (retval is not None, retval)

    def do_get_path(self, iter_):
        return self.__store.get_path(iter_)

    def do_get_value(self, iter_, column):
        retval = self.__store.get_value(iter_, column)
        if retval is None and self.__store.get_column_type(column) == GObject.TYPE_STRING:
            return ''

        return retval

    def do_get_n_columns(self):
        return self.__store.get_n_columns()

    def do_get_column_type(self, column):
        return self.__store.get_column_type(column)

    def do_get_flags(self):
        return self.__store.get_flags()

