# Cambalache Application
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os

from cambalache import config
from gi.repository import Gio
resource = Gio.Resource.load(os.path.join(config.pkgdatadir, 'app.gresource'))
resource._register()

from .cmb_application import CmbApplication


