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
import traceback

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gio, Gtk

from cambalache import *


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/App/cmb_window.ui')
class CmbWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'CmbWindow'

    __gsignals__ = {
        'open-project': (GObject.SIGNAL_RUN_FIRST, None, (str, str)),
        'cmb-action': (GObject.SIGNAL_RUN_LAST | GObject.SIGNAL_ACTION, None, (str, )),
    }

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
    object_editor = Gtk.Template.Child()
    object_layout_editor = Gtk.Template.Child()
    signal_editor = Gtk.Template.Child()

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
                       'add_ui', 'delete',
                       'import', 'export',
                       'close', 'debug', 'about']:
            gaction = Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self._actions[action] = gaction
            self.add_action(gaction)

        self._sqlitebrowser = GLib.find_program_in_path('sqlitebrowser')
        self._sqlitebrowser_pid = None

        self._update_actions()

        self.version_label.props.label = config.VERSION
        self.about_dialog.props.version = config.VERSION

    @GObject.Property(type=CmbProject)
    def project(self):
        return self._project

    @project.setter
    def _set_project(self, project):
        if self._project is not None:
            self._project.disconnect_by_func(self._on_project_filename_notify)
            self._project.disconnect_by_func(self._on_project_selection_changed)
            self._project.disconnect_by_func(self._on_project_changed)

        self._project = project
        self.view.project = project
        self.tree_view.props.model = project
        self.type_entrycompletion.props.model = self.project.type_list if project else None

        if project is not None:
            self._on_project_filename_notify(None, None)
            self._project.connect("notify::filename", self._on_project_filename_notify)
            self._project.connect('selection-changed', self._on_project_selection_changed)
            self._project.connect('changed', self._on_project_changed)
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
            filename, host = GLib.filename_from_uri(uri)
            self.emit('open-project', filename, None)

    @Gtk.Template.Callback('on_np_cancel_button_clicked')
    def _on_np_cancel_button_clicked(self, button):
        self._set_page('workspace' if self.project is not None else 'cambalache')

    def _is_project_visible(self):
        page = self.stack.get_visible_child_name()
        return self.project is not None and page == 'workspace'

    def _set_page(self, page):
        self.stack.set_visible_child_name(page)
        self._update_actions()

    def _update_action_undo_redo(self):
        if self._is_project_visible():
            history_index = self.project.history_index
            history_index_max = self.project.history_index_max
            self._actions['undo'].set_enabled(history_index > 0)
            self._actions['redo'].set_enabled(history_index < history_index_max)
        else:
            self._actions['undo'].set_enabled(False)
            self._actions['redo'].set_enabled(False)

    def _update_action_delete(self):
        if self._is_project_visible():
            sel = self.project.get_selection()
            self._actions['delete'].set_enabled(len(sel) > 0 if sel is not None else False)
        else:
            self._actions['delete'].set_enabled(False)

    def _on_project_changed(self, project):
        self._update_action_undo_redo()

    def _on_project_selection_changed(self, project):
        sel = project.get_selection()
        self._update_action_delete()
        obj = sel[0] if len(sel) > 0 and type(sel[0]) == CmbObject else None
        self.object_editor.object = obj
        self.object_layout_editor.object = obj
        self.signal_editor.object = obj

    def _update_actions(self):
        has_project = self._is_project_visible()

        for action in ['undo', 'redo',
                       'save', 'save_as',
                       'add_ui', 'delete',
                       'import', 'export',
                       'close', 'debug']:
            self._actions[action].set_enabled(has_project)

        self._update_action_delete()
        self._update_action_undo_redo()
        self._actions['debug'].set_enabled(has_project and self._sqlitebrowser is not None)

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

    def open_project(self, filename, target_tk=None):
        try:
            self.project = CmbProject(filename=filename, target_tk=target_tk)
            self._set_page('workspace')
            self._update_actions()
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f'Error loading {filename}'
            )
            print(traceback.format_exc())

            dialog.run()
            dialog.destroy()

    def _on_open_activate(self, action, data):
        dialog = self._file_open_dialog_new("Choose file to open",
                                            filter_obj=self.open_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            self.emit('open-project', dialog.get_filename(), None)

        dialog.destroy()

    def _on_create_new_activate(self, action, data):
        self._set_page('new_project')
        self.set_focus(self.np_name_entry)

        home = GLib.get_home_dir()
        projects = os.path.join(home, 'Projects')
        directory = projects if os.path.isdir(projects) else home

        self.np_location_chooser.set_current_folder(directory)

    def _on_new_activate(self, action, data):
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

        self.emit('open-project', filename, target_tk)

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

    def _on_delete_activate(self, action, data):
        if self.project is None:
            return

        selection = self.project.get_selection()
        for obj in selection:
            if type(obj) == CmbUI:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text=f"Do you want to delete selected UI?",
                )

                if dialog.run() == Gtk.ResponseType.YES:
                    self.project.remove_ui(obj)

                dialog.destroy()
            elif type(obj) == CmbObject:
                self.project.remove_object(obj)

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
        self._set_page('cambalache')

    def _on_sqlitebrowser_exit(self, pid, status, data):
        self._sqlitebrowser_pid = None

    def _on_debug_activate(self, action, data):
        if self._sqlitebrowser is None:
            return

        filename = self.project.filename + '.db'
        self.project.db_backup(filename)

        if self._sqlitebrowser_pid is not None:
            return

        pid, stdin, stdout, stderr = GLib.spawn_async([self._sqlitebrowser, filename],
                                                      flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD )
        self._sqlitebrowser_pid = pid
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid,
                             self._on_sqlitebrowser_exit, None)

    def _on_about_activate(self, action, data):
        self.about_dialog.present()

    def do_cmb_action(self, action):
        self._actions[action].activate()


Gtk.WidgetClass.set_css_name(CmbWindow, 'CmbWindow')
