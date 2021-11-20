#
# Cambalache Tutor
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
# Based on glade-intro.c (C) 2017-2018 Juan Pablo Ugarte
#

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, GLib, Gdk, Gtk
from enum import Enum
from collections import namedtuple


class CmbTutorState(Enum):
    NULL = 1
    PLAYING = 2
    PAUSED = 3


class CmbTutorPosition(Enum):
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3
    CENTER = 4


ScriptNode = namedtuple('ScriptNode', 'widget text delay name position')


class CmbTutor(GObject.GObject):
    __gsignals__ = {
        'show-node': (GObject.SIGNAL_RUN_LAST, None, (str, Gtk.Widget)),
        'hide-node': (GObject.SIGNAL_RUN_LAST, None, (str, Gtk.Widget)),
    }

    window = GObject.Property(type=Gtk.Window, flags = GObject.ParamFlags.READWRITE)
    state = GObject.Property(type=int, flags = GObject.ParamFlags.READABLE)

    def __init__(self, script, **kwargs):
        # List of ScriptNode
        self.script = []

        # Popover to show the script text
        self.popover = None

        # Timeout id for running the script
        self.timeout_id = None

        # Current script node index
        self.current = None

        self.hiding_node = None

        super().__init__(**kwargs)

        for node in script:
            self.__add(*node)

    @GObject.Property()
    def state(self):
        if self.timeout_id:
            return CmbTutorState.PLAYING
        elif self.current:
            return CmbTutorState.PAUSED

        return CmbTutorState.NULL

    def __add(self, text, widget_name, delay, name=None, position=CmbTutorPosition.BOTTOM):
        widget = getattr(self.window, widget_name)
        self.script.append(ScriptNode(widget, text, delay, name, position))

    def play(self):
        if len(self.script) == 0:
            return

        if self.current is None:
          self.current = 0

        self.__script_play()

        self.notify('state')

    def pause(self):
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)

        self.timeout_id = None
        self.__hide_node(self.current)
        self.notify('state')

    def stop(self):
        self.pause()
        self.current = None
        self.notify('state')

    def __popover_new(self, text):
        popover = Gtk.Popover(modal=False)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                      spacing=6)

        box.add(Gtk.Image(icon_name="dialog-information-symbolic",
                          icon_size=Gtk.IconSize.DIALOG))
        box.add(Gtk.Label(label=text,
                          wrap=True,
                          max_width_chars=28))
        popover.add(box)
        popover.get_style_context().add_class("cmb-tutor")
        box.show_all()

        return popover

    def __script_transition(self):
        self.timeout_id = GLib.timeout_add (250, self.__script_play)

        self.__hide_current_node()

        # Set next node
        if self.current is not None:
            self.current = self.current + 1 if self.current < (len(self.script) - 1) else None;

        return GLib.SOURCE_REMOVE

    def __hide_node(self, index):
        if self.popover:
            self.popover.popdown()
            self.popover = None

        if index is not None:
            node = self.script[index]

            if node.widget:
                node.widget.get_style_context().remove_class("cmb-tutor-highlight")

    def __hide_current_node(self):
        if self.hiding_node:
            return

        self.hiding_node = True

        self.__hide_node(self.current)

        if self.current is not None:
            node = self.script[self.current]
            self.emit('hide-node', node.name, node.widget)

        self.hiding_node = False

    def __script_play(self):
        self.timeout_id = None;

        if self.current is None:
            return GLib.SOURCE_REMOVE

        node = self.script[self.current]

        if node and node.text:
            # Ensure the widget is visible
            if not node.widget.is_visible():
                # if the widget is inside a popover pop it up
                parent = node.widget.get_ancestor(Gtk.Popover)
                if parent:
                    parent.popup()

            node.widget.get_style_context().add_class("cmb-tutor-highlight")

            # Create popover
            self.popover = self.__popover_new(node.text)
            self.popover.set_relative_to(node.widget)

            if node.position == CmbTutorPosition.BOTTOM:
                self.popover.set_position(Gtk.PositionType.BOTTOM)
            elif node.position == CmbTutorPosition.LEFT:
                self.popover.set_position(Gtk.PositionType.LEFT)
            elif node.position == CmbTutorPosition.RIGHT:
                self.popover.set_position(Gtk.PositionType.RIGHT)
            elif node.position == CmbTutorPosition.CENTER:
                rect = Gdk.Rectangle();
                rect.x = node.widget.get_allocated_width() / 2
                rect.y = node.widget.get_allocated_height() / 2
                self.popover.set_pointing_to(rect);
                self.popover.set_position(Gtk.PositionType.TOP);

        self.emit('show-node', node.name, node.widget);

        if self.popover:
            self.popover.set_sensitive(True)
            self.popover.popup()

        self.timeout_id = GLib.timeout_add(node.delay * 1000, self.__script_transition);

        return GLib.SOURCE_REMOVE

