#
# Merengue CSS provider
#
# Copyright (C) 2022  Juan Pablo Ugarte
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
import gi
from gi.repository import GObject, Gio, Gdk, Gtk

from merengue import getLogger

logger = getLogger(__name__)


class MrgCssProvider(Gtk.CssProvider):
    filename = GObject.Property(type=str, flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)
    priority = GObject.Property(type=int, flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)
    is_global = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)

    ui_id = GObject.Property(type=int, flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)
    provider_for = GObject.Property(type=object, flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT)

    def __init__(self, **kwargs):
        self.monitor = None
        super().__init__(**kwargs)

        self.connect('notify', self.__on_notify)
        self.__update()

    def __on_notify(self, obj, pspec):
        self.__update()

    def __on_css_file_changed(self, file_monitor, file, other_file, event_type):
        if event_type != Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            return

        try:
            self.load_from_path(self.filename)
        except:
            pass

    def __update(self):
        self.remove()

        if self.filename is None or not os.path.exists(self.filename):
            return

        if self.is_global or (self.provider_for and self.ui_id in self.provider_for):
            self.load()

        gfile = Gio.File.new_for_path(self.filename)
        self.monitor = gfile.monitor(Gio.FileMonitorFlags.NONE, None)
        self.monitor.connect('changed', self.__on_css_file_changed)

    def load(self):
        try:
            self.load_from_path(self.filename)
        except Exception as e:
            # TODO: return exception to main app to show the user
            pass

        if Gtk.MAJOR_VERSION == 4:
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                self,
                self.priority
            )
        elif Gtk.MAJOR_VERSION == 3:
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                self,
                self.priority
            )

    def remove(self):
        if Gtk.MAJOR_VERSION == 4:
            Gtk.StyleContext.remove_provider_for_display(
                Gdk.Display.get_default(),
                self
            )
        elif Gtk.MAJOR_VERSION == 3:
            Gtk.StyleContext.remove_provider_for_screen(
                Gdk.Screen.get_default(),
                self
            )

        if self.monitor:
            self.monitor.cancel()
            self.monitor = None

