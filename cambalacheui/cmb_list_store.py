#
# CmbListStore - Cambalache List Store
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import io
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk


class CmbListStore(Gtk.ListStore):
    __gtype_name__ = 'CmbListStore'

    table = GObject.Property(type=str)
    query = GObject.Property(type=str)
    project = GObject.Property(type=GObject.GObject)

    def __init__(self, **kwargs):
        GObject.GObject.__init__(self, **kwargs)

        data = self.project._get_table_data(self.table)
        self.set_column_types(data['types'])
        self._populate()

    def _populate(self):
        c = self.project.db.cursor()
        for row in c.execute(self.query):
            self.append(row)

        c.close()
