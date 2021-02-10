#
# CmbWindow
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from cambalache import *


@Gtk.Template(filename='src/cmb_window.ui')
class CmbWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'CmbWindow'

    open_filter = Gtk.Template.Child()
    import_filter = Gtk.Template.Child()

    open_button_box = Gtk.Template.Child()
    import_button_box = Gtk.Template.Child()

    stack = Gtk.Template.Child()
    view = Gtk.Template.Child()
    tree_view = Gtk.Template.Child()
    type_entry = Gtk.Template.Child()

    about_dialog = Gtk.Template.Child()

    project = GObject.Property(type=CmbProject)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.open_button_box.props.homogeneous = False
        self.import_button_box.props.homogeneous = False

        self.connect("notify::project", self._on_project_notify)

    def _on_project_notify(self, obj, pspec):
        self.view.project = self.project
        self.tree_view.props.model = self.project

    @Gtk.Template.Callback('on_about_dialog_delete_event')
    def _on_about_dialog_delete_event(self, widget, event):
        widget.hide()
        return True

    @Gtk.Template.Callback('on_type_entry_activate')
    def _on_type_entry_activate(self, entry):
        self.project.add_object(1, entry.get_text())

