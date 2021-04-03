#
# CmbTreeView - Cambalache Tree View
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_objects import CmbUI, CmbObject


class CmbTreeView(Gtk.TreeView):
    __gtype_name__ = 'CmbTreeView'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._project = None
        self._selection = self.get_selection()
        self._selection.connect('changed', self._on_selection_changed)
        self.set_headers_visible (False)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Object(Type)', renderer)
        column.set_cell_data_func(renderer, self._name_cell_data_func, None)
        self.append_column(column)

        self.connect('notify::model', self._on_model_notify)
        self.connect('row-activated', self._on_row_activated)

    def _name_cell_data_func(self, column, cell, model, iter_, data):
        obj = model.get_value(iter_, 0)

        if type(obj) == CmbObject:
            name = obj.name or ''
            cell.set_property('text', f'{name}({obj.type_id})')
        elif type(obj) == CmbUI:
            cell.set_property('text', obj.filename)

    def _on_model_notify(self, treeview, pspec):
        if self._project is not None:
            self._project.disconnect_by_func(self._on_project_selection_changed)

        self._project = self.props.model

        if self._project:
            self._project.connect('selection-changed', self._on_project_selection_changed)

    def _on_row_activated(self, view, path, column):
        if self.row_expanded(path):
            self.collapse_row(path)
        else:
            self.expand_row(path, True)

    def _on_project_selection_changed(self, p):
        project, _iter = self._selection.get_selected()
        current = [project.get_value(_iter, 0)] if _iter is not None else []
        selection = project.get_selection()

        if selection == current:
            return

        if len(selection) > 0:
            _iter = project.get_iter_from_object(selection[0])
            path = project.get_path(_iter)
            self.expand_to_path(path)
            self._selection.select_iter(_iter)
        else:
            self._selection.unselect_all()

    def _on_selection_changed(self, selection):
        project, _iter = selection.get_selected()


        if _iter is not None:
            obj = project.get_value(_iter, 0)
            project.set_selection([obj])
