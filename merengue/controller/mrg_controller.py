#
# Cambalache controller object
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject


class MrgController(GObject.Object):
    object = GObject.Property(type=GObject.GObject,
                              flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        # Properties in this will will be ignored by set_object_property()
        self.property_ignore_list = set()

        super().__init__(**kwargs)

    # Object set property wrapper
    def set_object_property(self, name, value):
        if self.object and name not in self.property_ignore_list:
            self.object.set_property(name, value)

