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
from cambalache import getLogger

logger = getLogger(__name__)


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

    def get_library(self, library_id):
        c = self.project.db.execute("SELECT version FROM ui_library WHERE ui_id=? AND library_id=?;",
                                    (self.ui_id, library_id))
        row = c.fetchone()
        return row[0] if row is not None else None

    def set_library(self, library_id, version, comment=None):
        c = self.project.db.cursor()

        try:
            if version is None:
                c.execute("DELETE FROM ui_library WHERE ui_id=? AND library_id=?;",
                          (self.ui_id, library_id))
            else:
                # Do not use REPLACE INTO, to make sure both INSERT and UPDATE triggers are used
                count = self.db_get("SELECT count(version) FROM ui_library WHERE ui_id=? AND library_id=?;", (self.ui_id, library_id))

                if count:
                    c.execute("UPDATE ui_library SET version=?, comment=? WHERE ui_id=?, library_id=?;",
                              (str(version), comment, self.ui_id, library_id))
                else:
                    c.execute("INSERT INTO ui_library (ui_id, library_id, version, comment) VALUES (?, ?, ?, ?);",
                              (self.ui_id, library_id, str(version), comment))

        except Exception as e:
            logger.warning(f'{self} Error setting library {library_id}={version}: {e}')

        c.close()
