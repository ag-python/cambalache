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

        self._actions = {}
        self.open_button_box.props.homogeneous = False
        self.import_button_box.props.homogeneous = False

        for action in ['open', 'create_new', 'new',
                       'undo', 'redo',
                       'save', 'save_as',
                       'add_ui', 'remove_ui',
                       'import', 'export',
                       'close', 'about']:
            gaction = Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self._actions[action] = gaction
            self.add_action(gaction)

        self._update_actions()

    @GObject.Property(type=CmbProject)
    def project(self):
        return self._project

    @project.setter
    def _set_project(self, project):
        if self._project is not None:
            self._project.disconnect_by_func(self._on_project_filename_notify)
            self._project.disconnect_by_func(self._on_project_selection_changed)

        self._project = project
        self.view.project = project
        self.tree_view.props.model = project
        self.type_entrycompletion.props.model = self.project.type_list if project else None

        if project is not None:
            self._on_project_filename_notify(None, None)
            self._project.connect("notify::filename", self._on_project_filename_notify)
            self._project.connect('selection-changed', self._on_project_selection_changed)
            self.type_entry.set_placeholder_text(project.target_tk)
        else:
            self.headerbar.set_subtitle(None)

        self._update_actions()

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
            obj = selection[0]
            parent_id = obj.object_id if type(obj) == CmbObject else None
            self.project.add_object(obj.ui_id, entry.get_text(), parent_id=parent_id)

    @Gtk.Template.Callback('on_open_recent_action_item_activated')
    def _on_open_recent_action_item_activated(self, recent):
        uri = recent.get_current_uri()
        if uri is not None:
            try:
                filename, host = GLib.filename_from_uri(uri)
                self.project = CmbProject(filename=filename)
                self.stack.set_visible_child_name('workspace')
                self._update_actions()
            except Exception as e:
                pass

    def _update_action_undo_redo(self):
        if self.project is not None:
            self._actions['undo'].set_enabled(self.project.history_index > 0)
            self._actions['redo'].set_enabled(self.project.history_index <
                                              self.project.history_index_max)

    def _update_action_remove_ui(self):
        if self.project is not None:
            selection = self.project.get_selection()
            ui_selected = len(selection) > 0 and type(selection[0]) == CmbUI
            self._actions['remove_ui'].set_enabled(ui_selected)

    def _on_project_selection_changed(self, project):
        self._update_action_remove_ui()

    def _update_actions(self):
        has_project = self.project is not None

        for action in ['undo', 'redo',
                       'save', 'save_as',
                       'add_ui', 'remove_ui',
                       'import', 'export',
                       'close']:
            self._actions[action].set_enabled(has_project)

        self._update_action_remove_ui()
        self._update_action_undo_redo()

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
            dialog.set_current_folder(os.path.dirname(self.project.filename))

        return dialog

    def _on_open_activate(self, action, data):
        dialog = self._file_open_dialog_new("Choose file to open",
                                            filter_obj=self.open_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            try:
                self.project = CmbProject(filename=dialog.get_filename())
                self.stack.set_visible_child_name('workspace')
                self._update_actions()
            except Exception as e:
                pass

        dialog.destroy()

    def _on_create_new_activate(self, action, data):
        self.stack.set_visible_child_name('new_project')
        self.set_focus(self.np_name_entry)

        home = GLib.get_home_dir()
        projects = os.path.join(home, 'Projects')
        directory = projects if os.path.isdir(projects) else home

        self.np_location_chooser.set_current_folder(directory)

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

        if os.path.exists(filename):
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="File name already exists, choose a different name.",
            )

            dialog.run()
            dialog.destroy()
            self.set_focus(self.np_name_entry)
            return

        self.project = CmbProject(target_tk=target_tk, filename=filename)
        self.stack.set_visible_child_name('workspace')

    def _on_undo_activate(self, action, data):
        if self.project is not None:
            self.project.undo()
            self._update_action_undo_redo()

    def _on_redo_activate(self, action, data):
        if self.project is not None:
            self.project.redo()
            self._update_action_undo_redo()

    def _on_save_activate(self, action, data):
        if self.project is not None:
            self.project.save()

    def _on_save_as_activate(self, action, data):
        if self.project is None:
            return

        dialog = self._file_open_dialog_new("Choose a new file to save the project",
                                            Gtk.FileChooserAction.SAVE)
        if dialog.run() == Gtk.ResponseType.OK:
            self.project.filename = dialog.get_filename()
            self.project.save()

        dialog.destroy()

    def _on_add_ui_activate(self, action, data):
        if self.project is None:
            return

        dialog = self._file_open_dialog_new("Choose a file name for the new UI",
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

