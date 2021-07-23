#
# Cambalache UI wrapper
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

from .cmb_objects_base import CmbBaseUI


class CmbUI(CmbBaseUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @GObject.Property(type=int)
    def template_id(self):
        retval = self.db_get('SELECT template_id FROM ui WHERE (ui_id) IS (?);',
                             (self.ui_id, ))
        return retval if retval is not None else 0

    @template_id.setter
    def _set_template_id(self, value):
        self.db_set('UPDATE ui SET template_id=? WHERE (ui_id) IS (?);',
                    (self.ui_id, ), value if value != 0 else None)

