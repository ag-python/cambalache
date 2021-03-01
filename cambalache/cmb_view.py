#
# CmbView - Cambalache View
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import io
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_project import CmbProject

class CmbView(Gtk.ScrolledWindow):
    __gtype_name__ = 'CmbView'

    def __init__(self, **kwargs):
        self._project = None
        self._ui_id = 0

        super().__init__(**kwargs)

        self.buffer = Gtk.TextBuffer()
        text_view = Gtk.TextView(buffer=self.buffer, visible=True)
        self.add(text_view)

    def _update_view(self):
        if self._project is not None and self._ui_id > 0:
            ui = self._project.export_ui(self._ui_id)
            self.buffer.set_text(ui.decode('unicode_escape'))
            return

        self.buffer.set_text('')

    def _on_project_selection_changed(self, project):
        selection = project.get_selection()

        if len(selection) > 0:
            ui_id = selection[0].ui_id

            if self._ui_id != ui_id:
                self._ui_id = ui_id
                self._update_view()
        elif self._ui_id > 0:
            self._ui_id = 0
            self._update_view()

    def _on_project_change(self, *args):
        self._update_view()

    @GObject.property(type=GObject.GObject)
    def project(self):
        return self._project

    @project.setter
    def _set_project(self, project):
        if self._project is not None:
            self._project.disconnect_by_func(self._on_project_change)
            self._project.disconnect_by_func(self._on_project_selection_changed)

        self._project = project

        self._update_view()

        if project is not None:
            self._project.connect('selection-changed', self._on_project_selection_changed)
            self._project.connect('object-property-changed', self._on_project_change)

            for table in ['ui', 'object']:
                table = table.replace('_', '-')
                for action in ['added', 'removed']:
                    self._project.connect( f'{table}-{action}', self._on_project_change)

