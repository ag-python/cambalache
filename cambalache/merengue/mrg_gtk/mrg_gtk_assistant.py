# GtkAssistant
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

from .mrg_gtk_window import MrgGtkWindow
from merengue import MrgPlaceholder, getLogger, utils

logger = getLogger(__name__)


class MrgGtkAssistant(MrgGtkWindow):
    object = GObject.Property(type=Gtk.Assistant,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect("notify::object", self.__on_object_changed)
        self.__ensure_placeholders()

    def __get_placeholder(self):
        for i in range(0, self.object.get_n_pages()):
            page = self.object.get_nth_page(i)
            if isinstance(page, MrgPlaceholder):
                return page
        return None

    def __ensure_placeholders(self):
        if self.object is None:
            return

        if self.object.get_n_pages() == 0:
            self.add(MrgPlaceholder(visible=True, controller=self))

    def __on_object_changed(self, obj, pspec):
        self.__ensure_placeholders()
        self.__update_page_status()

    def __update_page_status(self):
        if self.object is None:
            return

        self.object.show()
        n_pages = self.object.get_n_pages();

        for i in range(0, n_pages):
            page = self.object.get_nth_page(i)

            if page is None:
                continue;

            page.show()

            if i == 0:
                page_type = Gtk.AssistantPageType.INTRO
            elif i == n_pages - 1:
                page_type = Gtk.AssistantPageType.CONFIRM
            else:
                page_type = Gtk.AssistantPageType.CONTENT

            self.object.set_page_type(page, page_type)
            self.object.set_page_complete(page, True)

        self.object.update_buttons_state()

    def show_child(self, child):
        if self.object is None:
            return

        for i in range(0, self.object.get_n_pages()):
            if child == self.object.get_nth_page(i):
                self.object.set_current_page(i)
                break

    def add(self, child):
        if self.object is None:
            return

        self.object.append_page(child)
        self.__update_page_status()

    def remove_child(self, child):
        if self.object is None:
            return

        for i in range(0, self.object.get_n_pages()):
            if child == self.object.get_nth_page(i):
                self.object.remove_page(i)
                break

        self.__update_page_status()

    def add_placeholder(self, mod):
        placeholder = self.__get_placeholder()

        if placeholder is None:
            placeholder = MrgPlaceholder(visible=True, controller=self)
            self.add(placeholder)

        self.show_child(placeholder)

    def remove_placeholder(self, mod):
        placeholder = self.__get_placeholder()
        if placeholder:
            self.remove_child(placeholder)
