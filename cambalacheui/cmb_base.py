#
# Cambalache Object wrappers base class
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject


class CmbBase(GObject.GObject):
    project = GObject.Property(type=GObject.GObject, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def db_get(self, query, pk):
        c = self.project.db.execute(query, pk)
        row = c.fetchone()
        c.close()
        return row[0] if row is not None else None

    def db_set(self, query, pk, value):
        self.project.db.execute(query, (value, ) + pk)
