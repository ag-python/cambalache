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
from locale import gettext as _

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, GObject, Gtk
from .config import *


def _get_text_resource(name):
    gbytes = Gio.resources_lookup_data(f'/ar/xjuan/Cambalache/{name}',
                                       Gio.ResourceLookupFlags.NONE)
    return gbytes.get_data().decode('UTF-8')

BASE_SQL = _get_text_resource('cmb_base.sql')
PROJECT_SQL = _get_text_resource('cmb_project.sql')
HISTORY_SQL = _get_text_resource('cmb_history.sql')

GOBJECT_XML = os.path.join(catalogsdir, 'gobject-2.0.xml')
GTK3_XML = os.path.join(catalogsdir, 'gtk+-3.0.xml')
GTK4_XML = os.path.join(catalogsdir, 'gtk-4.0.xml')


class CmbDB(GObject.GObject):
    __gtype_name__ = 'CmbDB'

    target_tk = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        self.type_info = None

        self.history_commands = {}

        self.conn = sqlite3.connect(':memory:')

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
        self._init_history_and_triggers()
        self._init_data()


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

    def _create_support_table(self, c, table):
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

    def _init_history_and_triggers(self):
        c = self.conn.cursor()

        # Create history main tables
        c.executescript(HISTORY_SQL)

        # Create history tables for each tracked table
        self._create_support_table(c, 'ui')
        self._create_support_table(c, 'ui_library')
        self._create_support_table(c, 'object')
        self._create_support_table(c, 'object_property')
        self._create_support_table(c, 'object_layout_property')
        self._create_support_table(c, 'object_signal')
        self._create_support_table(c, 'object_data')
        self._create_support_table(c, 'object_data_arg')

        self.conn.commit()
        c.close()

    def _init_data(self):
        if self.target_tk not in ['gtk+-3.0', 'gtk-4.0']:
            raise Exception(f'Unknown target tk {self.target_tk}')

        # Add GObject data
        self.load_catalog(GOBJECT_XML)

        # Add gtk data
        if self.target_tk == 'gtk+-3.0':
            self.load_catalog(GTK3_XML)
        elif self.target_tk == 'gtk-4.0':
            self.load_catalog(GTK4_XML)

        # TODO: Load all libraries that depend on self.target_tk

    @staticmethod
    def get_target_from_file(filename):
        retval = None
        try:
            f = open(filename, 'r')
            for line in f:
                line = line.strip()

                # FIXME: find a robust way of doing this without parsing the
                # whole file
                if line.startswith('<cambalache-project'):
                    root = etree.fromstring(line + '</cambalache-project>')
                    retval = root.get('target_tk', None)
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

    def _load_table_from_tuples(self, c, table, tuples):
        data = ast.literal_eval(f'[{tuples}]') if tuples else []

        if len(data):
            cols = ', '.join(['?' for col in data[0]])
            c.executemany(f'INSERT INTO {table} VALUES ({cols})', data)

    def load(self, filename):
        # TODO: drop all data before loading?

        if filename is None or not os.path.isfile(filename):
            return

        tree = etree.parse(filename)
        root = tree.getroot()

        target_tk = root.get('target_tk', None)

        if target_tk != self.target_tk:
            raise Exception(f'Can not load a {target_tk} target in {self.target_tk} project.')


        c = self.conn.cursor()

        # Avoid circular dependencies errors
        self.foreign_keys = False

        for child in root.getchildren():
            self._load_table_from_tuples(c, child.tag, child.text)

        self.foreign_keys = True
        c.close()

    def load_catalog(self, filename):
        tree = etree.parse(filename)
        root = tree.getroot()

        name = root.get('name', None)
        version = root.get('version', None)
        targets = root.get('targets', '')
        depends = root.get('depends', '')

        c = self.conn.cursor()

        # Insert library
        c.execute("INSERT INTO library(library_id, version) VALUES (?, ?);",
                  (name, version))

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
                print(f'Missing dependency {dep} for {filename}')
                deps.pop(dep)

        # Insert dependencies
        for dep in deps:
            try:
                c.execute("INSERT INTO library_dependency(library_id, dependency_id) VALUES (?, ?);",
                          (name, dep))
            except Exception as e:
                print(e)
                # TODO: should we try to load the module?
                #pass

        # Avoid circular dependencies errors
        self.foreign_keys = False

        for child in root.getchildren():
            self._load_table_from_tuples(c, child.tag, child.text)

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

        for table in ['ui', 'ui_library', 'object', 'object_property',
                      'object_layout_property', 'object_signal',
                      'object_data', 'object_data_arg']:
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

    def add_object(self, ui_id, obj_type, name=None, parent_id=None, internal_child=None, child_type=None, comment=None):
        c = self.conn.cursor()

        c.execute("SELECT coalesce((SELECT object_id FROM object WHERE ui_id=? ORDER BY object_id DESC LIMIT 1), 0) + 1;", (ui_id, ))
        object_id = c.fetchone()[0]

        c.execute("INSERT INTO object (ui_id, object_id, type_id, name, parent_id, internal, type, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                  (ui_id, object_id, obj_type, name, parent_id, internal_child, child_type, comment))
        c.close()

        return object_id

    def _import_object(self, ui_id, node, parent_id, internal_child=None, child_type=None, is_template=False):
        is_template = node.tag == 'template'

        if is_template:
            klass = node.get('parent')
            name = node.get('class')
        else:
            klass = node.get('class')
            name = node.get('id')

        comment = self._node_get_comment(node)
        info = self.type_info.get(klass, None)

        # Insert object
        try:
            assert info
            object_id = self.add_object(ui_id, klass, name, parent_id, internal_child, child_type, comment)
        except:
            print('Error importing', klass)
            return

        c = self.conn.cursor()

        if is_template:
            c.execute("UPDATE ui SET template_id=? WHERE ui_id=?", (object_id, ui_id))

        # Properties
        for prop in node.iterfind('property'):
            property_id = prop.get('name').replace('_', '-')
            translatable = prop.get('translatable', None)
            comment = self._node_get_comment(prop)

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

            # Insert property
            if not pinfo:
                print(f'Could not find owner type for {klass}:{property_id} property')
                continue

            try:
                c.execute("INSERT INTO object_property (ui_id, object_id, owner_id, property_id, value, translatable, comment) VALUES (?, ?, ?, ?, ?, ?, ?);",
                          (ui_id, object_id, pinfo.owner_id, property_id, prop.text, translatable, comment))
            except Exception as e:
                raise Exception(f'Can not save object {object_id} {owner_id}:{property_id} property: {e}')

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
            comment = self._node_get_comment(signal)

            # Find owner type for signal
            if signal_id in info.signals:
                owner_id = klass
            else:
                for parent in info.hierarchy:
                    pinfo = self.type_info[parent]
                    if signal_id in pinfo.signals:
                        owner_id = parent
                        break

            # Insert signal
            if owner_id:
                try:
                    c.execute("INSERT INTO object_signal (ui_id, object_id, owner_id, signal_id, handler, detail, user_data, swap, after, comment) VALUES (?, ?, ?, ?, ?, ?, (SELECT object_id FROM object WHERE ui_id=? AND name=?), ?, ?, ?);",
                              (ui_id, object_id, owner_id, signal_id, handler, detail, ui_id, user_data, swap, after, comment))
                except Exception as e:
                    raise Exception(f'Can not save object {object_id} {owner_id}:{signal_id} signal: {e}')
            else:
                print(f'Could not find owner type for {klass}:{signal_id} signal')

        # Children
        for child in node.iterfind('child'):
            obj = child.find('object')
            ctype = child.get('type', None)
            internal = child.get('internal-child', None)

            if obj is not None:
                self._import_object(ui_id, obj, object_id, internal, ctype)

        # Packing properties
        if self.target_tk == 'gtk+-3.0':
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

            if self.target_tk == 'gtk+-3.0':
                # For Gtk 3 we fake a LayoutChild class for each GtkContainer
                owner_id = f'{parent_type[0]}LayoutChild'
            else:
                # FIXME: Need to get layout-manager-type from class
                owner_id = f'{parent_type[0]}LayoutChild'

            for prop in packing.iterfind('property'):
                comment = self._node_get_comment(prop)
                property_id = prop.get('name').replace('_', '-')
                translatable = prop.get('translatable', None)
                try:
                    c.execute("INSERT INTO object_layout_property (ui_id, object_id, child_id, owner_id, property_id, value, translatable, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                              (ui_id, parent_id, object_id, owner_id, property_id, prop.text, translatable, comment))
                except Exception as e:
                    raise Exception(f'Can not save object {object_id} {owner_id}:{property_id} layout property: {e}')

        # Custom buildable tags
        def import_object_data(owner_id, taginfo, ntag, parent_id):
            data_id = taginfo.data_id
            text = ntag.text.strip() if ntag.text else None
            value = text if text and len(text) > 0 else None
            comment = self._node_get_comment(ntag)

            c.execute("SELECT coalesce((SELECT id FROM object_data WHERE ui_id=? AND object_id=? AND owner_id=? AND data_id=? ORDER BY id DESC LIMIT 1), 0) + 1;",
                      (ui_id, object_id, owner_id, data_id))
            id = c.fetchone()[0]

            c.execute("INSERT INTO object_data (ui_id, object_id, owner_id, data_id, id, value, parent_id, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                      (ui_id, object_id, owner_id, data_id, id, value, parent_id, comment))

            for key in taginfo.args:
                val = ntag.get(key, None)
                c.execute("INSERT INTO object_data_arg (ui_id, object_id, owner_id, data_id, id, key, value) VALUES (?, ?, ?, ?, ?, ?, ?);",
                          (ui_id, object_id, owner_id, data_id, id, key, val))

            for child in taginfo.children:
                for nchild in ntag.iterfind(child):
                    import_object_data(owner_id,
                                       taginfo.children[child],
                                       nchild,
                                       id)

        def import_type_data(info, node):
            if len(info.data.keys()) == 0:
                return

            for tag in info.data:
                taginfo = info.data[tag]

                for ntag in node.iterfind(tag):
                    if ntag is not None:
                        import_object_data(info.type_id, taginfo, ntag, None)

        # Iterate over all hierarchy extra data
        import_type_data(info, node)
        for parent in info.hierarchy:
            pinfo = self.type_info[parent]
            import_type_data(pinfo, node)

        c.close()

    def _node_get_comment(self, node):
        prev = node.getprevious()
        if prev is not None and prev.tag is etree.Comment:
            return prev.text
        return None

    def _node_get_requirements(self, root):
        retval = {}

        # Collect requirements and comments
        for req in root.iterfind('requires'):
            lib = req.get('lib')
            version = req.get('version')

            retval[lib] = {
              'version': version,
              'comment': self._node_get_comment(req)
            }

        return retval

    def _get_target_from_node(self, root, requirements):
        # Look for explicit gtk version first
        for lib in ['gtk', 'gtk+']:
            if lib in requirements:
                return (lib, requirements[lib]['version'], False)

        # Infer target by looking for layout/packing tags
        if root.find('.//layout') is not None:
            return ('gtk', '4.0', True)

        if root.find('.//packing') is not None:
            return ('gtk+', '3.0', True)

        return (None, None, None)

    def import_file(self, filename, projectdir='.'):
        tree = etree.parse(filename)
        root = tree.getroot()

        requirements = self._node_get_requirements(root)

        target_tk = self.target_tk
        lib, ver, inferred = self._get_target_from_node(root, requirements)

        if (target_tk == 'gtk-4.0' and lib != 'gtk') or \
           (target_tk == 'gtk+-3.0' and lib != 'gtk+'):
            if inferred:
                raise Exception(_(f'Can not import what looks like a {lib}-{ver} file in a {target_tk} project.'))
            else:
                raise Exception(_(f'Can not import a {lib}-{ver} file in a {target_tk} project.'))

        c = self.conn.cursor()

        # Update interface comment
        comment = self._node_get_comment(root)
        if comment and comment.startswith('Created with Cambalache'):
            comment = None

        basename = os.path.basename(filename)
        relpath = os.path.relpath(filename, projectdir)
        ui_id = self.add_ui(basename, relpath, requirements, comment)

        # Import objects
        for child in root.iterchildren():
            if child.tag == 'object':
                self._import_object(ui_id, child, None)
            elif child.tag == 'template':
                self._import_object(ui_id, child, None)

            while Gtk.events_pending():
                Gtk.main_iteration_do(False)

        # Do not use UPDATE FROM since its not supported in gnome sdk sqlite
        #c.execute("UPDATE object_property AS op SET value=o.object_id FROM property AS p, object AS o WHERE op.ui_id=? AND p.is_object AND op.owner_id = p.owner_id AND op.property_id = p.property_id AND o.ui_id = op.ui_id AND o.name = op.value;", (ui_id, ))

        # Fix object references!
        cc = self.conn.cursor()
        for row in c.execute("SELECT o.object_id, ?, op.object_id, op.owner_id, op.property_id FROM object_property AS op, property AS p, object AS o WHERE op.ui_id=? AND p.is_object AND op.owner_id = p.owner_id AND op.property_id = p.property_id AND o.ui_id = op.ui_id AND o.name = op.value;",
                             (ui_id, ui_id)):
            cc.execute("UPDATE object_property SET value=? WHERE ui_id=? AND object_id=? AND owner_id=? AND property_id=?", row)

        self.conn.commit()
        cc.close()
        c.close()

        return ui_id

    def _node_add_comment(self, node, comment):
        if comment:
            node.addprevious(etree.Comment(comment))

    def _export_object(self, ui_id, object_id, use_id=False, template_id=None):

        def node_set(node, attr, val):
            if val is not None:
                node.set(attr, str(val))

        c = self.conn.cursor()
        cc = self.conn.cursor()

        c.execute('SELECT type_id, name FROM object WHERE ui_id=? AND object_id=?;', (ui_id, object_id))
        type_id, name = c.fetchone()

        if not use_id and template_id == object_id:
            obj = E.template()
            node_set(obj, 'class', name)
            node_set(obj, 'parent', type_id)
        else:
            obj = E.object()
            node_set(obj, 'class', type_id)

            if use_id:
                node_set(obj, 'id', f'__cmb__{ui_id}.{object_id}')
            else:
                node_set(obj, 'id', name)

        info = self.type_info.get(type_id, None)

        # Create class hierarchy list
        hierarchy = [type_id] + info.hierarchy if info else [type_id]

        # SQL placeholder for every class in the list
        placeholders = ','.join((['?'] * len(hierarchy)))

        # Properties + save_always default values
        for row in c.execute(f'''
                SELECT op.value, op.property_id, op.comment, p.is_object
                  FROM object_property AS op, property AS p
                  WHERE op.ui_id=? AND op.object_id=? AND
                    p.owner_id = op.owner_id AND
                    p.property_id = op.property_id
                UNION
                SELECT default_value, property_id, null, is_object
                  FROM property
                  WHERE save_always=1 AND owner_id IN ({placeholders}) AND
                    property_id NOT IN
                    (SELECT property_id
                     FROM object_property
                     WHERE ui_id=? AND object_id=?)
                ORDER BY op.property_id
                ''',
                (ui_id, object_id) + tuple(hierarchy) + (ui_id, object_id)):
            val, property_id, comment, is_object = row

            if is_object:
                if use_id:
                    value = f'__cmb__{ui_id}.{val}'
                else:
                    cc.execute('SELECT name FROM object WHERE ui_id=? AND object_id=?;', (ui_id, val))
                    value, = cc.fetchone()
            else:
                value = val

            node = E.property(value, name=property_id)

            obj.append(node)
            self._node_add_comment(node, comment)

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
            self._node_add_comment(node, comment)

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
                self._node_add_comment(ntag, comment)

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
                    self._node_add_comment(ntag, comment)

                    for child in taginfo.children:
                        export_object_data(owner_id, child, taginfo.children[child], ntag, id)

        # Iterate over all hierarchy extra data
        export_type_data(type_id, info, obj)
        for parent in info.hierarchy:
            pinfo = self.type_info[parent]
            export_type_data(parent, pinfo, obj)

        # Layout properties class
        layout_class = f'{type_id}LayoutChild'
        linfo = self.type_info.get(layout_class, None)

        # Construct Layout Child class hierarchy list
        hierarchy = [layout_class] + linfo.hierarchy if linfo else [layout_class]

        # SQL placeholder for every class in the list
        placeholders = ','.join((['?'] * len(hierarchy)))

        # Children
        for row in c.execute('SELECT object_id, internal, type, comment FROM object WHERE ui_id=? AND parent_id=?;', (ui_id, object_id)):
            child_id, internal, ctype,  comment = row
            child_obj = self._export_object(ui_id, child_id, use_id=use_id)
            child = E.child(child_obj)
            node_set(child, 'internal-child', internal)
            node_set(child, 'type', ctype)
            self._node_add_comment(child_obj, comment)

            obj.append(child)

            if linfo is None:
                continue

            # Packing / Layout
            layout = E('packing' if self.target_tk == 'gtk+-3.0' else 'layout')

            # TODO: support object packing properties
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
                self._node_add_comment(node, comment)

            if len(layout) > 0:
                if self.target_tk == 'gtk+-3.0':
                    child.append(layout)
                else:
                    child_obj.append(layout)

        c.close()
        cc.close()
        return obj

    def export_ui(self, ui_id, use_id=False):
        c = self.conn.cursor()

        node = E.interface()
        node.addprevious(etree.Comment(f" Created with Cambalache {VERSION} "))

        c.execute('SELECT comment, template_id FROM ui WHERE ui_id=?;', (ui_id,))
        comment, template_id = c.fetchone()
        self._node_add_comment(node, comment)

        # requires
        tk_library_id, tk_version = self.target_tk.split('-')
        has_tk_requires = False

        for row in c.execute('SELECT library_id, version, comment FROM ui_library WHERE ui_id=?;', (ui_id,)):
            library_id, version, comment = row
            req = E.requires(lib=library_id, version=version)
            self._node_add_comment(req, comment)
            node.append(req)

            if library_id == tk_library_id:
                has_tk_requires = True

        # Ensure we output a requires lib
        if not has_tk_requires:
            library_id, version = self.target_tk.split('-')
            req = E.requires(lib=library_id, version=version)
            node.append(req)

        # Iterate over toplovel objects
        for row in c.execute('SELECT object_id, comment FROM object WHERE parent_id IS NULL AND ui_id=?;',
                             (ui_id,)):
            object_id, comment = row
            child = self._export_object(ui_id, object_id, use_id=use_id, template_id=template_id)
            node.append(child)
            self._node_add_comment(child, comment)

        c.close()

        return etree.ElementTree(node)
