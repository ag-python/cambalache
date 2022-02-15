# GtkListBox Controller
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
from gi.repository import GObject, Gdk, Gtk

from .mrg_gtk_box import MrgGtkBoxController
from merengue import MrgPlaceholder, utils


class MrgGtkListBoxController(MrgGtkBoxController):
    object = GObject.Property(type=Gtk.ListBox,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_children(self):
        children = super().get_children()
        retval = []

        if children is None:
            return None

        for child in children:
            id = utils.object_get_id(child)
            if id:
                retval.append(child)
            else:
                grandchild = child.props.child if Gtk.MAJOR_VERSION == 4 else child.get_child()
                id = utils.object_get_id(grandchild)
                if id or isinstance(grandchild, MrgPlaceholder):
                    retval.append(grandchild)

        return retval

    def get_child_layout(self, child, layout):
        # GtkListBox has not layout properties
        return layout

    def remove_child(self, child):
        if self.object is None:
            return

        if isinstance(child, Gtk.ListBoxRow):
            super().remove_child(child)
        else:
            super().remove_child(child.props.parent)
