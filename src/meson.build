pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), 'cambalache')
moduledir = join_paths(pkgdatadir, 'cambalache')

gnome.compile_resources('cambalache',
  'cambalache.gresource.xml',
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

configure_file(
  input: 'config.py.in',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: moduledir
)

run_command('python3', '-m', 'compileall', '-b', '.')

install_data([
    '__init__.pyc',
    'cmb_application.pyc',
    'cmb_window.pyc'
    ],
    install_dir: moduledir)


