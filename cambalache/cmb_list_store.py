#
# CmbListStore - Cambalache List Store
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

import io
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk


class CmbListStore(Gtk.ListStore):
    __gtype_name__ = 'CmbListStore'

    table = GObject.Property(type=str)
    query = GObject.Property(type=str)
    project = GObject.Property(type=GObject.GObject)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        data = self.project._get_table_data(self.table)
        self.set_column_types(data['types'])
        self.__populate()

    def __populate(self):
        c = self.project.db.cursor()
        for row in c.execute(self.query):
            self.append(row)

        c.close()
