#
# Cambalache controller registry
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
import sys
import inspect
from gi.repository import GObject

from .mrg_controller import MrgController


class MrgControllerRegistry(GObject.GObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Registered controllers
        self.registry = {}

    # Object set property wrapper
    def load_module(self, module):
        def get_object_type(klass):
            props = klass.list_properties()

            for pspec in props:
                if pspec.name == 'object':
                    return pspec.value_type

            return None

        for component in module.__dict__.items():
            name, klass = component
            if inspect.isclass(klass) and issubclass(klass, MrgController):
                object_type = get_object_type(klass)
                self.registry[object_type] = klass

    def new_controller_for_type(self, gtype, app):
        klass = None

        while gtype and klass is None:
            klass = self.registry.get(gtype, None)
            try:
                gtype = GObject.type_parent(gtype)
            except:
                gtype = None
                break

        return klass(app=app) if klass else MrgController(app=app)
