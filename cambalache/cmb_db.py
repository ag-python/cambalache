#
# CmbDB - Cambalache DataBase
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

import os
import sys
import sqlite3
import ast
import gi

from lxml import etree
from lxml.builder import E

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, GObject, Gtk
from .config import *
from cambalache import getLogger
from . import cmb_db_migration

logger = getLogger(__name__)


def _get_text_resource(name):
    gbytes = Gio.resources_lookup_data(f'/ar/xjuan/Cambalache/{name}',
                                       Gio.ResourceLookupFlags.NONE)
    return gbytes.get_data().decode('UTF-8')

BASE_SQL = _get_text_resource('db/cmb_base.sql')
PROJECT_SQL = _get_text_resource('db/cmb_project.sql')
HISTORY_SQL = _get_text_resource('db/cmb_history.sql')

GOBJECT_XML = os.path.join(catalogsdir, 'gobject-2.0.xml')
GIO_XML = os.path.join(catalogsdir, 'gio-2.0.xml')
GDKPIXBUF_XML = os.path.join(catalogsdir, 'gdkpixbuf-2.0.xml')
PANGO_XML = os.path.join(catalogsdir, 'pango-1.0.xml')
GDK3_XML = os.path.join(catalogsdir, 'gdk-3.0.xml')
GDK4_XML = os.path.join(catalogsdir, 'gdk-4.0.xml')
GSK4_XML = os.path.join(catalogsdir, 'gsk-4.0.xml')
GTK3_XML = os.path.join(catalogsdir, 'gtk+-3.0.xml')
GTK4_XML = os.path.join(catalogsdir, 'gtk-4.0.xml')

LIBHANDY_XML = os.path.join(catalogsdir, 'libhandy-1.xml')
LIBADWAITA_XML = os.path.join(catalogsdir, 'libadwaita-1.xml')


class CmbDB(GObject.GObject):
    __gtype_name__ = 'CmbDB'

    target_tk = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        self.version = self.__parse_version(VERSION)

        self.type_info = None

        self.__tables = [
            'ui',
            'ui_library',
            'object',
            'object_property',
            'object_layout_property',
            'object_signal',
            'object_data',
            'object_data_arg'
        ]

        self.history_commands = {}

        self.clipboard = []
        self.clipboard_ids = []

        self.conn = sqlite3.connect(':memory:')

        self.conn.create_function('VERSION_CMP', 2, sqlite_version_cmp)
        self.conn.create_aggregate('MAX_VERSION', 1, MaxVersion)

        super().__init__(**kwargs)

        c = self.conn.cursor()
        self.foreign_keys = True

        # Create type system tables
        c.executescript(BASE_SQL)

        # Create project tables
        c.executescript(PROJECT_SQL)

        self.conn.commit()
        c.close()

        # Initialize history (Undo/Redo) tables
        self.__init_dynamic_tables()
        self.__init_data()


    def __del__(self):
        self.conn.commit()
        self.conn.close()

    @GObject.Property(type=bool, default=True)
    def foreign_keys(self):
        self.conn.commit()
        c = self.conn.execute("PRAGMA foreign_keys;")
        fk = c.fetchone()[0]
        c.close()
        return fk

    @foreign_keys.setter
    def _set_foreign_keys(self, value):
        fk = 'ON' if value else 'OFF'
        self.conn.commit()
        self.conn.execute(f"PRAGMA foreign_keys={fk};")

    def __create_support_table(self, c, table):
        _table = table.replace('_', '-')

        # Create a history table to store data for INSERT and DELETE commands
        c.executescript(f'''
    CREATE TABLE history_{table} AS SELECT * FROM {table} WHERE 0;
    ALTER TABLE history_{table} ADD COLUMN history_old BOOLEAN;
    ALTER TABLE history_{table} ADD COLUMN history_id INTERGER REFERENCES history ON DELETE CASCADE;
    CREATE INDEX history_{table}_history_id_fk ON history_{table} (history_id);
    ''')

        # Get table columns
        columns = None
        old_values = None
        new_values = None

        all_columns = []
        pk_columns = []
        non_pk_columns = []

        # Use this flag to know if we should log history or not
        history_is_enabled = "(SELECT value FROM global WHERE key='history_enabled') IS TRUE"
        history_seq = "(SELECT MAX(history_id) FROM history)"
        history_next_seq = f"(coalesce({history_seq}, 0) + 1)"
        clear_history = '''
            DELETE FROM history WHERE (SELECT value FROM global WHERE key='history_index') > 0 AND history_id > (SELECT value FROM global WHERE key='history_index');
            UPDATE global SET value=-1 WHERE key='history_index' AND value >= 0
        '''
        self.__clear_history = clear_history

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
            if pk:
                pk_columns.append(col)
            else:
                non_pk_columns.append(col)

        pkcolumns = ', '.join(pk_columns)
        nonpkcolumns = ', '.join(non_pk_columns)

        command = {
            'PK': f"SELECT {pkcolumns} FROM history_{table} WHERE history_id=?;",
            'COUNT': f"SELECT count(1) FROM {table} WHERE ({pkcolumns}) IS (SELECT {pkcolumns} FROM history_{table} WHERE history_id=?);",
            'DATA': f"SELECT {columns} FROM history_{table} WHERE history_id=?;",
            'DELETE': f"DELETE FROM {table} WHERE ({pkcolumns}) IS (SELECT {pkcolumns} FROM history_{table} WHERE history_id=?);",
            'INSERT': f"INSERT INTO {table} ({columns}) SELECT {columns} FROM history_{table} WHERE history_id=?;",
            'UPDATE': f'UPDATE {table} SET ({nonpkcolumns}) = (SELECT {nonpkcolumns} FROM history_{table} WHERE history_id=? AND history_old=?) \
                        WHERE ({pkcolumns}) IS (SELECT {pkcolumns} FROM history_{table} WHERE history_id=? AND history_old=?);'
        }
        self.history_commands[table] = command

        # INSERT Trigger
        c.execute(f'''
    CREATE TRIGGER on_{table}_insert AFTER INSERT ON {table}
    WHEN
      {history_is_enabled}
    BEGIN
      {clear_history};
      INSERT INTO history (history_id, command, table_name) VALUES ({history_next_seq}, 'INSERT', '{table}');
      INSERT INTO history_{table} (history_id, history_old, {columns})
        VALUES (last_insert_rowid(), 0, {new_values});
    END;
        ''')

        c.execute(f'''
    CREATE TRIGGER on_{table}_delete AFTER DELETE ON {table}
    WHEN
      {history_is_enabled}
    BEGIN
      {clear_history};
      INSERT INTO history (history_id, command, table_name) VALUES ({history_next_seq}, 'DELETE', '{table}');
      INSERT INTO history_{table} (history_id, history_old, {columns})
        VALUES (last_insert_rowid(), 1, {old_values});
    END;
        ''')

        pkcolumns_values = None
        for col in pk_columns:
            if pkcolumns_values == None:
                pkcolumns_values = 'NEW.' + col
            else:
                pkcolumns_values += ', NEW.' + col

        if len(pk_columns) == 0:
            return

        # UPDATE Trigger for each non PK column
        for column in non_pk_columns:
            c.execute(f'''
    CREATE TRIGGER on_{table}_update_{column} AFTER UPDATE OF {column} ON {table}
    WHEN
      NEW.{column} IS NOT OLD.{column} AND {history_is_enabled} AND
      ((SELECT command, table_name, column_name FROM history WHERE history_id = {history_seq})
         IS NOT ('UPDATE', '{table}', '{column}')
         OR
       (SELECT {pkcolumns} FROM history_{table} WHERE history_id = {history_seq} AND history_old=0)
         IS NOT ({pkcolumns_values}))
    BEGIN
      {clear_history};
      INSERT INTO history (history_id, command, table_name, column_name) VALUES ({history_next_seq}, 'UPDATE', '{table}', '{column}');
      INSERT INTO history_{table} (history_id, history_old, {columns})
        VALUES (last_insert_rowid(), 1, {old_values}),
               (last_insert_rowid(), 0, {new_values});
    END;
            ''')

            c.execute(f'''
    CREATE TRIGGER on_{table}_update_{column}_compress AFTER UPDATE OF {column} ON {table}
    WHEN
      NEW.{column} IS NOT OLD.{column} AND {history_is_enabled} AND
      ((SELECT command, table_name, column_name FROM history WHERE history_id = {history_seq})
         IS ('UPDATE', '{table}', '{column}')
         AND
       (SELECT {pkcolumns} FROM history_{table} WHERE history_id = {history_seq} AND history_old=0)
         IS ({pkcolumns_values}))
    BEGIN
      UPDATE history_{table} SET {column}=NEW.{column} WHERE history_id = {history_seq} AND history_old=0;
    END;
            ''')

    def __init_dynamic_tables(self):
        c = self.conn.cursor()

        # Create history main tables
        c.executescript(HISTORY_SQL)

        # Create history tables for each tracked table
        for table in self.__tables:
            self.__create_support_table(c,table)

        self.conn.commit()
        c.close()

    def __init_data(self):
        if self.target_tk not in ['gtk+-3.0', 'gtk-4.0']:
            raise Exception(f'Unknown target tk {self.target_tk}')

        # Add GObject and Gio data
        self.load_catalog(GOBJECT_XML)
        self.load_catalog(GIO_XML)

        # Add GdkPixbuf and Pango data
        self.load_catalog(GDKPIXBUF_XML)
        self.load_catalog(PANGO_XML)

        # Add gtk data
        if self.target_tk == 'gtk+-3.0':
            self.load_catalog(GDK3_XML)
            self.load_catalog(GTK3_XML)
            # FIXME: this should be optional
            self.load_catalog(LIBHANDY_XML)
        elif self.target_tk == 'gtk-4.0':
            self.load_catalog(GDK4_XML)
            self.load_catalog(GSK4_XML)
            self.load_catalog(GTK4_XML)
            # FIXME: this should be optional
            self.load_catalog(LIBADWAITA_XML)

        # TODO: Load all libraries that depend on self.target_tk

    @staticmethod
    def get_target_from_file(filename):
        def get_target_from_line(line, tag):
            if not line.endswith('/>'):
                line = line + f'</{tag}>'

            root = etree.fromstring(line)
            return root.get('target_tk', None)

        retval = None
        try:
            f = open(filename, 'r')
            for line in f:
                line = line.strip()

                # FIXME: find a robust way of doing this without parsing the
                # whole file
                if line.startswith('<cambalache-project'):
                    retval = get_target_from_line(line, 'cambalache-project')
                    break
                elif line.startswith('<project'):
                    retval = get_target_from_line(line, 'project')
                    break
            f.close()
        except:
            pass

        return retval

    def get_data(self, key):
        c = self.execute("SELECT value FROM global WHERE key=?;", (key, ))
        row = c.fetchone()
        c.close()
        return row[0] if row is not None else None

    def set_data(self, key, value):
        self.execute("UPDATE global SET value=? WHERE key=?;", (value, key))

    def get_toplevels(self, ui_id):
        retval = []
        for row in self.execute("SELECT object_id FROM object WHERE ui_id=? AND parent_id IS NULL;", (ui_id, )):
            retval.append(row[0])

        return retval

    def __parse_version(self, version):
        if version is None:
            return (0, 0, 0)

        return parse_version(version)

    def __ensure_table_data_columns(self, version, table, data):
        if version is None:
            return data

        if version < (0, 7, 5):
            return cmb_db_migration.ensure_columns_for_0_7_5(table, data)

        if version < (0, 9, 0):
            return cmb_db_migration.ensure_columns_for_0_9_0(table, data)

        return data

    def __migrate_table_data(self, c, version, table, data):
        if version is None:
            return

        if version < (0, 7, 5):
            cmb_db_migration.migrate_table_data_to_0_7_5(c, table, data)

        if version < (0, 9, 0):
            cmb_db_migration.migrate_table_data_to_0_9_0(c, table, data)

    def __load_table_from_tuples(self, c, table, tuples, version=None):
        data = ast.literal_eval(f'[{tuples}]') if tuples else []

        if len(data) == 0:
            return

        # Ensure table data has the right ammount of columns
        data = self.__ensure_table_data_columns(version, table, data)

        # Load table data
        cols = ', '.join(['?' for col in data[0]])
        c.executemany(f'INSERT INTO {table} VALUES ({cols})', data)

        # Migrate data to current format
        self.__migrate_table_data(c, version, table, data)

    def load(self, filename):
        # TODO: drop all data before loading?

        if filename is None or not os.path.isfile(filename):
            return

        tree = etree.parse(filename)
        root = tree.getroot()

        target_tk = root.get('target_tk', None)

        if target_tk != self.target_tk:
            raise Exception(f'Can not load a {target_tk} target in {self.target_tk} project.')


        version = self.__parse_version(root.get('version', None))

        if version > self.version:
            raise Exception(f'Can not open file version {version}')

        c = self.conn.cursor()

        # Avoid circular dependencies errors
        self.foreign_keys = False

        for child in root.getchildren():
            self.__load_table_from_tuples(c, child.tag, child.text, version)

        self.foreign_keys = True
        c.close()

    def load_catalog(self, filename):
        tree = etree.parse(filename)
        root = tree.getroot()

        name = root.get('name', None)
        version = root.get('version', None)
        namespace = root.get('namespace', None)
        prefix = root.get('prefix', None)
        targets = root.get('targets', '')
        depends = root.get('depends', '')

        c = self.conn.cursor()

        # Insert library
        c.execute("INSERT INTO library(library_id, version, namespace, prefix) VALUES (?, ?, ?, ?);",
                  (name, version, namespace, prefix))

        # Insert target versions
        for target in targets.split(','):
            c.execute("INSERT INTO library_version(library_id, version) VALUES (?, ?);",
                  (name, target))

        # Get dependencies
        deps = {}
        for dep in root.get('depends', '').split(','):
            tokens = dep.split('-')
            if len(tokens) == 2:
                lib, ver = tokens
                deps[lib] = ver

        c = self.conn.cursor()

        # Load dependencies
        for dep in deps:
            c.execute("SELECT version FROM library WHERE library_id=?;",
                      (dep,))
            row = c.fetchone()
            if row and row[0] == deps[dep]:
                continue
            else:
                logger.warning(f'Missing dependency {dep} for {filename}')
                deps.pop(dep)

        # Insert dependencies
        for dep in deps:
            try:
                c.execute("INSERT INTO library_dependency(library_id, dependency_id) VALUES (?, ?);",
                          (name, dep))
            except Exception as e:
                logger.warning(e)
                # TODO: should we try to load the module?
                #pass

        # Avoid circular dependencies errors
        self.foreign_keys = False

        for child in root.getchildren():
            self.__load_table_from_tuples(c, child.tag, child.text)

        self.foreign_keys = True
        c.close()

        self.commit()

    def save(self, filename):
        def get_row(row):
            r = None

            for c in row:
                if r:
                    r += ','
                else:
                    r = ''

                if type(c)  == str:
                    # FIXME: find a better way to escape string
                    val = c.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                    r += f'"{val}"'
                elif c:
                    r += str(c)
                else:
                    r += 'None'

            return f'\t({r})'

        def _dump_table(c, table):
            c.execute(f"SELECT * FROM {table};")
            row = c.fetchone()

            if row is None:
                return None

            retval = ''
            while row is not None:
                retval += get_row(row)
                row = c.fetchone()

                if row:
                    retval += ',\n'

            return f'\n{retval}\n  '

        self.conn.commit()
        c = self.conn.cursor()

        project = E('cambalache-project',
                    version=VERSION,
                    target_tk=self.target_tk)

        for table in self.__tables:
            data = _dump_table(c, table)

            if data is None:
                continue

            element = etree.Element(table)
            element.text = data
            project.append(element)

        # Dump xml to file
        with open(filename, 'wb') as fd:
            tree = etree.ElementTree(project)
            tree.write(fd,
                       pretty_print=True,
                       xml_declaration=True,
                       encoding='UTF-8',
                       standalone=False,
                       doctype='<!DOCTYPE cambalache-project SYSTEM "cambalache-project.dtd">')
            fd.close()

        c.close()

    def backup(self, filename):
        self.conn.commit()
        bck = sqlite3.connect(filename)

        with bck:
            self.conn.backup(bck)

        bck.close()

    def cursor(self):
        return self.conn.cursor()

    def commit(self):
        return self.conn.commit()

    def execute(self, *args):
        return self.conn.execute(*args)

    def add_ui(self, name, filename, requirements={}, comment=None):
        c = self.conn.cursor()
        c.execute("INSERT INTO ui (name, filename, comment) VALUES (?, ?, ?);",
                  (name, filename, comment))
        ui_id = c.lastrowid

        for key in requirements:
            req = requirements[key]
            c.execute('INSERT INTO ui_library (ui_id, library_id, version, comment) VALUES (?, ?, ?, ?);',
                      (ui_id, key, req['version'], req['comment']))
        c.close()

        return ui_id

    def add_object(self, ui_id, obj_type, name=None, parent_id=None, internal_child=None, child_type=None, comment=None, layout=None, position=None, inline_property=None):
        c = self.conn.cursor()

        c.execute("SELECT coalesce((SELECT object_id FROM object WHERE ui_id=? ORDER BY object_id DESC LIMIT 1), 0) + 1;", (ui_id, ))
        object_id = c.fetchone()[0]

        if position is None:
            c.execute("""
                SELECT count(object_id)
                    FROM object
                    WHERE ui_id=? AND parent_id=?
                        AND object_id NOT IN (SELECT inline_object_id FROM object_property WHERE inline_object_id IS NOT NULL AND ui_id=? AND object_id=?);
                """,
                      (ui_id, parent_id, ui_id, parent_id))
            position = c.fetchone()[0]

        c.execute("INSERT INTO object (ui_id, object_id, type_id, name, parent_id, internal, type, comment, position) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                  (ui_id, object_id, obj_type, name, parent_id, internal_child, child_type, comment, position))

        # Get parent type for later
        if layout or inline_property:
            c.execute("SELECT type_id FROM object WHERE ui_id=? AND object_id=?;", (ui_id, parent_id))
            row = c.fetchone()
            parent_type = row[0] if row else None
        else:
            parent_type = None

        if layout and parent_type:
            for property_id in layout:
                owner_id = self.__get_layout_property_owner(parent_type, property_id)
                c.execute("INSERT INTO object_layout_property (ui_id, object_id, child_id, owner_id, property_id, value) VALUES (?, ?, ?, ?, ?, ?);",
                          (ui_id, parent_id, object_id, owner_id, property_id, layout[property_id]))

        if parent_id and parent_type and inline_property:
            info = self.type_info.get(parent_type, None)
            pinfo = self.__get_property_info(info, inline_property)

            c.execute("SELECT count(object_id) FROM object_property WHERE ui_id=? AND object_id=? AND owner_id=? AND property_id=?;",
                      (ui_id, parent_id, pinfo.owner_id, inline_property))
            count = c.fetchone()[0]

            if count:
                c.execute("UPDATE object_property SET inline_object_id=? WHERE ui_id=? AND object_id=? AND owner_id=? AND property_id;",
                          (object_id, ui_id, parent_id, pinfo.owner_id, inline_property))
            else:
                c.execute("INSERT INTO object_property(ui_id, object_id, owner_id, property_id, inline_object_id) VALUES(?, ?, ?, ?, ?)",
                          (ui_id, parent_id, pinfo.owner_id, inline_property, object_id))

        c.close()

        return object_id

    def __collect_error(self, error, node, name):
        # Ensure error object
        if error not in self.errors:
            self.errors[error] = {}

        errors = self.errors[error]

        # Ensure list
        if name not in errors:
            errors[name] = []

        # Add unknown tag occurence
        errors[name].append(node.sourceline)

    def __unknown_tag(self, node, owner, name):
        if node.tag is etree.Comment:
            return;

        self.__collect_error('unknown-tag', node, f'{owner}:{name}' if owner and name else name)

    def __node_get(self, node, *args):
        keys = node.keys()
        knowns = []
        retval = []

        for attr in args:
            if isinstance(attr, list):
                for opt in attr:
                    retval.append(node.get(opt, None))
                    knowns.append(opt)
            elif attr in keys:
                retval.append(node.get(attr))
                knowns.append(attr)
            else:
                self.__collect_error('missing-attr', node, attr)

        unknown = list(set(keys) - set(knowns))

        for attr in unknown:
            self.__collect_error('unknown-attr', node, attr)

        return retval

    def __get_property_info(self, info, property_id):
        pinfo = None

        # Find owner type for property
        if property_id in info.properties:
            pinfo = info.properties[property_id]
        else:
            for parent in info.hierarchy:
                type_info = self.type_info[parent]
                if property_id in type_info.properties:
                    pinfo = type_info.properties[property_id]
                    break

        return pinfo

    def __import_property(self, c, info, ui_id, object_id, prop, object_id_map=None):
        name, translatable, context, comments = self.__node_get(prop, 'name', ['translatable', 'context', 'comments'])

        property_id = name.replace('_', '-')
        comment = self.__node_get_comment(prop)

        pinfo = self.__get_property_info(info, property_id)

        # Insert property
        if not pinfo:
            self.__collect_error('unknown-property', prop, f'{info.type_id}:{property_id}')
            return

        # Property value
        value = prop.text

        # Initialize to null
        inline_object_id = None

        # GtkBuilder in Gtk4 supports defining an object in a property
        if self.target_tk == 'gtk-4.0' and pinfo.is_object and pinfo.is_inline_object:
            obj_node = prop.find('object')
            if obj_node is not None:
                inline_object_id = self.__import_object(ui_id, obj_node, object_id)
                value = None

        # Need to remap object ids on paste
        if object_id_map and pinfo.is_object:
            value = object_id_map.get(value, value)

        try:
            c.execute("INSERT INTO object_property (ui_id, object_id, owner_id, property_id, value, translatable, comment, translation_context, translation_comments, inline_object_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                      (ui_id, object_id, pinfo.owner_id, property_id, value, translatable, comment, context, comments, inline_object_id))
        except Exception as e:
            raise Exception(f'XML:{prop.sourceline} - Can not import object {object_id} {pinfo.owner_id}:{property_id} property: {e}')

    def __import_signal(self, c, info, ui_id, object_id, signal, object_id_map=None):
        name, handler, user_data, swap, after, = self.__node_get(signal, 'name', ['handler', 'object', 'swapped', 'after'])

        tokens = name.split('::')

        if len(tokens) > 1:
            signal_id = tokens[0]
            detail = tokens[1]
        else:
            signal_id = tokens[0]
            detail = None

        comment = self.__node_get_comment(signal)

        # Find owner type for signal
        if signal_id in info.signals:
            owner_id = info.type_id
        else:
            for parent in info.hierarchy:
                pinfo = self.type_info[parent]
                if signal_id in pinfo.signals:
                    owner_id = parent
                    break

        # Need to remap object ids on paste
        if object_id_map and user_data:
            user_data = object_id_map.get(user_data, user_data)

        # Insert signal
        if not owner_id:
            self.__collect_error('unknown-signal', signal, f'{info.type_id}:{signal_id}')
            return

        try:
            c.execute("INSERT INTO object_signal (ui_id, object_id, owner_id, signal_id, handler, detail, user_data, swap, after, comment) VALUES (?, ?, ?, ?, ?, ?, (SELECT object_id FROM object WHERE ui_id=? AND name=?), ?, ?, ?);",
                      (ui_id, object_id, owner_id, signal_id, handler, detail, ui_id, user_data, swap, after, comment))
        except Exception as e:
            raise Exception(f'XML:{signal.sourceline} - Can not import object {object_id} {owner_id}:{signal_id} signal: {e}')

    def __import_child(self, c, info, ui_id, parent_id, child, object_id_map=None):
        ctype, internal = self.__node_get(child, ['type', 'internal-child'])
        object_id = None
        packing = None

        for node in child.iterchildren():
            if node.tag == 'object':
                object_id = self.__import_object(ui_id, node, parent_id, internal, ctype, object_id_map=object_id_map)
            elif node.tag == 'packing' and self.target_tk == 'gtk+-3.0':
                # Gtk 3, packing props are sibling to <object>
                packing = node
            elif node.tag == 'placeholder':
                # Ignore placeholder tags
                pass
            else:
                self.__unknown_tag(node, ctype, node.tag)

        if packing is not None and object_id:
            self.__import_layout_properties(c, info, ui_id, parent_id, object_id, packing)

    def __get_layout_property_owner(self, type_id, property_id):
        info = self.type_info.get(type_id, None)

        if info is None:
            return None

        # Walk type hierarchy until we find the Layout child property
        while info:
            owner = self.type_info.get(f'{info.type_id}LayoutChild', None)

            if owner and owner.properties.get(property_id, None) is not None:
                return owner.type_id

            info = info.parent

        return None

    def __import_layout_properties(self, c, info, ui_id, parent_id, object_id, layout):
        c.execute("SELECT type_id FROM object WHERE ui_id=? AND object_id=?;", (ui_id, parent_id))
        parent_type = c.fetchone()

        if parent_type is None:
            return

        for prop in layout.iterchildren():
            if prop.tag != 'property':
                self.__unknown_tag(prop, owner_id, prop.tag)
                continue

            name, translatable, context, comments = self.__node_get(prop, 'name', ['translatable', 'context', 'comments'])
            property_id = name.replace('_', '-')
            comment = self.__node_get_comment(prop)
            owner_id = self.__get_layout_property_owner(parent_type[0], property_id)
            owner_info = self.type_info.get(owner_id, None)

            if owner_info:
                pinfo = owner_info.properties.get(property_id, None)

                # Update object position if this layout property is_position
                if pinfo and pinfo.is_position:
                    c.execute("UPDATE object SET position=? WHERE ui_id=? AND object_id=?;",
                              (prop.text, ui_id, object_id))
                    continue

            try:
                c.execute("INSERT INTO object_layout_property (ui_id, object_id, child_id, owner_id, property_id, value, translatable, comment, translation_context, translation_comments) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                          (ui_id, parent_id, object_id, owner_id, property_id, prop.text, translatable, comment, context, comments))
            except Exception as e:
                raise Exception(f'XML:{prop.sourceline} - Can not import object {object_id} {owner_id}:{property_id} layout property: {e}')

    def object_add_data(self, ui_id, object_id, owner_id, data_id, value=None, parent_id=None, comment=None):
        c = self.conn.cursor()

        c.execute("SELECT coalesce((SELECT id FROM object_data WHERE ui_id=? AND object_id=? AND owner_id=? ORDER BY id DESC LIMIT 1), 0) + 1;",
                  (ui_id, object_id, owner_id))
        id = c.fetchone()[0]

        c.execute("INSERT INTO object_data (ui_id, object_id, owner_id, data_id, id, value, parent_id, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                  (ui_id, object_id, owner_id, data_id, id, value, parent_id, comment))
        c.close()

        return id

    def object_add_data_arg(self, ui_id, object_id, owner_id, data_id, id, key, val):
        c = self.conn.cursor()
        c.execute("INSERT INTO object_data_arg (ui_id, object_id, owner_id, data_id, id, key, value) VALUES (?, ?, ?, ?, ?, ?, ?);",
                  (ui_id, object_id, owner_id, data_id, id, key, val))
        c.close()

    def __import_object_data(self, ui_id, object_id, owner_id, taginfo, ntag, parent_id):
        c = self.conn.cursor()

        data_id = taginfo.data_id
        text = ntag.text.strip() if ntag.text else None
        value = text if text and len(text) > 0 else None
        comment = self.__node_get_comment(ntag)

        id = self.object_add_data(ui_id, object_id, owner_id, data_id, value, parent_id, comment)

        for key in taginfo.args:
            val = ntag.get(key, None)
            self.object_add_data_arg(ui_id, object_id, owner_id, data_id, id, key, val)

        for child in ntag.iterchildren():
            if child.tag in taginfo.children:
                self.__import_object_data(ui_id,
                                          object_id,
                                          owner_id,
                                          taginfo.children[child.tag],
                                          child,
                                          id)
            else:
                self.__unknown_tag(child, owner_id, child.tag)

        c.close()

    def __import_object(self, ui_id, node, parent_id, internal_child=None, child_type=None, is_template=False, object_id_map=None):
        is_template = node.tag == 'template'

        if is_template:
            klass, name = self.__node_get(node, 'parent', 'class')
        else:
            klass, name = self.__node_get(node, 'class', ['id'])

        comment = self.__node_get_comment(node)
        info = self.type_info.get(klass, None)

        if not info:
            self.__collect_error('unknown-type', node, klass)
            return

        # Need to remap object ids on paste
        if object_id_map:
            name = object_id_map.get(name, name)

        # Insert object
        try:
            object_id = self.add_object(ui_id, klass, name, parent_id, internal_child, child_type, comment)
        except:
            logger.warning(f'XML:{node.sourceline} - Error importing {klass}')
            return

        c = self.conn.cursor()

        if is_template:
            c.execute("UPDATE ui SET template_id=? WHERE ui_id=?", (object_id, ui_id))

        def find_data_info(info, tag):
            if tag in info.data:
                return info

            for parent in info.hierarchy:
                pinfo = self.type_info[parent]

                if tag in pinfo.data:
                    return pinfo

        for child in node.iterchildren():
            if child.tag == 'property':
                self.__import_property(c, info, ui_id, object_id, child, object_id_map=object_id_map)
            elif child.tag == 'signal':
                self.__import_signal(c, info, ui_id, object_id, child, object_id_map=object_id_map)
            elif child.tag == 'child':
                self.__import_child(c, info, ui_id, object_id, child, object_id_map=object_id_map)
            elif child.tag == 'layout' and self.target_tk == 'gtk-4.0':
                # Gtk 4, layout props are children of <object>
                self.__import_layout_properties(c, info, ui_id, parent_id, object_id, child)
            else:
                # Custom buildable tags
                taginfo = info.get_data_info(child.tag)

                if taginfo is not None:
                    self.__import_object_data(ui_id, object_id, taginfo.owner_id, taginfo, child, None)
                else:
                    self.__unknown_tag(child, klass, child.tag)

        c.close()

        return object_id

    def __node_get_comment(self, node):
        prev = node.getprevious()
        if prev is not None and prev.tag is etree.Comment:
            return prev.text if not prev.text.strip().startswith('interface-') else None
        return None

    def __node_get_requirements(self, root):
        retval = {}

        # Collect requirements and comments
        for req in root.iterfind('requires'):
            lib, version = self.__node_get(req, 'lib', 'version')

            retval[lib] = {
              'version': version,
              'comment': self.__node_get_comment(req)
            }

        return retval

    @staticmethod
    def _get_target_from_node(root):
        if root.tag != 'interface':
            return (None, None, None)

        # Look for explicit gtk version first
        for req in root.iterfind('requires'):
            lib = req.get('lib', None)
            version = req.get('version', '')

            if lib == 'gtk' and version.startswith('4.'):
                return (lib, '4.0', False)
            elif lib == 'gtk+' and version.startswith('3.'):
                return (lib, '3.0', False)

        # Infer target by looking for layout/packing tags
        if root.find('.//layout') is not None:
            return ('gtk', '4.0', True)

        if root.find('.//packing') is not None:
            return ('gtk+', '3.0', True)

        return (None, None, None)

    def __fix_object_references(self, ui_id):
        self.conn.execute('''
            UPDATE object_property AS op SET value=o.object_id
            FROM property AS p, object AS o
            WHERE op.ui_id=? AND p.is_object AND op.owner_id = p.owner_id AND
                  op.property_id = p.property_id AND o.ui_id = op.ui_id AND
                  o.name = op.value;
            ''',
            (ui_id, ))

    def import_file(self, filename, projectdir='.'):
        # Clear parsing errors
        self.errors = {}

        tree = etree.parse(filename)
        root = tree.getroot()

        requirements = self.__node_get_requirements(root)

        target_tk = self.target_tk
        lib, ver, inferred = CmbDB._get_target_from_node(root)

        if (target_tk == 'gtk-4.0' and lib != 'gtk') or \
           (target_tk == 'gtk+-3.0' and lib != 'gtk+'):
            # Translators: This text will be used in the next two string as {convert}
            convert = _('\nUse gtk4-builder-tool first to convert file.') if target_tk == 'gtk-4.0' else ''

            if lib is None:
                raise Exception(_('Can not recognize file format'))

            if inferred:
                # Translators: {convert} will be replaced with the gtk4-builder-tool string
                raise Exception(_('Can not import what looks like a {lib}-{ver} file in a {target_tk} project.{convert}').format(lib=lib, ver=ver, target_tk=target_tk, convert=convert))
            else:
                # Translators: {convert} will be replaced with the gtk4-builder-tool string
                raise Exception(_('Can not import a {lib}-{ver} file in a {target_tk} project.{convert}').format(lib=lib, ver=ver, target_tk=target_tk, convert=convert))

        c = self.conn.cursor()

        # Update interface comment
        comment = self.__node_get_comment(root)
        if comment and comment.strip().startswith('Created with Cambalache'):
            comment = None

        # Make sure there is no attributes in root tag
        self.__node_get(root)

        basename = os.path.basename(filename)
        relpath = os.path.relpath(filename, projectdir)
        ui_id = self.add_ui(basename, relpath, requirements, comment)

        # These values come from Glade
        license_map = {
            'other': 'custom',
            'gplv2': 'gpl_2_0',
            'gplv3': 'gpl_3_0',
            'lgplv2': 'lgpl_2_1',
            'lgplv3': 'lgpl_3_0',
            'bsd2c': 'bsd',
            'bsd3c': 'bsd_3',
            'apache2': 'apache_2_0',
            'mit': 'mit_x11'
        }

        # XML key <-> table column
        interface_key_map = {
            'interface-license-id': 'license_id',
            'interface-name': 'name',
            'interface-description': 'description',
            'interface-copyright': 'copyright',
            'interface-authors': 'authors'
        }

        # Import objects
        for child in root.iterchildren():
            if child.tag == 'object':
                self.__import_object(ui_id, child, None)
            elif child.tag == 'template':
                self.__import_object(ui_id, child, None)
            elif child.tag == 'requires':
                pass
            elif child.tag is etree.Comment:
                comment = etree.tostring(child).decode('utf-8').strip()
                comment = comment.removeprefix('<!--').removesuffix('-->').strip()

                # Import interface data from Glade comments
                if comment.startswith('interface-'):
                    key, value = comment.split(' ', 1)
                    if key == 'interface-license-type':
                        license = license_map.get(value, 'unknown')
                        c.execute("UPDATE ui SET license_id=? WHERE ui_id=?", (license, ui_id))
                    else:
                        column = interface_key_map.get(key, None)
                        if column is not None:
                            c.execute(f"UPDATE ui SET {column}=? WHERE ui_id=?", (value, ui_id))
            else:
                self.__unknown_tag(child, None, child.tag)

            while Gtk.events_pending():
                Gtk.main_iteration_do(False)

        # Fix object references!
        self.__fix_object_references(ui_id)

        # Check for parsing errors and append .cmb if something is not supported
        if len(self.errors):
            filename, etx = os.path.splitext(relpath)
            c.execute("UPDATE ui SET filename=? WHERE ui_id=?", (f"{filename}.cmb.ui", ui_id))

        self.conn.commit()
        c.close()

        return ui_id

    def __node_add_comment(self, node, comment):
        if comment:
            node.addprevious(etree.Comment(comment))

    def __export_object(self, ui_id, object_id, merengue=False, template_id=None):

        def node_set(node, attr, val):
            if val is not None:
                node.set(attr, str(val))

        c = self.conn.cursor()
        cc = self.conn.cursor()

        c.execute('SELECT type_id, name FROM object WHERE ui_id=? AND object_id=?;', (ui_id, object_id))
        type_id, name = c.fetchone()

        info = self.type_info.get(type_id, None)

        if not merengue and template_id == object_id:
            obj = E.template()
            node_set(obj, 'class', name)
            node_set(obj, 'parent', type_id)
        else:
            obj = E.object()

            if merengue:
                workspace_type = info.workspace_type
                node_set(obj, 'class', workspace_type if workspace_type else type_id)
                node_set(obj, 'id', f'__cmb__{ui_id}.{object_id}')
            else:
                node_set(obj, 'class', type_id)
                node_set(obj, 'id', name)

        # Create class hierarchy list
        hierarchy = [type_id] + info.hierarchy if info else [type_id]

        # SQL placeholder for every class in the list
        placeholders = ','.join((['?'] * len(hierarchy)))

        # Properties + save_always default values
        for row in c.execute(f'''
                SELECT op.value, op.property_id, op.inline_object_id, op.comment, op.translatable, op.translation_context, op.translation_comments, p.is_object, p.is_inline_object
                  FROM object_property AS op, property AS p
                  WHERE op.ui_id=? AND op.object_id=? AND
                    p.owner_id = op.owner_id AND
                    p.property_id = op.property_id
                UNION
                SELECT default_value, property_id, null, null, null, null, null, is_object, is_inline_object
                  FROM property
                  WHERE save_always=1 AND owner_id IN ({placeholders}) AND
                    property_id NOT IN
                    (SELECT property_id
                     FROM object_property
                     WHERE ui_id=? AND object_id=?)
                ORDER BY op.property_id
                ''',
                (ui_id, object_id) + tuple(hierarchy) + (ui_id, object_id)):
            val, property_id, inline_object_id, comment, translatable, translation_context, translation_comments, is_object, is_inline_object = row

            if is_object:
                # Ignore object properties with 0/null ID
                if val is not None and int(val) == 0:
                    continue

                if inline_object_id and is_inline_object:
                    value = self.__export_object(ui_id, inline_object_id, merengue=merengue)
                else:
                    if merengue:
                        value = f'__cmb__{ui_id}.{val}'
                    else:
                        cc.execute('SELECT name FROM object WHERE ui_id=? AND object_id=?;', (ui_id, val))
                        row = cc.fetchone()
                        if row is None:
                            continue
                        value = row[0]
            else:
                value = val

            node = E.property(value, name=property_id)

            if translatable:
                node_set(node, 'translatable', 'yes')
                node_set(node, 'context', translation_context)
                node_set(node, 'comments', translation_comments)

            obj.append(node)
            self.__node_add_comment(node, comment)

        # Signals
        for row in c.execute('SELECT signal_id, handler, detail, (SELECT name FROM object WHERE ui_id=? AND object_id=user_data), swap, after, comment FROM object_signal WHERE ui_id=? AND object_id=?;',
                             (ui_id, ui_id, object_id,)):
            signal_id, handler, detail, data, swap, after, comment = row
            name = f'{signal_id}::{detail}' if detail is not None else signal_id
            node = E.signal(name=name, handler=handler)
            node_set(node, 'object', data)
            if swap:
                node_set(node, 'swapped', 'yes')
            if after:
                node_set(node, 'after', 'yes')
            obj.append(node)
            self.__node_add_comment(node, comment)

        # Layout properties class
        layout_class = f'{type_id}LayoutChild'
        linfo = self.type_info.get(layout_class, None)

        # Construct Layout Child class hierarchy list
        hierarchy = [layout_class] + linfo.hierarchy if linfo else [layout_class]

        # SQL placeholder for every class in the list
        placeholders = ','.join((['?'] * len(hierarchy)))

        child_position = 0

        # Children
        for row in c.execute('''
            SELECT object_id, internal, type, comment, position
                FROM object
                WHERE ui_id=? AND parent_id=?
                    AND object_id NOT IN (SELECT inline_object_id FROM object_property WHERE inline_object_id IS NOT NULL AND ui_id=? AND object_id=?)
                ORDER BY position;''', (ui_id, object_id, ui_id, object_id)):
            child_id, internal, ctype,  comment, position = row

            if merengue:
                position = position if position is not None else 0

                while child_position < position:
                    placeholder = E.object()
                    placeholder.set('class', 'MrgPlaceholder')
                    obj.append(E.child(placeholder))
                    child_position += 1

                child_position += 1

            child_obj = self.__export_object(ui_id, child_id, merengue=merengue)
            child = E.child(child_obj)
            node_set(child, 'internal-child', internal)
            node_set(child, 'type', ctype)
            self.__node_add_comment(child_obj, comment)

            obj.append(child)

            if linfo is None:
                continue

            # Packing / Layout
            layout = E('packing' if self.target_tk == 'gtk+-3.0' else 'layout')
            for prop in cc.execute(f'''
                    SELECT value, property_id, comment
                      FROM object_layout_property
                      WHERE ui_id=? AND object_id=? AND child_id=?
                    UNION
                    SELECT default_value AS value, property_id, null
                      FROM property
                      WHERE save_always=1 AND owner_id IN ({placeholders}) AND property_id NOT IN
                        (SELECT property_id FROM object_layout_property
                         WHERE ui_id=? AND object_id=? AND child_id=?)
                    ORDER BY property_id
                    ''',
                    (ui_id, object_id, child_id) +
                    tuple(hierarchy) +
                    (ui_id, object_id, child_id)):
                value, property_id, comment = prop
                node = E.property(value, name=property_id)
                layout.append(node)
                self.__node_add_comment(node, comment)

            if len(layout) > 0:
                if self.target_tk == 'gtk+-3.0':
                    child.append(layout)
                else:
                    child_obj.append(layout)

        # Custom buildable tags
        def export_object_data(owner_id, name, info, node, parent_id):
            c = self.conn.cursor()
            cc = self.conn.cursor()

            for row in c.execute('SELECT id, value, comment FROM object_data WHERE ui_id=? AND object_id=? AND owner_id=? AND data_id=? AND parent_id=?;',
                                 (ui_id, object_id, owner_id, info.data_id, parent_id)):
                id, value, comment = row
                ntag = etree.Element(name)
                if value:
                    ntag.text = value
                node.append(ntag)
                self.__node_add_comment(ntag, comment)

                for row in cc.execute('SELECT key, value FROM object_data_arg WHERE ui_id=? AND object_id=? AND owner_id=? AND data_id=? AND id=? AND value IS NOT NULL;',
                                      (ui_id, object_id, owner_id, info.data_id, id)):
                    key, value = row
                    ntag.set(key, value)

                for tag in info.children:
                    export_object_data(owner_id, tag, info.children[tag], ntag, id)

            c.close()
            cc.close()

        def export_type_data(owner_id, info, node):
            if len(info.data.keys()) == 0:
                return

            for tag in info.data:
                taginfo = info.data[tag]

                for row in c.execute('SELECT id, value, comment FROM object_data WHERE ui_id=? AND object_id=? AND owner_id=? AND data_id=?;',
                                     (ui_id, object_id, owner_id, taginfo.data_id)):
                    id, value, comment = row
                    ntag = etree.Element(tag)
                    if value:
                        ntag.text = value
                    node.append(ntag)
                    self.__node_add_comment(ntag, comment)

                    for child in taginfo.children:
                        export_object_data(owner_id, child, taginfo.children[child], ntag, id)

        # Iterate over all hierarchy extra data
        export_type_data(type_id, info, obj)
        for parent in info.hierarchy:
            pinfo = self.type_info[parent]
            export_type_data(parent, pinfo, obj)

        c.close()
        cc.close()

        return obj

    def export_ui(self, ui_id, merengue=False):
        c = self.conn.cursor()

        node = E.interface()
        node.addprevious(etree.Comment(f" Created with Cambalache {VERSION} "))

        c.execute('SELECT comment, template_id FROM ui WHERE ui_id=?;', (ui_id,))
        row = c.fetchone()

        if row is None:
            return None

        comment, template_id = row
        self.__node_add_comment(node, comment)

        # Export UI data as comments
        for key in ['name', 'description', 'copyright', 'authors', 'license_id']:
            c.execute(f'SELECT {key} FROM ui WHERE ui_id=?;', (ui_id, ))
            value = c.fetchone()[0]

            if value is not None:
                key = key.replace('_', '-')
                node.append(etree.Comment(f' interface-{key} {value} '))

        # Requires selected by the user
        for row in c.execute('SELECT library_id, version, comment FROM ui_library WHERE ui_id=?;', (ui_id,)):
            library_id, version, comment = row
            req = E.requires(lib=library_id, version=version)
            self.__node_add_comment(req, comment)
            node.append(req)

        # Ensure we output a requires lib for every used module
        # If the user did not specify a requirement version we use the latest
        for row in c.execute('''SELECT l.library_id, MAX_VERSION(v.version)
            FROM library AS l, library_version AS v
            WHERE l.library_id=v.library_id AND
                l.library_id NOT IN (SELECT library_id FROM ui_library WHERE ui_id=?) AND
                l.library_id IN (SELECT DISTINCT t.library_id FROM object AS o, type AS t WHERE o.ui_id=? AND o.type_id = t.type_id)
            GROUP BY l.library_id;''', (ui_id, ui_id)):
            library_id, version = row
            req = E.requires(lib=library_id, version=version)
            node.append(req)

        # Iterate over toplovel objects
        for row in c.execute('SELECT object_id, comment FROM object WHERE parent_id IS NULL AND ui_id=?;',
                             (ui_id,)):
            object_id, comment = row
            child = self.__export_object(ui_id, object_id, merengue=merengue, template_id=template_id)
            node.append(child)
            self.__node_add_comment(child, comment)

        c.close()

        return etree.ElementTree(node)

    def tostring(self, ui_id, merengue=False):
        ui = self.export_ui(ui_id, merengue=merengue)

        if ui is None:
            return None

        return etree.tostring(ui,
                              pretty_print=True,
                              xml_declaration=True,
                              encoding='UTF-8').decode('UTF-8')

    def clipboard_copy(self, selection):
        self.clipboard = []
        self.clipboard_ids = []

        c = self.conn.cursor()

        # Copy data for every object in selection
        for ui_id, object_id in selection:
            node = self.__export_object(ui_id, object_id)
            self.clipboard.append(node)

            c.execute('''
                 WITH RECURSIVE ancestor(object_id, parent_id, name) AS (
                   SELECT object_id, parent_id, name
                     FROM object
                     WHERE ui_id=? AND object_id=?
                   UNION
                   SELECT object.object_id, object.parent_id, object.name
                     FROM object JOIN ancestor ON object.parent_id=ancestor.object_id
                     WHERE ui_id=?
                 )
                 SELECT name FROM ancestor WHERE name IS NOT NULL''',
                 (ui_id, object_id, ui_id))

            # Object ids that will need to be remapped
            self.clipboard_ids += tuple([ x[0] for x in c.fetchall() ])

        c.close()

    def clipboard_paste(self, ui_id, parent_id):
        c = self.conn.cursor()
        object_id_map = {}
        retval = {}

        # Generate new object_id mapping
        for object_id in self.clipboard_ids:
            object_id_base = object_id

            tokens = object_id_base.rsplit('_', 1)
            if len(tokens) == 2 and tokens[1].isdigit():
                object_id_base = tokens[0]

            max_index = 0
            for row in c.execute('SELECT name FROM object WHERE ui_id=? AND name IS NOT NULL AND name LIKE ?;',
                                  (ui_id, f'{object_id_base}%')):
                tokens = row[0].rsplit('_', 1)

                if len(tokens) == 2 and tokens[0] == object_id_base:
                    try:
                        max_index = max(max_index, int(tokens[1]))
                    except:
                        pass
                elif row[0] == object_id_base:
                    max_index = 1

            object_id_map[object_id] = f'{object_id_base}_{max_index+1}' if max_index else object_id

        for node in self.clipboard:
            object_id = self.__import_object(ui_id, node, parent_id, object_id_map=object_id_map)

            c.execute('''
                 WITH RECURSIVE ancestor(object_id, parent_id) AS (
                   SELECT object_id, parent_id
                     FROM object
                     WHERE ui_id=? AND object_id=?
                   UNION
                   SELECT object.object_id, object.parent_id
                     FROM object JOIN ancestor ON object.parent_id=ancestor.object_id
                     WHERE ui_id=?
                 )
                 SELECT object_id FROM ancestor''',
                 (ui_id, object_id, ui_id))

            # Object and children ids
            retval[object_id] = tuple([ x[0] for x in c.fetchall() ])

        self.__fix_object_references(ui_id)

        c.close()
        return retval

    def clear_history(self):
        self.conn.executescript(self.__clear_history)


# Function used in SQLite

def parse_version(version):
    return tuple([int(x) for x in version.split('.')])

def version_cmp(a, b):
    an = len(a)
    bn = len(a)

    for i in range(0, max(an, bn)):
        val_a = a[i] if i < an else 0
        val_b = b[i] if i < bn else 0
        retval = val_a - val_b

        if retval != 0:
            return retval

    return 0

# Compares two version strings
def sqlite_version_cmp(a, b):
    return version_cmp(parse_version(a), parse_version(b))


# Aggregate class to get the MAX version
class MaxVersion:
    def __init__(self):
        self.max_ver = None
        self.max_ver_str = None

    def step(self, value):
        ver = parse_version(value)

        if self.max_ver is None or version_cmp(self.max_ver, ver) < 0:
            self.max_ver = ver
            self.max_ver_str = value

    def finalize(self):
        return self.max_ver_str
