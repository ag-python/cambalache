# Merengue Application
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
import logging

from . import config
from gi.repository import Gio
resource = Gio.Resource.load(os.path.join(config.pkgdatadir, 'merengue.gresource'))
resource._register()

def getLogger(name):
    formatter = logging.Formatter('%(levelname)s:%(name)s %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('MERENGUE_LOGLEVEL', 'WARNING').upper())
    logger.addHandler(ch)

    return logger

from .mrg_placeholder import MrgPlaceholder
from .mrg_application import MrgApplication
