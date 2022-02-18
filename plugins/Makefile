CAMBALACHE_DB=flatpak run \
	--env=LD_LIBRARY_PATH=../tools \
	--env=GI_TYPELIB_PATH=../tools \
	--share=ipc \
	--socket=fallback-x11 \
	--socket=wayland \
	--device=all \
	--filesystem=host \
	--command=python3 \
	org.gnome.Sdk//40 \
	../tools/cambalache-db.py

BASE_CATALOG_FILES = \
	glib/gobject-2.0.xml \
	glib/gio-2.0.xml \
	gdkpixbuf/gdk-pixbuf-2.0.xml \
	pango/pango-1.0.xml \
	gtk/gdk-3.0.xml \
	gtk/gdk-4.0.xml \
	gtk/gsk-4.0.xml

CATALOG_FILES = \
	${BASE_CATALOG_FILES} \
	gtk/gtk-4.0.xml \
	gtk/gtk+-3.0.xml

all: ${CATALOG_FILES}

glib/gobject-2.0.xml:
	${CAMBALACHE_DB} \
		--gir /usr/share/gir-1.0/GObject-2.0.gir \
		--types GObject GBinding GBindingFlags \
		--boxed-types GStrv GBytes\
		--skip-types GBinding \
		--output $@

glib/gio-2.0.xml:
	${CAMBALACHE_DB} \
		--gir /usr/share/gir-1.0/Gio-2.0.gir \
		--types GFile \
		--exclude-objects \
		--output $@

gdkpixbuf/gdk-pixbuf-2.0.xml:
	${CAMBALACHE_DB} \
		--dependencies gobject-2.0 \
		--gir /usr/share/gir-1.0/GdkPixbuf-2.0.gir \
		--types GdkPixbuf \
		--exclude-objects \
		--output $@

pango/pango-1.0.xml:
	${CAMBALACHE_DB} \
		--dependencies gobject-2.0 \
		--gir /usr/share/gir-1.0/Pango-1.0.gir \
		--exclude-objects \
		--output $@

gtk/gdk-3.0.xml:
	${CAMBALACHE_DB} \
		--dependencies gdkpixbuf-2.0 \
		--gir /usr/share/gir-1.0/Gdk-3.0.gir \
		--boxed-types GdkColor GdkRGBA \
		--exclude-objects \
		--output $@

gtk/gdk-4.0.xml:
	${CAMBALACHE_DB} \
		--target-gtk4 \
		--dependencies gdkpixbuf-2.0 \
		--gir /usr/share/gir-1.0/Gdk-4.0.gir \
		--boxed-types GdkRGBA GdkContentFormats\
		--exclude-objects \
		--output $@

gtk/gsk-4.0.xml:
	${CAMBALACHE_DB} \
		--target-gtk4 \
		--dependencies gobject-2.0 \
		--gir /usr/share/gir-1.0/Gsk-4.0.gir \
		--boxed-types GskTransform \
		--exclude-objects \
		--output $@

gtk/gtk+-3.0.xml: gtk/Gtk.xml ${BASE_CATALOG_FILES}
	${CAMBALACHE_DB} \
		--dependencies gobject-2.0 \
		--gir /usr/share/gir-1.0/Gtk-3.0.gir \
		--external-catalogs ${BASE_CATALOG_FILES} \
		--extra-data gtk/Gtk.xml \
		--output $@

gtk/gtk-4.0.xml: gtk/Gtk.xml ${BASE_CATALOG_FILES}
	${CAMBALACHE_DB} \
		--target-gtk4 \
		--dependencies gobject-2.0 \
		--gir /usr/share/gir-1.0/Gtk-4.0.gir \
		--external-catalogs ${BASE_CATALOG_FILES} \
		--extra-data gtk/Gtk.xml \
		--skip-types GtkActivateAction GtkMnemonicAction GtkNamedAction GtkNeverTrigger GtkNothingAction GtkSignalAction GtkPrintJob \
		--output $@ && true

.PHONY: all clean

clean:
	rm -rf ${CATALOG_FILES}

