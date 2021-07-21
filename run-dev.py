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

import xml.etree.ElementTree as ET
from gi.repository import GLib

basedir = os.path.dirname(__file__)
sys.path.insert(1, basedir)

os.environ['PATH'] = os.path.join(basedir, 'merengue') + ':' + os.environ.get('PATH')

glib_compile_resources = GLib.find_program_in_path ('glib-compile-resources')

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

def compile_resource(dirname, filename):
    if glib_compile_resources is None:
        return

    filename_xml = f'{filename}.xml'
    resource = os.path.join(basedir, dirname, filename)
    resource_xml = os.path.join(basedir, dirname, filename_xml)

    if not os.path.exists(resource) or \
       os.path.getmtime (resource) < get_resource_mtime(resource_xml):
        print('glib-compile-resources', dirname, filename_xml)
        GLib.spawn_sync(dirname,
                        [glib_compile_resources, filename_xml],
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
    dev_config('cambalacheui/config.py',
               f"VERSION = 'git'\npkgdatadir = '{os.path.abspath('cambalacheui')}'")
    dev_config('merengue/config.py',
               f"VERSION = 'git'\npkgdatadir = '{os.path.abspath('merengue')}'")
    dev_config('src/config.py',
               f"VERSION = 'git'\npkgdatadir = '{os.path.abspath('src')}'")

    # Create merengue bin script
    configure_file('merengue/merengue.in', 'merengue/merengue', {
        'PYTHON': GLib.find_program_in_path('python3'),
        'pkgdatadir': os.path.abspath('.')
    })
    os.chmod('merengue/merengue', stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)

    # Ensure gresources are up to date
    compile_resource('cambalacheui', 'cambalacheui.gresource')
    compile_resource('merengue', 'merengue.gresource')
    compile_resource('src', 'cambalache.gresource')

    # Run Application
    from src import CmbApplication
    app = CmbApplication()
    app.run(sys.argv)
