#
# CmbTypeChooser - Cambalache Type Chooser
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

from .cmb_type_info import CmbTypeInfo
from cambalache import getLogger

logger = getLogger(__name__)


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_type_chooser.ui')
class CmbTypeChooser(Gtk.Box):
    __gtype_name__ = 'CmbTypeChooser'

    __gsignals__ = {
        'type-selected': (GObject.SignalFlags.RUN_LAST, None, (str, )),
    }

    model = GObject.Property(type=Gtk.ListStore, flags = GObject.ParamFlags.READWRITE)

    entrycompletion = Gtk.Template.Child()
    scrolledwindow = Gtk.Template.Child()
    treeview = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self._search_text = ''
        self._filter = None

        super().__init__(**kwargs)

        self.connect('map', self._on_map)

    @GObject.Property(type=Gtk.ListStore)
    def model(self):
        return self.entrycompletion.props.model if self._filter else None

    @model.setter
    def _set_model(self, value):
        self._filter = Gtk.TreeModelFilter(child_model=value) if value else None
        if self._filter:
            self._filter.set_visible_func(self._visible_func)

        self.entrycompletion.props.model = value
        self.treeview.props.model = self._filter

    @Gtk.Template.Callback('on_searchentry_activate')
    def _on_searchentry_activate(self, entry):
        search_text = entry.props.text
        for row in self._filter:
            if row[0].lower() == search_text:
                self.emit('type-selected', search_text)
                return

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
        type_id = model[iter][0].lower()
        return type_id.find(self._search_text) >= 0

    def _on_map(self, widget):
        toplevel = widget.get_toplevel()

        if toplevel:
            height = toplevel.get_allocated_height() - 100;
            if height > 460:
                height = height * 0.7;

            self.scrolledwindow.set_max_content_height(height)
        return False


Gtk.WidgetClass.set_css_name(CmbTypeChooser, 'CmbTypeChooser')


class CmbTypeChooserPopover(Gtk.Popover):
    __gtype_name__ = 'CmbTypeChooserPopover'

    __gsignals__ = {
        'type-selected': (GObject.SignalFlags.RUN_LAST, None, (str, )),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.chooser = CmbTypeChooser()
        self.chooser.connect('type-selected', self._on_type_selected)
        self.chooser.show_all()
        self.add(self.chooser)

    def _on_type_selected(self, chooser, type):
        self.emit('type-selected', type)
        self.popdown()
