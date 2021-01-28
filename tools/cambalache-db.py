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

from utils import gir


class CambalacheDb:
    def __init__(self):
        # Create DB file
        self.conn = sqlite3.connect(":memory:")

        dirname = os.path.dirname(__file__) or '.'

        # Create DB tables
        with open(os.path.join(dirname, '../cambalache/cmb_base.sql'), 'r') as sql:
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
            for row in c.execute("SELECT name FROM sqlite_master WHERE type = 'table';"):
                self._dump_table(fd, row[0])
            fd.close();

        c.close()

    def populate_from_gir(self, girfile):
        lib = gir.GirData(girfile)
        lib.populate_db(self.conn)
        self.conn.commit()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Ussage: {sys.argv[0]} library.gir database.sqlite")
        exit()

    db = CambalacheDb()
    db.populate_from_gir(sys.argv[1])
    db.dump(sys.argv[2])
