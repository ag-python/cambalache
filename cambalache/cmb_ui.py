#
# Cambalache UI wrapper
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
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

