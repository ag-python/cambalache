#
# CmbProject - Cambalache Project
#
# Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import sqlite3
import gi

from lxml import etree
from lxml.builder import E

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_objects import CmbUI, CmbObject


basedir = os.path.dirname(__file__) or '.'

def _load_sql(filename):
    with open(os.path.join(basedir, filename), 'r') as sql:
        retval = sql.read()
        sql.close()
    return retval

BASE_SQL = _load_sql('cmb_base.sql')
PROJECT_SQL = _load_sql('cmb_project.sql')
HISTORY_SQL = _load_sql('cmb_history.sql')


class CmbProject(GObject.GObject, Gtk.TreeModel):
    __gtype_name__ = 'CmbProject'

    _signal_params = {}
    _table_columns = {}

    def __init__(self):
        GObject.GObject.__init__(self)

        # DataModel is only used internally
        self.conn = sqlite3.connect(":memory:")

        c = self.conn.cursor()

        # Create type system tables
        c.executescript(BASE_SQL)

        # Create project tables
        c.executescript(PROJECT_SQL)

        self._init_signals(c)

        # Create TreeModel store
        self._ui_id = {}
        self._object_id = {}

        # Use a TreeStore to hold object tree instead of using SQL for every
        # TreeStore call
        self._store = Gtk.TreeStore(GObject.GObject)

        # Foward signals to CmbProject, this way the user can not add data to
        # the TreeModel using Gtk API
        self._store.connect('row-changed', lambda o, p, i: self.row_changed(p, i))
        self._store.connect('row-inserted', lambda o, p, i: self.row_inserted(p, i))
        self._store.connect('row-has-child-toggled', lambda o, p, i: self.row_has_child_toggled(p, i))
        self._store.connect('row-deleted', lambda o, p, d: self.row_deleted(p))
        self._store.connect('rows-reordered', lambda o, p, i, n: self.rows_reordered(p, i, n))

        # Initialize history (Undo/Redo) tables
        self._init_history_and_triggers()

        # Load library support data
        self._load_libraries()

        c.execute("PRAGMA foreign_keys = ON;")

        self.conn.commit()
        c.close()

    def __del__(self):
        self.conn.commit()
        self.conn.close()

    def _load_libraries(self):
        c = self.conn.cursor()

        # TODO: implement own format instead of sql
        with open('gtk3.sql', 'r') as sql:
            c.executescript(sql.read())

        self.conn.commit()
        c.close()

    def _get_columns(self, c, table):
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
                print('Error unknown type', col_type)

            columns.append(col)
            types.append(col_type)

            if pk:
                pks.append(col)

        return { 'names': columns, 'types': types, 'pks': pks }

    def _init_signals(self, c):
        # Make sure we only initialize signals once
        if (len(self._signal_params) > 0):
            return

        for table in ['ui', 'ui_library', 'object', 'object_property', 'object_layout_property', 'object_signal']:
            columns = self._get_columns(c, table)
            self._table_columns[table] = columns
            table = table.replace('_', '-')
            for action in ['added', 'removed', 'updated']:
                signal = f'{table}-{action}'
                self._signal_params[signal] = columns
                GObject.signal_new(signal,
                                   CmbProject,
                                   GObject.SignalFlags.RUN_LAST,
                                   None,
                                   tuple(columns['types']))

    def _init_history_and_triggers(self):
        c = self.conn.cursor()

        # Create history main tables
        c.executescript(HISTORY_SQL)

        # Create history tables for each tracked table
        self._create_support_table(c, 'ui')
        self._create_support_table(c, 'ui_library')
        self._create_support_table(c, 'object',
                                   "printf('Delete object %s:%s', OLD.type_id, OLD.name)")
        self._create_support_table(c, 'object_property')
        self._create_support_table(c, 'object_layout_property')
        self._create_support_table(c, 'object_signal')

        self.conn.commit()
        c.close()

    def _emit(self, signal, *args):
        params = []
        signal_params = self._signal_params[signal]['types']

        # Make sure there is no None parameter
        for i in range(0, len(signal_params)):
            arg = args[i]
            if arg is not None:
                params.append(arg)
            else:
                arg_type = signal_params[i]
                if arg_type == GObject.TYPE_INT:
                    params.append(0)
                elif arg_type == GObject.TYPE_STRING:
                    params.append('')
                elif arg_type == GObject.TYPE_BOOLEAN:
                    params.append(False)

        self.emit(signal, *params)

    def _create_support_table(self, c, table, group_msg=None):
        # Create a history table to store data for INSERT and DELETE commands
        c.executescript(f'''
    CREATE TABLE history_{table} AS SELECT * FROM {table} WHERE 0;
    ALTER TABLE history_{table} ADD COLUMN history_id INTERGER REFERENCES history ON DELETE CASCADE;
    CREATE INDEX history_{table}_history_id_fk ON history_{table} (history_id);
    ''')

        # Get table columns
        columns = None
        old_values = None
        new_values = None

        all_columns = []
        non_pk_columns = []

        for row in c.execute(f'PRAGMA table_info({table});'):
            col = row[1]
            col_type =  row[2]
            pk = row[5]

            if columns == None:
                columns = col
                old_values = 'OLD.' + col
                new_values = 'NEW.' + col
            else:
                columns += ', ' + col
                old_values += ', OLD.' + col
                new_values += ', NEW.' + col

            all_columns.append(col)
            if not pk:
                non_pk_columns.append(col)

        # Create notify callbacks, this is needed if we want to listen to events
        # from another process using just sqlite
        _table = table.replace('_', '-')
        self.conn.create_function(f'_on_{table}_insert', len(all_columns),
                                  lambda *args: self._emit(f'{_table}-added', *args))

        self.conn.create_function(f'_on_{table}_delete', len(all_columns),
                                  lambda *args: self._emit(f'{_table}-removed', *args))

        self.conn.create_function(f'_on_{table}_update', len(all_columns),
                                  lambda *args: self._emit(f'{_table}-updated', *args))

        # Triggers will get executed for row that break foreign key contraint
        # So we can not rely on getting notifications without making sure
        # there wont be a FK constraint failure.
        # FIXME: Only use rowid tables to be able to use update hook function
        fkeys = {}
        for row in c.execute(f'PRAGMA foreign_key_list({table});'):
            fk_id = row[0]
            key = fkeys.get(fk_id, None)

            fk_table = row[2]
            from_col = row[3]
            to_col = row[4]

            if to_col is None:
                to_col = from_col

            if key is None:
                key = {
                    'table': fk_table,
                    'from': [from_col],
                    'to': [to_col]
                }
            else:
                key['from'].append(from_col)
                key['to'].append(to_col)

            fkeys[fk_id] = key


        fk_check = ''
        for key in fkeys:
            if fk_check != '':
                fk_check += '\n    AND\n    '
            k = fkeys[key]
            fk_table = k['table']
            f = k['from']
            to = k['to']

            first_check=''
            where=''
            for i in range(0, len(to)):
                if i > 0:
                    where += ' AND '
                    first_check += ' OR '
                first_check += f'NEW.{f[i]} IS NULL'
                where += f'{to[i]} = NEW.{f[i]}'

            fk_check += f'({first_check} OR (SELECT EXISTS(SELECT 1 FROM {fk_table} WHERE {where})))'

        # INSERT Trigger
        c.execute(f'''
    CREATE TRIGGER on_{table}_insert AFTER INSERT ON {table}
    WHEN
        {fk_check}
    BEGIN
      INSERT INTO history (command, data) VALUES ('INSERT', '{table}');
      INSERT INTO history_{table} (history_id, {columns})
        VALUES (last_insert_rowid(), {new_values});
      SELECT _on_{table}_insert({new_values});
    END;
        ''')

        # DELETE Trigger
        if group_msg:
            c.execute(f'''
    CREATE TRIGGER on_{table}_before_delete BEFORE DELETE ON {table}
    BEGIN
      INSERT INTO history (command, data) VALUES ('PUSH', {group_msg});
    END;
            ''')
            pop = f"INSERT INTO history (command) VALUES ('POP');"
        else:
            pop = ''

        c.execute(f'''
    CREATE TRIGGER on_{table}_delete AFTER DELETE ON {table}
    BEGIN
      INSERT INTO history (command, data) VALUES ('DELETE', '{table}');
      INSERT INTO history_{table} (history_id, {columns})
        VALUES (last_insert_rowid(), {old_values});
      {pop}
      SELECT _on_{table}_delete({old_values});
    END;
        ''')

        c.execute(f'''
    CREATE TRIGGER on_{table}_update AFTER UPDATE ON {table}
    BEGIN
      SELECT _on_{table}_update({new_values});
    END;
        ''')

        last_history_id = "(SELECT seq FROM sqlite_sequence WHERE name='history')"

        # UPDATE Trigger for each non PK column
        for column in non_pk_columns:
            all_but_column = None
            all_but_column_values = None

            for col in all_columns:
                if col != column:
                    if all_but_column == None:
                        all_but_column = col
                        all_but_column_values = 'NEW.' + col
                    else:
                        all_but_column += ', ' + col
                        all_but_column_values += ', NEW.' + col

            c.execute(f'''
    CREATE TRIGGER on_{table}_update_{column} AFTER UPDATE OF {column} ON {table}
    WHEN
      (SELECT command, data FROM history WHERE history_id = {last_history_id})
        IS NOT ('UPDATE', '{table}')
        OR
      (SELECT {all_but_column} FROM history_{table} WHERE history_id = {last_history_id})
        IS NOT ({all_but_column_values})
    BEGIN
      INSERT INTO history (command, data) VALUES ('UPDATE', '{table}');
      INSERT INTO history_{table} (history_id, {columns})
        VALUES (last_insert_rowid(), {new_values});
    END;
            ''')

            c.execute(f'''
    CREATE TRIGGER on_{table}_update_{column}_compress AFTER UPDATE OF {column} ON {table}
    WHEN
      (SELECT command, data FROM history WHERE history_id = {last_history_id})
        IS ('UPDATE', '{table}')
        AND
      (SELECT {all_but_column} FROM history_{table} WHERE history_id = {last_history_id})
        IS ({all_but_column_values})
    BEGIN
      UPDATE history_{table} SET {column}=NEW.{column} WHERE history_id = {last_history_id};
    END;
            ''')

    def load(self, filename):
        pass

    def save(self, filename):
        # TODO: create custom XML file format with all the data from project tables
        pass

    def _import_object(self, builder_ver, ui_id, node, parent_id):
        c = self.conn.cursor()
        klass = node.get('class')
        name = node.get('id')

        # Insert object
        c.execute("SELECT coalesce((SELECT object_id FROM object WHERE ui_id=? ORDER BY object_id DESC LIMIT 1), 0) + 1;", (ui_id, ))
        object_id = c.fetchone()[0]

        c.execute("INSERT INTO object (ui_id, object_id, type_id, name, parent_id) VALUES (?, ?, ?, ?, ?);",
                  (ui_id, object_id, klass, name, parent_id))

        # Properties
        for prop in node.iterfind('property'):
            property_id = prop.get('name')
            translatable = prop.get('translatable', None)

            # Find owner type for property
            c.execute("SELECT owner_id FROM property WHERE property_id=? AND owner_id IN (SELECT parent_id FROM type_tree WHERE type_id=? UNION SELECT ?);",
                      (property_id, klass, klass))
            owner_id = c.fetchone()

            # Insert property
            if owner_id:
                c.execute("INSERT INTO object_property (ui_id, object_id, owner_id, property_id, value, translatable) VALUES (?, ?, ?, ?, ?, ?);",
                          (ui_id, object_id, owner_id[0], property_id, prop.text, translatable))
            else:
                print(f'Could not find owner type for {klass}:{property_id}')

        # Signals
        for signal in node.iterfind('signal'):
            tokens = signal.get('name').split('::')

            if len(tokens) > 1:
                signal_id = tokens[0]
                detail = tokens[1]
            else:
                signal_id = tokens[0]
                detail = None

            handler = signal.get('handler')
            user_data = signal.get('object')
            swap = signal.get('swapped')
            after = signal.get('after')

            # Find owner type for signal
            c.execute("SELECT owner_id FROM signal WHERE signal_id=? AND owner_id IN (SELECT parent_id FROM type_tree WHERE type_id=? UNION SELECT ?);",
                      (signal_id, klass, klass))
            owner_id = c.fetchone()

            # Insert signal
            c.execute("INSERT INTO object_signal (ui_id, object_id, owner_id, signal_id, handler, detail, user_data, swap, after) VALUES (?, ?, ?, ?, ?, ?, (SELECT object_id FROM object WHERE ui_id=? AND name=?), ?, ?);",
                      (ui_id, object_id, owner_id[0] if owner_id else None, signal_id, handler, detail, ui_id, user_data, swap, after))

        # Children
        for child in node.iterfind('child'):
            obj = child.find('object')
            if obj is not None:
                self._import_object(builder_ver, ui_id, obj, object_id)

        # Packing properties
        if builder_ver == 3:
            # Gtk 3, packing props are sibling to <object>
            packing = node.getnext()
            if packing is not None and packing.tag != 'packing':
                packing = None
        else:
            # Gtk 4, layout props are children of <object>
            packing = node.find('layout')

        if parent_id and packing is not None:
            c.execute("SELECT type_id FROM object WHERE ui_id=? AND object_id=?;", (ui_id, parent_id))
            parent_type = c.fetchone()

            if parent_type is None:
                return

            if builder_ver == 3:
                # For Gtk 3 we fake a LayoutChild class for each GtkContainer
                owner_id = f'Cambalache{parent_type[0]}LayoutChild'
            else:
                # FIXME: Need to get layout-manager-type from class
                owner_id = f'{parent_type[0]}LayoutChild'

            for prop in packing.iterfind('property'):
                property_id = prop.get('name')
                translatable = prop.get('translatable', None)
                c.execute("INSERT INTO object_layout_property (ui_id, object_id, child_id, owner_id, property_id, value, translatable) VALUES (?, ?, ?, ?, ?, ?, ?);",
                          (ui_id, parent_id, object_id, owner_id, property_id, prop.text, translatable))
        c.close()

    def import_file(self, filename, overwrite=False):
        c = self.conn.cursor()

        basename = os.path.basename(filename)

        # Remove old UI
        if overwrite:
            c.execute("DELETE FROM ui WHERE filename=?;", (filename, ))

        c.execute("INSERT INTO ui (name, filename) VALUES (?, ?);",
                  (basename, filename))
        ui_id = c.lastrowid

        tree = etree.parse(filename)
        root = tree.getroot()

        # Requires
        builder_ver = 4
        for req in root.iterfind('requires'):
            lib = req.get('lib')
            version = req.get('version')

            if lib == 'gtk+':
                builder_ver = 3;

            c.execute("INSERT INTO ui_library (ui_id, library_id, version) VALUES (last_insert_rowid(), ?, ?);",
                      (lib, version))

        for child in root.iterfind('object'):
            self._import_object(builder_ver, ui_id, child, None)
            self.conn.commit()

        c.close()

    def _get_object(self, builder_ver, ui_id, object_id):
        def node_set(node, attr, val):
            if val is not None:
                node.set(attr, str(val))

        c = self.conn.cursor()
        cc = self.conn.cursor()
        obj = E.object()

        c.execute('SELECT type_id, name FROM object WHERE ui_id=? AND object_id=?;', (ui_id, object_id))
        row = c.fetchone()
        node_set(obj, 'class', row[0])
        node_set(obj, 'id', row[1])

        # Properties
        for row in c.execute('SELECT value, property_id FROM object_property WHERE ui_id=? AND object_id=?;',
                             (ui_id, object_id,)):
            obj.append(E.property(row[0], name=row[1]))
            # Signals
        for row in c.execute('SELECT signal_id, handler, detail, (SELECT name FROM object WHERE ui_id=? AND object_id=user_data), swap, after FROM object_signal WHERE ui_id=? AND object_id=?;',
                             (ui_id, ui_id, object_id,)):
            node = E.signal(name=row[0], handler=row[1])
            node_set(node, 'object', row[3])
            node_set(node, 'swapped', row[4])
            node_set(node, 'after', row[5])
            obj.append(node)

        # Children
        for row in c.execute('SELECT object_id FROM object WHERE ui_id=? AND parent_id=?;', (ui_id, object_id)):
            child_id = row[0]
            child_obj = self._get_object(builder_ver, ui_id, child_id)
            child = E.child(child_obj)

            # Packing / Layout
            layout = E('packing' if builder_ver == 3 else 'layout')

            for prop in cc.execute('SELECT value, property_id FROM object_layout_property WHERE ui_id=? AND object_id=? AND child_id=?;',
                                 (ui_id, object_id, child_id)):
                layout.append(E.property(prop[0], name=prop[1]))

            if len(layout) > 0:
                if builder_ver == 3:
                    child.append(layout)
                else:
                    child_obj.append(layout)

            obj.append(child)

        c.close()
        cc.close()
        return obj

    def export_ui(self, ui_id, filename=None):
        c = self.conn.cursor()

        node = E.interface()
        node.addprevious(etree.Comment(" Created with Cambalache prototype "))

        # requires
        builder_ver = 4
        for row in c.execute('SELECT library_id, version FROM ui_library WHERE ui_id=?;', (ui_id,)):
            node.append(E.requires(lib=row[0], version=row[1]))
            if row[0] == 'gtk+':
                builder_ver = 3;

        # Iterate over toplovel objects
        for row in c.execute('SELECT object_id FROM object WHERE parent_id IS NULL AND ui_id=?;',
                             (ui_id,)):
            child = self._get_object(builder_ver, ui_id, row[0])
            node.append(child)

        c.close()

        tree = etree.ElementTree(node)

        if filename is not None:
            # Dump xml to file
            with open(filename, 'wb') as fd:
                tree.write(fd,
                           pretty_print=True,
                           xml_declaration=True,
                           encoding='UTF-8')
                fd.close()
        else:
            return etree.tostring(tree,
                                  pretty_print=True,
                                  xml_declaration=True,
                                  encoding='UTF-8')

    def export(self):
        c = self.conn.cursor()

        # FIXME: remove cmb suffix once we have full GtkBuilder support
        for row in c.execute('SELECT ui_id, filename FROM ui;'):
            self.export_ui(row[0], os.path.splitext(row[1])[0] + '.cmb.ui')

        c.close()

    def add_ui(self, filename):
        basename = os.path.basename(filename)

        self.conn.execute("INSERT INTO ui (name, filename) VALUES (?, ?);",
                          (basename, filename))

    def remove_ui(self, filename):
        self.conn.execute("DELETE FROM ui WHERE filename=?;", (filename, ))

    def add_object(self, ui_id, obj_type, name=None, parent_id=None):
        c = self.conn.cursor()

        # Insert object
        c.execute("SELECT coalesce((SELECT object_id FROM object WHERE ui_id=? ORDER BY object_id DESC LIMIT 1), 0) + 1;", (ui_id, ))
        object_id = c.fetchone()[0]

        c.execute("INSERT INTO object (ui_id, object_id, type_id, name, parent_id) VALUES (?, ?, ?, ?, ?);",
                  (ui_id, object_id, obj_type, name, parent_id))
        c.close()

    def remove_object(self, ui_id, object_id):
        self.conn.execute("DELETE FROM object WHERE ui_id=? AND object_id=?;", (ui_id, object_id))

    # Signal handlers
    def _get_object_from_args(self, table, args):
        columns = self._table_columns[table]

        data = {}
        i = 0

        for c in columns['names']:
            data[c] = args[i]
            i += 1

        return data

    def _update_object(self, obj, table, args):
        columns = self._table_columns[table]
        pks = columns['pks']

        i = 0
        for c in columns['names']:
            if c not in pks:
                obj.set_property(c, args[i])
            i += 1

    def do_ui_added(self, *args):
        ui = CmbUI(**self._get_object_from_args ('ui', args))
        self._ui_id[ui.ui_id] = self._store.append(None, [ui])

    def do_ui_removed(self, *args):
        ui_id = args[0]
        iter_ = self._ui_id.pop(ui_id, None)
        if iter_ is not None:
            self._store.remove(iter_)

    def do_ui_updated(self, *args):
        ui_id = args[0]

        iter_ = self._ui_id.get(ui_id, None)
        if iter_ is None:
            return

        ui = self._store.get_value(iter_, 0)
        self._update_object(ui, 'ui', args)

    def do_object_added(self, *args):
        obj = CmbObject(**self._get_object_from_args ('object', args))

        if obj.parent_id == 0:
            parent = self._ui_id.get(obj.ui_id, None)
        else:
            parent = self._object_id.get(f'{obj.ui_id}.{obj.parent_id}', None)

        self._object_id[f'{obj.ui_id}.{obj.object_id}'] = self._store.append(parent, [obj])

    def do_object_removed(self, *args):
        ui_id = args[0]
        object_id = args[1]

        iter_ = self._object_id.pop(f'{ui_id}.{object_id}', None)
        if iter_ is not None:
            self._store.remove(iter_)

    def do_object_updated(self, *args):
        ui_id = args[0]
        object_id = args[1]

        iter_ = self._object_id.get(f'{ui_id}.{object_id}', None)
        if iter_ is None:
            return

        obj = self._store.get_value(iter_, 0)
        self._update_object(obj, 'object', args)

    # GtkTreeModel iface

    def do_get_iter(self, path):
        # NOTE: We could implement TreeModel iface directly with sqlite using
        # row_number() function and the object_id as the iter but it would be
        # too intensive just to save some memory
        # "SELECT * FROM (SELECT object_id, row_number() OVER (ORDER BY object_id) AS row_number FROM object WHERE ui_id=1 ORDER BY object_id) WHERE row_number=?;"

        try:
            retval = self._store.get_iter(path)
            return (retval is not None, retval)
        except:
            return (False, None)

    def do_iter_next(self, iter_):
        retval = self._store.iter_next(iter_)

        if retval is not None:
            iter_.user_data = retval.user_data
            iter_.user_data2 = retval.user_data2
            iter_.user_data3 = retval.user_data3
            return True
        return False

    def do_iter_previous(self, iter_):
        retval = self._store.iter_previous(iter_)
        if retval is not None:
            iter_.user_data = retval.user_data
            iter_.user_data2 = retval.user_data2
            iter_.user_data3 = retval.user_data3
            return True
        return False

    def do_iter_has_child(self, iter_):
        return self._store.iter_has_child(iter_)

    def do_iter_nth_child(self, iter_, n):
        retval = self._store.iter_nth_child(iter_, n)
        return (retval is not None, retval)

    def do_iter_children(self, parent):
        if parent is None:
            retval = self._store.get_iter_first()
            return (retval is not None, retval)
        elif self._store.iter_has_child(parent):
            retval = self._store.iter_children(parent)
            return (True, retval)

        return (False, None)

    def do_iter_n_children(self, iter_):
        return self._store.iter_n_children(iter_)

    def do_iter_parent(self, child):
        retval = self._store.iter_parent(child)
        return (retval is not None, retval)

    def do_get_path(self, iter_):
        return self._store.get_path(iter_)

    def do_get_value(self, iter_, column):
        retval = self._store.get_value(iter_, column)
        if retval is None and self._store.get_column_type(column) == GObject.TYPE_STRING:
            return ''

        return retval

    def do_get_n_columns(self):
        return self._store.get_n_columns()

    def do_get_column_type(self, column):
        return self._store.get_column_type(column)

    def do_get_flags(self):
        return self._store.get_flags()

