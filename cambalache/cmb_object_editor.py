#
# CmbObjectEditor - Cambalache Object Editor
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
import math

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gtk

from .cmb_object import CmbObject
from .cmb_property_controls import *


class CmbObjectEditor(Gtk.Box):
    __gtype_name__ = 'CmbObjectEditor'

    layout = GObject.Property(type=bool,
                              flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY,
                              default=False)

    def __init__(self, **kwargs):
        self.__object = None
        self.__id_label = None
        self.__labels = {}

        super().__init__(**kwargs)

        self.props.orientation = Gtk.Orientation.VERTICAL

    def __create_id_editor(self):
        grid = Gtk.Grid(hexpand=True,
                        row_spacing=4,
                        column_spacing=4)

        # Label
        self.__id_label = Gtk.Label(label=_('Object Id'),
                                    halign=Gtk.Align.START)

        # Id/Class entry
        entry = CmbEntry()
        GObject.Object.bind_property(self.__object, 'name',
                                     entry, 'cmb-value',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)

        grid.attach(self.__id_label, 0, 0, 1, 1)
        grid.attach(entry, 1, 0, 1, 1)

        # Template check
        if self.__object and not self.__object.parent_id:
            is_template = self.__object.object_id == self.__object.ui.template_id
            tooltip_text=_('Switch between object and template')

            label = Gtk.Label(label=_('Template'),
                              halign=Gtk.Align.START,
                              tooltip_text=tooltip_text)
            switch = Gtk.Switch(active=is_template,
                                halign=Gtk.Align.START,
                                tooltip_text=tooltip_text)

            switch.connect('notify::active', self.__on_template_switch_notify)
            self.__update_template_label()

            grid.attach(label, 0, 1, 1, 1)
            grid.attach(switch, 1, 1, 1, 1)

        return grid

    def __update_template_label(self):
        istmpl = self.__object.ui.template_id == self.__object.object_id
        self.__id_label.props.label = _('Type Name') if istmpl else _('Object Id')

    def __on_template_switch_notify(self, switch, pspec):
        self.__object.ui.template_id = self.__object.object_id if switch.props.active else 0
        self.__update_template_label()

    def __on_expander_expanded(self, expander, pspec, revealer):
        expanded = expander.props.expanded

        if expanded:
            revealer.props.transition_type = Gtk.RevealerTransitionType.SLIDE_DOWN
        else:
            revealer.props.transition_type = Gtk.RevealerTransitionType.SLIDE_UP

        revealer.props.reveal_child = expanded

    def __create_child_type_editor(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                      spacing=6)

        box.add(Gtk.Label(label=_('Child Type'), width_chars=8))

        combo = CmbChildTypeComboBox(object=self.__object)

        GObject.Object.bind_property(self.__object, 'type',
                                     combo, 'cmb-value',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)
        box.pack_start(combo, True, True, 0)
        return box

    def __update_view(self):
        self.__labels = {}

        for child in self.get_children():
            self.remove(child)

        if self.__object is None:
            return

        parent = self.__object.parent

        if self.layout:
            if parent is None:
                return

            # Child Type input
            if parent.info.has_child_types():
                self.add(self.__create_child_type_editor())
        else:
            # ID
            self.add(self.__create_id_editor())

        info = parent.info if self.layout and parent else self.__object.info
        for owner_id in [info.type_id] + info.hierarchy:
            if self.layout:
                owner_id = f'{owner_id}LayoutChild'

            info = self.__object.project.type_info.get(owner_id, None)

            if info is None:
                continue

            # Editor count
            i = 0

            # Grid for all properties and custom data editors
            grid = Gtk.Grid(hexpand=True,
                            margin_start=16,
                            row_spacing=4,
                            column_spacing=4)

            # Properties
            properties = self.__object.layout_dict if self.layout else self.__object.properties_dict
            for property_id in info.properties:
                prop = properties.get(property_id, None)

                if prop is None:
                    continue

                editor = self.__create_editor_for_property(prop)

                if editor is None:
                    continue

                label = Gtk.Label(label=prop.property_id,
                                  xalign=0)

                # Keep a dict of labels
                self.__labels[prop.property_id] = label

                # Update labe status
                self.__update_property_label(prop)

                grid.attach(label, 0, i, 1, 1)
                grid.attach(editor, 1, i, 1, 1)
                i += 1

            # Continue if class had no editors to add
            if i == 0:
                continue

            # Create expander/revealer to pack editor grid
            expander = Gtk.Expander(label=f'<b>{owner_id}</b>',
                                    use_markup=True,
                                    expanded=True)
            revealer = Gtk.Revealer(reveal_child=True)
            expander.connect('notify::expanded', self.__on_expander_expanded, revealer)
            revealer.add(grid)
            self.add(expander)
            self.add(revealer)

        self.show_all()

    def __on_property_changed(self, obj, prop):
        self.__update_property_label(prop)

    def __on_layout_property_changed(self, obj, child, prop):
        self.__update_property_label(prop)

    def __update_property_label(self, prop):
        label = self.__labels.get(prop.property_id, None)

        if label is None:
            return

        if prop.value != prop.info.default_value:
            label.get_style_context().add_class('modified')
        else:
            label.get_style_context().remove_class('modified')

    @GObject.Property(type=CmbObject)
    def object(self):
        return self.__object

    @object.setter
    def _set_object(self, obj):
        if obj == self.__object:
            return

        if self.__object:
            self.__object.disconnect_by_func(self.__on_property_changed)
            self.__object.disconnect_by_func(self.__on_layout_property_changed)

        self.__object = obj

        if obj:
            self.__object.connect('property-changed',
                                 self.__on_property_changed)
            self.__object.connect('layout-property-changed',
                                 self.__on_layout_property_changed)

        self.__update_view()

    def __get_min_max_for_type(self, type_id):
        if type_id == 'gchar':
            return (GLib.MININT8, GLib.MAXINT8)
        elif type_id == 'guchar':
            return (0, GLib.MAXUINT8)
        elif type_id == 'gint':
            return (GLib.MININT, GLib.MAXINT)
        elif type_id == 'guint':
            return (0, GLib.MAXUINT)
        elif type_id == 'glong':
            return (GLib.MINLONG, GLib.MAXLONG)
        elif type_id == 'gulong':
            return (0, GLib.MAXULONG)
        elif type_id == 'gint64':
            return (GLib.MININT64, GLib.MAXINT64)
        elif type_id == 'guint64':
            return (0, GLib.MAXUINT64)
        elif type_id == 'gfloat':
            return (-GLib.MAXFLOAT, GLib.MAXFLOAT)
        elif type_id == 'gdouble':
            return (-GLib.MAXDOUBLE, GLib.MAXDOUBLE)

    def __create_editor_for_property(self, prop):
        editor = None

        if prop.info is None:
            return None

        info = prop.info
        type_id = info.type_id
        tinfo = self.__object.project.type_info.get(type_id, None)

        if type_id == 'gboolean':
            editor = CmbSwitch()
        if type_id == 'gunichar':
            editor = CmbEntry(hexpand=True,
                              max_length=1,
                              placeholder_text=f'<{type_id}>')
        elif type_id == 'gchar' or type_id == 'guchar' or \
             type_id == 'gint' or type_id == 'guint' or \
             type_id == 'glong' or type_id == 'gulong' or \
             type_id == 'gint64' or type_id == 'guint64'or \
             type_id == 'gfloat' or type_id == 'gdouble':

            digits = 0
            step_increment = 1
            minimum, maximum = self.__get_min_max_for_type(type_id)

            # FIXME: is there a better way to handle inf -inf values other
            # than casting to str?
            if info.minimum is not None:
                value = float(info.minimum)
                minimum = value if value != -math.inf else -GLib.MAXDOUBLE
            if info.maximum is not None:
                value = float(info.maximum)
                maximum = value if value != math.inf else GLib.MAXDOUBLE

            if type_id == 'gfloat' or type_id == 'gdouble':
                digits = 4
                step_increment = 0.1

            adjustment = Gtk.Adjustment(lower=minimum,
                                        upper=maximum,
                                        step_increment=step_increment,
                                        page_increment=10)

            editor = CmbSpinButton(digits=digits,
                                   adjustment=adjustment)
        elif type_id == 'GdkRGBA':
            editor = CmbColorEntry()
        elif type_id == 'GdkColor':
            editor = CmbColorEntry(use_color=True)
        elif type_id == 'CmbIconName':
            editor = CmbIconNameEntry(hexpand=True,
                                      placeholder_text=f'<Icon Name>')
        elif info.is_object:
            editor = CmbObjectChooser(prop=prop)
        elif tinfo:
            if tinfo.parent_id == 'enum':
                editor = CmbEnumComboBox(info=tinfo)
            elif tinfo.parent_id == 'flags':
                editor = CmbFlagsEntry(info=tinfo)

        if editor is None:
            editor = CmbEntry(hexpand=True, placeholder_text=f'<{type_id}>')
            if info.translatable == True:
                editor.make_translatable(target = prop)

        GObject.Object.bind_property(prop, 'value',
                                     editor, 'cmb-value',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)
        return editor


Gtk.WidgetClass.set_css_name(CmbObjectEditor, 'CmbObjectEditor')
