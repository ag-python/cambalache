#
# Cambalache UI Maker
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk, Gio

from cambalache import *

from .cmb_window import CmbWindow


class CmbApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.gnome.jpu.Cambalache',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window = None
        self.project = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        for action in ['open', 'new',
                       'undo', 'redo',
                       'save', 'save_as',
                       'add_ui', 'remove_ui',
                       'import', 'export',
                       'close', 'about', 'quit']:
            gaction= Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self.add_action(gaction)

    def do_activate(self):
        if not self.window:
            self.window = CmbWindow(application=self)

        self.window.present()

    def _file_open_dialog_new(self, title, action=Gtk.FileChooserAction.OPEN, filter_obj=None):
        dialog = Gtk.FileChooserDialog(
            title=title,
            parent=self.window,
            action=action,
            filter=filter_obj
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        return dialog

    def _on_open_activate(self, action, data):
        dialog = self._file_open_dialog_new("Choose file to open",
                                            filter_obj=self.window.open_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            self.window.project = CmbProject(filename=dialog.get_filename())

        dialog.destroy()

    def _on_new_activate(self, action, data):
        if self.window.project is None:
            self.window.project = CmbProject()

        self.window.stack.set_visible_child_name('workspace')

    def _on_undo_activate(self, action, data):
        print('_on_undo_activate')

    def _on_redo_activate(self, action, data):
        print('_on_redo_activate')

    def _on_save_activate(self, action, data):
        print('_on_save_activate')

    def _on_save_as_activate(self, action, data):
        print('_on_save_as_activate')

    def _on_add_ui_activate(self, action, data):
        dialog = self._file_open_dialog_new("Choose a file to save the project",
                                            Gtk.FileChooserAction.SAVE)
        if dialog.run() == Gtk.ResponseType.OK:
            self.window.project.add_ui(dialog.get_filename())

        dialog.destroy()

    def _on_remove_ui_activate(self, action, data):
        print('_on_remove_ui_activate')

    def _on_import_activate(self, action, data):
        if self.window.project is None:
            return

        dialog = self._file_open_dialog_new("Choose file to import",
                                            filter_obj=self.window.import_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            self.window.project.import_file(dialog.get_filename())

        dialog.destroy()

    def _on_export_activate(self, action, data):
        if self.window.project is not None:
            self.window.project.export()

    def _on_close_activate(self, action, data):
        self.window.project = None
        self.window.stack.set_visible_child_name('cambalache')

    def _on_about_activate(self, action, data):
        self.window.about_dialog.present()

    def _on_quit_activate(self, action, data):
        self.quit()


if __name__ == "__main__":
    app = CmbApplication()
    app.run(sys.argv)
