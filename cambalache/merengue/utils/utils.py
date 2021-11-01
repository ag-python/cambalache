#
# Merengue utilities
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

import sys
import json

import gi
from gi.repository import GLib, Gdk, Gtk


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
    if builder_id and builder_id.startswith('__cmb__'):
        return builder_id[7:]

    return None


def gesture_click_new(widget, **kwargs):
    if Gtk.MAJOR_VERSION == 4:
        retval = Gtk.GestureClick(**kwargs)
        widget.add_controller(retval)
    else:
        widget.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                          Gdk.EventMask.BUTTON_RELEASE_MASK)
        retval = Gtk.GestureMultiPress(widget=widget, **kwargs)
    return retval


def scroll_controller_new(widget, **kwargs):
    if Gtk.MAJOR_VERSION == 4:
        retval = Gtk.EventControllerScroll(**kwargs)
        widget.add_controller(retval)
    else:
        widget.add_events(Gdk.EventMask.SCROLL_MASK)
        retval = Gtk.EventControllerScroll(widget=widget, **kwargs)
    return retval

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
