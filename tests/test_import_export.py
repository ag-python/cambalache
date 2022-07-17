"""
import .ui files into cambalache and export to compare results
"""
import os

from cambalache import CmbProject, config

def assert_original_and_exported(target_tk, filename):
    """
    import .ui file and compare it with the exported version
    """
    path = os.path.join(os.path.dirname(__file__), target_tk, filename)
    str_original = open(path, 'r').read()

    project = CmbProject(target_tk=target_tk)
    ui_id = project.db.import_file(path)
    str_exported = project.db.tostring(ui_id)
    
    # Remove "Created with" comment since version will not match
    str_exported = str_exported.replace(f"<!-- Created with Cambalache {config.VERSION} -->\n", '')

    assert str_exported == str_original

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

def test_gtk3_comboboxtext():
    assert_original_and_exported("gtk+-3.0", "comboboxtext.ui")

def test_gtk3_dialog():
    assert_original_and_exported("gtk+-3.0", "dialog.ui")

def test_gtk3_label():
    assert_original_and_exported("gtk+-3.0", "label.ui")

def test_gtk3_levelbar():
    assert_original_and_exported("gtk+-3.0", "levelbar.ui")

def test_gtk3_liststore():
    assert_original_and_exported("gtk+-3.0", "liststore.ui")

def test_gtk3_scale():
    assert_original_and_exported("gtk+-3.0", "scale.ui")

def test_gtk3_sizegroup():
    assert_original_and_exported("gtk+-3.0", "sizegroup.ui")

def test_gtk3_style():
    assert_original_and_exported("gtk+-3.0", "style.ui")

def test_gtk3_treestore():
    assert_original_and_exported("gtk+-3.0", "treestore.ui")


def test_gtk3_custom_fragment():
    assert_original_and_exported("gtk+-3.0", "custom_fragment.ui")


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

def test_gtk4_inline_object():
    assert_original_and_exported("gtk-4.0", "inline_object.ui")

def test_gtk4_stack_page():
    assert_original_and_exported("gtk-4.0", "stack_page.ui")

def test_gtk4_liststore():
    assert_original_and_exported("gtk-4.0", "liststore.ui")

def test_gtk4_custom_fragment():
    assert_original_and_exported("gtk-4.0", "custom_fragment.ui")
