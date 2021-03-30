#!/bin/bash

# flatpak run --device=all --runtime=org.gnome.Sdk//40 --devel --filesystem=host --command=tools/update_type_data.sh ar.xjuan.Cambalache

echo GObject ...
python3 tools/cambalache-db.py /usr/share/gir-1.0/GObject-2.0.gir cambalache/gobject-2.0.sql

echo Gtk 3 ...
python3 tools/cambalache-db.py /usr/share/gir-1.0/Gtk-3.0.gir cambalache/gtk+-3.0.sql

echo Gtk 4 ...
python3 tools/cambalache-db.py /usr/share/gir-1.0/Gtk-4.0.gir cambalache/gtk-4.0.sql
