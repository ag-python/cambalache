#
# CambalacheDB - Data Model for Cambalache
#
# Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import sys
import sqlite3


def db_create_history_table(c, table):
    # Create Table
    c.executescript(f'''
CREATE TABLE history_{table} AS SELECT * FROM {table} WHERE 0;
ALTER TABLE history_{table} ADD COLUMN history_id INTERGER REFERENCES history;
''')

    # Get table columns
    columns = None
    old_values = None
    new_values = None

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

        if not pk:
            non_pk_columns.append(col)

    # Create history triggers
    select_history_group_id = "(SELECT history_group_id FROM history_group WHERE history_group_id=(SELECT seq FROM sqlite_sequence WHERE name='history_group') AND done IS NULL)"

    # INSERT Trigger
    c.execute(f'''
CREATE TRIGGER on_{table}_insert AFTER INSERT ON {table}
BEGIN
  INSERT INTO history (history_group_id, command, table_name)
    VALUES ({select_history_group_id}, 'INSERT', '{table}');
  INSERT INTO history_{table} (history_id, {columns})
    VALUES (last_insert_rowid(), {new_values});
END;
    ''')

    # DELETE Trigger
    c.execute(f'''
CREATE TRIGGER on_{table}_delete AFTER DELETE ON {table}
BEGIN
  INSERT INTO history (history_group_id, command, table_name)
    VALUES ({select_history_group_id}, 'DELETE', '{table}');
  INSERT INTO history_{table} (history_id, {columns})
    VALUES (last_insert_rowid(), {old_values});
END;
    ''')

    for column in non_pk_columns:
        # UPDATE Trigger
        c.execute(f'''
CREATE TRIGGER on_{table}_update_{column} AFTER UPDATE OF {column} ON {table}
BEGIN
  INSERT INTO history (history_group_id, command, table_name, column_name, column_value)
    VALUES ({select_history_group_id}, 'UPDATE', '{table}', '{column}', NEW.{column});
END;
        ''')


def db_create_history_tables(conn):
    c = conn.cursor()
    db_create_history_table(c, 'object')
    db_create_history_table(c, 'object_property')
    db_create_history_table(c, 'object_child_property')
    db_create_history_table(c, 'object_signal')
    db_create_history_table(c, 'interface')
    db_create_history_table(c, 'interface_object')
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
    if len(sys.argv) < 2:
        print(f"Ussage: {sys.argv[0]} database.sqlite")
        exit()

    conn = db_create(sys.argv[1])
    conn.commit()
    conn.close()
