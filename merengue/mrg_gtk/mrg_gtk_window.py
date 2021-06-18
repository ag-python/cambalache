# GtkWindow Controller
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject, Gdk, Gtk

from .mrg_gtk_widget import MrgGtkWidgetController

from merengue import utils

preselected_widget = None


class FindInContainerData():
    def __init__(self, toplevel, x, y):
        self.toplevel = toplevel
        self.x = x
        self.y = y
        self.child = None
        self.level = None


class MrgGtkWindowController(MrgGtkWidgetController):
    def __init__(self, **kwargs):
        self._object = None
        self._position = None
        self._size = None
        self._is_maximized = None
        self._is_fullscreen = None

        super().__init__(**kwargs)

        self.property_ignore_list.add('modal')

    @GObject.property(type=Gtk.Window)
    def object(self):
        return self._object

    @object.setter
    def _set_object(self, obj):
        # keep track of size, position, and window state (maximized)
        self._save_state()

        if self._object:
            self._object.destroy()

        self._object = obj

        if obj:
            self._update_name()

            # Handle widget selection
            self.gesture = self._add_selection_handler()

            # Make sure the user can not close the window
            if Gtk.MAJOR_VERSION == 3:
                obj.connect('delete-event', lambda o, e: True)
            else:
                obj.connect('close-request', lambda o: True)

            # Restore size
            if self._size and not self._is_maximized:
                self.object.set_default_size(*self._size)

            # Disable modal at runtime
            obj.props.modal = False

            # Always show toplevels windows
            if Gtk.MAJOR_VERSION == 3:
                obj.show_all()
            else:
                obj.show()

            # Add gtk version CSS class
            gtkversion = 'gtk3' if Gtk.MAJOR_VERSION == 3 else 'gtk4'
            obj.get_style_context().add_class(gtkversion)

            self._restore_state()
        else:
            self.gesture = None

    def _update_name(self):
        if self._object is None:
            return

        name = utils.object_get_name(self._object)
        type_name = GObject.type_name(self._object.__gtype__)
        self._object.props.title = f'{name} - {type_name}' if name else type_name

    def _save_state(self):
        if self._object is None:
            return

        self._is_maximized = self.object.is_maximized()

        if self._is_maximized:
            return

        if Gtk.MAJOR_VERSION == 3:
            self._position = self.object.get_position()
            self._size = self.object.get_size()
        else:
            self._size = [self.object.get_width(), self.object.get_height()]

    def _restore_state(self):
        if self._is_maximized:
            self.object.maximize()
            return

        if Gtk.MAJOR_VERSION == 3:
            if self._position:
                self.object.move(*self._position)
        else:
            # TODO: find a way to store position on gtk4
            pass

    def _on_gesture_button_pressed(self, gesture, n_press, x, y):
        global preselected_widget

        child = self.get_child_at_position(self.object, x, y)
        object_id = utils.object_get_id(child)

        # Pre select a widget on button press
        preselected_widget = child if object_id else None

    def _on_gesture_button_released(self, gesture, n_press, x, y):
        global preselected_widget

        child = self.get_child_at_position(self.object, x, y)
        object_id = utils.object_get_id(child)

        # Select widget on button release only if its preselected
        if object_id and child == preselected_widget:
            utils.write_command('selection_changed', args={ 'selection': [object_id] })

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

    def is_widget_from_ui(self, obj):
        object_id = utils.object_get_builder_id(obj)
        return object_id is not None and object_id.startswith('__cambalache__')


    def _find_first_child_inside_container (self, widget, data):
        if data.child is not None or not widget.get_mapped():
            return

        x, y = data.toplevel.translate_coordinates(widget, data.x, data.y)

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        if x >= 0 and x < w and y >= 0 and y < h:
            from_ui = self.is_widget_from_ui(widget)

            if issubclass(type(widget), Gtk.Container):
                if from_ui:
                    data.child = self.get_child_at_position(widget, x, y)
                else:
                    widget.forall(self._find_first_child_inside_container, data)

            if data.child is None and from_ui:
                data.child = widget


    def get_child_at_position(self, widget, x, y):
        if Gtk.MAJOR_VERSION == 4:
            pick = widget.pick(x, y, Gtk.PickFlags.INSENSITIVE | Gtk.PickFlags.NON_TARGETABLE)
            while pick and not self.is_widget_from_ui(pick):
                pick = pick.props.parent
            return pick

        if not widget.get_mapped():
            return None

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        if x >= 0 and x <= w and y >= 0 and y <= h:
            if issubclass(type(widget), Gtk.Container):
                data = FindInContainerData(widget, x, y)

                widget.forall(self._find_first_child_inside_container, data)

                return data.child if data.child is not None else widget
            else:
                return widget

        return None

