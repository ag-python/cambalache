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
    'cmb_context_menu.py',
    'cmb_css.py',
    'cmb_css_editor.py',
    'cmb_db.py',
    'cmb_db_migration.py',
    'cmb_fragment_editor.py',
    'cmb_layout_property.py',
    'cmb_library_info.py',
    'cmb_list_store.py',
    'cmb_object.py',
    'cmb_object_data.py',
    'cmb_object_editor.py',
    'cmb_objects_base.py',
    'cmb_project.py',
    'cmb_property.py',
    'cmb_property_controls.py',
    'cmb_signal_editor.py',
    'cmb_translatable_popover.py',
    'cmb_translatable_widget.py',
    'cmb_tree_view.py',
    'cmb_type_chooser.py',
    'cmb_type_chooser_popover.py',
    'cmb_type_chooser_widget.py',
    'cmb_type_info.py',
    'cmb_ui.py',
    'cmb_ui_editor.py',
    'cmb_view.py',
    'icon_naming_spec.py',
    '__init__.py'
    ],
    install_dir: moduledir)

subdir('private')
subdir('merengue')
subdir('app')
