pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), 'cambalache')
moduledir = join_paths(merenguedir, 'merengue')

gnome.compile_resources('merengue',
  'merengue.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

conf = configuration_data()
conf.set('VERSION', meson.project_version())
conf.set('PYTHON', python_bin.path())
conf.set('pkgdatadir', pkgdatadir)
conf.set('merenguedir', merenguedir)

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
  install_dir: moduledir
)

install_data([
  'mrg_application.py',
  '__init__.py',
  ],
  install_dir: moduledir
)

install_data([
  'controller/__init__.py',
  'controller/mrg_controller.py',
  'controller/mrg_controller_registry.py',
  ],
  install_dir: join_paths(moduledir, 'controller')
)

install_data([
  'mrg_gtk/__init__.py',
  'mrg_gtk/mrg_selection.py',
  'mrg_gtk/mrg_gtk_widget.py',
  'mrg_gtk/mrg_gtk_window.py',
  ],
  install_dir: join_paths(moduledir, 'mrg_gtk')
)

install_data([
  'utils/__init__.py',
  'utils/utils.py',
  ],
  install_dir: join_paths(moduledir, 'utils')
)

