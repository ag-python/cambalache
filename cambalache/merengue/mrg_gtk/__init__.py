# Merengue Gtk plugin
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
from gi.repository import Gtk

from .mrg_gtk_aspect_frame import MrgGtkAspectFrame
from .mrg_gtk_assistant import MrgGtkAssistant
from .mrg_gtk_bin import MrgGtkBin

if Gtk.MAJOR_VERSION == 3:
    from .mrg_gtk_menu_item import MrgGtkMenuItem
elif Gtk.MAJOR_VERSION == 4:
    from .mrg_gtk_center_box import MrgGtkCenterBox

from .mrg_gtk_box import MrgGtkBox
from .mrg_gtk_expander import MrgGtkExpander
from .mrg_gtk_frame import MrgGtkFrame
from .mrg_gtk_grid import MrgGtkGrid
from .mrg_gtk_label import MrgGtkLabel
from .mrg_gtk_list_box import MrgGtkListBox
from .mrg_gtk_list_box_row import MrgGtkListBoxRow
from .mrg_gtk_overlay import MrgGtkOverlay
from .mrg_gtk_paned import MrgGtkPaned
from .mrg_gtk_revealer import MrgGtkRevealer
from .mrg_gtk_scrolled_window import MrgGtkScrolledWindow
from .mrg_gtk_stack import MrgGtkStack
from .mrg_gtk_viewport import MrgGtkViewport
from .mrg_gtk_widget import MrgGtkWidget
from .mrg_gtk_window import MrgGtkWindow
from .mrg_selection import MrgSelection
