PRAGMA foreign_keys = OFF;
INSERT INTO library VALUES
('gobject', '2.0', 'libgobject-2.0.so.0', NULL, NULL);

INSERT INTO type VALUES
('GBinding', 'GObject', 'gobject', '2.26', NULL, NULL, NULL),
('GBindingFlags', 'flags', 'gobject', NULL, NULL, NULL, NULL),
('GObject', 'object', 'gobject', NULL, NULL, NULL, NULL);

INSERT INTO type_flags VALUES
('GBindingFlags', 'G_BINDING_BIDIRECTIONAL', 'bidirectional', 1, 'Bidirectional binding; if either the property of the source or the property of the target changes, the other is updated.'),
('GBindingFlags', 'G_BINDING_DEFAULT', 'default', 0, 'The default binding; if the source property changes, the target property is updated with its value.'),
('GBindingFlags', 'G_BINDING_INVERT_BOOLEAN', 'invert-boolean', 4, 'If the two properties being bound are booleans, setting one to %TRUE will result in the other being set to %FALSE and vice versa. This flag will only work for boolean properties, and cannot be used when passing custom transformation functions to g_object_bind_property_full().'),
('GBindingFlags', 'G_BINDING_SYNC_CREATE', 'sync-create', 2, 'Synchronize the values of the source and target properties when creating the binding; the direction of the synchronization is always from the source to the target.');

INSERT INTO property VALUES
('GBinding', 'flags', 'GBindingFlags', NULL, NULL, NULL, NULL, NULL, NULL, '2.26', NULL),
('GBinding', 'source', 'GObject', 1, NULL, NULL, NULL, NULL, NULL, '2.26', NULL),
('GBinding', 'source-property', 'gchararray', NULL, NULL, NULL, NULL, NULL, NULL, '2.26', NULL),
('GBinding', 'target', 'GObject', 1, NULL, NULL, NULL, NULL, NULL, '2.26', NULL),
('GBinding', 'target-property', 'gchararray', NULL, NULL, NULL, NULL, NULL, NULL, '2.26', NULL);

INSERT INTO signal VALUES
('GObject', 'notify', NULL, NULL, 1);

PRAGMA foreign_keys = ON;
