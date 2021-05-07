project(
    'cambalache',
    version: '0.5.91',
    meson_version: '>= 0.50.0'
)

python = import('python')
python_bin = python.find_installation('python3')
python_dir = join_paths(get_option('prefix'), python_bin.get_install_dir())

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(python_dir, meson.project_name())
gnome = import('gnome')

subdir('cambalache')
subdir('merengue')
subdir('src')

