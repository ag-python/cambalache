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
from gi.repository import Gtk


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

    if Gtk.MAJOR_VERSION == 3:
        return Gtk.Buildable.get_name(obj)
    else:
        return Gtk.Buildable.get_buildable_id (obj)


def object_get_id(obj):
    if obj:
        builder_id = object_get_builder_id(obj)
        if builder_id.startswith('__cambalache__'):
            return builder_id[14:]

    return None

