# Cambalache
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
from .config import *
from gi.repository import Gio
resource = Gio.Resource.load(os.path.join(pkgdatadir, 'cambalache.gresource'))
resource._register()

from .cmb_ui import CmbUI
from .cmb_object import CmbObject
from .cmb_property import CmbProperty
from .cmb_layout_property import CmbLayoutProperty
from .cmb_type_info import CmbTypeInfo
from .cmb_project import CmbProject

from .cmb_view import CmbView
from .cmb_tree_view import CmbTreeView
from .cmb_object_editor import CmbObjectEditor
from .cmb_signal_editor import CmbSignalEditor
