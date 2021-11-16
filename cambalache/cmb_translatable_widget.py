#
# CmbTranslatableWidget - Cambalache Translatable Widget
#
# Copyright (C) 2021  Philipp Unger
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
#   Philipp Unger <philipp.unger.1988@gmail.com>
#

import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_translatable_widget.ui')
class CmbTranslatableWidget(Gtk.Box):
    __gtype_name__ = 'CmbTranslatableWidget'

    text_view_value = Gtk.Template.Child()
    check_button_translatable = Gtk.Template.Child()
    text_view_context = Gtk.Template.Child()
    text_view_comments = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self._object = None
        super().__init__(**kwargs)

        self.text_view_value.get_buffer().connect('notify::text', self._on_text_notify)
        self.check_button_translatable.connect('toggled', self._on_translatable_notify)
        self.text_view_context.get_buffer().connect('notify::text', self._on_context_notify)
        self.text_view_comments.get_buffer().connect('notify::text', self._on_comments_notify)

    def _on_text_notify(self, obj, pspec):
        self.notify('cmb-value')

    def _on_translatable_notify(self, data):
        self.notify('cmb-translatable')

    def _on_context_notify(self, obj, pspec):
        self.notify('cmb-context')

    def _on_comments_notify(self, obj, pspec):
        self.notify('cmb-comment')

    def bind_properties(self, target):
        for source_prop, target_prop in [('value', 'cmb-value'),
                                         ('translatable', 'cmb-translatable'),
                                         ('translation_context', 'cmb-context'),
                                         ('translation_comments', 'cmb-comment')]:
            GObject.Object.bind_property(target, source_prop,
                                     self, target_prop,
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)

    @GObject.Property(type=str)
    def cmb_value(self):
        return self.text_view_value.get_buffer().props.text if self.text_view_value.get_buffer().props.text != '' else None

    @cmb_value.setter
    def _set_cmb_value(self, value):
        self.text_view_value.get_buffer().props.text = value if value is not None else ''

    @GObject.Property(type=bool, default = False)
    def cmb_translatable(self):
        return self.check_button_translatable.props.active

    @cmb_translatable.setter
    def _set_cmb_translatable(self, value):
        self.check_button_translatable.props.active = value

    @GObject.Property(type=str)
    def cmb_context(self):
        return self.text_view_context.get_buffer().props.text if self.text_view_context.get_buffer().props.text != '' else None

    @cmb_context.setter
    def _set_cmb_context(self, value):
        self.text_view_context.get_buffer().props.text = value if value is not None else ''

    @GObject.Property(type=str)
    def cmb_comment(self):
        return self.text_view_comments.get_buffer().props.text if self.text_view_comments.get_buffer().props.text != '' else None

    @cmb_comment.setter
    def _set_cmb_comment(self, value):
        self.text_view_comments.get_buffer().props.text = value if value is not None else ''
