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

from lxml import etree
from lxml.builder import E

basedir = os.path.dirname(__file__) or '.'

def _load_sql(filename):
    with open(os.path.join(basedir, filename), 'r') as sql:
        retval = sql.read()
        sql.close()
    return retval

BASE_SQL = _load_sql('cmb_base.sql')
PROJECT_SQL = _load_sql('cmb_project.sql')
HISTORY_SQL = _load_sql('cmb_history.sql')

class CmbProject:
    def __init__(self):
        # DataModel is only used internally
        self.conn = sqlite3.connect(":memory:")

        c = self.conn.cursor()

        # Create type system tables
        c.executescript(BASE_SQL)

        # Create project tables
        c.executescript(PROJECT_SQL)

        # Initialize history (Undo/Redo) tables
        self._init_history()

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

    def _init_history(self):
        c = self.conn.cursor()

        # Create history main tables
        c.executescript(HISTORY_SQL)

        # Create history tables for each tracked table
        self._create_history_table(c, 'ui')
        self._create_history_table(c, 'ui_library')
        self._create_history_table(c, 'object',
                                   "printf('Delete object %s:%s', OLD.type_id, OLD.name)")
        self._create_history_table(c, 'object_property')
        self._create_history_table(c, 'object_child_property')
        self._create_history_table(c, 'object_signal')

        self.conn.commit()
        c.close()

    def _create_history_table(self, c, table, group_msg=None):
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

        # INSERT Trigger
        c.execute(f'''
    CREATE TRIGGER on_{table}_insert AFTER INSERT ON {table}
    BEGIN
      INSERT INTO history (command, data) VALUES ('INSERT', '{table}');
      INSERT INTO history_{table} (history_id, {columns})
        VALUES (last_insert_rowid(), {new_values});
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
        c.execute("INSERT INTO object (type_id, name, parent_id, ui_id) VALUES (?, ?, ?, ?);",
                  (klass, name, parent_id, ui_id))
        object_id = c.lastrowid

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
                c.execute("INSERT INTO object_property (object_id, owner_id, property_id, value, translatable) VALUES (?, ?, ?, ?, ?);",
                          (object_id, owner_id[0], property_id, prop.text, translatable))
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
            c.execute("INSERT INTO object_signal (object_id, owner_id, signal_id, handler, detail, user_data, swap, after) VALUES (?, ?, ?, ?, ?, (SELECT object_id FROM object WHERE name=?), ?, ?);",
                      (object_id, owner_id[0] if owner_id else None, signal_id, handler, detail, user_data, swap, after))

        # Children
        for child in node.iterfind('child'):
            obj = child.find('object')
            if obj is not None:
                self._import_object(builder_ver, None, obj, object_id)

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
            c.execute("SELECT type_id FROM object WHERE object_id=?;", (parent_id, ))
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
                c.execute("INSERT INTO object_child_property (object_id, child_id, owner_id, property_id, value, translatable) VALUES (?, ?, ?, ?, ?, ?);",
                          (parent_id, object_id, owner_id, property_id, prop.text, translatable))
        c.close()

    def import_file(self, filename, overwrite=False):
        c = self.conn.cursor()

        basename = os.path.basename(filename)

        # Remove old UI
        if overwrite:
            c.execute("DELETE FROM ui WHERE name=?;", (basename, ))

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

    def _get_object(self, builder_ver, object_id):
        def node_set(node, attr, val):
            if val is not None:
                node.set(attr, str(val))

        c = self.conn.cursor()
        cc = self.conn.cursor()
        obj = E.object()

        c.execute('SELECT type_id, name FROM object WHERE object_id=?;', (object_id,))
        row = c.fetchone()
        node_set(obj, 'class', row[0])
        node_set(obj, 'id', row[1])

        # Properties
        for row in c.execute('SELECT value, property_id FROM object_property WHERE object_id=?;',
                             (object_id,)):
            obj.append(E.property(row[0], name=row[1]))
            # Signals
        for row in c.execute('SELECT signal_id, handler, detail, (SELECT name FROM object WHERE object_id=user_data), swap, after FROM object_signal WHERE object_id=?;',
                             (object_id,)):
            node = E.signal(name=row[0], handler=row[1])
            node_set(node, 'object', row[3])
            node_set(node, 'swapped', row[4])
            node_set(node, 'after', row[5])
            obj.append(node)

        # Children
        for row in c.execute('SELECT object_id FROM object WHERE parent_id=?;', (object_id,)):
            child_id = row[0]
            child_obj = self._get_object(builder_ver, child_id)
            child = E.child(child_obj)

            # Packing / Layout
            layout = E('packing' if builder_ver == 3 else 'layout')

            for prop in cc.execute('SELECT value, property_id FROM object_child_property WHERE object_id=? AND child_id=?;',
                                 (object_id, child_id)):
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

    def _export_ui(self, ui_id, filename):
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
        for row in c.execute('SELECT object_id FROM object WHERE ui_id=?;',
                             (ui_id,)):
            child = self._get_object(builder_ver, row[0])
            node.append(child)

        c.close()

        # Dump xml to file
        with open(filename, 'wb') as fd:
            tree = etree.ElementTree(node)
            tree.write(fd,
                       pretty_print=True,
                       xml_declaration=True,
                       encoding='UTF-8')
            fd.close()

    def export(self):
        c = self.conn.cursor()

        # FIXME: remove cmb suffix once we have full GtkBuilder support
        for row in c.execute('SELECT ui_id, filename FROM ui;'):
            self._export_ui(row[0], os.path.splitext(row[1])[0] + '.cmb.ui')

        c.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Ussage: {sys.argv[0]} import.ui")
        exit()

    project = CmbProject()
    project.import_file(sys.argv[1], True)
    project.export()
