#
# CambalacheDB - Data Model for Cambalache
#
# Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import sys
import sqlite3

import gir

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
    db_create_history_table(c, 'object',
                            "printf('Delete object %s:%s', OLD.type_id, OLD.name)")
    db_create_history_table(c, 'object_property')
    db_create_history_table(c, 'object_child_property')
    db_create_history_table(c, 'object_signal')
    db_create_history_table(c, 'ui')
    db_create_history_table(c, 'ui_object')
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


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Ussage: {sys.argv[0]} database.sqlite library.gir")
        exit()

    conn = db_create(sys.argv[1])

    lib = gir.GirData(sys.argv[2])
    lib.populate_db(conn)

    conn.commit()
    conn.close()
