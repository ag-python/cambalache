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
        'type-selected': (GObject.SignalFlags.RUN_LAST, None, (CmbTypeInfo, )),
    }

    project = GObject.Property(type=CmbProject, flags = GObject.ParamFlags.READWRITE)
    category = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)
    uncategorized_only = GObject.Property(type=bool, flags = GObject.ParamFlags.READWRITE, default=False)
    show_categories = GObject.Property(type=bool, flags = GObject.ParamFlags.READWRITE, default=False)
    parent_type_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)
    derived_type_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)

    entrycompletion = Gtk.Template.Child()
    scrolledwindow = Gtk.Template.Child()
    treeview = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self._search_text = ''
        self._filter = None

        super().__init__(**kwargs)

        self.connect('notify::project', self.__on_project_notify)
        self.connect('map', self.__on_map)

    def __model_from_project(self, project):
        if project is None:
            return None

        categories = {
            'toplevel': _('Toplevel'),
            'layout': _('Layout'),
            'control': _('Control'),
            'display': _('Display'),
            'model': _('Model')
        }

        order = {
            'toplevel': 0,
            'layout': 1,
            'control': 2,
            'display': 3,
            'model': 4
        }

        # type_id, type_id.lower(), CmbTypeInfo, sensitive
        store = Gtk.ListStore(str, str, CmbTypeInfo, bool)
        infos = []

        for key in project.type_info:
            i = project.type_info[key]

            if not i.abstract and i.parent_id not in [None, 'interface', 'enum', 'flags'] and i.layout in [None, 'container']:
                infos.append(i)

        infos = sorted(infos, key=lambda i: (order.get(i.category, 99), i.type_id))
        show_categories = self.show_categories
        last_category = None

        for i in infos:
            # Append category
            if show_categories and last_category != i.category:
                last_category = i.category
                category = categories.get(i.category, _('Others'))
                store.append([f'<i>▾ {category}</i>', '', None, False])

            if self.parent_type_id != '':
                append = self.project._check_can_add(i.type_id, self.parent_type_id)
            else:
                append = i.category is None if self.uncategorized_only else \
                         (self.category != '' and i.category == self.category) or  self.category == ''

            if append and self.derived_type_id != '':
                append = i.is_a(self.derived_type_id)

            if append:
                store.append([i.type_id, i.type_id.lower(), i, True])

        return store

    def __on_project_notify(self, object, pspec):
        model = self.__model_from_project(self.project)
        self._filter = Gtk.TreeModelFilter(child_model=model) if model else None
        if self._filter:
            self._filter.set_visible_func(self.__visible_func)

        self.entrycompletion.props.model = model
        self.treeview.props.model = self._filter

    @Gtk.Template.Callback('on_searchentry_activate')
    def __on_searchentry_activate(self, entry):
        search_text = entry.props.text

        info = self.project.type_info.get(search_text, None)
        if info:
            self.emit('type-selected', info)

    @Gtk.Template.Callback('on_searchentry_search_changed')
    def __on_searchentry_search_changed(self, entry):
        self._search_text = entry.props.text.lower()
        self._filter.refilter()

    @Gtk.Template.Callback('on_treeview_row_activated')
    def __on_treeview_row_activated(self, treeview, path, column):
        model = treeview.props.model
        info = model[model.get_iter(path)][2]

        if info is not None:
            self.emit('type-selected', info)

    def __visible_func(self, model, iter, data):
        type_id, type_id_lower, info, sensitive = model[iter]

        # Always show categories if we are not searching
        if self._search_text == '' and info is None:
            return True

        return type_id_lower.find(self._search_text) >= 0

    def __on_map(self, widget):
        toplevel = widget.get_toplevel()

        if toplevel:
            height = toplevel.get_allocated_height() - 100;
            if height > 460:
                height = height * 0.7;

            self.scrolledwindow.set_max_content_height(height)
        return False


Gtk.WidgetClass.set_css_name(CmbTypeChooserWidget, 'CmbTypeChooserWidget')

