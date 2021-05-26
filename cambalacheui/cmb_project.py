#
# CmbProject - Cambalache Project
#
# Copyright (C) 2020-2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import gi

from locale import gettext as _

from lxml import etree
from lxml.builder import E

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, GObject, Gtk

from .cmb_db import CmbDB
from .cmb_ui import CmbUI
from .cmb_object import CmbObject
from .cmb_property import CmbProperty
from .cmb_layout_property import CmbLayoutProperty
from .cmb_type_info import CmbTypeInfo
from .cmb_objects_base import CmbPropertyInfo, CmbSignal, CmbSignalInfo
from .cmb_list_store import CmbListStore
from .config import *


class CmbProject(GObject.GObject, Gtk.TreeModel):
    __gtype_name__ = 'CmbProject'

    __gsignals__ = {
        'changed': (GObject.SIGNAL_RUN_FIRST, None, ()),

        'ui-added': (GObject.SIGNAL_RUN_FIRST, None,
                     (CmbUI,)),

        'ui-removed': (GObject.SIGNAL_RUN_FIRST, None,
                       (CmbUI,)),

        'object-added': (GObject.SIGNAL_RUN_FIRST, None,
                         (CmbObject,)),

        'object-removed': (GObject.SIGNAL_RUN_FIRST, None,
                           (CmbObject,)),

        'object-property-changed': (GObject.SIGNAL_RUN_FIRST, None,
                                    (CmbObject, CmbProperty)),

        'object-layout-property-changed': (GObject.SIGNAL_RUN_FIRST, None,
                                           (CmbObject, CmbObject, CmbLayoutProperty)),

        'object-signal-added': (GObject.SIGNAL_RUN_FIRST, None,
                                (CmbObject, CmbSignal)),

        'object-signal-removed': (GObject.SIGNAL_RUN_FIRST, None,
                                  (CmbObject, CmbSignal)),

        'selection-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    target_tk = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)
    filename = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)

    undo_msg = GObject.Property(type=str)
    redo_msg = GObject.Property(type=str)

    def __init__(self, **kwargs):
        # Type Information
        self._type_info = {}

        self.type_list = None

        # Property Information
        self._property_info = {}

        # Selection
        self._selection = []

        # Create TreeModel store
        self._object_id = {}

        GObject.GObject.__init__(self, **kwargs)

        # Target from file take precedence over target_tk property
        if self.filename:
            target_tk = CmbDB.get_target_from_file(self.filename)

            if target_tk is not None:
                self.target_tk = target_tk

        if self.target_tk is None:
            raise Exception('Either target_tk or filename are required')

        # Use a TreeStore to hold object tree instead of using SQL for every
        # TreeStore call
        self._store = Gtk.TreeStore(GObject.GObject)

        # Foward signals to CmbProject, this way the user can not add data to
        # the TreeModel using Gtk API
        self._store.connect('row-changed', lambda o, p, i: self.row_changed(p, i))
        self._store.connect('row-inserted', lambda o, p, i: self.row_inserted(p, i))
        self._store.connect('row-has-child-toggled', lambda o, p, i: self.row_has_child_toggled(p, i))
        self._store.connect('row-deleted', lambda o, p: self.row_deleted(p))
        self._store.connect('rows-reordered', lambda o, p, i, n: self.rows_reordered(p, i, n))

        # DataModel is only used internally
        self.db = CmbDB(target_tk=self.target_tk)
        self._init_data()

        self._load()

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
                print('Error unknown type', col_type)

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


    def _init_list_stores(self):
        # Public List Stores
        type_query = '''SELECT * FROM type
                          WHERE
                            parent_id IS NOT NULL AND
                            abstract IS NOT True AND
                            parent_id NOT IN ('interface', 'enum', 'flags') AND
                            (layout IS NULL OR layout = 'container')
                          ORDER BY type_id;'''
        self.type_list = CmbListStore(project=self, table='type', query=type_query)

    def _init_type_info(self, c):
        owner_id = None
        props = None

        # Dictionary with all the types hierarchy
        type_hierarchy = {}
        type_id = None
        hierarchy = None
        for row in c.execute('SELECT type_id, parent_id FROM type_tree;'):
            if type_id != row[0]:
                type_id = row[0]
                hierarchy = []
                type_hierarchy[type_id] = hierarchy
            hierarchy.append(row[1])

        # Dictionary with all the type signals
        type_signals = {}
        owner_id = None
        signals = None
        for row in c.execute('SELECT * FROM signal ORDER BY owner_id, signal_id;'):
            if owner_id != row[0]:
                owner_id = row[0]
                signals = []
                type_signals[owner_id] = signals
            signals.append(CmbSignalInfo.from_row(self, *row))

        for row in c.execute('''SELECT * FROM type
                                  WHERE
                                    parent_id IS NOT NULL
                                  ORDER BY type_id;'''):
            type_id = row[0]
            info = CmbTypeInfo.from_row(self, *row)
            info.hierarchy = type_hierarchy.get(type_id, [])
            info.signals = type_signals.get(type_id, [])
            self._type_info[type_id] = info

    def _init_property_info(self, c):
        owner_id = None
        props = None

        for row in c.execute("SELECT * FROM property ORDER BY owner_id, property_id;"):
            if owner_id != row[0]:
                owner_id = row[0]
                props = {}
                self._property_info[owner_id] = props

            property_id = row[1]
            props[property_id] = CmbPropertyInfo.from_row(self, *row)

    def _init_data(self):
        if self.target_tk is None:
            return

        c = self.db.cursor()

        # Init GtkListStore wrappers for different tables
        self._init_list_stores()

        self._init_type_info(c)

        self._init_property_info(c)

        c.close()

    def _load(self):
        if self.filename is None or not os.path.isfile(self.filename):
            return

        self.history_enabled = False
        self.db.load(self.filename)
        self.history_enabled = True

        c = self.db.cursor()
        cc = self.db.cursor()

        # Populate tree view
        for row in c.execute('SELECT * FROM ui;'):
            ui_id = row[0]
            self._add_ui(False, *row)

            # Update UI objects
            for obj in cc.execute('SELECT * FROM object WHERE ui_id=?;', (ui_id, )):
                self._add_object(False, *obj)

        c.close()
        cc.close()

    def save(self):
        self.db.save(self.filename)

    def comment_from_node(self, node):
        prev = node.getprevious()
        if prev is not None and prev.tag is etree.Comment:
            return prev.text
        return None

    def _import_object(self, ui_id, node, parent_id):
        c = self.db.cursor()
        klass = node.get('class')
        name = node.get('id')

        # Insert object
        obj = self.add_object(ui_id, klass, name, parent_id)
        object_id = obj.object_id
        comment = self.comment_from_node(node)
        if comment:
            obj.comment = comment

        # Properties
        for prop in node.iterfind('property'):
            property_id = prop.get('name')
            translatable = prop.get('translatable', None)
            comment = self.comment_from_node(prop)

            # Find owner type for property
            c.execute("SELECT owner_id FROM property WHERE property_id=? AND owner_id IN (SELECT parent_id FROM type_tree WHERE type_id=? UNION SELECT ?);",
                      (property_id, klass, klass))
            owner_id = c.fetchone()

            # Insert property
            if owner_id:
                try:
                    c.execute("INSERT INTO object_property (ui_id, object_id, owner_id, property_id, value, translatable, comment) VALUES (?, ?, ?, ?, ?, ?, ?);",
                              (ui_id, object_id, owner_id[0], property_id, prop.text, translatable, comment))
                except Exception as e:
                    raise Exception(f'Can not save object {object_id} {property_id} property: {e}')
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
            comment = self.comment_from_node(signal)

            # Find owner type for signal
            c.execute("SELECT owner_id FROM signal WHERE signal_id=? AND owner_id IN (SELECT parent_id FROM type_tree WHERE type_id=? UNION SELECT ?);",
                      (signal_id, klass, klass))
            owner_id = c.fetchone()

            # Insert signal
            try:
                c.execute("INSERT INTO object_signal (ui_id, object_id, owner_id, signal_id, handler, detail, user_data, swap, after, comment) VALUES (?, ?, ?, ?, ?, ?, (SELECT object_id FROM object WHERE ui_id=? AND name=?), ?, ?, ?);",
                          (ui_id, object_id, owner_id[0] if owner_id else None, signal_id, handler, detail, ui_id, user_data, swap, after, comment))
            except Exception as e:
                raise Exception(f'Can not save object {object_id} {signal_id} signal: {e}')

        # Make sure object create its signals
        obj._populate_signals()

        # Children
        for child in node.iterfind('child'):
            obj = child.find('object')
            if obj is not None:
                self._import_object(ui_id, obj, object_id)

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
                comment = self.comment_from_node(prop)
                property_id = prop.get('name')
                translatable = prop.get('translatable', None)
                try:
                    c.execute("INSERT INTO object_layout_property (ui_id, object_id, child_id, owner_id, property_id, value, translatable, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                              (ui_id, parent_id, object_id, owner_id, property_id, prop.text, translatable, comment))
                except Exception as e:
                    raise Exception(f'Can not save object {object_id} {owner_id}:{property_id} layout property: {e}')
        c.close()

    def import_file(self, filename, overwrite=False):
        tree = etree.parse(filename)
        root = tree.getroot()

        requirements = {}
        req_comments = {}

        # Collect requirements, comments and target_tk
        target_tk = None
        for req in root.iterfind('requires'):
            lib = req.get('lib')
            version = req.get('version')

            requirements[lib] = version
            req_comments[lib] = self.comment_from_node(req)

            if lib == 'gtk':
                target_tk = 'gtk-4.0'
            elif lib == 'gtk+':
                target_tk = 'gtk+-3.0'

            # TODO: look for layout properties tag to infer if its for gtk 4 or 3

        # Make sure we support target_tk
        if target_tk not in ['gtk+-3.0', 'gtk-4.0']:
            raise Exception(_('Could not determine gtk version'))

        if target_tk != self.target_tk:
            raise Exception(_('Target version mismatch'))

        self.history_push(_(f'Import file "{filename}"'))
        c = self.db.cursor()

        # Remove old UI
        if overwrite:
            c.execute("DELETE FROM ui WHERE filename=?;", (filename, ))

        ui = self.add_ui(filename, requirements)

        # Update requirement comments
        for key in req_comments:
            comment = req_comments[key]
            if comment:
                c.execute('UPDATE ui_library SET comment=? WHERE ui_id=? AND library_id=?;',
                          (comment, ui.ui_id, key))

        # Update interface comment
        comment = self.comment_from_node(root)
        if comment and not comment.startswith('Created with Cambalache'):
            ui.comment = comment

        # Import objects
        for child in root.iterfind('object'):
            self._import_object(ui.ui_id, child, None)
            self.db.commit()

        c.close()

        self.history_pop()

    def node_add_comment(self, node, comment):
        if comment:
            node.addprevious(etree.Comment(comment))

    def _get_object(self, ui_id, object_id, use_id=False):
        def node_set(node, attr, val):
            if val is not None:
                node.set(attr, str(val))

        c = self.db.cursor()
        cc = self.db.cursor()
        obj = E.object()

        c.execute('SELECT type_id, name FROM object WHERE ui_id=? AND object_id=?;', (ui_id, object_id))
        type_id, name = c.fetchone()
        node_set(obj, 'class', type_id)

        if use_id and name:
            name = GLib.uri_escape_string(name, None, True)
            node_set(obj, 'id', f'__cambalache__{ui_id}.{object_id}+{name}')
        else:
            node_set(obj, 'id', f'__cambalache__{ui_id}.{object_id}' if use_id else name)

        # Properties
        for row in c.execute('SELECT value, property_id, comment FROM object_property WHERE ui_id=? AND object_id=?;',
                             (ui_id, object_id,)):
            val, name, comment = row
            node = E.property(val, name=name)
            obj.append(node)
            self.node_add_comment(node, comment)

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
            self.node_add_comment(node, comment)

        # Children
        for row in c.execute('SELECT object_id, comment FROM object WHERE ui_id=? AND parent_id=?;', (ui_id, object_id)):
            child_id, comment = row
            child_obj = self._get_object(ui_id, child_id, use_id=use_id)
            child = E.child(child_obj)
            self.node_add_comment(child_obj, comment)

            # Packing / Layout
            layout = E('packing' if self.target_tk == 'gtk+-3.0' else 'layout')

            for prop in cc.execute('SELECT value, property_id, comment FROM object_layout_property WHERE ui_id=? AND object_id=? AND child_id=?;',
                                 (ui_id, object_id, child_id)):
                value, property_id, comment = prop
                node = E.property(value, name=property_id)
                layout.append(node)
                self.node_add_comment(node, comment)

            if len(layout) > 0:
                if self.target_tk == 'gtk+-3.0':
                    child.append(layout)
                else:
                    child_obj.append(layout)

            obj.append(child)

        c.close()
        cc.close()
        return obj

    def export_ui(self, ui_id, filename=None, use_id=False):
        c = self.db.cursor()

        node = E.interface()
        node.addprevious(etree.Comment(f" Created with Cambalache {VERSION} "))

        c.execute('SELECT comment FROM ui WHERE ui_id=?;', (ui_id,))
        comment, = c.fetchone()
        self.node_add_comment(node, comment)

        # requires
        for row in c.execute('SELECT library_id, version, comment FROM ui_library WHERE ui_id=?;', (ui_id,)):
            library_id, version, comment = row
            req = E.requires(lib=library_id, version=version)
            self.node_add_comment(req, comment)
            node.append(req)

        # Iterate over toplovel objects
        for row in c.execute('SELECT object_id, comment FROM object WHERE parent_id IS NULL AND ui_id=?;',
                             (ui_id,)):
            object_id, comment = row
            child = self._get_object(ui_id, object_id, use_id)
            node.append(child)
            self.node_add_comment(child, comment)

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
        c = self.db.cursor()

        dirname = os.path.dirname(self.filename)

        # FIXME: remove cmb suffix once we have full GtkBuilder support
        for row in c.execute('SELECT ui_id, filename FROM ui;'):
            filename = os.path.splitext(row[1])[0] + '.cmb.ui'

            if os.path.isabs(filename):
                self.export_ui(row[0], filename)
            else:
                self.export_ui(row[0], os.path.join(dirname, filename))

        c.close()

    def _selection_remove(self, obj):
        try:
            self._selection.remove(obj)
        except:
            pass
        else:
            self.emit('selection-changed')

    def _add_ui(self, emit, ui_id, template_id, name, filename, description, copyright, authors, license_id, translation_domain, comment):
        ui = CmbUI(project=self,
                   ui_id=ui_id,
                   template_id=template_id if template_id is not None else 0,
                   name=name,
                   filename=filename,
                   description=description,
                   copyright=copyright,
                   authors=authors,
                   license_id=license_id,
                   translation_domain=translation_domain,
                   comment=comment)

        self._object_id[ui_id] = self._store.append(None, [ui])

        if emit:
            self.emit('ui-added', ui)

        return ui

    def add_ui(self, filename, requirements={}):
        basename = os.path.basename(filename)
        dirname = os.path.dirname(self.filename)
        relpath = os.path.relpath(filename, dirname)
        try:
            self.history_push(_(f"Add UI {basename}"))
            c = self.db.cursor()
            c.execute("INSERT INTO ui (name, filename) VALUES (?, ?);",
                      (basename, relpath))
            ui_id = c.lastrowid

            for req in requirements:
                c.execute('INSERT INTO ui_library (ui_id, library_id, version) VALUES (?, ?, ?);',
                          (ui_id, req, requirements[req]))
            c.close()
            self.history_pop()
            self.db.commit()
        except:
            return None
        else:
            return self._add_ui(True, ui_id, None, basename, relpath, None, None, None, None, None, None)

    def _remove_ui(self, ui):
        iter_ = self._object_id.pop(ui.ui_id, None)

        if iter_ is not None:
            self._selection_remove(ui)
            self._store.remove(iter_)
            self.emit('ui-removed', ui)

    def remove_ui(self, ui):
        try:
            self.history_push(_(f'Remove UI "{ui.name}"'))
            self.db.execute("DELETE FROM ui WHERE ui_id=?;", (ui.ui_id, ))
            self.history_pop()
            self.db.commit()
            self._remove_ui(ui);
        except:
            pass

    def _add_object(self, emit, ui_id, object_id, obj_type, name=None, parent_id=None, comment=None):
        obj = CmbObject(project=self,
                        ui_id=ui_id,
                        object_id=object_id,
                        type_id=obj_type,
                        name=name,
                        parent_id=parent_id if parent_id is not None else 0,
                        info=self._type_info[obj_type],
                        comment=comment)

        if obj.parent_id == 0:
            parent = self._object_id.get(obj.ui_id, None)
        else:
            parent = self._object_id.get(f'{obj.ui_id}.{obj.parent_id}', None)

        self._object_id[f'{obj.ui_id}.{obj.object_id}'] = self._store.append(parent, [obj])

        if emit:
            self.emit('object-added', obj)

        return obj

    def _check_can_add(self, obj_type, parent_type):
        obj_info = self._type_info.get(obj_type, None)
        parent_info = self._type_info.get(parent_type, None)

        if obj_info is None or parent_info is None:
            return False

        # Only GtkWidget can be a child
        if not obj_info.is_a('GtkWidget'):
            return False

        # GtkWindow can not be a child
        if obj_info.is_a('GtkWindow'):
            return False

        return parent_info.layout == 'container'

    def add_object(self, ui_id, obj_type, name=None, parent_id=None):
        if parent_id:
            parent = self._get_object_by_id(ui_id, parent_id)
            if parent is None:
                return None

            if not self._check_can_add(obj_type, parent.type_id):
                return None

        c = self.db.cursor()

        try:
            # Insert object
            c.execute("SELECT coalesce((SELECT object_id FROM object WHERE ui_id=? ORDER BY object_id DESC LIMIT 1), 0) + 1;", (ui_id, ))
            object_id = c.fetchone()[0]

            c.execute("INSERT INTO object (ui_id, object_id, type_id, name, parent_id) VALUES (?, ?, ?, ?, ?);",
                      (ui_id, object_id, obj_type, name, parent_id))
            c.close()
            self.db.commit()
        except:
            return None
        else:
            return self._add_object(True, ui_id, object_id, obj_type, name, parent_id)

    def _remove_object(self, obj):
        iter_ = self._object_id.pop(f'{obj.ui_id}.{obj.object_id}', None)
        if iter_ is not None:
            self._selection_remove(obj)
            self._store.remove(iter_)
            self.emit('object-removed', obj)

    def remove_object(self, obj):
        try:
            name = obj.name if obj.name is not None else obj.type_id
            self.history_push(_(f'Remove object {name}'))
            self.db.execute("DELETE FROM object WHERE ui_id=? AND object_id=?;",
                            (obj.ui_id, obj.object_id))
            self.history_pop()
            self.db.commit()
        except:
            pass
        else:
            self._remove_object(obj)

    def get_selection(self):
        return self._selection

    def set_selection(self, selection):
        if type(selection) != list or self._selection == selection:
            return

        for obj in selection:
            if type(obj) != CmbUI and type(obj) != CmbObject:
                return

        self._selection = selection
        self.emit('selection-changed')

    def get_iter_from_object(self, obj):
        if type(obj) == CmbObject:
            return self._object_id.get(f'{obj.ui_id}.{obj.object_id}', None)
        elif type(obj) == CmbUI:
            return self._object_id.get(obj.ui_id, None)

    def _get_object_by_key(self, key):
        _iter = self._object_id.get(key, None)
        return self._store.get_value(_iter, 0) if _iter else None

    def _get_object_by_id(self, ui_id, object_id = None):
        key = f'{ui_id}.{object_id}' if object_id is not None else ui_id
        return self._get_object_by_key(key)

    def _undo_redo_property_notify(self, obj, layout, prop, owner_id, property_id):
        # FIXME:use a dict instead of walking the array
        properties = obj.layout if layout else obj.properties
        for p in properties:
            if p.owner_id == owner_id and p.property_id == property_id:
                p.notify(prop)
                if layout:
                    parent = self._get_object_by_id(obj.ui_id, obj.parent_id)
                    self.emit('object-layout-property-changed', parent, obj, p)
                else:
                    self.emit('object-property-changed', obj, p)

    def _get_history_command(self, history_index):
        c = self.db.cursor()
        c.execute("SELECT command, range_id, table_name, column_name FROM history WHERE history_id=?", (history_index, ))
        retval = c.fetchone()
        c.close()
        return retval

    def _undo_redo_do(self, undo):
        c = self.db.cursor()

        # Get last command
        command, range_id, table, column = self._get_history_command(self.history_index)

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
            print('Error unknown history command')

        c.close()

        # Update project state
        self._undo_redo_update(command, range_id, table, column)

    def _undo_redo_update(self, command, range_id, table, column):
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
            if table == 'object_property':
                obj = self._get_object_by_id(pk[0], pk[1])
                self._undo_redo_property_notify(obj, False, column, pk[2], pk[3])
            elif table == 'object_layout_property':
                child = self._get_object_by_id(pk[0], pk[2])
                self._undo_redo_property_notify(child, True, column, pk[3], pk[4])
            elif table == 'object_signal':
                pass
        elif command == 'INSERT' or command == 'DELETE':
            if table == 'object_property':
                obj = self._get_object_by_id(pk[0], pk[1])
                self._undo_redo_property_notify(obj, False, 'value', pk[2], pk[3])
            elif table == 'object_layout_property':
                child = self._get_object_by_id(pk[0], pk[2])
                self._undo_redo_property_notify(child, True, 'value', pk[3], pk[4])
            elif table =='object' or table == 'ui':
                c.execute(commands['COUNT'], (self.history_index, ))
                count = c.fetchone()

                if count[0] == 0:
                    obj = self._get_object_by_id(pk[0], pk[1] if len(pk) > 1 else None)

                    if table =='object':
                        self._remove_object(obj)
                    elif table == 'ui':
                        self._remove_ui(obj)
                else:
                    c.execute(commands['DATA'], (self.history_index, ))
                    row = c.fetchone()
                    if table == 'ui':
                        self._add_ui(True, *row)
                    elif table == 'object':
                        self._add_object(True, *row)
            elif table == 'object_signal':
                c.execute(commands['COUNT'], (self.history_index, ))
                count = c.fetchone()

                c.execute(commands['DATA'], (self.history_index, ))
                row = c.fetchone()

                obj = self._get_object_by_id(row[1], row[2])

                if count[0] == 0:
                    for signal in obj.signals:
                        if signal.signal_pk == row[0]:
                            obj._remove_signal(signal)
                            break
                else:
                    obj._add_signal(row[0], row[3], row[4], row[5], row[6], row[7], row[8], row[9])

        c.close()

    def _undo_redo(self, undo):
        c = self.db.cursor()

        self.history_enabled = False

        command, range_id, table, column = self._get_history_command(self.history_index)

        if command == 'POP':
            if undo:
                self.history_index -= 1
                while range_id < self.history_index:
                    self._undo_redo_do(True)
                    self.history_index -= 1
            else:
                print("Error on undo/redo stack: we should not try to redo a POP command")
        elif command == 'PUSH':
            if not undo:
                while range_id > self.history_index:
                    self.history_index += 1
                    self._undo_redo_do(undo)
            else:
                print("Error on undo/redo stack: we should not try to undo a PUSH command")
        else:
            # Undo / Redo in DB
            self._undo_redo_do(undo)

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

        self._undo_redo(True)
        self.history_index -= 1

    def redo(self):
        if self.history_index >= self.history_index_max:
            return

        self.history_index += 1
        self._undo_redo(False)

    def get_type_properties(self, name):
        return self._property_info.get(name, None)

    def _object_property_changed(self, ui_id, object_id, prop):
        self.emit('object-property-changed',
                  self._get_object_by_id(ui_id, object_id),
                  prop)

    def _object_layout_property_changed(self, ui_id, object_id, child_id, prop):
        self.emit('object-layout-property-changed',
                  self._get_object_by_id(ui_id, object_id),
                  self._get_object_by_id(ui_id, child_id),
                  prop)

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

    # Default handlers
    def do_ui_added(self, ui):
        self.emit('changed')

    def do_ui_removed(self, ui):
        self.emit('changed')

    def do_object_added(self, obj):
        self.emit('changed')

    def do_object_removed(self, obj):
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
