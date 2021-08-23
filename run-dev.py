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

# Set GSchema dir before loading GLib
os.environ['GSETTINGS_SCHEMA_DIR'] = 'data'
os.environ['XDG_DATA_DIRS'] = os.environ['XDG_DATA_DIRS'] + ':data'

import xml.etree.ElementTree as ET
from gi.repository import GLib

basedir = os.path.dirname(__file__)
sys.path.insert(1, basedir)

glib_compile_resources = GLib.find_program_in_path ('glib-compile-resources')
glib_compile_schemas = GLib.find_program_in_path ('glib-compile-schemas')
update_mime_database = GLib.find_program_in_path ('update-mime-database')

signal.signal(signal.SIGINT, signal.SIG_DFL)

def dev_config(filename, content):
    abspath = os.path.join(basedir, filename)
    if not os.path.exists(abspath):
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

if __name__ == '__main__':
    if glib_compile_resources is None:
        print('Could not find glib-compile-resources in PATH')
        exit()

    # Create config files pointing to source directories
    dev_config('cambalache/config.py',
               f"VERSION = 'git'\npkgdatadir = '{os.path.abspath('cambalache')}'\nmerenguedir = '{os.path.abspath('cambalache')}'")

    # Create config files pointing to source directories
    dev_config('cambalache/merengue/config.py',
               f"VERSION = 'git'\npkgdatadir = '{os.path.abspath('cambalache')}'\nmerenguedir = '{os.path.abspath('cambalache')}'")

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

    # Run Application
    from cambalache.app import CmbApplication
    app = CmbApplication()
    app.run(sys.argv)
