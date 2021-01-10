#
# CambalacheDB - Data Model for Cambalache
#
# Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
import sqlite3
import importlib

# We need to use lxml to get access to nsmap
from lxml import etree
from toposort import toposort_flatten
from gi.repository import GObject

# Global XML name space
nsmap = {}

# Helper function to get a namespaced attribute
def ns(namespace, name):
    return f"{{{nsmap[namespace]}}}{name}"


class GirData:

    def __init__(self, gir_file):
        tree = etree.parse(gir_file)
        root = tree.getroot()

        # Set global NS map
        global nsmap
        nsmap = root.nsmap

        # Get <namespace/>
        namespace = root.find('namespace', nsmap)

        # Get module/name space data
        self.name = namespace.get('name')
        self.version = namespace.get('version')
        self.shared_library = namespace.get('shared-library')

        # Load Module described by gir
        try:
            gi.require_version(self.name, self.version)
            self.mod = importlib.import_module(f'gi.repository.{self.name}')
        except ValueError:
            print(f"Oops! Could not load {self.name} {self.version} module")

        # Dictionary of all classes/types
        self.types = self._get_types(namespace)

        # Dictionary of all enumerations
        self.enumerations = self._get_enumerations(namespace)

        # Dictionary of all flags
        self.flags = self._get_flags(namespace)

        # Dictionary of all interfaces
        self.ifaces = self._get_ifaces(namespace)

        if self.name == 'Gtk':
            if self.version == '3.0':
                self._gtk3_init()
            if self.version == '4.0':
                self._gtk4_init()

        # Types dependency graph
        types_deps = {}
        for gtype in self.types:
            dep = self.types[gtype]['parent']
            if dep:
                types_deps[gtype] = { dep }

        # Types in topological order, to avoid FK errors
        self.sorted_types = toposort_flatten(types_deps)

    def _type_is_a (self, type, is_a_type):
        parent = self.types[type]

        while parent:
            if parent['parent'] == is_a_type:
                return True
            else:
                parent = self.types.get(parent['parent'], None)

        return False

    def _container_list_child_properties(self, name):
        if name.startswith(self.name):
            parentClass = getattr(self.mod, name[len(self.name):])
        else:
            parentClass = getattr(self.mod, name)

        if parentClass is not None:
            # Ensure class is instantiable
            class InstanceClass(parentClass):
                pass

            instance = InstanceClass()
            props = instance.list_child_properties()

            return props if len(props) > 0 else None

        return None

    def _gtk3_init(self):
        def get_properties (name, props):
            retval = {}

            if not props:
                return {}

            for pspec in props:
                owner = GObject.type_name(pspec.owner_type)
                type_name = GObject.type_name(pspec.value_type)

                if owner != name or type_name.startswith('Gdk'):
                    continue

                retval[pspec.name] = {
                    'type': type_name,
                    'version': None,
                    'deprecated_version': None,
                    'writable': 1 if pspec.flags & GObject.ParamFlags.WRITABLE else None,
                    'construct': 1 if pspec.flags & GObject.ParamFlags.CONSTRUCT else None,
                }

            return retval

        layout_types = {}

        # Create LayoutChild classes for GtkContainer child properties
        for name in self.types:
            if not self._type_is_a(name, 'GtkContainer'):
                continue

            data = self.types[name]
            props = self._container_list_child_properties(name)
            properties = get_properties(name, props)

            if len(properties) > 0:
                layout_types[f'Cambalache{name}LayoutChild'] = {
                    'parent': 'object',
                    'layout': 'child',
                    'properties': properties,
                    'abstract': 1,
                    'version': None,
                    'deprecated_version': None,
                    'get_type': None,
                    'signals': {},
                    'interfaces': []
                }

        self.types.update(layout_types)

    def _gtk4_init(self):
        # Mark Layout classes
        for name in self.types:
            data = self.types[name]

            if self._type_is_a(name, 'GtkLayoutManager'):
                data['layout'] = 'manager'
            elif self._type_is_a(name, 'GtkLayoutChild'):
                data['layout'] = 'child'

    def _type_get_properties (self, element):
        retval = {}

        for child in element.iterfind('property', nsmap):
            name = child.get('name')
            type = child.find('type', nsmap)

            if type is None:
                continue

            type_name = type.get('name')

            # FIXME: Ignore types defined in other NS for now
            if type_name.find('.') >= 0:
                continue

            # FIXME: Crappy test to see if types refers to an object
            if type_name[0].isupper():
                type_name = self.name + type_name

            if type_name == 'utf8':
                type_name = 'gchararray'

            retval[name] = {
                'type': type_name,
                'version': child.get('version'),
                'deprecated_version': child.get('deprecated-version'),
                'writable': child.get('writable'),
                'construct': child.get('construct'),
            }

        return retval

    def _type_get_signals (self, element):
        retval = {}

        for child in element.iterfind('virtual-method', nsmap):
            name = child.get('name').replace('_', '-')
            retval[name] = {
                'version': child.get('version'),
                'deprecated_version': child.get('deprecated-version'),
            }

        return retval

    def _type_get_interfaces (self, element):
        retval = []

        for child in element.iterfind('implements', nsmap):
            name = child.get('name')
            if name.find('.') < 0:
                retval.append(self.name + name)

        return retval

    def _get_type_data (self, element):
        parent = element.get('parent')

        if parent and parent.find('.') < 0:
            parent = self.name + parent

        # Get version and deprecated-version from constructor if possible
        constructor = element.find('constructor', nsmap)
        if constructor is None:
            constructor = element

        return {
            'parent': parent,
            'layout': None,
            'abstract': element.get('abstract'),
            'version': constructor.get('version'),
            'deprecated_version': constructor.get('deprecated-version'),
            'get_type': element.get(ns('glib','get-type')),
            'properties': self._type_get_properties(element),
            'signals': self._type_get_signals(element),
            'interfaces': self._type_get_interfaces(element)
        }

    def _get_types (self, namespace):
        retval = {}

        for child in namespace.iterfind('class', nsmap):
            name = child.get(ns('glib','type-name'))
            data = self._get_type_data(child)
            if name and data is not None:
                retval[name] = data

        return retval

    def _get_enumerations (self, namespace):
        retval = {}

        for child in namespace.iterfind('enumeration', nsmap):
            name = child.get(ns('glib','type-name'))
            if name:
                retval[name] = {
                    'parent': 'enum',
                    'members': self._enum_flags_get_members(child)
                }

        return retval

    def _enum_flags_get_members (self, element):
        retval = {}

        for child in element.iterfind('member', nsmap):
            doc = child.find('doc', nsmap)
            doc_text = None

            if doc is not None:
                doc_text = ' '.join(doc.text.split())

            retval[child.get('name')] = {
                'value': child.get('value'),
                'identifier': child.get(ns('c','identifier')),
                'doc': doc_text
            }

        return retval

    def _get_flags (self, namespace):
        retval = {}

        for child in namespace.iterfind('bitfield', nsmap):
            name = child.get(ns('glib','type-name'))
            if name:
                retval[name] = {
                    'parent': 'flags',
                    'members': self._enum_flags_get_members(child)
                }

        return retval

    def _get_ifaces (self, namespace):
        retval = {}

        for child in namespace.iterfind('interface', nsmap):
            name = child.get(ns('glib','type-name'))
            if name:
                retval[name] = {
                    'parent': 'interface',
                }

        return retval

    def populate_db (self, conn):
        def db_insert_enum_flags(conn, name, data):
            parent = data['parent']
            conn.execute(f"INSERT INTO type (catalog_id, type_id, parent_id) VALUES (?, ?, ?);",
                         (self.name, name, parent))

            members = data['members']
            for member in members:
                m = members[member]
                conn.execute(f"INSERT INTO type_{parent} (type_id, name, value, identifier, doc) VALUES (?, ?, ?, ?, ?);",
                             (name, member, m['value'], m['identifier'], m['doc']))


        def db_insert_iface(conn, name, data):
            parent = data['parent']
            conn.execute(f"INSERT INTO type (catalog_id, type_id, parent_id) VALUES (?, ?, ?);",
                         (self.name, name, parent))


        def db_insert_type(conn, name, data):
            parent = data['parent']

            if parent and parent.find('.') >= 0:
                parent = 'object'

            conn.execute(f"INSERT INTO type (catalog_id, type_id, parent_id, get_type, version, deprecated_version, abstract, layout) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                         (self.name, name, parent, data['get_type'], data['version'], data['deprecated_version'], data['abstract'], data['layout']))


        def db_insert_type_data(conn, name, data):
            properties = data['properties']
            for prop in properties:
                p = properties[prop]
                prop_type = p['type']

                # Ignore unknown types (Propably GBoxed)
                if prop_type.startswith(self.name) and prop_type not in self.types:
                    continue

                conn.execute(f"INSERT INTO property (owner_id, property_id, type_id, writable, construct_only, version, deprecated_version) VALUES (?, ?, ?, ?, ?, ?, ?);",
                             (name, prop, prop_type, p['writable'], p['construct'] , p['version'], p['deprecated_version']))

            signals = data['signals']
            for signal in signals:
                s = signals[signal]
                conn.execute(f"INSERT INTO signal (owner_id, signal_id, version, deprecated_version) VALUES (?, ?, ?, ?);",
                             (name, signal, s['version'], s['deprecated_version']))

            for iface in data['interfaces']:
                conn.execute(f"INSERT INTO type_iface (type_id, iface_id) VALUES (?, ?);",
                             (name, iface))

        # Import catalog
        conn.execute(f"INSERT INTO catalog (catalog_id, version, shared_library) VALUES (?, ?, ?);",
                     (self.name, self.version, self.shared_library));

        # Import ifaces
        for name in self.ifaces:
            db_insert_iface(conn, name, self.ifaces[name])

        # Import enumeration
        for name in self.enumerations:
            db_insert_enum_flags(conn, name, self.enumerations[name])

        # Import bitfield
        for name in self.flags:
            db_insert_enum_flags(conn, name, self.flags[name])

        # Import types in topological order
        for name in self.sorted_types:
            if name not in self.types:
                continue
            db_insert_type(conn, name, self.types[name])

        # Now insert type data (properties, signals, etc)
        for name in self.sorted_types:
            if name not in self.types:
                continue
            db_insert_type_data(conn, name, self.types[name])

