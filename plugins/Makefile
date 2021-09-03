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

CATALOG_FILES = \
	gobject/gobject-2.0.xml \
	gtk/gtk-4.0.xml \
	gtk/gtk+-3.0.xml

all: ${CATALOG_FILES}

gobject/gobject-2.0.xml:
	${CAMBALACHE_DB} \
		--gir /usr/share/gir-1.0/GObject-2.0.gir \
		--types GObject GBinding GBindingFlags \
		--skip-types GBinding \
		--output $@

gtk/gtk+-3.0.xml: gtk/Gtk.xml
	${CAMBALACHE_DB} \
		--dependencies gobject-2.0 \
		--gir /usr/share/gir-1.0/Gtk-3.0.gir \
		--extra-data gtk/Gtk.xml \
		--output $@

gtk/gtk-4.0.xml: gtk/Gtk.xml
	${CAMBALACHE_DB} \
		--target-gtk4 \
		--dependencies gobject-2.0 \
		--gir /usr/share/gir-1.0/Gtk-4.0.gir \
		--extra-data gtk/Gtk.xml \
		--skip-types GtkActivateAction GtkMnemonicAction GtkNamedAction GtkNeverTrigger GtkNothingAction GtkSignalAction GtkPrintJob \
		--output $@ && true

.PHONY: all clean

clean:
	rm ${CATALOG_FILES}

