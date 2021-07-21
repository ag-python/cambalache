# THIS FILE IS AUTOGENERATED, DO NOT EDIT!!!
#
# Cambalache Base Object wrappers
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
from gi.repository import GObject
from .cmb_base import *


class CmbPropertyInfo(CmbBase):
    __gtype_name__ = 'CmbPropertyInfo'

    owner_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    property_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    type_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    is_object = GObject.Property(type=bool, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY, default = False)
    construct_only = GObject.Property(type=bool, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY, default = False)
    default_value = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    minimum = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    maximum = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    version = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    deprecated_version = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, project, owner_id, property_id, type_id, is_object, construct_only, default_value, minimum, maximum, version, deprecated_version):
        return cls(project=project,
                   owner_id=owner_id,
                   property_id=property_id,
                   type_id=type_id,
                   is_object=is_object,
                   construct_only=construct_only,
                   default_value=default_value,
                   minimum=minimum,
                   maximum=maximum,
                   version=version,
                   deprecated_version=deprecated_version)


class CmbSignalInfo(CmbBase):
    __gtype_name__ = 'CmbSignalInfo'

    owner_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    signal_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    version = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    deprecated_version = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    detailed = GObject.Property(type=bool, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY, default = False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, project, owner_id, signal_id, version, deprecated_version, detailed):
        return cls(project=project,
                   owner_id=owner_id,
                   signal_id=signal_id,
                   version=version,
                   deprecated_version=deprecated_version,
                   detailed=detailed)


class CmbBaseTypeInfo(CmbBase):
    __gtype_name__ = 'CmbBaseTypeInfo'

    type_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    parent_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    library_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    version = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    deprecated_version = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    abstract = GObject.Property(type=bool, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY, default = False)
    layout = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, project, type_id, parent_id, library_id, version, deprecated_version, abstract, layout):
        return cls(project=project,
                   type_id=type_id,
                   parent_id=parent_id,
                   library_id=library_id,
                   version=version,
                   deprecated_version=deprecated_version,
                   abstract=abstract,
                   layout=layout)


class CmbBaseUI(CmbBase):
    __gtype_name__ = 'CmbBaseUI'

    ui_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, project, ui_id, template_id, name, filename, description, copyright, authors, license_id, translation_domain, comment):
        return cls(project=project,
                   ui_id=ui_id)

    @GObject.Property(type=int)
    def template_id(self):
        return self.db_get('SELECT template_id FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @template_id.setter
    def _set_template_id(self, value):
        self.db_set('UPDATE ui SET template_id=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)

    @GObject.Property(type=str)
    def name(self):
        return self.db_get('SELECT name FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @name.setter
    def _set_name(self, value):
        self.db_set('UPDATE ui SET name=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)

    @GObject.Property(type=str)
    def filename(self):
        return self.db_get('SELECT filename FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @filename.setter
    def _set_filename(self, value):
        self.db_set('UPDATE ui SET filename=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)

    @GObject.Property(type=str)
    def description(self):
        return self.db_get('SELECT description FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @description.setter
    def _set_description(self, value):
        self.db_set('UPDATE ui SET description=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)

    @GObject.Property(type=str)
    def copyright(self):
        return self.db_get('SELECT copyright FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @copyright.setter
    def _set_copyright(self, value):
        self.db_set('UPDATE ui SET copyright=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)

    @GObject.Property(type=str)
    def authors(self):
        return self.db_get('SELECT authors FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @authors.setter
    def _set_authors(self, value):
        self.db_set('UPDATE ui SET authors=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)

    @GObject.Property(type=str)
    def license_id(self):
        return self.db_get('SELECT license_id FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @license_id.setter
    def _set_license_id(self, value):
        self.db_set('UPDATE ui SET license_id=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)

    @GObject.Property(type=str)
    def translation_domain(self):
        return self.db_get('SELECT translation_domain FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @translation_domain.setter
    def _set_translation_domain(self, value):
        self.db_set('UPDATE ui SET translation_domain=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)

    @GObject.Property(type=str)
    def comment(self):
        return self.db_get('SELECT comment FROM ui WHERE (ui_id) IS (?);',
                           (self.ui_id, ))

    @comment.setter
    def _set_comment(self, value):
        self.db_set('UPDATE ui SET comment=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value)


class CmbBaseProperty(CmbBase):
    __gtype_name__ = 'CmbBaseProperty'

    ui_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    object_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    owner_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    property_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, project, ui_id, object_id, owner_id, property_id, value, translatable, comment):
        return cls(project=project,
                   ui_id=ui_id,
                   object_id=object_id,
                   owner_id=owner_id,
                   property_id=property_id)

    @GObject.Property(type=str)
    def value(self):
        return self.db_get('SELECT value FROM object_property WHERE (ui_id, object_id, owner_id, property_id) IS (?, ?, ?, ?);',
                           (self.ui_id, self.object_id, self.owner_id, self.property_id, ))

    @value.setter
    def _set_value(self, value):
        self.db_set('UPDATE object_property SET value=? WHERE (ui_id, object_id, owner_id, property_id) IS (?, ?, ?, ?);',
                    (self.ui_id, self.object_id, self.owner_id, self.property_id, ), value)

    @GObject.Property(type=bool, default = False)
    def translatable(self):
        return self.db_get('SELECT translatable FROM object_property WHERE (ui_id, object_id, owner_id, property_id) IS (?, ?, ?, ?);',
                           (self.ui_id, self.object_id, self.owner_id, self.property_id, ))

    @translatable.setter
    def _set_translatable(self, value):
        self.db_set('UPDATE object_property SET translatable=? WHERE (ui_id, object_id, owner_id, property_id) IS (?, ?, ?, ?);',
                    (self.ui_id, self.object_id, self.owner_id, self.property_id, ), value)

    @GObject.Property(type=str)
    def comment(self):
        return self.db_get('SELECT comment FROM object_property WHERE (ui_id, object_id, owner_id, property_id) IS (?, ?, ?, ?);',
                           (self.ui_id, self.object_id, self.owner_id, self.property_id, ))

    @comment.setter
    def _set_comment(self, value):
        self.db_set('UPDATE object_property SET comment=? WHERE (ui_id, object_id, owner_id, property_id) IS (?, ?, ?, ?);',
                    (self.ui_id, self.object_id, self.owner_id, self.property_id, ), value)


class CmbBaseLayoutProperty(CmbBase):
    __gtype_name__ = 'CmbBaseLayoutProperty'

    ui_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    object_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    child_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    owner_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    property_id = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, project, ui_id, object_id, child_id, owner_id, property_id, value, translatable, comment):
        return cls(project=project,
                   ui_id=ui_id,
                   object_id=object_id,
                   child_id=child_id,
                   owner_id=owner_id,
                   property_id=property_id)

    @GObject.Property(type=str)
    def value(self):
        return self.db_get('SELECT value FROM object_layout_property WHERE (ui_id, object_id, child_id, owner_id, property_id) IS (?, ?, ?, ?, ?);',
                           (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id, ))

    @value.setter
    def _set_value(self, value):
        self.db_set('UPDATE object_layout_property SET value=? WHERE (ui_id, object_id, child_id, owner_id, property_id) IS (?, ?, ?, ?, ?);',
                    (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id, ), value)

    @GObject.Property(type=bool, default = False)
    def translatable(self):
        return self.db_get('SELECT translatable FROM object_layout_property WHERE (ui_id, object_id, child_id, owner_id, property_id) IS (?, ?, ?, ?, ?);',
                           (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id, ))

    @translatable.setter
    def _set_translatable(self, value):
        self.db_set('UPDATE object_layout_property SET translatable=? WHERE (ui_id, object_id, child_id, owner_id, property_id) IS (?, ?, ?, ?, ?);',
                    (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id, ), value)

    @GObject.Property(type=str)
    def comment(self):
        return self.db_get('SELECT comment FROM object_layout_property WHERE (ui_id, object_id, child_id, owner_id, property_id) IS (?, ?, ?, ?, ?);',
                           (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id, ))

    @comment.setter
    def _set_comment(self, value):
        self.db_set('UPDATE object_layout_property SET comment=? WHERE (ui_id, object_id, child_id, owner_id, property_id) IS (?, ?, ?, ?, ?);',
                    (self.ui_id, self.object_id, self.child_id, self.owner_id, self.property_id, ), value)


class CmbSignal(CmbBase):
    __gtype_name__ = 'CmbSignal'

    signal_pk = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, project, signal_pk, ui_id, object_id, owner_id, signal_id, handler, detail, user_data, swap, after, comment):
        return cls(project=project,
                   signal_pk=signal_pk)

    @GObject.Property(type=int)
    def ui_id(self):
        return self.db_get('SELECT ui_id FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @ui_id.setter
    def _set_ui_id(self, value):
        self.db_set('UPDATE object_signal SET ui_id=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=int)
    def object_id(self):
        return self.db_get('SELECT object_id FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @object_id.setter
    def _set_object_id(self, value):
        self.db_set('UPDATE object_signal SET object_id=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=str)
    def owner_id(self):
        return self.db_get('SELECT owner_id FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @owner_id.setter
    def _set_owner_id(self, value):
        self.db_set('UPDATE object_signal SET owner_id=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=str)
    def signal_id(self):
        return self.db_get('SELECT signal_id FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @signal_id.setter
    def _set_signal_id(self, value):
        self.db_set('UPDATE object_signal SET signal_id=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=str)
    def handler(self):
        return self.db_get('SELECT handler FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @handler.setter
    def _set_handler(self, value):
        self.db_set('UPDATE object_signal SET handler=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=str)
    def detail(self):
        return self.db_get('SELECT detail FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @detail.setter
    def _set_detail(self, value):
        self.db_set('UPDATE object_signal SET detail=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=int)
    def user_data(self):
        return self.db_get('SELECT user_data FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @user_data.setter
    def _set_user_data(self, value):
        self.db_set('UPDATE object_signal SET user_data=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=bool, default = False)
    def swap(self):
        return self.db_get('SELECT swap FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @swap.setter
    def _set_swap(self, value):
        self.db_set('UPDATE object_signal SET swap=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=bool, default = False)
    def after(self):
        return self.db_get('SELECT after FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @after.setter
    def _set_after(self, value):
        self.db_set('UPDATE object_signal SET after=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)

    @GObject.Property(type=str)
    def comment(self):
        return self.db_get('SELECT comment FROM object_signal WHERE (signal_pk) IS (?);',
                           (self.signal_pk, ))

    @comment.setter
    def _set_comment(self, value):
        self.db_set('UPDATE object_signal SET comment=? WHERE (signal_pk) IS (?);',
                    (self.signal_pk, ), value)


class CmbBaseObject(CmbBase):
    __gtype_name__ = 'CmbBaseObject'

    ui_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)
    object_id = GObject.Property(type=int, flags = GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT_ONLY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_row(cls, project, ui_id, object_id, type_id, name, parent_id, internal, type, comment):
        return cls(project=project,
                   ui_id=ui_id,
                   object_id=object_id)

    @GObject.Property(type=str)
    def type_id(self):
        return self.db_get('SELECT type_id FROM object WHERE (ui_id, object_id) IS (?, ?);',
                           (self.ui_id, self.object_id, ))

    @type_id.setter
    def _set_type_id(self, value):
        self.db_set('UPDATE object SET type_id=? WHERE (ui_id, object_id) IS (?, ?);',
                    (self.ui_id, self.object_id, ), value)

    @GObject.Property(type=str)
    def name(self):
        return self.db_get('SELECT name FROM object WHERE (ui_id, object_id) IS (?, ?);',
                           (self.ui_id, self.object_id, ))

    @name.setter
    def _set_name(self, value):
        self.db_set('UPDATE object SET name=? WHERE (ui_id, object_id) IS (?, ?);',
                    (self.ui_id, self.object_id, ), value)

    @GObject.Property(type=int)
    def parent_id(self):
        return self.db_get('SELECT parent_id FROM object WHERE (ui_id, object_id) IS (?, ?);',
                           (self.ui_id, self.object_id, ))

    @parent_id.setter
    def _set_parent_id(self, value):
        self.db_set('UPDATE object SET parent_id=? WHERE (ui_id, object_id) IS (?, ?);',
                    (self.ui_id, self.object_id, ), value)

    @GObject.Property(type=str)
    def internal(self):
        return self.db_get('SELECT internal FROM object WHERE (ui_id, object_id) IS (?, ?);',
                           (self.ui_id, self.object_id, ))

    @internal.setter
    def _set_internal(self, value):
        self.db_set('UPDATE object SET internal=? WHERE (ui_id, object_id) IS (?, ?);',
                    (self.ui_id, self.object_id, ), value)

    @GObject.Property(type=str)
    def type(self):
        return self.db_get('SELECT type FROM object WHERE (ui_id, object_id) IS (?, ?);',
                           (self.ui_id, self.object_id, ))

    @type.setter
    def _set_type(self, value):
        self.db_set('UPDATE object SET type=? WHERE (ui_id, object_id) IS (?, ?);',
                    (self.ui_id, self.object_id, ), value)

    @GObject.Property(type=str)
    def comment(self):
        return self.db_get('SELECT comment FROM object WHERE (ui_id, object_id) IS (?, ?);',
                           (self.ui_id, self.object_id, ))

    @comment.setter
    def _set_comment(self, value):
        self.db_set('UPDATE object SET comment=? WHERE (ui_id, object_id) IS (?, ?);',
                    (self.ui_id, self.object_id, ), value)
