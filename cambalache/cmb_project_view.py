#
# CmbProjectView - Cambalache Project View
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_objects import CmbUI, CmbObject


class CmbProjectView(Gtk.TreeView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_headers_visible (False)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Object(Type)', renderer)
        column.set_cell_data_func(renderer, self._name_cell_data_func, None)
        self.append_column(column)

    def _name_cell_data_func(self, column, cell, model, iter_, data):
        obj = model.get_value(iter_, 0)

        if type(obj) == CmbObject:
            cell.set_property('text', f'{obj.name}({obj.type_id})')
        elif type(obj) == CmbUI:
            cell.set_property('text', obj.filename)

