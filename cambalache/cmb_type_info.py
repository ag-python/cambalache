#
# Cambalache Type Info wrapper
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_objects_base import CmbBaseTypeInfo


class CmbTypeInfo(CmbBaseTypeInfo):
    def __init__(self, **kwargs):
        self.hierarchy = []
        self.signals = []
        super().__init__(**kwargs)

        if self.parent_id == 'enum':
            self.enum = self._init_enum_flags('enum')
        elif self.parent_id == 'flags':
            self.flags = self._init_enum_flags('flags')

    def _init_enum_flags(self, name):
        retval = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_INT)

        for row in self.project.conn.execute(f'SELECT name, nick, value FROM type_{name} WHERE type_id=?', (self.type_id,)):
            retval.append(row)

        return retval

