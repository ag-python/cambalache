#
# CmbObjectEditor - Cambalache Object Editor
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import io
import gi
import math

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gtk

from .cmb_object import CmbObject
from .cmb_type_info import CmbTypeInfo


class CmbEntry(Gtk.Entry):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('notify::text', self._on_text_notify)

    def _on_text_notify(self, obj, pspec):
        self.notify('cmb-value')

    @GObject.property(type=str)
    def cmb_value(self):
        return self.props.text if self.props.text != '' else None

    @cmb_value.setter
    def _set_value(self, value):
        self.props.text = value if value is not None else ''


class CmbSpinButton(Gtk.SpinButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('notify::value', self._on_text_notify)
        self.props.halign=Gtk.Align.START
        self.props.numeric=True
        self.props.width_chars=8

    def _on_text_notify(self, obj, pspec):
        self.notify('cmb-value')

    @GObject.property(type=str)
    def cmb_value(self):
        # FIXME: value should always use C locale
        if self.props.digits == 0:
            return str(int(self.props.value))
        else:
            # NOTE: round() to avoid setting numbers like 0.7000000000000001
            return str(round(self.props.value, 15))

    @cmb_value.setter
    def _set_value(self, value):
        self.props.value = float(value)


class CmbSwitch(Gtk.Switch):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('notify::active', self._on_notify)
        self.props.halign=Gtk.Align.START

    def _on_notify(self, obj, pspec):
        self.notify('cmb-value')

    @GObject.property(type=str)
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


class CmbComboBox(Gtk.ComboBox):
    text_column = GObject.Property(type=int)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('changed', self._on_changed)

        renderer_text = Gtk.CellRendererText()
        self.pack_start(renderer_text, True)
        self.add_attribute(renderer_text, "text", self.text_column)

    def _on_changed(self, obj):
        self.notify('cmb-value')

    @GObject.property(type=str)
    def cmb_value(self):
        return self.props.active_id

    @cmb_value.setter
    def _set_value(self, value):
        self.props.active_id = value


class CmbFlagsEntry(Gtk.Entry):
    info = GObject.Property(type=CmbTypeInfo, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    id_column = GObject.Property(type=int, default = 0, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    text_column = GObject.Property(type=int, default = 1, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    value_column = GObject.Property(type=int, default = 2, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY )

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

    @GObject.property(type=str)
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

                check = self._checks.get(flag_id, None)
                if check:
                    val = flag_id in tokens
                    check.props.active = val
                    self.flags[flag_id] = val


class CmbObjectEditor(Gtk.Box):
    __gtype_name__ = 'CmbObjectEditor'

    layout = GObject.Property(type=bool,
                              flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY,
                              default=False)

    def __init__(self, **kwargs):
        self._object = None

        super().__init__(**kwargs)

        self.props.orientation = Gtk.Orientation.VERTICAL

    def _create_id_editor(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                      spacing=6)
        box.add(Gtk.Label(label='Object Id:'))

        entry = CmbEntry()
        GObject.Object.bind_property(self._object, 'name',
                                     entry, 'cmb-value',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)

        box.pack_start(entry, True, True, 0)
        return box

    def _on_expander_expanded(self, expander, pspec, revealer):
        expanded = expander.props.expanded

        if expanded:
            revealer.props.transition_type = Gtk.RevealerTransitionType.SLIDE_DOWN
        else:
            revealer.props.transition_type = Gtk.RevealerTransitionType.SLIDE_UP

        revealer.props.reveal_child = expanded

    def _update_view(self):
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
            editor = self._create_editor_for_property(prop)
            grid.attach(label, 0, i, 1, 1)
            grid.attach(editor, 1, i, 1, 1)
            i += 1

        self.show_all()

    @GObject.property(type=CmbObject)
    def object(self):
        return self._object

    @object.setter
    def _set_object(self, obj):
        self._object = obj
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
            elif tinfo:
                if tinfo.parent_id == 'enum':
                    editor = CmbComboBox(model=tinfo.enum,
                                         id_column=0,
                                         text_column=1)
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
