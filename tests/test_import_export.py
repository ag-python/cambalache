"""
import .ui files into cambalache and export to compare results
"""
import os
from io import BytesIO
from lxml import etree
from cambalache import CmbProject

def get_original_exported_as_str(gtk_version,filename):
    """
    import .ui file and return the original and a new one exported, both like a string
    """
    path = os.path.join(os.path.dirname(__file__), f'gtk{gtk_version}', filename)
    str_original = open(path, 'r').read()

    project = CmbProject(target_tk=('gtk+-3.0' if gtk_version==3 else 'gtk-4.0'))
    ui_id = project.db.import_file(path)
    tree_exported = project.db.export_ui(ui_id, use_id=False)
    str_exported=etree.tostring(tree_exported,
                      pretty_print=True,
                      xml_declaration=True,
                      encoding='UTF-8').decode('UTF-8')
    
    return (str_original, str_exported)

def test_gtk3_gtkwindow_ui():
    """
    test for gtkwindow.ui file in gtk3 version
    """
    original, exported = get_original_exported_as_str(3,"gtkwindow.ui")
    assert  original == exported

def test_gtk4_gtkwindow_ui():
    """
    test for gtkwindow.ui file in gtk4 version
    """
    original, exported = get_original_exported_as_str(4,"gtkwindow.ui")
    assert  original == exported
