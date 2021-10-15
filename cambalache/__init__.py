# Cambalache
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
import logging

from .config import *

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gdk, Gtk
resource = Gio.Resource.load(os.path.join(pkgdatadir, 'cambalache.gresource'))
resource._register()

provider = Gtk.CssProvider()
provider.load_from_resource('/ar/xjuan/Cambalache/cambalache.css')
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

def getLogger(name):
    formatter = logging.Formatter('%(levelname)s:%(name)s %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('MERENGUE_LOGLEVEL', 'WARNING').upper())
    logger.addHandler(ch)

    return logger

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
from .cmb_ui_editor import CmbUIEditor
