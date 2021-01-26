#
# CmbObjectTree - Cambalache Tree Store wrapper
#
# Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import sqlite3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk


class CmbObjectTree(Gtk.TreeStore):

    def __init__(self, project, columns):
        GObject.GObject.__init__(self)

        self._ui_id = {}
        self._object_id = {}

        self.set_column_types (columns)

        for table in ['ui', 'object']:
            for action in ['added', 'removed', 'updated']:
                project.connect(f'{table}-{action}', getattr(self, f'_on_{table}_{action}'))

    def _on_ui_added(self, project, *args):
        ui_id = args[0]
        self._ui_id[ui_id] = self.append(None, [ui_id, None, None, args[2],  None])

    def _on_ui_removed(self, project, *args):
        ui_id = args[0]
        iter_ = self._ui_id.pop(ui_id, None)
        if iter_ is not None:
            self.remove(iter_)

    def _on_ui_updated(self, project, *args):
        ui_id = args[0]

        iter_ = self._ui_id.get(ui_id, None)
        if iter_ is not None:
            self.set(iter_, list(range(0, leb(args))), *args)

    def _on_object_added(self, project, *args):
        ui_id = args[0]
        object_id = args[1]
        parent_id = args[4]

        if parent_id == 0:
            parent = self._ui_id.get(ui_id, None)
        else:
            parent = self._object_id.get(f'{ui_id}.{parent_id}', None)

        self._object_id[f'{ui_id}.{object_id}'] = self.append(parent, args)

    def _on_object_removed(self, project, *args):
        ui_id = args[0]
        object_id = args[1]

        iter_ = self._object_id.pop(f'{ui_id}.{object_id}', None)
        if iter_ is not None:
            self.remove(iter_)

    def _on_object_updated(self, project, *args):
        ui_id = args[0]
        object_id = args[1]

        iter_ = self._object_id.get(f'{ui_id}.{object_id}', None)
        if iter_ is not None:
            self.set(iter_, list(range(0, leb(args))), *args)

