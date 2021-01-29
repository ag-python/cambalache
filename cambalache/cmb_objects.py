#
# Cambalache Object wrappers
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import gi
from gi.repository import GObject

from .cmb_objects_base import *


class CmbUI(CmbBaseUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CmbObject(CmbBaseObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

