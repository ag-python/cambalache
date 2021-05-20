pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), 'cambalacheui')
moduledir = join_paths(get_option('prefix'), python_bin.get_install_dir(), 'cambalacheui')

gnome.compile_resources('cambalacheui',
  'cambalacheui.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

conf = configuration_data()
conf.set('VERSION', meson.project_version())
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'config.py.in',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: moduledir
)

run_command('python3', '-m', 'compileall', '-b', '.')

install_data([
    'cmb_base.pyc',
    'cmb_objects_base.pyc',
    'cmb_tree_view.pyc',
    'cmb_list_store.pyc',
    'cmb_ui.pyc',
    'cmb_property.pyc',
    'cmb_layout_property.pyc',
    'cmb_type_info.pyc',
    'cmb_object.pyc',
    'cmb_view.pyc',
    'cmb_object_editor.pyc',
    'cmb_project.pyc',
    'cmb_signal_editor.pyc',
    '__init__.pyc'
    ],
    install_dir: moduledir)

