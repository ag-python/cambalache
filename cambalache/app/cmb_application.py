#
# Cambalache Application
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

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gdk, Gtk, Gio

from cambalache import *

from .cmb_window import CmbWindow

basedir = os.path.dirname(__file__) or '.'


class CmbApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='ar.xjuan.Cambalache',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

        self.add_main_option('version', b'v',
                             GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE,
                             _("Print version"),
                             None)

        self.add_main_option('export-all', b'E',
                             GLib.OptionFlags.NONE,
                             GLib.OptionArg.FILENAME,
                             _("Export project"),
                             None)

    def __add_window(self):
        window = CmbWindow(application=self)
        window.connect('open-project', self.__on_open_project)
        window.connect('delete-event', self.__on_window_delete_event)
        self.add_window(window)
        return window

    def open(self, path, target_tk=None, uiname=None):
        window = None

        for win in self.get_windows():
            if win.project is not None and win.project.filename == path:
                window = win

        if window is None:
            window = self.__add_window()
            if path is not None:
                window.open_project(path, target_tk=target_tk, uiname=uiname)

        window.present()

    def import_file(self, path):
        window = self.__add_window() if self.props.active_window is None else self.props.active_window
        window.import_file(path)
        window.present()

    def do_open(self, files, nfiles, hint):
        for file in files:
            path = file.get_path()

            content_type, uncertain = Gio.content_type_guess(path, None)
            if uncertain:
                with open(path, 'rb') as fd:
                    data = fd.read(1024)
                content_type, uncertain = Gio.content_type_guess(path, data)

            if content_type == 'application/x-cambalache-project':
                self.open(path)
            elif content_type in ['application/x-gtk-builder', 'application/x-glade']:
                self.import_file(path)

    def do_startup(self):
        Gtk.Application.do_startup(self)

        for action in ['quit']:
            gaction= Gio.SimpleAction.new(action, None)
            gaction.connect("activate", getattr(self, f'_on_{action}_activate'))
            self.add_action(gaction)

        provider = Gtk.CssProvider()
        provider.load_from_resource('/ar/xjuan/Cambalache/app/cambalache.css')
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_activate(self):
        if self.props.active_window is None:
            self.open(None)

    def __on_open_project(self, window, filename, target_tk, uiname):
        if window.project is None:
            window.open_project(filename, target_tk, uiname)
        else:
            self.open(filename, target_tk, uiname)

    def __check_can_quit(self, windows):
        unsaved_windows = []
        projects2save = []

        # Gather projects that needs saving
        for win in windows:
            if win.project is None:
                continue

            if win.actions['save'].get_enabled():
                unsaved_windows.append(win)

        unsaved_windows_len = len(unsaved_windows)
        if unsaved_windows_len == 0:
            return True

        # Create Dialog
        text = _('Save changes before closing?')
        dialog = Gtk.MessageDialog(
            transient_for=windows[0],
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            text=f'<b><big>{text}</big></b>',
            use_markup=True
        )

        # Add buttons
        dialog.add_buttons(_('Close without Saving'), Gtk.ResponseType.CLOSE,
                           _('Cancel'), Gtk.ResponseType.CANCEL,
                           _('Save'), Gtk.ResponseType.ACCEPT)

        dialog.set_default_response(Gtk.ResponseType.ACCEPT)

        if unsaved_windows_len > 1:
            # Add checkbox for each unsaved project
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.add(Gtk.Label(label=_('Select which files:'),
                              halign=Gtk.Align.START))

            for win in unsaved_windows:
                path = win.project.filename.replace(GLib.get_home_dir(), '~')
                check = Gtk.CheckButton(label=path,
                                        active=True,
                                        margin_start=8,
                                        can_focus=False)
                projects2save.append((win.project, check))
                box.add(check)

            box.show_all()
            dialog.props.message_area.add(box)

        # Run Dialog
        response = dialog.run()
        dialog.destroy()

        # Handle response
        if response == Gtk.ResponseType.ACCEPT:
            if unsaved_windows_len > 1:
                for project, check in projects2save:
                    if check is None or check.props.active:
                        project.save()
            elif unsaved_windows_len:
                unsaved_windows[0].project.save()
        elif response == Gtk.ResponseType.CANCEL:
            return False

        return True

    def __get_windows(self):
        retval = []

        for win in self.get_windows():
            if win.props.application is not None:
                retval.append(win)

        return retval

    def __on_window_delete_event(self, window, event):
        return not self.__check_can_quit([window])

    def do_window_removed(self, window):
        windows = self.__get_windows()

        if len(windows) == 0:
            self.activate_action('quit')

    def _on_quit_activate(self, action, data):
        if self.__check_can_quit(self.__get_windows()):
            self.quit()

    def do_handle_local_options(self, options):
        if options.contains('version'):
            print(VERSION)
            return 0

        if options.contains('export-all'):
            filename = options.lookup_value('export-all')
            filename = ''.join([ chr(c) for c in filename.unpack()])
            project = CmbProject(filename=filename)
            project.export()
            return 0

        return -1

if __name__ == '__main__':
    app = CmbApplication()
    app.run(sys.argv)
