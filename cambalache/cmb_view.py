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

        super().__init__(**kwargs)

        self.buffer = Gtk.TextBuffer()
        text_view = Gtk.TextView(buffer=self.buffer, visible=True)
        self.add(text_view)

    def _update_view(self):
        if self._project is not None:
            ui = self._project.export_ui(1)
            self.buffer.set_text(ui.decode('unicode_escape'))
        else:
            self.buffer.set_text('')

    def _on_project_change(self, *args):
        self._update_view()

    @GObject.property(type=GObject.GObject)
    def project(self):
        return self._project

    @project.setter
    def _set_project(self, project):
        if self._project is not None:
            self._project.disconnect_by_func(self._on_project_change)

        self._project = project

        self._update_view()

        if project is not None:
            for table in ['ui', 'object']:
                table = table.replace('_', '-')
                for action in ['added', 'removed']:
                    self._project.connect( f'{table}-{action}', self._on_project_change)

