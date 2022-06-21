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
  'mrg_controller.py',
  'mrg_controller_registry.py',
  'mrg_css_provider.py',
  'mrg_placeholder.py',
  'utils.py',
  '__init__.py',
  ],
  install_dir: moduledir
)

install_data([
  'mrg_gtk/__init__.py',
  'mrg_gtk/mrg_g_binding.py',
  'mrg_gtk/mrg_gtk_aspect_frame.py',
  'mrg_gtk/mrg_gtk_assistant.py',
  'mrg_gtk/mrg_gtk_bin.py',
  'mrg_gtk/mrg_gtk_box.py',
  'mrg_gtk/mrg_gtk_center_box.py',
  'mrg_gtk/mrg_gtk_expander.py',
  'mrg_gtk/mrg_gtk_frame.py',
  'mrg_gtk/mrg_gtk_grid.py',
  'mrg_gtk/mrg_gtk_label.py',
  'mrg_gtk/mrg_gtk_list_box.py',
  'mrg_gtk/mrg_gtk_list_box_row.py',
  'mrg_gtk/mrg_gtk_menu.py',
  'mrg_gtk/mrg_gtk_menu_item.py',
  'mrg_gtk/mrg_gtk_notebook.py',
  'mrg_gtk/mrg_gtk_overlay.py',
  'mrg_gtk/mrg_gtk_paned.py',
  'mrg_gtk/mrg_gtk_popover.py',
  'mrg_gtk/mrg_gtk_revealer.py',
  'mrg_gtk/mrg_gtk_scrolled_window.py',
  'mrg_gtk/mrg_gtk_stack.py',
  'mrg_gtk/mrg_gtk_viewport.py',
  'mrg_gtk/mrg_gtk_widget.py',
  'mrg_gtk/mrg_gtk_window.py',
  'mrg_gtk/mrg_selection.py',
  ],
  install_dir: join_paths(moduledir, 'mrg_gtk')
)


install_data([
  'mrg_handy/__init__.py',
  'mrg_handy/mrg_container.py',
  'mrg_handy/mrg_hdy_deck.py',
  'mrg_handy/mrg_hdy_leaflet.py',
  'mrg_handy/mrg_hdy_search_bar.py',
  ],
  install_dir: join_paths(moduledir, 'mrg_handy')
)


install_data([
  'mrg_adw/__init__.py',
  'mrg_adw/mrg_adw_application_window.py',
  'mrg_adw/mrg_adw_bin.py',
  'mrg_adw/mrg_adw_carousel.py',
  'mrg_adw/mrg_adw_window.py',
  ],
  install_dir: join_paths(moduledir, 'mrg_adw')
)
