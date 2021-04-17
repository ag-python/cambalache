#!/usr/bin/python3
#
# Cambalache UI Maker developer mode
#
# Copyright (C) 2021  Juan Pablo Ugarte - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited.
#

import os
import sys
import stat
import signal
import xml.etree.ElementTree as ET
from gi.repository import GLib

basedir = os.path.dirname(__file__)
sys.path.insert(0, basedir)

os.environ['PATH'] += os.environ.get('PATH') + ':' + os.path.join(basedir, 'merengue')

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
    filename_xml = f'{filename}.xml'
    resource = os.path.join(basedir, dirname, filename)
    resource_xml = os.path.join(basedir, dirname, filename_xml)

    if not os.path.exists(resource) or \
       os.path.getmtime (resource) < get_resource_mtime(resource_xml):
        compiler = GLib.find_program_in_path ('glib-compile-resources')
        print('glib-compile-resources', dirname, filename_xml)
        GLib.spawn_sync(dirname,
                        [compiler, filename_xml],
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


# Create config files pointing to source directories
dev_config('cambalache/config.py',
           f"VERSION = 'git'\npkgdatadir = '{os.path.abspath('cambalache')}'")
dev_config('merengue/config.py',
           f"VERSION = 'git'\npkgdatadir = '{os.path.abspath('merengue')}'")
dev_config('src/config.py',
           f"VERSION = 'git'\npkgdatadir = '{os.path.abspath('src')}'")

configure_file('merengue/merengue.in', 'merengue/merengue', {
    'PYTHON': GLib.find_program_in_path('python3'),
    'pythondir': os.path.abspath('.')
})
os.chmod('merengue/merengue', stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)

# Ensure gresources are up to date
compile_resource('cambalache', 'cambalache.gresource')
compile_resource('merengue', 'merengue.gresource')
compile_resource('src', 'cambalache_app.gresource')

from src import CmbApplication

if __name__ == '__main__':
    app = CmbApplication()
    app.run(sys.argv)
