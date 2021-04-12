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

all: ../cambalache/gobject-2.0.sql ../cambalache/gtk+-3.0.sql ../cambalache/gtk-4.0.sql

../cambalache/gobject-2.0.sql: CmbUtils-0.1.typelib
	${CAMBALACHE_DB} /usr/share/gir-1.0/GObject-2.0.gir ../cambalache/gobject-2.0.sql

../cambalache/gtk+-3.0.sql: CmbUtils-0.1.typelib
	${CAMBALACHE_DB} /usr/share/gir-1.0/Gtk-3.0.gir ../cambalache/gtk+-3.0.sql && true

../cambalache/gtk-4.0.sql: CmbUtils-0.1.typelib
	${CAMBALACHE_DB} /usr/share/gir-1.0/Gtk-4.0.gir ../cambalache/gtk-4.0.sql

CmbUtils-0.1.typelib: CmbUtils-0.1.gir
	g-ir-compiler CmbUtils-0.1.gir --output=CmbUtils-0.1.typelib

libcmbutils.so: utils/utils.h utils/utils.c
	cc -c -fpic -Wall `pkg-config gobject-2.0 --cflags` -Iutils utils/utils.c -o utils.o
	cc -shared -o libcmbutils.so utils.o `pkg-config gobject-2.0 --libs`
	rm utils.o

CmbUtils-0.1.gir: libcmbutils.so
	g-ir-scanner -i GObject-2.0 -n CmbUtils --nsversion=0.1 --identifier-prefix=cmb_utils --library=cmbutils --symbol-prefix=cmb_utils utils/*.c utils/*.h --warn-all -o CmbUtils-0.1.gir

.PHONY: all clean

clean:
	rm -f libcmbutils.so CmbUtils-0.1.gir CmbUtils-0.1.typelib
