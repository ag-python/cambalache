datadir = get_option('datadir')

install_data('ar.xjuan.Cambalache.svg',
  install_dir: join_paths(datadir, 'icons', 'hicolor', 'scalable', 'apps')
)

install_data('ar.xjuan.Cambalache-symbolic.svg',
  install_dir: join_paths(datadir, 'icons', 'hicolor', 'symbolic', 'apps')
)

install_data('ar.xjuan.Cambalache.mime.svg',
  install_dir: join_paths(datadir, 'icons', 'hicolor', 'scalable', 'mimetypes')
)

install_data('ar.xjuan.Cambalache.mime.xml',
    install_dir: join_paths(datadir, 'mime', 'packages')
)

desktop_file = i18n.merge_file(
  input: 'ar.xjuan.Cambalache.desktop.in',
  output: 'ar.xjuan.Cambalache.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(datadir, 'applications')
)

appstream_file = i18n.merge_file(
  input: 'ar.xjuan.Cambalache.metainfo.xml.in',
  output: 'ar.xjuan.Cambalache.metainfo.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(datadir, 'metainfo')
)

desktop_file_validate = find_program('desktop-file-validate', required: false)
if desktop_file_validate.found()
  test('Validating desktop file', desktop_file_validate, args: [desktop_file])
endif

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validating appstream file',
       appstream_util,
       args: ['validate', appstream_file])
endif

install_data('ar.xjuan.Cambalache.gschema.xml',
  install_dir: join_paths(datadir, 'glib-2.0', 'schemas')
)
