
sources = [
  'cmb_private.c',
]

headers = [
  'cmb_private.h',
]

# Build private library against Gtk 3 and 4
foreach d : [['3', gtk3_dep], ['4', gtk4_dep]]
  ver = d[0]
  dep = d[1]
  libcmbprivate = shared_library('cambalacheprivate-@0@'.format(ver),
    sources,
    dependencies: dep,
    install: true,
  )

  gnome.generate_gir(
    libcmbprivate,
    sources: sources + headers,
    includes: 'Gtk-@0@.0'.format(ver),
    nsversion: '@0@.0'.format(ver),
    namespace: 'CambalachePrivate',
    identifier_prefix: 'CmbPrivate',
    symbol_prefix: 'cmb_private',
    header: 'cmb_private.h',
    install: true,
  )
endforeach
