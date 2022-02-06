#
# CmbTypeChooserBar - Cambalache Type Chooser Bar
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


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_type_chooser.ui')
class CmbTypeChooser(Gtk.Box):
    __gtype_name__ = 'CmbTypeChooser'

    __gsignals__ = {
        'type-selected': (GObject.SignalFlags.RUN_LAST, None, (CmbTypeInfo, )),
        'chooser-popup': (GObject.SignalFlags.RUN_LAST, None, (GObject.Object, )),
        'chooser-popdown': (GObject.SignalFlags.RUN_LAST, None, (GObject.Object, ))
    }

    project = GObject.Property(type=CmbProject, flags = GObject.ParamFlags.READWRITE)
    selected_type = GObject.Property(type=CmbTypeInfo, flags = GObject.ParamFlags.READWRITE)

    type_label = Gtk.Template.Child()
    all = Gtk.Template.Child()
    toplevel = Gtk.Template.Child()
    layout = Gtk.Template.Child()
    control = Gtk.Template.Child()
    display = Gtk.Template.Child()
    model = Gtk.Template.Child()
    extra = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._choosers = [
            self.all,
            self.toplevel,
            self.layout,
            self.control,
            self.display,
            self.model,
            self.extra
        ]

        self.connect('notify::project', self.__on_project_notify)
        self.connect('notify::selected-type', self.__on_selected_type_notify)

        for chooser in self._choosers:
            chooser.connect('type-selected', lambda o, t: self.emit('type-selected', t))
            chooser.connect('notify::visible', self.__on_chooser_visible_notify)

    def __on_project_notify(self, object, pspec):
        project = self.project
        self.selected_type = None

        for chooser in self._choosers:
            chooser.project = project

    def __on_selected_type_notify(self, object, pspec):
        project_target = self.project.target_tk if self.project else ''
        self.type_label.props.label = self.selected_type.type_id if self.selected_type else project_target

    def __on_chooser_visible_notify(self, obj, pspec):
        if obj.props.visible:
            self.emit('chooser-popup', obj)
        else:
            self.emit('chooser-popdown', obj)
