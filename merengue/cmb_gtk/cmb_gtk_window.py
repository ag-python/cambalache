# Merengue Gtk plugin
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject, Gdk, Gtk

from .cmb_gtk_widget import CmbGtkWidgetController

import utils

preselected_widget = None


class CmbGtkWindowController(CmbGtkWidgetController):
    __gsignals__ = {
        'object-selected': (GObject.SIGNAL_RUN_FIRST, None, (str, )),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @GObject.property(type=Gtk.Window)
    def object(self):
        return self._object

    @object.setter
    def _set_object(self, obj):
        self._object = obj

        if obj:
            # Handle widget selection
            self.gesture = self._add_selection_handler()

            # Make sure the user can not close the window
            if Gtk.MAJOR_VERSION == 3:
                obj.connect('delete-event', lambda o, e: True)
            else:
                obj.connect('close-request', lambda o: True)

            # TODO: keep track of size, position, and window state (maximized, fullscreen)
        else:
            self.gesture = None

    def _on_gesture_button_pressed(self, gesture, n_press, x, y):
        global preselected_widget

        child = utils.get_child_at_position(self.object, x, y)
        object_id = utils.object_get_id(child)

        # Pre select a widget on button press
        preselected_widget = child if object_id else None

    def _on_gesture_button_released(self, gesture, n_press, x, y):
        global preselected_widget

        child = utils.get_child_at_position(self.object, x, y)
        object_id = utils.object_get_id(child)

        # Select widget on button release only if its preselected
        if object_id and child == preselected_widget:
            self.emit('object-selected', object_id)

    def _add_selection_handler(self):
        if Gtk.MAJOR_VERSION == 3:
            self.object.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                                   Gdk.EventMask.BUTTON_RELEASE_MASK)
            gesture = Gtk.GestureMultiPress(widget=self.object,
                                            propagation_phase=Gtk.PropagationPhase.CAPTURE)
        else:
            gesture = Gtk.GestureClick(propagation_phase=Gtk.PropagationPhase.CAPTURE)
            self.object.add_controller(gesture)

        gesture.connect('pressed', self._on_gesture_button_pressed)
        gesture.connect('released', self._on_gesture_button_released)

        return gesture
