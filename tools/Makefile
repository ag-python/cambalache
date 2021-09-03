all: CmbUtils-3.0.typelib CmbUtils-4.0.typelib

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

.PHONY: all clean

clean:
	rm -f libcmbutils.so CmbUtils*.gir CmbUtils*.typelib


.SUFFIXES: .gir .typelib

.gir.typelib:
	g-ir-compiler $< --output=$@
