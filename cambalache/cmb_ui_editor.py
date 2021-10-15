#
# CmbUIEditor - Cambalache UI Editor
#
# Copyright (C) 2021  Juan Pablo Ugarte
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation;
# version 2.1 of the License.
#
# library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors:
#   Juan Pablo Ugarte <juanpablougarte@gmail.com>
#

import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_ui import CmbUI
from .cmb_property_controls import *


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_ui_editor.ui')
class CmbUIEditor(Gtk.Grid):
    __gtype_name__ = 'CmbUIEditor'

    filename = Gtk.Template.Child()
    template_id = Gtk.Template.Child()
    description = Gtk.Template.Child()
    copyright = Gtk.Template.Child()
    authors = Gtk.Template.Child()
    translation_domain = Gtk.Template.Child()

    fields = [
        'filename',
        'template_id',
        'description',
        'copyright',
        'authors',
        'translation_domain'
    ]

    def __init__(self, **kwargs):
        self._object = None
        self._bindings = []

        super().__init__(**kwargs)

    @GObject.Property(type=CmbUI)
    def object(self):
        return self._object

    @object.setter
    def _set_object(self, obj):
        if obj == self._object:
            return

        for binding in self._bindings:
            binding.unbind()

        self._bindings = []

        self._object = obj

        if obj is None:
            self.set_sensitive(False)
            for field in self.fields:
                widget = getattr(self, field)

                if type(widget.cmb_value) == int:
                    widget.cmb_value = 0
                else:
                    widget.cmb_value = None
            return

        self.set_sensitive(True)
        self.template_id.object = obj

        for field in self.fields:
            binding = GObject.Object.bind_property(obj, field,
                                                   getattr(self, field), 'cmb-value',
                                                   GObject.BindingFlags.SYNC_CREATE |
                                                   GObject.BindingFlags.BIDIRECTIONAL)
            self._bindings.append(binding)

    @Gtk.Template.Callback('on_remove_button_clicked')
    def _on_remove_button_clicked(self, button):
        self.emit('remove-ui')

    @Gtk.Template.Callback('on_export_button_clicked')
    def _on_export_button_clicked(self, button):
        self.emit('export-ui')

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(),
                    accumulator=GObject.signal_accumulator_true_handled)
    def export_ui(self):
        if self.object:
            self.object.project.export_ui(self.object)

        return True

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST, return_type=bool,
                    arg_types=(),
                    accumulator=GObject.signal_accumulator_true_handled)
    def remove_ui(self):
        if self.object:
            self.object.project.remove_ui(self.object)

        return True
