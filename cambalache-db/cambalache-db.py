#
# CambalacheDB - Data Model for Cambalache
#
# Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import sqlite3

import gir

from lxml import etree
from lxml.builder import E


def db_create_history_table(c, table, group_msg=None):
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


def db_create_history_tables(conn):
    c = conn.cursor()
    db_create_history_table(c, 'ui')
    db_create_history_table(c, 'object',
                            "printf('Delete object %s:%s', OLD.type_id, OLD.name)")
    db_create_history_table(c, 'object_property')
    db_create_history_table(c, 'object_child_property')
    db_create_history_table(c, 'object_signal')
    conn.commit()


def row_diff_count(*args):
    return len(args)


def db_create(filename):
    # Create DB file
    conn = sqlite3.connect(filename)

    conn.create_function("row_diff_count", -1, row_diff_count, deterministic=True)

    # Create DB tables
    with open('cambalache-db.sql', 'r') as sql:
        c = conn.cursor()
        c.executescript(sql.read())
        conn.commit()
        sql.close()

    db_create_history_tables(conn)

    return conn


def db_import_object(c, lib, ui_id, node, parent_id):
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
            db_import_object(c, lib, None, obj, object_id)

    # Packing properties
    if lib == 'gtk+':
        # Gtk 3, packing props are sibling to <object>
        packing = node.getnext()
        if packing is not None and packing.tag != 'packing':
            packing = None
    elif lib == 'gtk':
        # Gtk 4, layout props are children of <object>
        packing = node.find('layout')

    if parent_id and packing is not None:
        c.execute("SELECT type_id FROM object WHERE object_id=?;", (parent_id, ))
        parent_type = c.fetchone()

        if parent_type is None:
            return

        if lib == 'gtk+':
            # For Gtk 3 we fake a LayoutChild class for each GtkContainer
            owner_id = f'Cambalache{parent_type[0]}LayoutChild'
        elif lib == 'gtk':
            # FIXME: Need to get layout-manager-type from class
            owner_id = f'{parent_type[0]}LayoutChild'

        for prop in packing.iterfind('property'):
            property_id = prop.get('name')
            translatable = prop.get('translatable', None)
            c.execute("INSERT INTO object_child_property (object_id, child_id, owner_id, property_id, value, translatable) VALUES (?, ?, ?, ?, ?, ?);",
                      (parent_id, object_id, owner_id, property_id, prop.text, translatable))


def db_import(conn, filename):
    c = conn.cursor()

    c.execute("INSERT INTO ui (name, filename) VALUES (?, ?);",
              (os.path.basename(filename), filename))
    ui_id = c.lastrowid

    tree = etree.parse(filename)
    root = tree.getroot()

    requires = root.find('requires')
    if requires is not None:
        lib = requires.get('lib')
    else:
        raise Exception(f'{filename} does not have <requires>')

    for child in root.iterfind('object'):
        db_import_object(c, lib, ui_id, child, None)
        conn.commit()


def db_export_ui(conn, ui_id, filename):
    def node_set(node, attr, val):
        if val is not None:
            node.set(attr, str(val))

    def get_object(conn, object_id):
        c = conn.cursor()
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
            child = E.child(get_object(conn, child_id))

            # Packing / Layout
            layout = E.packing()
            cc = conn.cursor()
            for prop in cc.execute('SELECT value, property_id FROM object_child_property WHERE object_id=? AND child_id=?;',
                                 (object_id, child_id)):
                layout.append(E.property(prop[0], name=prop[1]))
            cc.close()

            if len(layout) > 0:
                child.append(layout)

            obj.append(child)

        c.close()
        return obj

    c = conn.cursor()

    node = E.interface()

    # Iterate over toplovel objects
    for row in c.execute('SELECT object_id FROM object WHERE ui_id=?;',
                         (ui_id,)):
        child = get_object(conn, row[0])
        node.append(child)

    c.close()

    # Dump xml to file
    with open(filename, 'wb') as xml:
        xml.write(etree.tostring(node,
                                 pretty_print=True,
                                 xml_declaration=True,
                                 encoding='UTF-8'))
        xml.close()


def db_export(conn):
    c = conn.cursor()

    for row in c.execute('SELECT ui_id, filename FROM ui;'):
        db_export_ui(conn, row[0], row[1] + '.test.ui')

    c.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Ussage: {sys.argv[0]} database.sqlite library.gir")
        exit()

    conn = db_create(sys.argv[1])

    lib = gir.GirData(sys.argv[2])
    lib.populate_db(conn)

    if len(sys.argv) >= 4:
        db_import(conn, sys.argv[3])
        conn.commit()
        db_export(conn)

    conn.close()
