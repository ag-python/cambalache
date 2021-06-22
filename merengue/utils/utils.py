#
# Merengue utilities
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import sys
import json

import gi
from gi.repository import GLib, Gtk


def write_command(command, payload=None, args=None):
    cmd = {
        'command': command,
        'payload_length': len(payload) if payload is not None else 0
    }

    if args is not None:
        cmd['args'] = args

    # Send command in one line as json
    sys.stdout.write(json.dumps(cmd))
    sys.stdout.write('\n')

    # Send payload if any
    if payload is not None:
        sys.stdout.write(payload)

    # Flush
    sys.stdout.flush()


def object_get_builder_id(obj):
    if obj is None:
        return None

    if issubclass(type(obj), Gtk.Buildable):
        if Gtk.MAJOR_VERSION == 4:
            return Gtk.Buildable.get_buildable_id(obj)
        else:
            return Gtk.Buildable.get_name(obj)
    else:
        return _g_object_get_data(obj, 'gtk-builder-name')


def object_get_id(obj):
    if obj is None:
        return None

    builder_id = object_get_builder_id(obj)
    if builder_id and builder_id.startswith('__cambalache__'):
        tokens = builder_id[14:].split('+', 2)
        return tokens[0]

    return None


def object_get_name(obj):
    if obj:
        builder_id = object_get_builder_id(obj)
        if builder_id.startswith('__cambalache__'):
            tokens = builder_id[14:].split('+', 2)
            if len(tokens) > 1:
                return GLib.uri_unescape_string(tokens[1], None)

    return None


#
# CTYPES HACKS
#
import ctypes
from ctypes.util import find_library

# Python object size, needed to calculate GObject pointer
object_size = sys.getsizeof(object())

# Return C object pointer
def _cobject(obj):
    return ctypes.c_void_p.from_address(id(obj) + object_size)


# GObject library
gobject = ctypes.CDLL(find_library('gobject-2.0'))

# g_object_get_data
gobject.g_object_get_data.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
gobject.g_object_get_data.restype = ctypes.c_char_p

def _g_object_get_data (obj, key):
    retval = gobject.g_object_get_data(_cobject(obj), key.encode('utf-8'))
    return retval.decode('utf-8') if retval else None
