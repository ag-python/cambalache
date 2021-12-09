project(
    'cambalache',
    version: '0.8.0',
    meson_version: '>= 0.50.0'
)

python = import('python')
python_bin = python.find_installation('python3')
pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), 'cambalache')
catalogsdir = join_paths(pkgdatadir, 'catalogs')
localedir = join_paths(get_option('prefix'), get_option('localedir'))
gnome = import('gnome')

i18n = import('i18n')


# Python requirements ['module', 'version', 'gi required version]
modules = [
    ['lxml', '>= 4.5.0'],
    ['gi', '>= 3.38.0'],
    ['gi.repository.GLib', '>= 2.66.0'],
    ['gi.repository.Gtk', '>= 3.24.0', '3.0'],
    ['gi.repository.Gtk', '>= 4.0.0', '4.0'],
    ['gi.repository.WebKit2', '>= 2.32.0', '4.0'],
]

# Python script to check for gi repository module
gi_check_py = '''
import gi
if @1@:
  gi.require_version('@0@', '@1@')
from gi.repository import @0@
if hasattr(@0@, "MAJOR_VERSION"):
  print("{}.{}.{}".format(@0@.MAJOR_VERSION, @0@.MINOR_VERSION, @0@.MICRO_VERSION))
'''

all_required = true

foreach mod_ver: modules
    mod = mod_ver[0]
    version = (mod_ver.length() > 1) ? mod_ver[1] : ''
    gi_req = (mod_ver.length() > 2) ? mod_ver[2] : 'None'

    if mod.startswith('gi.repository.')
        mod = mod.split('.')[2]
        m = run_command('python3', '-c', gi_check_py.format(mod, gi_req))
    else
        m = run_command('python3', '-c', 'import @0@\nprint(@0@.__version__)'.format(mod))
    endif

    ver = m.stdout().strip()
    found = m.returncode() == 0 and ver.version_compare(version)
    found_msg = found ? '\u001b[32mYES\u001b[0m' : '\u001b[31mNO\u001b[0m'

    message('Python module \u001b[1m@0@\u001b[0m @1@ found: @2@ @3@'.format(mod, version, found_msg, ver))

    if all_required
        all_required = found
    endif
endforeach

assert(all_required, 'One or more required modules where not found')

# Broadway is needed to display the workspace in CmbView
find_program('broadwayd', required: true)
find_program('gtk4-broadwayd', required: true)


subdir('data')
subdir('cambalache')
subdir('plugins')
subdir('po')

meson.add_install_script('postinstall.py')

test('Running PyTest',
     python_bin, args : ['-m', 'pytest'],
     workdir: meson.current_source_dir())

