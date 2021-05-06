moduledir = join_paths(python_dir, 'merengue')

gnome.compile_resources('merengue',
  'merengue.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

conf = configuration_data()
conf.set('VERSION', meson.project_version())
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('pythondir', python_dir)
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'config.py.in',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: moduledir
)

configure_file(
  input: 'merengue.in',
  output: 'merengue',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

run_command('python3', '-m', 'compileall', '-b', '.')

install_data([
  'mrg_application.pyc',
  'utils.pyc',
  '__init__.pyc',
  ],
  install_dir: moduledir
)
