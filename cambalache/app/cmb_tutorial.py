#
# CmbTutorial
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

from gettext import gettext as _
from .cmb_tutor import CmbTutorPosition

intro = [
    (_('Hi, I will show you around Cambalache'),
     'intro_button', 5),

    (_('You can open a project'),  'open_button', 3),
    (_('find recently used'), 'recent_button', 2,),
    (_('or create a new one'), 'new_button', 4),

    (_('Common actions like Undo'), 'undo_button', 4),
    (_('Redo'), 'redo_button', 2),
    (_('Add new UI file'), 'add_button', 3),
    (_('and Save are directly accessible in the headerbar'), 'save_button', 6),
    (_('just like Save As'), 'save_as_button', 2),
    (_('and the main menu'), 'menu_button', 3),

    (_('Create a project to continue'), 'intro_button', 2, 'add-project'),
    (_('Great!'), 'intro_button', 2),

    (_('This is the project workspace, where you can see and select the widgets to edit'),
     'view', 6, None, CmbTutorPosition.CENTER),
    (_('Project tree, with multiple UI support'),
     'tree_view', 4, None, CmbTutorPosition.CENTER),

    (_('Class selector'), 'type_entry', 3),
    (_('And the object editor'),
      'object_editor', 3, None, CmbTutorPosition.CENTER),

    (_('Now let\'s add a new UI file'), 'add_button', 5, 'add-ui'),

    (_('Good, now try to create a window'), 'intro_button', 4),
    (_('Make sure a UI is selected, type \'GtkWindow\' and press enter'),
      'type_entry', 6, 'add-window'),

    (_('Excelent!'), 'intro_button', 2),

    (_('Once you finish, you can export all UI files to xml here'),
      'export_all', 5, 'main-menu', CmbTutorPosition.LEFT),
    (_('That is all for now.\nIf you find Cambalache usefull please consider donating'),
      'donate', 7, 'donate', CmbTutorPosition.LEFT),
    (_('Have a nice day!'), 'intro_button', 3, 'intro-end'),
]
