#
# Merengue: Cambalache view process
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import gi
import sys
import json


def _print(*args):
    print(*args, file=sys.stderr)


def get_object(ui_id, object_id):
    return objects.get(f'{ui_id}.{object_id}', None)


def child_set_property(parent, child, property_id, val):
    if version == '3.0':
        obj.child_set_property(child, property_id, val)
    else:
        manager = parent.get_layout_manager()
        layout_child = manager.get_layout_child()
        layout_child.set_property(property_id, val)


def object_get_id(obj):
    if version == '3.0':
        return Gtk.Buildable.get_name(obj)
    else:
        return Gtk.Buildable.get_buildable_id (obj)


def widget_show(obj):
    if version == '3.0':
        obj.show_all()
    else:
        obj.show()


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


def clear_all():
    global toplevels, objects

    # Destroy all toplevels
    for win in toplevels:
        win.destroy()

    toplevels = []


def update_ui(ui_id, builder_string):
    global toplevels, objects

    clear_all()

    # Build everything
    builder = Gtk.Builder()
    builder.add_from_string(builder_string)

    # Show toplevels
    for obj in builder.get_objects():
        if obj.props.parent is None and issubclass(type(obj), Gtk.Window):
            toplevels.append(obj)
            widget_show(obj)

        # Keep dict of all objects by id
        object_id = object_get_id(obj)
        objects[f'{ui_id}.{object_id}'] = obj


def object_removed(ui_id, object_id):
    obj = get_object(ui_id, object_id)

    if obj:
        if issubclass(type(obj), Gtk.Widget):
            obj.destroy()

        if issubclass(type(obj), Gtk.Window):
            toplevels.remove(obj)


def object_property_changed(ui_id, object_id, property_id, value):
    obj = get_object(ui_id, object_id)

    if obj:
        pspec = obj.find_property(property_id)
        if pspec:
            status, val = global_builder.value_from_string_type(pspec.value_type, value)
            if status:
                try:
                    obj.set_property(property_id, val)
                except:
                    pass


def object_layout_property_changed(ui_id, object_id, child_id, property_id, value):
    obj = get_object(ui_id, object_id)
    child = get_object(ui_id, child_id)

    if obj and child:
        pspec = obj.find_child_property (property_id)
        if pspec:
            status, val = global_builder.value_from_string_type(pspec.value_type, value)
            if status:
                try:
                    child_set_property(obj, child, property_id, val)
                except:
                    pass


def selection_changed(ui_id, selection):
    # Clear objects
    for obj_id in objects:
        obj = objects[obj_id]
        obj.get_style_context().remove_class('merengue_selected')

    length = len(selection)

    # Add class to selected objects
    for obj_id in selection:
        obj = objects[f'{ui_id}.{obj_id}']

        if obj:
            obj.get_style_context().add_class('merengue_selected')

            if length == 1 and issubclass(type(obj), Gtk.Window):
                # TODO: fix broadway for this to work
                obj.present()

    write_command('selection_changed', args={ 'hola': 'mundo' })


def run_command(cmd, payload):
    command = cmd.get('command', None)
    args = cmd.get('args', {})

    _print(command, args)

    if command == 'clear_all':
        clear_all()
    elif command == 'update_ui':
        update_ui(cmd['args']['ui_id'], payload)
    elif command == 'selection_changed':
        selection_changed(**args)
    elif command == 'object_removed':
        object_removed(**args)
    elif command == 'object_property_changed':
        object_property_changed(**args)
    elif command == 'object_layout_property_changed':
        object_layout_property_changed(**args)
    else:
        _print('Unknown command', command)


def on_stdin(channel, condition):
    # We receive a command in each line
    retval = sys.stdin.readline()

    try:
        # Command is a Json string with a command and payload_length field
        # and any other command specific fields
        cmd = json.loads(retval)
    except Exception as e:
        _print(e)
    else:
        payload_length = cmd.get('payload_length', 0)

        # Read command payload if any
        payload = sys.stdin.read(payload_length) if payload_length else None

        # Run command
        run_command(cmd, payload)

    return GLib.SOURCE_CONTINUE


from gi.repository import GLib
Gdk = None
Gtk = None

# Globals
version = None
global_builder = None
toplevels = []
objects = {}

def merengue_init(ver):
    global version, Gdk, Gtk, global_builder

    version = '4.0' if ver == 'gtk-4.0' else '3.0'
    gi.require_version('Gdk', version)
    gi.require_version('Gtk', version)

    from gi.repository import Gdk, Gtk

    global_builder = Gtk.Builder()
    stdin_channel = GLib.IOChannel.unix_new(sys.stdin.fileno())
    GLib.io_add_watch(stdin_channel, GLib.PRIORITY_DEFAULT_IDLE, GLib.IOCondition.IN, on_stdin)

    provider = Gtk.CssProvider()
    provider.load_from_resource('/ar/xjuan/Merengue/cmb_merengue.css')

    if version == '3.0':
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    else:
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    return (version, Gdk, Gtk)
