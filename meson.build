project(
    'cambalache',
    version: '0.5.91',
    meson_version: '>= 0.50.0'
)

python = import('python')
python_bin = python.find_installation('python3')
localedir = join_paths(get_option('prefix'), get_option('localedir'))
gnome = import('gnome')

i18n = import('i18n')

subdir('data')
subdir('cambalacheui')
subdir('merengue')
subdir('src')
subdir('po')

meson.add_install_script('postinstall.py')
