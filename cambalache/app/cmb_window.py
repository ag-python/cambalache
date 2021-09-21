#
# CmbWindow
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

import os
import sys
import gi
import traceback

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gio, Gdk, Gtk

from locale import gettext as _
from cambalache import *
from .cmb_tutor import CmbTutor, CmbTutorState
from . import cmb_tutorial


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/app/cmb_window.ui')
class CmbWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'CmbWindow'

    __gsignals__ = {
        'open-project': (GObject.SIGNAL_RUN_FIRST, None, (str, str, str)),
        'cmb-action': (GObject.SIGNAL_RUN_LAST | GObject.SIGNAL_ACTION, None, (str, )),
    }

    open_filter = Gtk.Template.Child()
    import_filter = Gtk.Template.Child()

    open_button_box = Gtk.Template.Child()
    import_button_box = Gtk.Template.Child()

    headerbar = Gtk.Template.Child()
    undo_button = Gtk.Template.Child()
    redo_button = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    # Start screen
    version_label = Gtk.Template.Child()

    # New Project
    np_name_entry = Gtk.Template.Child()
    np_ui_entry = Gtk.Template.Child()
    np_location_chooser = Gtk.Template.Child()
    np_gtk3_radiobutton = Gtk.Template.Child()
    np_gtk4_radiobutton = Gtk.Template.Child()

    # Workspace
    view = Gtk.Template.Child()
    tree_view = Gtk.Template.Child()
    type_entry = Gtk.Template.Child()
    type_entrycompletion = Gtk.Template.Child()
    theme_combobox = Gtk.Template.Child()
    object_editor = Gtk.Template.Child()
    object_layout_editor = Gtk.Template.Child()
    signal_editor = Gtk.Template.Child()

    about_dialog = Gtk.Template.Child()

    # Tutor widgets
    intro_button = Gtk.Template.Child()
    open_button = Gtk.Template.Child()
    recent_button = Gtk.Template.Child()
    new_button = Gtk.Template.Child()
    add_button = Gtk.Template.Child()
    save_button = Gtk.Template.Child()
    save_as_button = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    main_menu = Gtk.Template.Child()
    export_all = Gtk.Template.Child()
    donate = Gtk.Template.Child()

    # Settings
    completed_intro = GObject.Property(type=bool, default=False, flags = GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self._project = None

        super().__init__(**kwargs)

        self._actions = {}
        self.open_button_box.props.homogeneous = False
        self.import_button_box.props.homogeneous = False

        for action in ['open', 'create_new', 'new',
                       'undo', 'redo', 'intro',
                       'save', 'save_as',
                       'add_ui', 'delete',
                       'import', 'export',
                       'close', 'debug', 'donate', 'about']:
            gaction = Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self._actions[action] = gaction
            self.add_action(gaction)

        self._opensqlite = GLib.find_program_in_path('sqlitebrowser')
        self._opensqlite_pid = None

        # Fallback to xdg-open
        if self._opensqlite is None:
            self._opensqlite = GLib.find_program_in_path('xdg-open')

        self.version_label.props.label = f"version {config.VERSION}"
        self.about_dialog.props.version = config.VERSION

        self._populate_about_dialog_sponsors()

        GObject.Object.bind_property(self.np_name_entry, 'text',
                                     self.np_ui_entry, 'placeholder-text',
                                     GObject.BindingFlags.SYNC_CREATE,
                                     self._np_name_to_ui,
                                     None)

        GObject.Object.bind_property(self.theme_combobox, 'active-id',
                                     self.view, 'gtk-theme',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)
        self.tutor = None
        self.turor_waiting_for_user_action = False

        # Create settings object
        self.settings = Gio.Settings(schema_id='ar.xjuan.Cambalache')

        # Settings list
        settings = [
            'completed-intro',
        ]

        # Bind settings
        for prop in settings:
            self.settings.bind(prop, self, prop.replace('-', '_'), Gio.SettingsBindFlags.DEFAULT)

        self._update_actions()

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

            # Populate gtk theme combo
            if self._project.target_tk == 'gtk+-3.0':
                self._populate_theme_combobox('3.0')
            elif self._project.target_tk == 'gtk-4.0':
                self._populate_theme_combobox('4.0')
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
            self.emit('open-project', filename, None, None)

    @Gtk.Template.Callback('on_np_cancel_button_clicked')
    def _on_np_cancel_button_clicked(self, button):
        self._set_page('workspace' if self.project is not None else 'cambalache')

    def _np_name_to_ui(self, binding, value):
        if len(value):
            return value.lower().rsplit('.', 1)[0] + '.ui'
        else:
            return _('<Choose a UI filename to create>')

    def _is_project_visible(self):
        page = self.stack.get_visible_child_name()
        return self.project is not None and page == 'workspace'

    def _set_page(self, page):
        self.stack.set_visible_child_name(page)
        self._update_actions()

    def _update_action_undo_redo(self):
        if self._is_project_visible():
            undo_msg, redo_msg = self.project.get_undo_redo_msg()
            self.undo_button.set_tooltip_text(f'Undo: {undo_msg}' if undo_msg is not None else None)
            self.redo_button.set_tooltip_text(f'Redo: {redo_msg}' if redo_msg is not None else None)

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

    def _update_action_intro(self):
        enabled = False

        if not self.completed_intro:
            enabled = True
            self.intro_button.props.tooltip_text = _('Start interactive introduction')

        self.intro_button.set_visible(enabled)

    def _update_actions(self):
        has_project = self._is_project_visible()

        for action in ['undo', 'redo',
                       'save', 'save_as',
                       'add_ui', 'delete',
                       'import', 'export',
                       'close', 'debug']:
            self._actions[action].set_enabled(has_project)

        self._update_action_intro()
        self._update_action_delete()
        self._update_action_undo_redo()
        self._actions['debug'].set_enabled(has_project and self._opensqlite is not None)

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

    def _populate_about_dialog_sponsors(self):
        gbytes = Gio.resources_lookup_data('/ar/xjuan/Cambalache/app/SUPPORTERS.md',
                                           Gio.ResourceLookupFlags.NONE)
        supporters = gbytes.get_data().decode('UTF-8').splitlines()
        sponsors = []

        for name in supporters:
            if name.startswith('* '):
                sponsors.append(name[2:])

        self.about_dialog.add_credit_section(_('Sponsors'), sponsors)

    def _populate_theme_combobox(self, version):
        self.theme_combobox.remove_all()

        dirs = []

        dirs += GLib.get_system_data_dirs()
        dirs.append(GLib.get_user_data_dir())

        # Add /themes to every dir
        dirs = list(map(lambda d: os.path.join(d, 'themes'), dirs))

        # Append ~/.themes
        dirs.append(os.path.join(GLib.get_home_dir(), '.themes'))

        # Default themes
        themes = ['Adwaita', 'HighContrast', 'HighContrastInverse']

        for path in dirs:
            if not os.path.isdir(path):
                continue

            for theme in os.listdir(path):
                tpath = os.path.join(path, theme, f'gtk-{version}', 'gtk.css')
                if os.path.exists(tpath):
                    themes.append(theme)

        # Dedup and sort
        themes = list(dict.fromkeys(themes))

        for theme in sorted(themes):
            self.theme_combobox.append(theme, theme)

    def present_message_to_user(self, message, secondary_text=None):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
            secondary_text=secondary_text
        )
        dialog.run()
        dialog.destroy()

    def open_project(self, filename, target_tk=None, uiname=None):
        try:
            self.project = CmbProject(filename=filename, target_tk=target_tk)

            if uiname:
                ui = self.project.add_ui(uiname)
                self.project.set_selection([ui])

            self._set_page('workspace')
            self._update_actions()
        except Exception as e:
            print(traceback.format_exc())
            self.present_message_to_user(_(f'Error loading {filename}'))

    def _on_open_activate(self, action, data):
        dialog = self._file_open_dialog_new(_("Choose project to open"),
                                            filter_obj=self.open_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            self.emit('open-project', dialog.get_filename(), None, None)

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
        uiname = self.np_ui_entry.props.text

        if len(name) < 1:
            self.set_focus(self.np_name_entry)
            return

        if self.np_gtk3_radiobutton.get_active():
            target_tk='gtk+-3.0'
        elif self.np_gtk4_radiobutton.get_active():
            target_tk='gtk-4.0'

        name, ext = os.path.splitext(name)
        filename = os.path.join(location, name + '.cmb')

        if len(uiname) == 0:
            uiname = self.np_ui_entry.props.placeholder_text

        if os.path.exists(filename):
            self.present_message_to_user(_("File name already exists, choose a different name."))
            self.set_focus(self.np_name_entry)
            return

        self.emit('open-project', filename, target_tk, os.path.join(location, uiname))
        self._set_page('workspace' if self.project is not None else 'cambalache')

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

        dialog = self._file_open_dialog_new(_("Choose a new file to save the project"),
                                            Gtk.FileChooserAction.SAVE)
        if dialog.run() == Gtk.ResponseType.OK:
            self.project.filename = dialog.get_filename()
            self.project.save()

        dialog.destroy()

    def _on_add_ui_activate(self, action, data):
        if self.project is None:
            return

        dialog = self._file_open_dialog_new(_("Choose a file name for the new UI"),
                                            Gtk.FileChooserAction.SAVE)
        if dialog.run() == Gtk.ResponseType.OK:
            ui = self.project.add_ui(dialog.get_filename())
            self.project.set_selection([ui])

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
                    text=_(f"Do you want to delete selected UI?"),
                )

                if dialog.run() == Gtk.ResponseType.YES:
                    self.project.remove_ui(obj)

                dialog.destroy()
            elif type(obj) == CmbObject:
                self.project.remove_object(obj)

    def _on_import_activate(self, action, data):
        if self.project is None:
            return

        dialog = self._file_open_dialog_new(_("Choose file to import"),
                                            filter_obj=self.import_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            try:
                self.project.import_file(filename)
            except Exception as e:
                filename = os.path.basename(filename)
                self.present_message_to_user(_(f"Error importing {filename}"),
                                             secondary_text=str(e))
        else:
            dialog.destroy()

    def _on_export_activate(self, action, data):
        if self.project is not None:
            self.project.export()

    def _on_close_activate(self, action, data):
        self.project = None
        self._set_page('cambalache')

    def _on_opensqlite_exit(self, pid, status, data):
        self._opensqlite_pid = None

    def _on_debug_activate(self, action, data):
        if self._opensqlite is None:
            return

        filename = self.project.filename + '.db'
        self.project.db_backup(filename)

        if self._opensqlite_pid is not None:
            return

        pid, stdin, stdout, stderr = GLib.spawn_async([self._opensqlite, filename],
                                                      flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD )
        self._opensqlite_pid = pid
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid,
                             self._on_opensqlite_exit, None)

    def _on_about_activate(self, action, data):
        self.about_dialog.present()

    def _on_donate_activate(self, action, data):
        Gtk.show_uri_on_window(self, "https://www.patreon.com/cambalache", Gdk.CURRENT_TIME)

    def do_cmb_action(self, action):
        self._actions[action].activate()

    def _clear_tutor(self):
        try:
            self.disconnect_by_func(self._on_project_notify)
            self.project.disconnect_by_func(self._on_ui_added)
            self.project.disconnect_by_func(self._on_object_added)
        except:
            pass
        self.tutor = None

    def _on_project_notify(self, obj, pspec):
        if self.project:
            self.turor_waiting_for_user_action = False
            self.tutor.play()
            self.disconnect_by_func(self._on_project_notify)

    def _on_object_added(self, project, obj):
        if obj.type_id == 'GtkWindow':
            project.disconnect_by_func(self._on_object_added)
            self.turor_waiting_for_user_action = False
            self.tutor.play()

    def _on_ui_added(self, project, ui):
        self.turor_waiting_for_user_action = False
        project.disconnect_by_func(self._on_ui_added)
        self.tutor.play()

    def _on_tutor_show_node(self, tutor, node, widget):
        if node == 'add-project':
            if self.project is None:
                self.connect('notify::project', self._on_project_notify)
        elif node == 'add-ui':
            self.project.connect('ui-added', self._on_ui_added)
        elif node == 'add-window':
            self.project.connect('object-added', self._on_object_added)
        elif node == 'main-menu':
            self.main_menu.props.modal = False

    def _on_tutor_hide_node(self, tutor, node, widget):
        if node == 'intro-end':
            self.completed_intro = True
            self._clear_tutor()
        elif node == 'add-project':
            if self._project is None:
                self.turor_waiting_for_user_action = True
                self.tutor.pause()
        elif node == 'add-ui' or node == 'add-window':
            self.turor_waiting_for_user_action = True
            self.tutor.pause()
        elif node == 'main-menu':
            self.export_all.get_style_context().remove_class("cmb-tutor-highlight")
        elif node == 'donate':
            self.main_menu.props.modal = True
            self.main_menu.popdown()

        self._update_actions()

    def _on_intro_activate(self, action, data):
        if self.turor_waiting_for_user_action:
            return

        if self.tutor:
            if self.tutor.state == CmbTutorState.PLAYING:
                self.tutor.pause()
            else:
                self.tutor.play()
            return

        # Ensure button is visible and reset config flag since we are playing
        # the tutorial from start
        self.intro_button.set_visible(True)
        self.completed_intro = False

        self.tutor = CmbTutor(script=cmb_tutorial.intro, window=self)
        self.tutor.connect('show-node', self._on_tutor_show_node)
        self.tutor.connect('hide-node', self._on_tutor_hide_node)
        self.tutor.play()


Gtk.WidgetClass.set_css_name(CmbWindow, 'CmbWindow')
