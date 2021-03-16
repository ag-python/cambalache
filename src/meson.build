gnome.compile_resources('cambalache_app',
  'cambalache_app.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

appdir = join_paths(moduledir, 'app')

conf = configuration_data()
conf.set('VERSION', meson.project_version())
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('pythondir', python_dir)
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'ar.xjuan.Cambalache.in',
  output: 'ar.xjuan.Cambalache',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

configure_file(
  input: 'config.py.in',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: appdir
)

run_command('python3', '-m', 'compileall', '-b', '.')

install_data([
    '__init__.pyc',
    'cmb_application.pyc',
    'cmb_window.pyc'
    ],
    install_dir: appdir)


