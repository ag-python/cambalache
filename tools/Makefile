CAMBALACHE_DB=flatpak run \
	--env=LD_LIBRARY_PATH=. \
	--env=GI_TYPELIB_PATH=. \
	--share=ipc \
	--socket=fallback-x11 \
	--socket=wayland \
	--device=all \
	--filesystem=host \
	--command=python3 \
	org.gnome.Sdk//40 \
	cambalache-db.py

all: CmbUtils-3.0.typelib CmbUtils-4.0.typelib

update: ../cambalache/gobject-2.0.sql ../cambalache/gtk+-3.0.sql ../cambalache/gtk-4.0.sql

../cambalache/gobject-2.0.sql: CmbUtils-3.0.typelib
	${CAMBALACHE_DB} /usr/share/gir-1.0/GObject-2.0.gir ../cambalache/gobject-2.0.sql

../cambalache/gtk+-3.0.sql: CmbUtils-3.0.typelib
	${CAMBALACHE_DB} /usr/share/gir-1.0/Gtk-3.0.gir ../cambalache/gtk+-3.0.sql && true

../cambalache/gtk-4.0.sql: CmbUtils-4.0.typelib
	${CAMBALACHE_DB} /usr/share/gir-1.0/Gtk-4.0.gir ../cambalache/gtk-4.0.sql

libcmbutils3.so: utils/utils.h utils/utils.c
	cc -c -fpic -Wall `pkg-config gtk+-3.0 --cflags` -Iutils utils/utils.c -o utils.o
	cc -shared -o libcmbutils3.so utils.o `pkg-config gtk+-3.0 --libs`
	rm utils.o

libcmbutils4.so: utils/utils.h utils/utils.c
	cc -c -fpic -Wall `pkg-config gtk4 --cflags` -Iutils utils/utils.c -o utils.o
	cc -shared -o libcmbutils4.so utils.o `pkg-config gtk4 --libs`
	rm utils.o

CmbUtils-3.0.gir: libcmbutils3.so
	LD_LIBRARY_PATH=. \
	g-ir-scanner -i Gtk-3.0 -n CmbUtils --nsversion=3.0 --identifier-prefix=cmb_utils --library=cmbutils3 --symbol-prefix=cmb_utils utils/utils.c utils/utils.h --warn-all -o CmbUtils-3.0.gir

CmbUtils-4.0.gir: libcmbutils4.so
	LD_LIBRARY_PATH=. \
	g-ir-scanner -i Gtk-4.0 -n CmbUtils --nsversion=4.0 --identifier-prefix=cmb_utils --library=cmbutils4 --symbol-prefix=cmb_utils utils/utils.c utils/utils.h --warn-all -o CmbUtils-4.0.gir

.PHONY: all update clean

clean:
	rm -f libcmbutils.so CmbUtils*.gir CmbUtils*.typelib


.SUFFIXES: .gir .typelib

.gir.typelib:
	g-ir-compiler $< --output=$@
