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

from gi.repository import GLib, Gio, Gdk, Gtk

from merengue.controller import MrgControllerRegistry
from merengue import utils


class MrgApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='ar.xjuan.Merengue',
                         flags=Gio.ApplicationFlags.NON_UNIQUE)

        # Needed to parse values from strings
        self.builder = Gtk.Builder()

        # List of available controler classes for objects
        self.registry = MrgControllerRegistry()

        # List of controllers
        self.controllers = {}

        # The widget that got the last button press this is used to select
        # a widget on button release
        self.preselected_widget = None

    def print(self, *args):
        print(*args, file=sys.stderr)

    def get_controller(self, ui_id, object_id):
        return self.controllers.get(f'{ui_id}.{object_id}', None)

    def get_controller_from_object(self, obj):
        object_id = utils.object_get_id(obj)
        return self.controllers.get(object_id, None)

    def clear_all(self):
        self.preselected_widget = None

        # Unset controllers objects
        for key in self.controllers:
            self.controllers[key].object = None

    def update_ui(self, ui_id, payload=None):
        self.clear_all()

        if payload == None:
            return

        # Build everything
        builder = Gtk.Builder()

        try:
            builder.add_from_string(payload)
        except Exception as e:
            self.print(e)

        # Keep dict of all object controllers by id
        for obj in builder.get_objects():
            object_id = utils.object_get_id(obj)

            if object_id is None:
                continue

            controller = self.controllers.get(object_id, None)

            if controller:
                # Reuse controller
                controller.object = obj
            else:
                # Create a new controller
                controller = self.registry.new_controller_for_object(obj, self)

            self.controllers[object_id] = controller

    def object_removed(self, ui_id, object_id):
        controller = self.get_controller(ui_id, object_id)

        if controller:
            controller.remove_object()
            del self.controllers[f'{ui_id}.{object_id}']

    def object_property_changed(self, ui_id, object_id, property_id, value):
        controller = self.get_controller(ui_id, object_id)

        if controller is None:
            return

        pspec = controller.object.find_property(property_id)

        if pspec:
            try:
                status, val = self.builder.value_from_string_type(pspec.value_type, value)
                if status:
                    controller.set_object_property(property_id, val)
            except:
                pass

    def object_layout_property_changed(self, ui_id, object_id, child_id, property_id, value):
        controller = self.get_controller(ui_id, object_id)
        child = self.get_controller(ui_id, child_id)

        if controller is None or child is None:
            return

        pspec = controller.find_child_property(child.object, property_id)

        if pspec:
            try:
                status, val = self.builder.value_from_string_type(pspec.value_type, value)
                if status:
                    controller.set_object_child_property(child.object, property_id, val)
            except:
                pass

    def selection_changed(self, ui_id, selection):
        # Clear objects
        for object_id in self.controllers:
            self.controllers[object_id].selected = False

        length = len(selection)

        # Add class to selected objects
        for object_id in selection:
            controller = self.get_controller(ui_id, object_id)
            if controller is None:
                continue

            obj = controller.object

            if obj and issubclass(type(obj), Gtk.Widget):
                controller.selected = True

                if length == 1 and issubclass(type(obj), Gtk.Window):
                    # TODO: fix broadway for this to work
                    obj.present()

    def run_command(self, command, args, payload):
        self.print(command, args)

        if command == 'clear_all':
            self.clear_all()
        elif command == 'update_ui':
            self.update_ui(**args, payload=payload)
        elif command == 'selection_changed':
            self.selection_changed(**args)
        elif command == 'object_removed':
            self.object_removed(**args)
        elif command == 'object_property_changed':
            self.object_property_changed(**args)
        elif command == 'object_layout_property_changed':
            self.object_layout_property_changed(**args)
        else:
            self.print('Unknown command', command)

    def on_stdin(self, channel, condition):
        if condition == GLib.IOCondition.HUP:
            sys.exit(-1)
            return GLib.SOURCE_REMOVE

        # We receive a command in each line
        retval = sys.stdin.readline()

        try:
            # Command is a Json string with a command, args and payload_length fields
            cmd = json.loads(retval)
        except Exception as e:
            print(e)
        else:
            payload_length = cmd.get('payload_length', 0)

            # Read command payload if any
            payload = sys.stdin.read(payload_length) if payload_length else None

            command = cmd.get('command', None)
            args = cmd.get('args', {})

            # Run command
            self.run_command(command, args, payload)

        return GLib.SOURCE_CONTINUE

    def do_startup(self):
        Gtk.Application.do_startup(self)

        # TODO: support multiples plugins
        from merengue import mrg_gtk
        self.registry.load_module(mrg_gtk)

        stdin_channel = GLib.IOChannel.unix_new(sys.stdin.fileno())
        GLib.io_add_watch(stdin_channel, GLib.PRIORITY_DEFAULT_IDLE,
                          GLib.IOCondition.IN | GLib.IOCondition.HUP,
                          self.on_stdin)

        provider = Gtk.CssProvider()
        provider.load_from_resource('/ar/xjuan/Merengue/merengue.css')

        if Gtk.MAJOR_VERSION == 4:
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        elif Gtk.MAJOR_VERSION == 3:
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        settings = Gtk.Settings.get_default()
        settings.props.gtk_enable_animations = False

        # We need to add at least a window for the app not to exit!
        self.add_window(Gtk.Window())

    def do_activate(self):
        utils.write_command('started')
