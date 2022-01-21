#
# CmbDBmigration - Cambalache DataBase Migration functions
#
# Copyright (C) 2021  Juan Pablo Ugarte
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation;
# version 2.1 of the License.
#
# library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors:
#   Juan Pablo Ugarte <juanpablougarte@gmail.com>
#

def ensure_columns_for_0_7_5(table, data):
    if table == 'object':
        # Append position column
        return [row + (None, ) for row in data]
    elif table in ['object_property', 'object_layout_property']:
        # Append translation_context, translation_comments columns
        return [row + (None, None) for row in data]

    return data


def migrate_table_data_to_0_7_5(c, table, data):
    if table == 'object':
        c.execute('''
            UPDATE object SET position=new.position - 1
            FROM (
                SELECT row_number() OVER (
                    PARTITION BY parent_id ORDER BY object_id
                ) position, ui_id, object_id
                FROM object
                WHERE parent_id IS NOT NULL
            ) AS new
            WHERE object.ui_id=new.ui_id AND object.object_id=new.object_id;
        ''')
        c.execute('''
            UPDATE object SET position=new.position - 1
            FROM (
                SELECT row_number() OVER (
                    PARTITION BY ui_id ORDER BY object_id
                ) position, ui_id, object_id
                FROM object
                WHERE parent_id IS NULL
            ) AS new
            WHERE object.ui_id=new.ui_id AND object.object_id=new.object_id;
        ''')


def ensure_columns_for_0_9_0(table, data):
    if table == 'object_property':
        # Append inline_object_id column
        return [row + (None, ) for row in data]

    return data
