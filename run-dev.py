#!/usr/bin/python3
#
# Cambalache UI Maker developer mode
#
# Copyright (C) 2021  Juan Pablo Ugarte
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Authors:
#   Juan Pablo Ugarte <juanpablougarte@gmail.com>
#

import os
import sys
import stat
import signal
import locale

# Set GSchema dir before loading GLib
os.environ['GSETTINGS_SCHEMA_DIR'] = 'data'
os.environ['XDG_DATA_DIRS'] = os.getenv('XDG_DATA_DIRS',
                                        '/usr/local/share/:/usr/share/') + ':data'

import xml.etree.ElementTree as ET
from gi.repository import GLib

basedir = os.path.dirname(__file__)
sys.path.insert(1, basedir)

privatedir = os.path.join(basedir, '.lib')
os.environ['GI_TYPELIB_PATH'] = privatedir
os.environ['LD_LIBRARY_PATH'] = privatedir

glib_compile_resources = GLib.find_program_in_path ('glib-compile-resources')
glib_compile_schemas = GLib.find_program_in_path ('glib-compile-schemas')
update_mime_database = GLib.find_program_in_path ('update-mime-database')
msgfmt = GLib.find_program_in_path ('msgfmt')

signal.signal(signal.SIGINT, signal.SIG_DFL)

def dev_config(filename, content):
    meson_mtime = os.path.getmtime(os.path.join(basedir, 'meson.build'))

    abspath = os.path.join(basedir, filename)
    if not os.path.exists(abspath) or meson_mtime > os.path.getmtime(abspath):
        with open(abspath, 'w') as fd:
            fd.write(content)

def get_resource_mtime(filename):
    max_mtime = os.path.getmtime (filename)
    dirname = os.path.dirname(filename)

    tree = ET.parse(filename)
    root = tree.getroot()

    for gresource in root:
        for file in gresource.findall('file'):
            mtime = os.path.getmtime (os.path.join(dirname, file.text))
            if mtime > max_mtime:
                max_mtime = mtime

    return max_mtime

def compile_resource(sourcedir, resource, resource_xml):
    if glib_compile_resources is None:
        return

    if not os.path.exists(resource) or \
       os.path.getmtime (resource) < get_resource_mtime(resource_xml):
        print('glib-compile-resources', resource)
        GLib.spawn_sync('.',
                        [glib_compile_resources, f'--sourcedir={sourcedir}', f'--target={resource}', resource_xml],
                        None,
                        GLib.SpawnFlags.DEFAULT,
                        None,
                        None)

def compile_schemas(schema_xml):
    if glib_compile_schemas is None:
        return

    schemadir = os.path.dirname(schema_xml)
    schema = os.path.join(schemadir, 'gschemas.compiled')

    if not os.path.exists(schema) or \
       os.path.getmtime (schema) < os.path.getmtime (schema_xml):
        print('glib-compile-schemas', schema)
        GLib.spawn_sync('.',
                        [glib_compile_schemas, schemadir],
                        None,
                        GLib.SpawnFlags.DEFAULT,
                        None,
                        None)

def update_mime(mime_xml):
    if update_mime_database is None:
        return

    dirname = os.path.dirname(mime_xml)
    basename = os.path.basename(mime_xml)

    mimedir = os.path.join(dirname, 'mime')
    packagesdir = os.path.join(mimedir, 'packages')
    mimefile = os.path.join(packagesdir, basename)
    mime = os.path.join(mimedir, 'mime.cache')

    if not os.path.exists(mimefile):
        GLib.mkdir_with_parents(packagesdir, 0o700)
        os.symlink(os.path.join('..', '..', basename), mimefile)

    if not os.path.exists(mime) or \
       os.path.getmtime (mime) < os.path.getmtime (mime_xml):
        print('update-mime-database', mimedir)
        GLib.spawn_sync('.',
                        [update_mime_database, mimedir],
                        None,
                        GLib.SpawnFlags.DEFAULT,
                        None,
                        None)

def configure_file(input_file, output_file, config):
    with open(input_file, 'r') as fd:
        content = fd.read()

        for key in config:
            content = content.replace(f'@{key}@', config[key])

        with open(output_file, 'w') as outfd:
            outfd.write(content)

def create_catalogs_dir():
    def link_plugin(filename):
        basename = os.path.basename(filename)
        link = os.path.join('.catalogs', basename)
        if not os.path.islink(link):
            print(f'Setting up {basename} catalog link')
            os.symlink(os.path.abspath(filename), os.path.abspath(link))

    if not os.path.exists('.catalogs'):
        GLib.mkdir_with_parents('.catalogs', 0o700)

    link_plugin('plugins/glib/gobject-2.0.xml')
    link_plugin('plugins/glib/gio-2.0.xml')
    link_plugin('plugins/gdkpixbuf/gdkpixbuf-2.0.xml')
    link_plugin('plugins/pango/pango-1.0.xml')
    link_plugin('plugins/gtk/gdk-3.0.xml')
    link_plugin('plugins/gtk/gdk-4.0.xml')
    link_plugin('plugins/gtk/gsk-4.0.xml')
    link_plugin('plugins/gtk/gtk-4.0.xml')
    link_plugin('plugins/gtk/gtk+-3.0.xml')
    link_plugin('plugins/gnome/libhandy-1.xml')

def get_version():
    meson = open(os.path.join(basedir, 'meson.build'))

    for line in meson:
        line = line.strip()
        if line.startswith('version'):
            tokens = line.split(':')
            return tokens[1].strip().replace('\'', '').replace(',', '')

    meson.close()

    return 'git'


def check_init_locale():
    localedir = os.path.join(basedir, 'po', '.lc_messages')

    if not os.path.exists(localedir):
        GLib.mkdir_with_parents(localedir, 0o700)

    linguas = open(os.path.join(basedir, 'po', 'LINGUAS'))

    for lang in linguas:
        lang = lang.strip()
        po_file = os.path.join(basedir, 'po', f'{lang}.po')
        mo_dir = os.path.join(basedir, 'po', '.lc_messages', lang, 'LC_MESSAGES')
        mo_file = os.path.join(mo_dir, 'cambalache.mo')

        if not os.path.exists(mo_dir):
            GLib.mkdir_with_parents(mo_dir, 0o700)

        if not os.path.exists(mo_file) or os.path.getmtime (mo_file) < os.path.getmtime (po_file):
            print('msgfmt', po_file, mo_file)
            GLib.spawn_sync('.',
                            [msgfmt, po_file, '-o', mo_file],
                            None,
                            GLib.SpawnFlags.DEFAULT,
                            None,
                            None)

    locale.bindtextdomain("cambalache", localedir)
    locale.textdomain("cambalache")


def compile_private():
    srcdir = os.path.join(basedir, 'cambalache', 'private')

    for prog in ['cc', 'pkg-config', 'g-ir-compiler', 'g-ir-scanner']:
        if GLib.find_program_in_path (prog) is None:
            print(f'{prog} is needed to compile Cambalache private library')
            return

    if not os.path.exists(privatedir):
        GLib.mkdir_with_parents(privatedir, 0o700)

    for v, pkg in [('3', 'gtk+-3.0'), ('4', 'gtk4')]:
        srcfile = f'{srcdir}/cmb_private.c'
        typelib = f'{privatedir}/CambalachePrivate-{v}.0.typelib'

        if os.path.exists(typelib) and os.path.getmtime (srcfile) < os.path.getmtime (typelib):
            continue

        os.system(f'cc -c -fpic -Wall `pkg-config {pkg} --cflags` -I{srcdir} {srcfile} -o {privatedir}/cmb_private.o')
        os.system(f'cc -shared -o {privatedir}/libcambalacheprivate-{v}.so {privatedir}/cmb_private.o `pkg-config {pkg} --libs`')
        os.system(f'g-ir-scanner -i Gtk-{v}.0 -n CambalachePrivate --nsversion={v}.0 \
                   --identifier-prefix=cmb_private -L {privatedir} -l cambalacheprivate-{v} --symbol-prefix=cmb_private \
                   {srcdir}/*.c {srcdir}/*.h --warn-all -o {privatedir}/CambalachePrivate-{v}.0.gir')
        os.system(f'g-ir-compiler {privatedir}/CambalachePrivate-{v}.0.gir --output={typelib}')


if __name__ == '__main__':
    if glib_compile_resources is None:
        print('Could not find glib-compile-resources in PATH')
        exit()

    version = get_version()

    check_init_locale()

    # Create config files pointing to source directories
    dev_config('cambalache/config.py',
               f"VERSION = '{version}'\npkgdatadir = '{os.path.abspath('cambalache')}'\nmerenguedir = '{os.path.abspath('cambalache')}'\ncatalogsdir = '{os.path.abspath('.catalogs')}'")

    # Create config files pointing to source directories
    dev_config('cambalache/merengue/config.py',
               f"VERSION = '{version}'\npkgdatadir = '{os.path.abspath('cambalache')}'\nmerenguedir = '{os.path.abspath('cambalache')}'")

    # Create merengue bin script
    configure_file('cambalache/merengue/merengue.in', 'cambalache/merengue/merengue', {
        'PYTHON': GLib.find_program_in_path('python3'),
        'merenguedir': os.path.abspath('cambalache')
    })
    os.chmod('cambalache/merengue/merengue', stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)

    # Ensure gresources are up to date
    compile_resource('cambalache', 'cambalache/cambalache.gresource', 'cambalache/cambalache.gresource.xml')
    compile_resource('cambalache/merengue', 'cambalache/merengue.gresource', 'cambalache/merengue/merengue.gresource.xml')
    compile_resource('cambalache/app', 'cambalache/app.gresource', 'cambalache/app/app.gresource.xml')

    compile_schemas('data/ar.xjuan.Cambalache.gschema.xml')
    update_mime('data/ar.xjuan.Cambalache.mime.xml')

    create_catalogs_dir()

    compile_private()

    # Run Application
    from cambalache.app import CmbApplication
    app = CmbApplication()
    app.run(sys.argv)
