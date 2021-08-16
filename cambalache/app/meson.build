pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), 'cambalache')
moduledir = join_paths(get_option('prefix'), python_bin.get_install_dir(), 'cambalache', 'app')

gnome.compile_resources('app',
  'app.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

conf = configuration_data()
conf.set('VERSION', meson.project_version())
conf.set('PYTHON', python_bin.path())
conf.set('localedir', localedir)
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'cambalache.in',
  output: 'cambalache',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

install_data([
    '__init__.py',
    'cmb_application.py',
    'cmb_window.py',
    'cmb_tutor.py',
    'cmb_tutorial.py',
    ],
    install_dir: moduledir)

