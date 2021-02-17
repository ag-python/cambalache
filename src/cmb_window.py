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
from gi.repository import GLib, GObject, Gio, Gtk

from cambalache import *


@Gtk.Template(filename='src/cmb_window.ui')
class CmbWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'CmbWindow'

    open_filter = Gtk.Template.Child()
    import_filter = Gtk.Template.Child()

    open_button_box = Gtk.Template.Child()
    import_button_box = Gtk.Template.Child()

    headerbar = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    # Start screen
    version_label = Gtk.Template.Child()

    # New Project
    np_name_entry = Gtk.Template.Child()
    np_location_chooser = Gtk.Template.Child()
    np_gtk3_radiobutton = Gtk.Template.Child()
    np_gtk4_radiobutton = Gtk.Template.Child()

    # Workspace
    view = Gtk.Template.Child()
    tree_view = Gtk.Template.Child()
    type_entry = Gtk.Template.Child()
    type_entrycompletion = Gtk.Template.Child()

    about_dialog = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self._project = None

        super().__init__(**kwargs)

        self.open_button_box.props.homogeneous = False
        self.import_button_box.props.homogeneous = False

        for action in ['open', 'create_new', 'new',
                       'undo', 'redo',
                       'save', 'save_as',
                       'add_ui', 'remove_ui',
                       'import', 'export',
                       'close', 'about']:
            gaction= Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self.add_action(gaction)

    @GObject.Property(type=CmbProject)
    def project(self):
        return self._project

    @project.setter
    def _set_project(self, project):
        if self._project is not None:
            self._project.disconnect_by_func(self._on_project_filename_notify)

        self._project = project
        self.view.project = project
        self.tree_view.props.model = project
        self.type_entrycompletion.props.model = self.project.type_list if project else None

        if project is not None:
            self._on_project_filename_notify(None, None)
            self._project.connect("notify::filename", self._on_project_filename_notify)
        else:
            self.headerbar.set_subtitle(None)

    def _on_project_filename_notify(self, obj, pspec):
        path = self.project.filename.replace(GLib.get_home_dir(), '~')
        self.headerbar.set_subtitle(path)

    @Gtk.Template.Callback('on_about_dialog_delete_event')
    def _on_about_dialog_delete_event(self, widget, event):
        widget.hide()
        return True

    @Gtk.Template.Callback('on_type_entry_activate')
    def _on_type_entry_activate(self, entry):
        selection = self.project.get_selection()

        if len(selection) > 0:
            self.project.add_object(selection[0].ui_id, entry.get_text())

    def _file_open_dialog_new(self, title, action=Gtk.FileChooserAction.OPEN, filter_obj=None):
        dialog = Gtk.FileChooserDialog(
            title=title,
            parent=self,
            action=action,
            filter=filter_obj
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        if self.project is not None:
            dialog.select_filename(self.project.filename)

        return dialog

    def _on_open_activate(self, action, data):
        dialog = self._file_open_dialog_new("Choose file to open",
                                            filter_obj=self.open_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            try:
                self.project = CmbProject(filename=dialog.get_filename())
                self.stack.set_visible_child_name('workspace')
            except Exception as e:
                pass

        dialog.destroy()

    def _on_create_new_activate(self, action, data):
        self.stack.set_visible_child_name('new_project')
        self.set_focus(self.np_name_entry)

        home = GLib.get_home_dir()
        projects = os.path.join(home, 'Projects')
        directory = projects if os.path.isdir(projects) else home

        self.np_location_chooser.select_filename(directory)

    def _on_new_activate(self, action, data):
        if self.project is not None:
            return

        name = self.np_name_entry.props.text
        location = self.np_location_chooser.get_filename() or '.'

        if len(name) < 1:
            self.set_focus(self.np_name_entry)
            return

        if self.np_gtk3_radiobutton.get_active():
            target_tk='gtk+-3.0'
        elif self.np_gtk4_radiobutton.get_active():
            target_tk='gtk-4.0'

        name, ext = os.path.splitext(name)
        filename = os.path.join(location, name + '.cmb')
        self.project = CmbProject(target_tk=target_tk, filename=filename)
        self.stack.set_visible_child_name('workspace')

    def _on_undo_activate(self, action, data):
        print('_on_undo_activate')

    def _on_redo_activate(self, action, data):
        print('_on_redo_activate')

    def _on_save_activate(self, action, data):
        if self.project is not None:
            self.project.save()

    def _on_save_as_activate(self, action, data):
        print('_on_save_as_activate')

    def _on_add_ui_activate(self, action, data):
        dialog = self._file_open_dialog_new("Choose a file to save the project",
                                            Gtk.FileChooserAction.SAVE)
        if dialog.run() == Gtk.ResponseType.OK:
            self.project.add_ui(dialog.get_filename())

        dialog.destroy()

    def _on_remove_ui_activate(self, action, data):
        if self.project is None:
            return

        selection = self.project.get_selection()
        if len(selection) > 0:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Do you want to delete selected UI?",
            )

            if dialog.run() == Gtk.ResponseType.YES:
                self.project.remove_ui(selection[0])

            dialog.destroy()

    def _on_import_activate(self, action, data):
        if self.project is None:
            return

        dialog = self._file_open_dialog_new("Choose file to import",
                                            filter_obj=self.import_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            self.project.import_file(dialog.get_filename())

        dialog.destroy()

    def _on_export_activate(self, action, data):
        if self.project is not None:
            self.project.export()

    def _on_close_activate(self, action, data):
        self.project = None
        self.stack.set_visible_child_name('cambalache')

    def _on_about_activate(self, action, data):
        self.about_dialog.present()

