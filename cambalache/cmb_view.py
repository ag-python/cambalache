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

    project = GObject.Property(type=CmbProject)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.buffer = Gtk.TextBuffer()
        text_view = Gtk.TextView(buffer=self.buffer, visible=True)
        self.add(text_view)

        self.connect("notify::project", self._on_project_notify)

    def _on_project_change(self, *args):
        ui = self.project.export_ui(1)
        self.buffer.set_text(ui.decode('unicode_escape'))

    def _on_project_notify(self, obj, pspec):
        if self.project is None:
            return

        for table in ['ui', 'object']:
            table = table.replace('_', '-')
            for action in ['added', 'removed']:
                self.project.connect( f'{table}-{action}', self._on_project_change)

