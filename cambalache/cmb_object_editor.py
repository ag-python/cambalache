#
# CmbObjectEditor - Cambalache Object Editor
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import io
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk

from .cmb_objects import CmbObject


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
            self.props.active = True if val == 'true' or val == 'yes' else False
        else:
            self.props.active = False


class CmbObjectEditor(Gtk.Box):
    __gtype_name__ = 'CmbObjectEditor'

    layout = GObject.Property(type=bool,
                              flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY,
                              default=False)

    def __init__(self, **kwargs):
        self._object = None

        super().__init__(**kwargs)

        self.props.orientation = Gtk.Orientation.VERTICAL

    def _update_view(self):
        for child in self.get_children():
            self.remove(child)

        if self._object is None:
            return

        owner_id = None
        grid = None
        i = 0

        properties = self._object.layout if self.layout else self._object.properties
        for prop in properties:
            if owner_id != prop.owner_id:
                owner_id = prop.owner_id
                expander = Gtk.Expander(label=f'<b>{owner_id}</b>',
                                        use_markup=True,
                                        expanded=True)
                grid = Gtk.Grid(hexpand=True,
                                margin_start=16,
                                row_spacing=4,
                                column_spacing=4)
                expander.add(grid)
                self.add(expander)
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

    def _create_editor_for_property(self, prop):
        editor = None

        if prop.info is not None:
            info = prop.info
            type_id = info.type_id

            if type_id == 'gboolean':
                editor = CmbSwitch()
            elif type_id == 'gchar' or type_id == 'guchar' or \
                 type_id == 'gint' or type_id == 'guint' or \
                 type_id == 'glong' or type_id == 'gulong' or \
                 type_id == 'gint64' or type_id == 'guint64'or \
                 type_id == 'gfloat' or type_id == 'gdouble':

                digits = 0
                step_increment = 1

                if type_id == 'gfloat' or type_id == 'gdouble':
                    digits = 4
                    step_increment = 0.1

                adjustment = Gtk.Adjustment(lower=float(info.minimum),
                                            upper=float(info.maximum),
                                            step_increment=step_increment,
                                            page_increment=10)

                editor = CmbSpinButton(digits=digits,
                                       adjustment=adjustment)

        if editor is None:
            editor = CmbEntry(hexpand=True,
                              placeholder_text=f'<{type_id}>')

        GObject.Object.bind_property(prop, 'value',
                                     editor, 'cmb-value',
                                     GObject.BindingFlags.SYNC_CREATE |
                                     GObject.BindingFlags.BIDIRECTIONAL)
        return editor
