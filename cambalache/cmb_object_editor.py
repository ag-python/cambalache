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
from gettext import gettext as _

from .cmb_object import CmbObject
from .cmb_property_controls import *


class CmbObjectEditor(Gtk.Box):
    __gtype_name__ = 'CmbObjectEditor'

    layout = GObject.Property(type=bool,
                              flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY,
                              default=False)

    def __init__(self, **kwargs):
        self._object = None
        self._id_label = None
        self._labels = {}

        super().__init__(**kwargs)

        self.props.orientation = Gtk.Orientation.VERTICAL

    def _create_id_editor(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                      spacing=6)

        # Label
        self._id_label = Gtk.Label(label=_('Object Id'), width_chars=8)

        # Template check
        if self._object and not self._object.parent_id:
            is_template = self._object.object_id == self._object.ui.template_id

            check = Gtk.CheckButton(active=is_template,
                                    tooltip_text=_('Switch between object and template'))
            check.connect('toggled', self._on_template_check_toggled)
            self._update_template_label()

            check.add(self._id_label)
            box.add(check)
        else:
            box.add(self._id_label)

        # Id/Class entry
        entry = CmbEntry()
        GObject.Object.bind_property(self._object, 'name',
                                     entry, 'cmb-value',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)
        box.pack_start(entry, True, True, 0)
        return box

    def _update_template_label(self):
        istmpl = self._object.ui.template_id == self._object.object_id
        self._id_label.props.label = _('Template') if istmpl else _('Object Id')

    def _on_template_check_toggled(self, button):
        self._object.ui.template_id = self._object.object_id if button.props.active else 0

    def _on_expander_expanded(self, expander, pspec, revealer):
        expanded = expander.props.expanded

        if expanded:
            revealer.props.transition_type = Gtk.RevealerTransitionType.SLIDE_DOWN
        else:
            revealer.props.transition_type = Gtk.RevealerTransitionType.SLIDE_UP

        revealer.props.reveal_child = expanded

    def _update_view(self):
        self._labels = {}

        for child in self.get_children():
            self.remove(child)

        if self._object is None:
            return

        # ID
        if not self.layout:
            self.add(self._create_id_editor())

        owner_id = None
        grid = None
        i = 0

        # Properties
        properties = self._object.layout if self.layout else self._object.properties
        for prop in properties:
            if owner_id != prop.owner_id:
                owner_id = prop.owner_id

                expander = Gtk.Expander(label=f'<b>{owner_id}</b>',
                                        use_markup=True,
                                        expanded=True)
                revealer = Gtk.Revealer(reveal_child=True)

                expander.connect('notify::expanded', self._on_expander_expanded, revealer)

                grid = Gtk.Grid(hexpand=True,
                                margin_start=16,
                                row_spacing=4,
                                column_spacing=4)

                revealer.add(grid)

                self.add(expander)
                self.add(revealer)
                i = 0

            label = Gtk.Label(label=prop.property_id,
                              xalign=0)

            # Keep a dict of labels
            self._labels[prop.property_id] = label

            # Update labe status
            self._update_property_label(prop)

            editor = self._create_editor_for_property(prop)
            grid.attach(label, 0, i, 1, 1)
            grid.attach(editor, 1, i, 1, 1)
            i += 1

        self.show_all()

    def _on_property_changed(self, obj, prop):
        self._update_property_label(prop)

    def _on_layout_property_changed(self, obj, child, prop):
        self._update_property_label(prop)

    def _update_property_label(self, prop):
        label = self._labels.get(prop.property_id, None)

        if label is None:
            return

        if prop.value != prop.info.default_value:
            label.get_style_context().add_class('modified')
        else:
            label.get_style_context().remove_class('modified')

    @GObject.Property(type=CmbObject)
    def object(self):
        return self._object

    @object.setter
    def _set_object(self, obj):
        if obj == self._object:
            return

        if self._object:
            self._object.disconnect_by_func(self._on_property_changed)
            self._object.disconnect_by_func(self._on_layout_property_changed)

        self._object = obj

        if obj:
            self._object.connect('property-changed',
                                 self._on_property_changed)
            self._object.connect('layout-property-changed',
                                 self._on_layout_property_changed)

        self._update_view()

    def _get_min_max_for_type(self, type_id):
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

    def _create_editor_for_property(self, prop):
        editor = None

        if prop.info is not None:
            info = prop.info
            type_id = info.type_id
            tinfo = self._object.project._type_info.get(type_id, None)

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
                minimum, maximum = self._get_min_max_for_type(type_id)

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
            elif info.is_object:
                editor = CmbObjectChooser(object=self._object,
                                          type_id=type_id)
            elif tinfo:
                if tinfo.parent_id == 'enum':
                    editor = CmbEnumComboBox(info=tinfo)
                elif tinfo.parent_id == 'flags':
                    editor = CmbFlagsEntry(info=tinfo)

        if editor is None:
            editor = CmbEntry(hexpand=True,
                              placeholder_text=f'<{type_id}>')

        GObject.Object.bind_property(prop, 'value',
                                     editor, 'cmb-value',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)
        return editor


Gtk.WidgetClass.set_css_name(CmbObjectEditor, 'CmbObjectEditor')
