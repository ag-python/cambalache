# GBinding Workspace proxy
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
from gi.repository import GObject


#
# PROBLEM: GBinding calls g_assert() in its constructor to check all construct properties
# are set correctly if not, it terminates the current process.
#
# WORKAROUND: only create the GBinding once we have all the properties
#
class MrgGBindingProxy(GObject.Object):
    __gtype_name__ = 'MrgGBindingProxy'

    flags = GObject.Property(type=GObject.BindingFlags, default=GObject.BindingFlags.DEFAULT, flags = GObject.ParamFlags.READWRITE)
    source = GObject.Property(type=GObject.Object, flags = GObject.ParamFlags.READWRITE)
    source_property = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)
    target = GObject.Property(type=GObject.Object, flags = GObject.ParamFlags.READWRITE)
    target_property = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self.__proxy = None

        super().__init__(**kwargs)

        self.connect('notify', self.__on_notify)

    def __on_notify(self, obj, pspec):
        if self.__proxy:
            self.__proxy.unbind()
            self.__proxy = None

        if self.flags and \
           self.source and self.source_property and \
           self.target and self.target_property and \
           self.source.find_property(self.source_property) and \
           self.target.find_property(self.target_property):
            self.__proxy = self.source.bind_property(self.source_property,
                                                     self.target,
                                                     self.target_property,
                                                     self.flags)
            
