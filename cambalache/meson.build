moduledir = join_paths(get_option('prefix'), python_bin.get_install_dir(), 'cambalache')
merenguedir = join_paths(moduledir, 'priv')

gnome.compile_resources('cambalache',
  'cambalache.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

conf = configuration_data()
conf.set('VERSION', meson.project_version())
conf.set('pkgdatadir', pkgdatadir)
conf.set('catalogsdir', catalogsdir)
conf.set('merenguedir', merenguedir)

configure_file(
  input: 'config.py.in',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: moduledir
)

install_data([
    'cmb_base.py',
    'cmb_db.py',
    'cmb_objects_base.py',
    'cmb_tree_view.py',
    'cmb_list_store.py',
    'cmb_ui.py',
    'cmb_property.py',
    'cmb_property_controls.py',
    'cmb_layout_property.py',
    'cmb_type_info.py',
    'cmb_object.py',
    'cmb_view.py',
    'cmb_object_editor.py',
    'cmb_project.py',
    'cmb_signal_editor.py',
    '__init__.py'
    ],
    install_dir: moduledir)

subdir('merengue')
subdir('app')
