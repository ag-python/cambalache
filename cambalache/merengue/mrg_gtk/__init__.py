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

from .mrg_gtk_aspect_frame import MrgGtkAspectFrameController

if Gtk.MAJOR_VERSION == 3:
    from .mrg_gtk_bin import MrgGtkBinController

from .mrg_gtk_box import MrgGtkBoxController
from .mrg_gtk_expander import MrgGtkExpanderController
from .mrg_gtk_frame import MrgGtkFrameController
from .mrg_gtk_grid import MrgGtkGridController
from .mrg_gtk_label import MrgGtkLabelController
from .mrg_gtk_list_box import MrgGtkListBoxController
from .mrg_gtk_list_box_row import MrgGtkListBoxRowController
from .mrg_gtk_overlay import MrgGtkOverlayController
from .mrg_gtk_paned import MrgGtkPanedController
from .mrg_gtk_revealer import MrgGtkRevealerController
from .mrg_gtk_scrolled_window import MrgGtkScrolledWindowController
from .mrg_gtk_viewport import MrgGtkViewportController
from .mrg_gtk_widget import MrgGtkWidgetController
from .mrg_gtk_window import MrgGtkWindowController
from .mrg_selection import MrgSelection
