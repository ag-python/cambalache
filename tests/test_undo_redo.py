"""
Test Undo/Redo API
"""
import os

from cambalache import CmbProject, config

def undo_test(target_tk, filename, name):
    path = os.path.join(os.path.dirname(__file__), target_tk, filename)

    project = CmbProject(target_tk=target_tk)

    ui, msgs, detail_msg = project.import_file(path)

    for i in range(0, 4):
        obj = project.get_object_by_name(ui.ui_id, name)
        assert obj is not None and obj.name == name

        project.remove_object(obj)

        assert project.get_object_by_name(ui.ui_id, name) is None

        project.undo()

        obj = project.get_object_by_name(ui.ui_id, name)
        assert obj is not None and obj.name == name



def test_gtk3_undo():
    undo_test('gtk+-3.0', 'dialog.ui', 'dialog')

def test_gtk4_undo():
    undo_test('gtk-4.0', 'liststore.ui', 'liststore_test')
