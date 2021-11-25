#
# CmbContextMenu - Cambalache UI Editor
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

gi.require_version('Gtk', '3.0')
from gi.repository import GObject, GLib, Gdk, Gtk


@Gtk.Template(resource_path='/ar/xjuan/Cambalache/cmb_context_menu.ui')
class CmbContextMenu(Gtk.PopoverMenu):
    __gtype_name__ = 'CmbContextMenu'

    gtk_theme = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)
    target_tk = GObject.Property(type=str, flags = GObject.ParamFlags.READWRITE)

    main_box = Gtk.Template.Child()
    separator = Gtk.Template.Child()
    css_theme = Gtk.Template.Child()
    css_theme_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect('notify::target-tk', lambda o, p: self.__populate_css_theme_box())

    def __on_css_theme_button_toggled(self, button, data):
        if button.props.active:
            self.gtk_theme = data

    def __populate_css_theme_box(self):
        gtk_path = 'gtk-3.0'

        if self.target_tk in [None, '']:
            return

        if self.target_tk == 'gtk-4.0':
            gtk_path = 'gtk-4.0'

        for child in self.css_theme_box.get_children():
            self.css_theme_box.remove(child)

        dirs = []

        dirs += GLib.get_system_data_dirs()
        dirs.append(GLib.get_user_data_dir())

        # Add /themes to every dir
        dirs = list(map(lambda d: os.path.join(d, 'themes'), dirs))

        # Append ~/.themes
        dirs.append(os.path.join(GLib.get_home_dir(), '.themes'))

        # Default themes
        themes = ['Adwaita', 'HighContrast', 'HighContrastInverse']

        for path in dirs:
            if not os.path.isdir(path):
                continue

            for theme in os.listdir(path):
                tpath = os.path.join(path, theme, gtk_path, 'gtk.css')
                if os.path.exists(tpath):
                    themes.append(theme)

        # Dedup and sort
        themes = list(dict.fromkeys(themes))

        # Add back item
        button = Gtk.ModelButton(text=_('CSS themes'),
                                 menu_name='main',
                                 inverted=True,
                                 centered=True,
                                 visible=True)
        self.css_theme_box.add(button)

        group = None
        for theme in sorted(themes):
            button = Gtk.RadioButton(label=theme,
                                     group=group,
                                     active=self.gtk_theme == theme,
                                     visible=True)
            if group is None:
                group = button

            button.connect('toggled', self.__on_css_theme_button_toggled, theme)
            self.css_theme_box.add(button)

        self.separator.props.visible = self.css_theme.props.visible = len(themes) > 0

    def popup_at(self, x, y):
        r = Gdk.Rectangle()
        r.x, r.y, r.width, r.height = (x, y, 10, 10)
        self.set_pointing_to(r)
        self.popup()
