#
# CmbTypeChooserWidget - Cambalache Type Chooser Widget
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

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_project import CmbProject
from .cmb_type_info import CmbTypeInfo


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_type_chooser_widget.ui')
class CmbTypeChooserWidget(Gtk.Box):
    __gtype_name__ = 'CmbTypeChooserWidget'

    __gsignals__ = {
        'type-selected': (GObject.SignalFlags.RUN_LAST, None, (str, )),
    }

    project = GObject.Property(type=CmbProject, flags = GObject.ParamFlags.READWRITE)
    category = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)

    entrycompletion = Gtk.Template.Child()
    scrolledwindow = Gtk.Template.Child()
    treeview = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self._search_text = ''
        self._filter = None

        super().__init__(**kwargs)

        self.connect('notify::project', self._on_project_notify)
        self.connect('map', self._on_map)

    def _model_from_project(self, project):
        if project is None:
            return None

        # type_id, type_id.lower(), CmbTypeInfo
        store = Gtk.ListStore(str, str, CmbTypeInfo)
        infos = []

        for key in project.type_info:
            i = project.type_info[key]

            if not i.abstract and i.parent_id not in [None, 'interface', 'enum', 'flags'] and i.layout in [None, 'container']:
                infos.append(i)

        infos = sorted(infos, key=lambda i: (i.category or '', i.type_id))

        for i in infos:
            store.append([i.type_id, i.type_id.lower(), i])

        return store

    def _on_project_notify(self, object, pspec):
        model = self._model_from_project(self.project)
        self._filter = Gtk.TreeModelFilter(child_model=model) if model else None
        if self._filter:
            self._filter.set_visible_func(self._visible_func)

        self.entrycompletion.props.model = model
        self.treeview.props.model = self._filter

    @Gtk.Template.Callback('on_searchentry_activate')
    def _on_searchentry_activate(self, entry):
        search_text = entry.props.text

        info = self.project.type_info.get(search_text, None)
        if info:
            self.emit('type-selected', info.type_id)

    @Gtk.Template.Callback('on_searchentry_search_changed')
    def _on_searchentry_search_changed(self, entry):
        self._search_text = entry.props.text.lower()
        self._filter.refilter()

    @Gtk.Template.Callback('on_treeview_row_activated')
    def _on_treeview_row_activated(self, treeview, path, column):
        model = treeview.props.model
        type_id = model[model.get_iter(path)][0]
        self.emit('type-selected', type_id)

    def _visible_func(self, model, iter, data):
        info = model[iter][2]

        if self.category and info.category != self.category:
            return False

        return info.type_id.find(self._search_text) >= 0

    def _on_map(self, widget):
        toplevel = widget.get_toplevel()

        if toplevel:
            height = toplevel.get_allocated_height() - 100;
            if height > 460:
                height = height * 0.7;

            self.scrolledwindow.set_max_content_height(height)
        return False


Gtk.WidgetClass.set_css_name(CmbTypeChooserWidget, 'CmbTypeChooserWidget')

