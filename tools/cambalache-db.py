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
from lxml import etree

from utils import gir


class CambalacheDb:
    def __init__(self):
        # Create DB file
        self.conn = sqlite3.connect(":memory:")

        dirname = os.path.dirname(__file__) or '.'

        # Create DB tables
        with open('../cambalacheui/cmb_base.sql', 'r') as sql:
            self.conn.executescript(sql.read())
            self.conn.commit()

    def _dump_table(self, fd, table):
        def get_row(row):
            r = '('
            first = True

            for c in row:
                if first:
                    first = False
                else:
                    r += ', '

                if type(c)  == str:
                    val = c.replace("'", "''")
                    r += f"'{val}'"
                elif c is None:
                    r += 'NULL'
                else:
                    r += str(c)

            r += ')'

            return r

        c = self.conn.cursor()

        if table == 'type':
            c.execute("SELECT * FROM type WHERE parent_id IS NOT NULL;")
        else:
            c.execute(f"SELECT * FROM {table};")
        row = c.fetchone()

        if row is not None:
            fd.write(f"INSERT INTO {table} VALUES\n")

        while row is not None:
            fd.write(get_row(row))
            row = c.fetchone()
            if row is not None:
                fd.write(',\n')
            else:
                fd.write(';\n\n')

        c.close()

    def dump(self, filename):
        c = self.conn.cursor()

        with open(filename, 'w') as fd:
            fd.write("PRAGMA foreign_keys = OFF;\n")

            for row in c.execute("SELECT name FROM sqlite_master WHERE type = 'table';"):
                self._dump_table(fd, row[0])

            fd.write("PRAGMA foreign_keys = ON;\n")
            fd.close();

        c.close()

    def populate_from_gir(self, girfile):
        lib = gir.GirData(girfile)
        lib.populate_db(self.conn)
        self.conn.commit()
        return lib

    def _import_tag(self, c, node, owner_id, parent_id):
        key = node.tag
        if node.text:
            text = node.text.strip()
            type_id = None if text == '' else text
        else:
            type_id = None

        c.execute("SELECT coalesce((SELECT data_id FROM type_data WHERE owner_id=? ORDER BY data_id DESC LIMIT 1), 0) + 1;",
                  (owner_id, ))
        data_id = c.fetchone()[0]

        c.execute("INSERT INTO type_data (owner_id, data_id, parent_id, key, type_id) VALUES (?, ?, ?, ?, ?);",
                  (owner_id, data_id, parent_id, key, type_id))

        for attr in node.keys():
            c.execute("INSERT INTO type_data_arg (owner_id, data_id, key, type_id) VALUES (?, ?, ?, ?);",
                      (owner_id, data_id, attr, node.get(attr)))

        # Iterate children tags
        for child in node:
            self._import_tag(c, child, owner_id, data_id)

    def populate_extra_data_from_xml(self, filename):
        if not os.path.exists(filename):
            return

        tree = etree.parse(filename)
        root = tree.getroot()

        c = self.conn.cursor()

        for klass in root:
            owner_id = klass.tag

            for child in klass:
                self._import_tag(c, child, owner_id, None)

        c.close()
        self.conn.commit()

if __name__ == "__main__":
    nargs = len(sys.argv)
    if nargs < 3:
        print(f"Ussage: {sys.argv[0]} library.gir database.sqlite")
        exit()

    db = CambalacheDb()

    lib = db.populate_from_gir(sys.argv[1])

    # Load custom type data from json file
    db.populate_extra_data_from_xml(f'{lib.name}.xml')
    db.populate_extra_data_from_xml(f'{lib.name}-{lib.version}.xml')

    db.dump(sys.argv[2])
