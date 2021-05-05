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


def child_set_property(parent, child, property_id, val):
    if Gtk.MAJOR_VERSION == 3:
        parent.child_set_property(child, property_id, val)
    else:
        manager = parent.get_layout_manager()
        layout_child = manager.get_layout_child()
        layout_child.set_property(property_id, val)


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


def widget_show(obj):
    if Gtk.MAJOR_VERSION == 3:
        obj.show_all()
    else:
        obj.show()


class FindInContainerData():
    def __init__(self, toplevel, x, y):
        self.toplevel = toplevel
        self.x = x
        self.y = y
        self.child = None
        self.level = None


def is_widget_from_ui(obj):
    object_id = object_get_builder_id(obj)
    return object_id is not None and object_id.startswith('__cambalache__')


def _find_first_child_inside_container (widget, data):
    if data.child is not None or not widget.get_mapped():
        return

    x, y = data.toplevel.translate_coordinates(widget, data.x, data.y)

    w = widget.get_allocated_width()
    h = widget.get_allocated_height()

    if x >= 0 and x < w and y >= 0 and y < h:
        from_ui = is_widget_from_ui(widget)

        if issubclass(type(widget), Gtk.Container):
            if from_ui:
                data.child = get_child_at_position(widget, x, y)
            else:
                widget.forall(_find_first_child_inside_container, data)

        if data.child is None and from_ui:
            data.child = widget


def get_child_at_position(widget, x, y):
    if Gtk.MAJOR_VERSION == 4:
        pick = widget.pick(x, y, Gtk.PickFlags.INSENSITIVE | Gtk.PickFlags.NON_TARGETABLE)
        while pick and not is_widget_from_ui(pick):
            pick = pick.props.parent
        return pick

    if not widget.get_mapped():
        return None

    w = widget.get_allocated_width()
    h = widget.get_allocated_height()

    if x >= 0 and x <= w and y >= 0 and y <= h:
        if issubclass(type(widget), Gtk.Container):
            data = FindInContainerData(widget, x, y)

            widget.forall(_find_first_child_inside_container, data)

            return data.child if data.child is not None else widget
        else:
            return widget

    return None

