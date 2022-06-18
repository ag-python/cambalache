#
# MrgPlaceholder
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

import gi

from gi.repository import GObject, Gdk, Gtk

from .mrg_controller import MrgController
from merengue import getLogger

logger = getLogger(__name__)


class MrgPlaceholder(Gtk.Box):
    __gtype_name__ = 'MrgPlaceholder'

    controller = GObject.Property(type=MrgController, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self.__binding = None

        super().__init__(**kwargs)

        self.props.can_focus = True
        self.props.hexpand = True
        self.props.vexpand = True
        self.set_size_request(32, 32)

        self.connect("notify::controller", self.__on_controller_notify)
        self.__update_preview_binding()

    def __on_controller_notify(self, obj, pspec):
        self.__update_preview_binding()

    def __update_preview_binding(self):
        if self.__binding:
            self.__binding.unbind()
            self.__binding = None

        if not self.controller:
            return

        self.__binding = GObject.Object.bind_property(self.controller.app, 'preview',
                                                      self, 'visible',
                                                      GObject.BindingFlags.SYNC_CREATE |
                                                      GObject.BindingFlags.BIDIRECTIONAL)

    def selected(self):
        if self.controller:
            self.controller.placeholder_selected(self)

    def activated(self):
        if self.controller:
            self.controller.placeholder_activated(self)

Gtk.WidgetClass.set_css_name(MrgPlaceholder, 'MrgPlaceholder')
