#
# CmbObject - Cambalache Object wrapper
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject


class CmbBaseObject(GObject.GObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CmbUI(CmbBaseObject):
    ui_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    template_id = GObject.Property(type=int)

    name = GObject.Property(type=str)
    filename = GObject.Property(type=str)
    description = GObject.Property(type=str)
    copyright = GObject.Property(type=str)
    authors = GObject.Property(type=str)
    license_id = GObject.Property(type=str)
    translation_domain = GObject.Property(type=str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CmbProperty(CmbBaseObject):
    ui_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    object_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    owner_id = GObject.Property(type=int)
    property_id = GObject.Property(type=str)
    value = GObject.Property(type=str)
    translatable = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CmbSignal(CmbBaseObject):
    ui_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    object_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    owner_id = GObject.Property(type=int)
    signal_id = GObject.Property(type=str)

    handler = GObject.Property(type=str)
    detail = GObject.Property(type=str)
    user_data = GObject.Property(type=str)
    swap = GObject.Property(type=bool, default=False)
    after = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CmbObject(CmbBaseObject):
    ui_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    object_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    type_id = GObject.Property(type=str)
    name = GObject.Property(type=str)
    parent_id = GObject.Property(type=int)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.properties = {}
        self.layout_properties = {}
        self.signals = []
