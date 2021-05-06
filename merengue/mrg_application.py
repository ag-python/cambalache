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


from gi.repository import GLib
Gdk = None
Gtk = None
mrg_gtk = None
utils = None

from controller import MrgControllerRegistry

# Globals
registry = MrgControllerRegistry()
global_builder = None
controllers = {}


def _print(*args):
    print(*args, file=sys.stderr)


def get_controller(ui_id, object_id):
    return controllers.get(f'{ui_id}.{object_id}', None)


def clear_all():
    global controllers, preselected_widget

    preselected_widget = None

    # Unset controllers objects
    for key in controllers:
        controllers[key].object = None


def update_ui(ui_id, payload=None):
    global controllers

    clear_all()

    if payload == None:
        return

    # Build everything
    builder = Gtk.Builder()
    builder.add_from_string(payload)

    # Keep dict of all object controllers by id
    for obj in builder.get_objects():
        object_id = utils.object_get_id(obj)

        if object_id is None:
            continue

        controller = controllers.get(object_id, None)

        if controller:
            # Reuse controller
            controller.object = obj
        else:
            # Create a new controller
            controller = registry.new_controller_for_object(obj)

        controllers[object_id] = controller


def object_removed(ui_id, object_id):
    controller = get_controller(ui_id, object_id)

    if controller:
        if issubclass(type(controller.object), Gtk.Widget):
            controller.object.destroy()
            controller.object = None

        del controllers[f'{ui_id}.{object_id}']


def object_property_changed(ui_id, object_id, property_id, value):
    controller = get_controller(ui_id, object_id)

    if controller is None:
        return

    pspec = controller.object.find_property(property_id)

    if pspec:
        try:
            status, val = global_builder.value_from_string_type(pspec.value_type, value)
            if status:
                controller.set_object_property(property_id, val)
                #controller.object.set_property(property_id, val)
        except:
            pass


def object_layout_property_changed(ui_id, object_id, child_id, property_id, value):
    controller = get_controller(ui_id, object_id)
    child = get_controller(ui_id, object_id)

    if controller is None or child is None:
        return

    pspec = controller.find_child_property(child.object, property_id)

    if pspec:
        try:
            status, val = global_builder.value_from_string_type(pspec.value_type, value)
            if status:
                controller.set_object_child_property(child.object, property_id, val)
        except:
            pass


def selection_changed(ui_id, selection):
    # Clear objects
    for object_id in controllers:
        controller = controllers[object_id]
        if controller.object:
            controller.object.get_style_context().remove_class('merengue_selected')

    length = len(selection)

    # Add class to selected objects
    for object_id in selection:
        controller = get_controller(ui_id, object_id)
        obj = controller.object

        if obj:
            obj.get_style_context().add_class('merengue_selected')

            if length == 1 and issubclass(type(obj), Gtk.Window):
                # TODO: fix broadway for this to work
                obj.present()


def run_command(command, args, payload):
    _print(command, args)

    if command == 'clear_all':
        clear_all()
    elif command == 'update_ui':
        update_ui(**args, payload=payload)
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
    if condition == GLib.IOCondition.HUP:
        sys.exit(-1)
        return GLib.SOURCE_REMOVE

    # We receive a command in each line
    retval = sys.stdin.readline()

    try:
        # Command is a Json string with a command, args and payload_length fields
        cmd = json.loads(retval)
    except Exception as e:
        _print(e)
    else:
        payload_length = cmd.get('payload_length', 0)

        # Read command payload if any
        payload = sys.stdin.read(payload_length) if payload_length else None

        command = cmd.get('command', None)
        args = cmd.get('args', {})

        # Run command
        run_command(command, args, payload)

    return GLib.SOURCE_CONTINUE


def merengue_init(ver):
    global Gdk, Gtk, mrg_gtk, utils, global_builder

    version = '4.0' if ver == 'gtk-4.0' else '3.0'
    gi.require_version('Gdk', version)
    gi.require_version('Gtk', version)

    from gi.repository import Gdk, Gtk

    import mrg_gtk, utils

    # TODO: support multiples plugins
    registry.load_module(mrg_gtk)

    global_builder = Gtk.Builder()
    stdin_channel = GLib.IOChannel.unix_new(sys.stdin.fileno())
    GLib.io_add_watch(stdin_channel, GLib.PRIORITY_DEFAULT_IDLE,
                      GLib.IOCondition.IN | GLib.IOCondition.HUP,
                      on_stdin)

    provider = Gtk.CssProvider()
    provider.load_from_resource('/ar/xjuan/Merengue/merengue.css')

    if Gtk.MAJOR_VERSION == 3:
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

    utils.write_command('started')

    return Gtk

