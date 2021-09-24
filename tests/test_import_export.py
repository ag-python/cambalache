"""
import .ui files into cambalache and export to compare results
"""
import os

from lxml import etree
from cambalache import CmbProject

def assert_original_and_exported(target_tk, filename):
    """
    import .ui file and compare it with the exported version
    """
    path = os.path.join(os.path.dirname(__file__), target_tk, filename)
    str_original = open(path, 'r').read()

    project = CmbProject(target_tk=target_tk)
    ui_id = project.db.import_file(path)
    tree_exported = project.db.export_ui(ui_id, use_id=False)
    str_exported = etree.tostring(tree_exported,
                      pretty_print=True,
                      xml_declaration=True,
                      encoding='UTF-8').decode('UTF-8')
    
    assert str_original == str_exported

#
# Gtk+ 3.0 Tests
#
def test_gtk3_window():
    assert_original_and_exported("gtk+-3.0", "window.ui")

def test_gtk3_children():
    assert_original_and_exported("gtk+-3.0", "children.ui")

def test_gtk3_packing():
    assert_original_and_exported("gtk+-3.0", "packing.ui")

def test_gtk3_signals():
    assert_original_and_exported("gtk+-3.0", "signals.ui")

def test_gtk3_template():
    assert_original_and_exported("gtk+-3.0", "template.ui")

#
# Gtk 4.0 Tests
#
def test_gtk4_window():
    assert_original_and_exported("gtk-4.0", "window.ui")

def test_gtk4_children():
    assert_original_and_exported("gtk-4.0", "children.ui")

def test_gtk4_layout():
    assert_original_and_exported("gtk-4.0", "layout.ui")

def test_gtk4_signals():
    assert_original_and_exported("gtk-4.0", "signals.ui")

def test_gtk4_template():
    assert_original_and_exported("gtk-4.0", "template.ui")
