#
# Cambalache controller registry
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
import sys
import inspect
from gi.repository import GObject

from .cmb_controller import CmbController


class CmbControllerRegistry(GObject.GObject):
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
            if inspect.isclass(klass) and issubclass(klass, CmbController):
                object_type = get_object_type(klass)
                self.registry[object_type] = klass

    def new_controller_for_object(self, obj):
        gtype = obj.__gtype__
        klass = None

        while gtype and klass is None:
            klass = self.registry.get(gtype, None)
            gtype = GObject.type_parent(gtype)

        return klass(object=obj)
