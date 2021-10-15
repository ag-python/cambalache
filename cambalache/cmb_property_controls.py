#
# CmbPropertyControls - Cambalache Property Controls
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
import math

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gtk

from .cmb_object import CmbObject
from .cmb_ui import CmbUI
from .cmb_type_info import CmbTypeInfo


class CmbEntry(Gtk.Entry):
    __gtype_name__ = 'CmbEntry'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('notify::text', self._on_text_notify)

    def _on_text_notify(self, obj, pspec):
        self.notify('cmb-value')

    @GObject.Property(type=str)
    def cmb_value(self):
        return self.props.text if self.props.text != '' else None

    @cmb_value.setter
    def _set_value(self, value):
        self.props.text = value if value is not None else ''


class CmbTextBuffer(Gtk.TextBuffer):
    __gtype_name__ = 'CmbTextBuffer'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('notify::text', self._on_text_notify)

    def _on_text_notify(self, obj, pspec):
        self.notify('cmb-value')

    @GObject.Property(type=str)
    def cmb_value(self):
        return self.props.text if self.props.text != '' else None

    @cmb_value.setter
    def _set_value(self, value):
        self.props.text = value if value is not None else ''


class CmbSpinButton(Gtk.SpinButton):
    __gtype_name__ = 'CmbSpinButton'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('notify::value', self._on_text_notify)
        self.props.halign=Gtk.Align.START
        self.props.numeric=True
        self.props.width_chars=8

    def _on_text_notify(self, obj, pspec):
        self.notify('cmb-value')

    @GObject.Property(type=str)
    def cmb_value(self):
        # FIXME: value should always use C locale
        if self.props.digits == 0:
            return str(int(self.props.value))
        else:
            # NOTE: round() to avoid setting numbers like 0.7000000000000001
            return str(round(self.props.value, 15))

    @cmb_value.setter
    def _set_value(self, value):
        value = float(value)

        if value == math.inf:
            self.props.value = GLib.MAXDOUBLE
        elif value == -math.inf:
            self.props.value = -GLib.MAXDOUBLE
        else:
            self.props.value = value


class CmbSwitch(Gtk.Switch):
    __gtype_name__ = 'CmbSwitch'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('notify::active', self._on_notify)
        self.props.halign=Gtk.Align.START

    def _on_notify(self, obj, pspec):
        self.notify('cmb-value')

    @GObject.Property(type=str)
    def cmb_value(self):
        return 'True' if self.props.active else 'False'

    @cmb_value.setter
    def _set_value(self, value):
        if value is not None:
            val = value.lower()

            if type(val) == str:
                if val.lower() in {'1', 't', 'y', 'true', 'yes'}:
                    self.props.active = True
                else:
                    self.props.active = False
            else:
                self.props.active = bool(value)
        else:
            self.props.active = False


class CmbEnumComboBox(Gtk.ComboBox):
    __gtype_name__ = 'CmbEnumComboBox'

    info = GObject.Property(type=CmbTypeInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    text_column = GObject.Property(type=int, default = 1, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('changed', self._on_changed)

        renderer_text = Gtk.CellRendererText()
        self.pack_start(renderer_text, True)
        self.add_attribute(renderer_text, "text", self.text_column)

        self.props.id_column = self.text_column
        self.props.model = self.info.enum

    def _on_changed(self, obj):
        self.notify('cmb-value')

    @GObject.Property(type=str)
    def cmb_value(self):
        return self.props.active_id

    @cmb_value.setter
    def _set_value(self, value):
        self.props.active_id = None

        for row in self.info.enum:
            enum_name = row[0]
            enum_nick = row[1]

            # Always use nick as value
            if value == enum_name or value == enum_nick:
                self.props.active_id = enum_nick


class CmbFlagsEntry(Gtk.Entry):
    __gtype_name__ = 'CmbFlagsEntry'

    info = GObject.Property(type=CmbTypeInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    id_column = GObject.Property(type=int, default = 1, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    text_column = GObject.Property(type=int, default = 1, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    value_column = GObject.Property(type=int, default = 2, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.props.editable = False
        self.props.secondary_icon_name = 'document-edit-symbolic'

        self.connect('icon-release', self._on_icon_release)

        self._init_popover()

    def _init_popover(self):
        self.flags = {}
        self._checks = {}
        self._popover = Gtk.Popover(relative_to=self)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(Gtk.Label(label=f'<b>{self.info.type_id}</b>',
                                 use_markup=True),
                       False, True, 4)
        box.pack_start(Gtk.Separator(), False, False, 0)
        sw = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER,
                                propagate_natural_height=True,
                                max_content_height=360)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sw.add(vbox)
        box.pack_start(sw, True, True, 0)

        for row in self.info.flags:
            flag = row[self.text_column]
            flag_id =  row[self.id_column]

            check = Gtk.CheckButton(label=flag)
            check.connect('toggled', self._on_check_toggled, flag_id)
            vbox.pack_start(check, False, True, 4)
            self._checks[flag_id] = check

        box.show_all()
        self._popover.add(box)

    def _on_check_toggled(self, check, flag_id):
        self.flags[flag_id] = check.props.active
        self.props.text = self._to_string()
        self.notify('cmb-value')

    def _on_icon_release(self, obj, pos, event):
        self._popover.popup()

    def _to_string(self):
        retval = None
        for row in self.info.flags:
            flag_id = row[self.id_column]
            if self.flags.get(flag_id, False):
                retval = flag_id if retval is None else f'{retval} | {flag_id}'

        return retval if retval is not None else ''

    @GObject.Property(type=str)
    def cmb_value(self):
        return self.props.text if self.props.text != '' else None

    @cmb_value.setter
    def _set_value(self, value):
        self.props.text = value if value is not None else ''

        self.flags = {}
        for check in self._checks:
            self._checks[check].props.active = False

        if value:
            tokens = [t.strip() for t in value.split('|')]

            for row in self.info.flags:
                flag = row[self.text_column]
                flag_id = row[self.id_column]
                flag_name = row[0]
                flag_nick = row[1]

                check = self._checks.get(flag_id, None)
                if check:
                    val = flag_name in tokens or flag_nick in tokens
                    check.props.active = val
                    self.flags[flag_id] = val


class CmbObjectChooser(Gtk.Entry):
    __gtype_name__ = 'CmbObjectChooser'

    object = GObject.Property(type=CmbObject, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    type_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self._value = None
        super().__init__(**kwargs)
        self.connect('notify::text', self._on_text_notify)
        self.props.placeholder_text = f'<{self.type_id}>'

    def _on_text_notify(self, obj, pspec):
        obj = self.object.project._get_object_by_name(self.object.ui_id,
                                                      self.props.text)
        if obj:
            self._value = obj.object_id

        self.notify('cmb-value')

    @GObject.Property(type=str)
    def cmb_value(self):
        return self._value

    @cmb_value.setter
    def _set_value(self, value):
        self._value = int(value) if value else 0

        if self._value:
            obj = self.object.project._get_object_by_id(self.object.ui_id,
                                                        self._value)
            self.props.text = obj.name if obj else ''
        else:
            self.props.text = ''


class CmbToplevelChooser(Gtk.ComboBoxText):
    __gtype_name__ = 'CmbToplevelChooser'

    object = GObject.Property(type=CmbUI, flags = GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        self._value = None
        super().__init__(**kwargs)
        self.connect('notify::object', self._on_object_notify)
        self.connect('changed', self._on_changed)

    def _filter_func(self, model, iter, data):
        obj = model[iter][0]

        if type(obj) == CmbObject:
            return obj.parent_id == 0

        return False

    def _on_object_notify(self, obj, pspec):
        self.remove_all()

        if self.object is None:
            return

        self.append('0', '(None)')

        # TODO: add api to get toplevels in CmbUI
        # TODO: update model on project change
        for ui in self.object.project:
            if ui[0] == self.object:
                for child in ui.iterchildren():
                    obj = child[0]
                    name = obj.name or ''
                    self.append(f'{obj.object_id}', f'{name}({obj.type_id})')

    def _on_changed(self, combo):
        self.notify('cmb-value')

    @GObject.Property(type=int)
    def cmb_value(self):
        active_id = self.get_active_id()
        return int(active_id) if active_id is not None else 0

    @cmb_value.setter
    def _set_value(self, value):
        if self.object is None:
            return

        self.set_active_id(str(value) if value is not None else None)

