# GtkPopover Controller
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

import gi
from gi.repository import GObject, Gtk

from .mrg_selection import MrgSelection
from .mrg_gtk_widget import MrgGtkWidget


class MrgGtkPopover(MrgGtkWidget):
    object = GObject.Property(type=Gtk.Popover,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self.window = None
        self.__object = None
        self.__button = None

        super().__init__(**kwargs)

        if Gtk.MAJOR_VERSION == 4:
            self.property_ignore_list.add('autohide')
        else:
            self.property_ignore_list.add('modal')
            self.property_ignore_list.add('relative_to')

    def __ensure_popup(self):
        if self.object is None:
            return

        self.__button.set_popover(self.object)

        if Gtk.MAJOR_VERSION == 3:
            self.object.set_modal(False)
        else:
            self.object.set_autohide(False)

    def popup(self):
        if self.__button is None:
            return

        if Gtk.MAJOR_VERSION == 3:
            self.__button.set_active(True)
        else:
            self.__button.popup()

    def on_object_changed(self):
        # Clear old popover
        if self.__object:
            self.__button.set_popover(None)

        # Keep a reference to object
        self.__object = self.object
        self.selection = None

        if self.object is None:
            if self.window:
                self.window.destroy()
                self.window = None
            return

        if self.window is None:
            self.__button = Gtk.MenuButton(visible=True,
                                           halign=Gtk.Align.CENTER,
                                           valign=Gtk.Align.CENTER,
                                           receives_default=False)

            self.window = Gtk.Window(title='Popover Preview Window',
                                     deletable=False,
                                     width_request=320,
                                     height_request=240)

            self.window.set_default_size(640, 480)

            if Gtk.MAJOR_VERSION == 4:
                self.__button.set_icon_name('open-menu-symbolic')
                self.window.set_child(self.__button)
            else:
                image = Gtk.Image(visible=True,
                                  icon_name='open-menu-symbolic')
                self.__button.add(image)
                self.window.add(self.__button)

        self.selection = MrgSelection(app=self.app, container=self.object)

        self.__ensure_popup()
        self.object.popup()

        if Gtk.MAJOR_VERSION == 4:
            self.object.show()
            self.window.show()
        else:
            self.object.show_all()
            self.window.show_all()

    def on_selected_changed(self):
        super().on_selected_changed()

        if self.object:
            self.object.popup()

    def show_child(self, child):
        if self.object:
            self.object.popup()
