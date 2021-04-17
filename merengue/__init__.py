# Merengue Application
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os

from .config import *
from gi.repository import Gio
resource = Gio.Resource.load(os.path.join(pkgdatadir, 'merengue.gresource'))
resource._register()

from .cmb_merengue import merengue_init
