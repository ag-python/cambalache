# GtkExpander Controller
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

from .mrg_gtk_bin import MrgGtkBinController


class MrgGtkExpanderController(MrgGtkBinController):
    object = GObject.Property(type=Gtk.Expander,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

