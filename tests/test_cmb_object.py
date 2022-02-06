"""
Test CmbObject API
"""
import os

from cambalache import CmbProject, config

def cmb_object_data_test(target_tk):
    # Load original UI file to compare
    path = os.path.join(os.path.dirname(__file__), target_tk, 'liststore.ui')
    str_original = open(path, 'r').read()

    # Create new project to recreate 'liststore.ui' using API
    project = CmbProject(target_tk=target_tk)

    # Add an UI
    ui = project.add_ui('liststore.ui')

    if target_tk == 'gtk+-3.0':
        ui.set_library('gtk+', '3.24')
    else:
        ui.set_library('gtk', '4.0')

    # Create a GtkListStore
    store = project.add_object(ui.ui_id, 'GtkListStore')

    # Set object id
    store.name = 'liststore_test'

    # Add columns
    cols = store.add_data('columns')
    for t, c in [('gchararray', ' column-name gchararray1 '),
                 ('gint64', ' column-name gint1 '),
                 ('gboolean', ' column-name gboolean1 ')]:
        col = cols.add_data('column', comment=c)
        col.set_arg('type', t)

    # Add data
    data = store.add_data('data')

    for values in [('Hola', 1, False),
                   ('Mundo', 2, True),
                   ('Hello', 12, True),
                   ('World', 1234, False)]:
        row = data.add_data('row')

        for i, val in enumerate(values):
            col = row.add_data('col', val)
            col.set_arg('id', i)

        # Add and remove data to CmbObjectData
        dummy_row = data.add_data('row')
        data.remove_data(dummy_row)

    # Add and remove data to CmbObject
    data2 = store.add_data('data')
    store.remove_data(data2)

    # Export UI file
    str_exported = project.db.tostring(ui.ui_id)

    # Remove "Created with" comment since version will not match
    str_exported = str_exported.replace(f"<!-- Created with Cambalache {config.VERSION} -->\n", '')

    assert str_exported == str_original

def test_gtk3_cmb_object_data():
    cmb_object_data_test('gtk+-3.0')

def test_gtk4_cmb_object_data():
    cmb_object_data_test('gtk-4.0')
