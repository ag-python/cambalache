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
from .toposort import toposort_flatten
from gi.repository import GObject

# Global XML name space
nsmap = {}

# Helper function to get a namespaced attribute
def ns(namespace, name):
    return f"{{{nsmap[namespace]}}}{name}"


class GirData:

    def __init__(self, gir_file):

        self._instances = {}

        tree = etree.parse(gir_file)
        root = tree.getroot()

        # Set global NS map
        global nsmap
        nsmap = root.nsmap

        # Get <namespace/>
        namespace = root.find('namespace', nsmap)

        # Get module/name space data
        self.name = namespace.get('name')
        self.prefix = namespace.get(ns('c', 'identifier-prefixes'))
        self.lib = self.name.lower()
        self.version = namespace.get('version')
        self.shared_library = namespace.get('shared-library')

        # Load Module described by gir
        try:
            gi.require_version(self.name, self.version)
            self.mod = importlib.import_module(f'gi.repository.{self.name}')
        except ValueError:
            print(f"Oops! Could not load {self.name} {self.version} module")

        types = None
        skip_types = []
        if self.name == 'GObject':
            types = ['GObject', 'GBinding', 'GBindingFlags']
            skip_types = ['GBinding']
        elif self.name == 'Gtk':
            if self.version == '3.0':
                pass
            elif self.version == '4.0':
                skip_types = ['GtkActivateAction',
                              'GtkMnemonicAction',
                              'GtkNamedAction',
                              'GtkNeverTrigger',
                              'GtkNothingAction',
                              'GtkSignalAction',
                              'GtkPrintJob']

        # Dictionary of all enumerations
        self.enumerations = self._get_enumerations(namespace, types)

        # Dictionary of all flags
        self.flags = self._get_flags(namespace, types)

        # Dictionary of all interfaces
        self.ifaces = self._get_ifaces(namespace, types)

        # Dictionary of all classes/types
        self.types = self._get_types(namespace, types, skip_types)

        if self.name == 'Gtk':
            if self.version == '3.0':
                self.lib = 'gtk+'
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

    def _get_instance_from_type(self, name):
        retval = self._instances.get(name, None)

        if retval is not None:
            return retval

        if name.startswith(self.prefix):
            InstanceClass = getattr(self.mod, name[len(self.prefix):], None)
        else:
            InstanceClass = getattr(self.mod, name, None)

        gtype = GObject.type_from_name(name)
        if InstanceClass is not None and GObject.type_is_a(gtype, GObject.GObject):
            if GObject.type_test_flags(gtype, GObject.TypeFlags.ABSTRACT):
                # Ensure class is instantiable
                class ChildClass(InstanceClass):
                    pass
                if ChildClass is not None:
                    retval = ChildClass()
            else:
                retval = InstanceClass()

        # keep the instance for later
        if retval is not None:
            self._instances[name] = retval

        return retval

    def _container_list_child_properties(self, name):
        instance = self._get_instance_from_type(name)

        if instance is not None:
            props = instance.list_child_properties()
            return props if len(props) > 0 else None

        return None

    def _get_enum_name_by_value(self, gtype, value):
        name = GObject.type_name(gtype)
        enum = self.enumerations.get(name, None)

        if enum is not None:
            members = enum['members']
            for member in members:
                if value == int(members[member]['value']):
                    return member
        return None

    def _get_flags_names_by_value(self, gtype, value):
        name = GObject.type_name(gtype)
        enum = self.flags.get(name, None)
        retval = None

        if enum is not None:
            members = enum['members']
            for member in members:
                if value & int(members[member]['value']):
                    retval = member if retval is None else f'{retval} | {member}'

        return retval

    def _get_default_value_from_pspec(self, pspec):
        if pspec is None:
            return None

        if pspec.value_type == GObject.TYPE_BOOLEAN:
            return 'True' if pspec.default_value != 0 else 'False'
        elif GObject.type_is_a(pspec.value_type, GObject.TYPE_ENUM):
            return self._get_enum_name_by_value(pspec.value_type, pspec.default_value)
        elif GObject.type_is_a(pspec.value_type, GObject.TYPE_FLAGS):
            return self._get_flags_names_by_value(pspec.value_type, pspec.default_value)

        return pspec.default_value

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
                    'default_value': self._get_default_value_from_pspec(pspec),
                    'minimum': pspec.minimum if hasattr(pspec, 'minimum') else None,
                    'maximum': pspec.maximum if hasattr(pspec, 'maximum') else None
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
                layout_types[f'{name}LayoutChild'] = {
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

    def _type_get_properties (self, element, instance):
        retval = {}
        pspecs = {}

        if instance is not None:
            props = instance.list_properties()

            for p in props:
                pspecs[p.name] = p

        for child in element.iterfind('property', nsmap):
            name = child.get('name')
            type = child.find('type', nsmap)

            if type is None:
                continue

            type_name = type.get('name')

            # FIXME: Ignore types defined in other NS for now
            if type_name is None or type_name.find('.') >= 0:
                continue

            # FIXME: Crappy test to see if types refers to an object
            if type_name[0].isupper():
                type_name = self.name + type_name

            if type_name == 'utf8':
                type_name = 'gchararray'

            # Property pspec
            pspec = pspecs.get(name, None)

            retval[name] = {
                'type': type_name,
                'version': child.get('version'),
                'deprecated_version': child.get('deprecated-version'),
                'writable': child.get('writable'),
                'construct': child.get('construct'),
                'default_value': self._get_default_value_from_pspec(pspec),
                'minimum': pspec.minimum if hasattr(pspec, 'minimum') else None,
                'maximum': pspec.maximum if hasattr(pspec, 'maximum') else None
            }

        return retval

    def _type_get_signals (self, element):
        retval = {}

        for child in element.iterfind(ns('glib', 'signal')):
            name = child.get('name').replace('_', '-')
            retval[name] = {
                'version': child.get('version'),
                'deprecated_version': child.get('deprecated-version'),
                'detailed': child.get('detailed'),
            }

        return retval

    def _type_get_interfaces (self, element):
        retval = []

        for child in element.iterfind('implements', nsmap):
            name = child.get('name')
            if name.find('.') < 0:
                retval.append(self.name + name)

        return retval

    def _get_type_data (self, element, name, use_instance=True):
        parent = element.get('parent')

        if parent and parent.find('.') < 0:
            parent = self.prefix + parent
        elif parent is None:
            parent = 'object'
        else:
            parent = 'GObject'

        # Get version and deprecated-version from constructor if possible
        constructor = element.find('constructor', nsmap)
        if constructor is None:
            constructor = element

        if use_instance:
            instance = self._get_instance_from_type(name)
        else:
            instance = None

        return {
            'parent': parent,
            'layout': None,
            'abstract': element.get('abstract'),
            'version': constructor.get('version'),
            'deprecated_version': constructor.get('deprecated-version'),
            'get_type': element.get(ns('glib','get-type')),
            'properties': self._type_get_properties(element, instance),
            'signals': self._type_get_signals(element),
            'interfaces': self._type_get_interfaces(element)
        }

    def _get_types (self, namespace, types=None, skip_types=[]):
        retval = {}

        for child in namespace.iterfind('class', nsmap):
            name = child.get(ns('glib','type-name'))

            if name and (types is None or name in types):
                data = self._get_type_data(child, name, not name in skip_types)
                if name and data is not None:
                    retval[name] = data

        return retval

    def _get_enumerations (self, namespace, types=None):
        retval = {}

        for child in namespace.iterfind('enumeration', nsmap):
            name = child.get(ns('glib','type-name'))
            if name and (types is None or name in types):
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
                'nick': child.get(ns('glib','nick')),
                'identifier': child.get(ns('c','identifier')),
                'doc': doc_text
            }

        return retval

    def _get_flags (self, namespace, types=None):
        retval = {}

        for child in namespace.iterfind('bitfield', nsmap):
            name = child.get(ns('glib','type-name'))
            if name and (types is None or name in types):
                retval[name] = {
                    'parent': 'flags',
                    'members': self._enum_flags_get_members(child)
                }

        return retval

    def _get_ifaces (self, namespace, types=None):
        retval = {}

        for child in namespace.iterfind('interface', nsmap):
            name = child.get(ns('glib','type-name'))
            if name and (types is None or name in types):
                retval[name] = {
                    'parent': 'interface',
                }

        return retval

    def populate_db (self, conn):
        def db_insert_enum_flags(conn, name, data):
            parent = data['parent']
            conn.execute(f"INSERT INTO type (library_id, type_id, parent_id) VALUES (?, ?, ?);",
                         (self.lib, name, parent))

            members = data['members']
            for member in members:
                m = members[member]
                conn.execute(f"INSERT INTO type_{parent} (type_id, name, value, nick, identifier, doc) VALUES (?, ?, ?, ?, ?, ?);",
                             (name, member, m['value'], m['nick'], m['identifier'], m['doc']))


        def db_insert_iface(conn, name, data):
            parent = data['parent']
            conn.execute(f"INSERT INTO type (library_id, type_id, parent_id) VALUES (?, ?, ?);",
                         (self.lib, name, parent))


        def db_insert_type(conn, name, data):
            parent = data['parent']

            if parent and parent.find('.') >= 0:
                parent = 'object'

            conn.execute(f"INSERT INTO type (library_id, type_id, parent_id, get_type, version, deprecated_version, abstract, layout) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                         (self.lib, name, parent, data['get_type'], data['version'], data['deprecated_version'], data['abstract'], data['layout']))


        def db_insert_type_data(conn, name, data):
            properties = data['properties']
            for prop in properties:
                p = properties[prop]
                prop_type = p['type']

                # Ignore unknown types (Propably GBoxed)
                if prop_type.startswith(self.name) and \
                   prop_type not in self.types and \
                   prop_type not in self.flags and \
                   prop_type not in self.enumerations and \
                   prop_type not in self.ifaces:
                    continue

                conn.execute(f"INSERT INTO property (owner_id, property_id, type_id, writable, construct_only, default_value, minimum, maximum, version, deprecated_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                             (name, prop, prop_type, p['writable'], p['construct'], p.get('default_value', None), p.get('minimum', None), p.get('maximum', None), p['version'], p['deprecated_version']))

            signals = data['signals']
            for signal in signals:
                s = signals[signal]
                conn.execute(f"INSERT INTO signal (owner_id, signal_id, version, deprecated_version, detailed) VALUES (?, ?, ?, ?, ?);",
                             (name, signal, s['version'], s['deprecated_version'], s['detailed']))

            for iface in data['interfaces']:
                conn.execute(f"INSERT INTO type_iface (type_id, iface_id) VALUES (?, ?);",
                             (name, iface))

        # Import library
        conn.execute(f"INSERT INTO library (library_id, version, shared_library) VALUES (?, ?, ?);",
                     (self.lib, self.version, self.shared_library));

        if hasattr(self.mod, 'get_major_version'):
            major = self.mod.get_major_version()
            for minor in range(0, self.mod.get_minor_version()+1, 2):
                conn.execute(f"INSERT INTO library_version (library_id, version) VALUES (?, ?);",
                             (self.lib, f"{major}.{minor}"));

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

