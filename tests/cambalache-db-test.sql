/*
 * CambalacheDB - Data Model for Cambalache
 *
 * Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
 *
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 */

/* Test Project */
INSERT INTO ui (name, filename) VALUES ('Test UI', 'test.ui');

INSERT INTO object (ui_id, object_id, type_id, name, parent_id) VALUES
(1, 1, 'GtkWindow', 'main', NULL),
(1, 2, 'GtkGrid', 'grid', 1),
(1, 3, 'GtkLabel', 'label', 2),
(1, 4, 'GtkButton', 'button', 2),
(1, 5, 'GtkButton', 'todelete', 2),
(1, 6, 'GtkLabel', 'label2', NULL);

INSERT INTO object_property (ui_id, object_id, owner_id, property_id, value) VALUES
(1, 3, 'GtkLabel', 'label', 'Hello World'),
(1, 4, 'GtkButton', 'label', 'Click Me'),
(1, 5, 'GtkButton', 'label', 'Bye Bye World'),
(1, 6, 'GtkLabel', 'label', 'Hola Mundo');

INSERT INTO object_layout_property (ui_id, object_id, child_id, owner_id, property_id, value) VALUES
(1, 1, 3, 'GtkGridLayoutChild', 'column', 1),
(1, 1, 3, 'GtkGridLayoutChild', 'row', 1),
(1, 1, 4, 'GtkGridLayoutChild', 'column', 2),
(1, 1, 4, 'GtkGridLayoutChild', 'row', 1),
(1, 1, 5, 'GtkGridLayoutChild', 'column', 1),
(1, 1, 5, 'GtkGridLayoutChild', 'row', 2);

INSERT INTO object_signal (ui_id, object_id, owner_id, signal_id, handler) VALUES
(1, 4, 'GtkButton', 'clicked', 'on_button_clicked'),
(1, 5, 'GtkButton', 'clicked', 'on_todelete_clicked');

/* Test history */
UPDATE object_property SET value ='Hello World 1' WHERE (object_id=3 AND owner_id='GtkLabel' AND property_id='label');
UPDATE object_property SET value ='Hello World 2' WHERE (object_id=3 AND owner_id='GtkLabel' AND property_id='label');
UPDATE object_property SET value ='Hello World 3' WHERE (object_id=3 AND owner_id='GtkLabel' AND property_id='label');
UPDATE object_property SET value ='Hola Mundo!!!' WHERE (object_id=6 AND owner_id='GtkLabel' AND property_id='label');

/* Push history group */
INSERT INTO history (command, data) VALUES ('PUSH', 'Update several props');

UPDATE object_property SET value ='Do not Click Me' WHERE (object_id=5 AND owner_id='GtkButton' AND property_id='label');
UPDATE object_property SET value ='Hello World 4' WHERE (object_id=3 AND owner_id='GtkLabel' AND property_id='label');

/* Delete an object, it should also delete all properties, signals, etc */
DELETE FROM object WHERE name = 'todelete';

UPDATE object_property SET value ='Click Me 2' WHERE (object_id=4 AND owner_id='GtkButton' AND property_id='label');

/* Pop history group */
INSERT INTO history (command) VALUES ('POP');


