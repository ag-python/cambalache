#
# CmbObjectDataEditor - Cambalache Object Data Editor
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

from gi.repository import GObject, Gtk, Gdk
import gi

gi.require_version('Gtk', '3.0')


class CmbObjectDataEditor(Gtk.Box):
    __gtype_name__ = 'CmbObjectDataEditor'

    def __init__(self, data):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self._list = Gtk.ListStore()
        self._types = []

        if data.type_id is not None:
            self._add_type(data.type_id)
        for arg_name in data.args:
            type = data.args[arg_name].type_id
            self._add_type(type)

        self._list.set_column_types(self._types)
        self._add_dummy_row()

        self._tree = Gtk.TreeView(model=self._list, margin_start=16)

        i = 0
        if data.type_id is not None:
            rendererValue = Gtk.CellRendererText()
            rendererValue.set_property('editable', True)
            #rendererValue.connect('edited', self._data_edited_value)
            columnValue = Gtk.TreeViewColumn(
                data.key, rendererValue, text=0, weight=1)
            columnValue.set_cell_data_func(
                rendererValue, self._custom_cell_data_func, func_data=i)
            columnValue.set_expand(True)
            self._tree.append_column(columnValue)

            i = i + 1

        for arg_name in data.args:
            rendererValue = Gtk.CellRendererText()
            rendererValue.set_property('editable', True)
            #rendererValue.connect('edited', self._data_edited_value)
            columnValue = Gtk.TreeViewColumn(
                arg_name, rendererValue, text=0, weight=1)
            columnValue.set_cell_data_func(
                rendererValue, self._custom_cell_data_func, func_data=i)
            columnValue.set_expand(True)
            self._tree.append_column(columnValue)

            i = i + 1

        self._tree.connect("key-release-event", self._on_treeview_keyrelease)

        self._tree.set_hexpand(True)
        self.add(self._tree)

    def _add_type(self, type):
        if type == 'gchararray':
            self._types.append(GObject.TYPE_STRING)
        elif type == 'gint':
            self._types.append(GObject.TYPE_INT)
        else:
            pass

    def _on_treeview_keyrelease(self, view, event):
        # escape key is captured globally, so we check for ctrl+d
        if event.keyval == Gdk.KEY_d and (event.state & Gdk.ModifierType.CONTROL_MASK):
            selected = self._tree.get_selection()
            model, iter = selected.get_selected()
            dummy = model.get_value(iter, Col.DUMMY.value)
            if not dummy:
                model.remove(iter)

    def _custom_cell_data_func(self, column, renderer, model, iter, data):
        text = model.get_value(iter, data)
        renderer.set_property('text', text)

    def _data_edited_value(self, renderer, path, text):
        pass

    def _add_dummy_row(self):
        dummy_values = []
        first_value = True
        for type in self._types:
            if first_value:
                if type == GObject.TYPE_STRING:
                    dummy_values.append('<type_here>')
                elif type == GObject.TYPE_INT:
                    dummy_values.append(0)
                first_value = False
            else:
                if type == GObject.TYPE_STRING:
                    dummy_values.append('')
                elif type == GObject.TYPE_INT:
                    dummy_values.append(0)

        self._list.append(dummy_values)
