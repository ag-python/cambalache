#
# CmbFragmentEditor - Cambalache CSS Editor
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

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gio, Gtk, GtkSource

from .cmb_css import CmbCSS
from .cmb_property_controls import *


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_fragment_editor.ui')
class CmbFragmentEditor(Gtk.Box):
    __gtype_name__ = 'CmbFragmentEditor'

    view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self._object = None
        self.__binding = None

        super().__init__(**kwargs)

    @GObject.Property(type=GObject.Object)
    def object(self):
        return self._object

    @object.setter
    def _set_object(self, obj):
        if obj == self._object:
            return

        if self.__binding:
            self.__binding.unbind()
            self.__binding = None

        self._object = obj

        if obj is None:
            return

        binding = GObject.Object.bind_property(obj, 'custom-fragment',
                                               self.view, 'text',
                                               GObject.BindingFlags.SYNC_CREATE |
                                               GObject.BindingFlags.BIDIRECTIONAL)
        self.__binding = binding

