# Cambalache

Cambalache is a new RAD tool for Gtk 4 and 3 with a clear MVC design and data model first philosophy.
This translates to a wide feature coverage with minimal/none developer intervention for basic support.

![Data Model Diagram](datamodel.svg)

To support multiple Gtk versions it renders the workspace out of process using
the Gdk broadway backend.

![Merengue Diagram](merengue.svg)

## License

Cambalache is distributed under the [GNU Lesser General Public License](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html),
version 2.1 (LGPL) as described in the COPYING file.

Tools are distributed under the [GNU General Public License](https://www.gnu.org/licenses/gpl-2.0.en.html),
version 2 (GPL) as described in the COPYING.GPL file.

## Source code

Source code lives on GNOME gitlab at [gitlab](https://gitlab.gnome.org/jpu/cambalache)

`git clone https://gitlab.gnome.org/jpu/cambalache.git`

## Running from sources

To run it without installing use run-dev.py script, it will automatically compile
resources and create extra files needed to run.

`./run-dev.py`

## Flatpak

The preferred way to run Cambalache is using flatpak.
You can find prebuilt bundles in [gitlab pkgs](https://gitlab.gnome.org/jpu/cambalache/-/packages)

Or build your own with the following commands
```
flatpak-builder --force-clean --repo=repo build ar.xjuan.Cambalache.json
flatpak build-bundle repo cambalache.flatpak ar.xjuan.Cambalache
flatpak install --user cambalache.flatpak
```

## Tools

 - cambalache-db:
   Generate Data Model from Gir files

 - db-codegen:
   Generate GObject classes from DB tables
