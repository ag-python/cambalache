# HdySearchBar Controller
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

from gi.repository import GObject, Gtk, Handy

from merengue import utils
from merengue.mrg_gtk import MrgGtkBin


class MrgHdySearchBar(MrgGtkBin):
    object = GObject.Property(type=Handy.SearchBar,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_children(self):
        if not self.object:
            return []

        revealer = self.object.get_child()
        if not issubclass(type(revealer), Gtk.Revealer):
            return []

        box = revealer.get_child()
        if not issubclass(type(box), Gtk.Box):
            return []

        for child in box.get_children():
            name = utils.object_get_builder_id(child)

            if name in ['start', 'end']:
                continue

            return [child]

        return []

    def show_child(self, child):
        if self.object:
            self.object.props.search_mode_enabled = True
