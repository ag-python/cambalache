/*
 * CambalacheDB - Data Model for Cambalache
 *
 * Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
 *
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 */

PRAGMA foreign_keys = ON;

/** Common Data Model **/

CREATE TABLE license (
  license_id TEXT PRIMARY KEY,
  name TEXT,
  license_text TEXT NOT NULL
) WITHOUT ROWID;


/* Catalog
 *
 * Support for different libraries
 */
CREATE TABLE catalog (
  catalog_id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  targetable TEXT,
  shared_library TEXT,
  license_id TEXT REFERENCES license,
  license_text TEXT
) WITHOUT ROWID;

CREATE INDEX catalog_license_id_fk ON catalog (license_id);


/* Catalog dependecies
 *
 */
CREATE TABLE catalog_dependency (
  catalog_id TEXT REFERENCES catalog,
  dependency_id TEXT REFERENCES catalog,
  PRIMARY KEY(catalog_id, dependency_id)
) WITHOUT ROWID;


/* Type
 *
 * Base table to keep type information
 */
CREATE TABLE type (
  type_id TEXT PRIMARY KEY,

  parent_id TEXT REFERENCES type,
  catalog_id TEXT REFERENCES catalog,
  get_type TEXT,
  version TEXT,
  deprecated_version TEXT,
  abstract BOOLEAN,
  layout TEXT CHECK (layout IN ('manager', 'child'))
) WITHOUT ROWID;

CREATE INDEX type_parent_id_fk ON type (parent_id);
CREATE INDEX type_catalog_id_fk ON type (catalog_id);


/* Add fundamental types */
INSERT INTO type (type_id) VALUES
 ('object'), ('interface'), ('enum'), ('flags'), ('gtype'),
 ('gchar'), ('guchar'), ('gchararray'),
 ('gboolean'),
 ('gint'), ('guint'), ('glong'), ('gulong'), ('gint64'), ('guint64'),
 ('gfloat'), ('gdouble'),
 ('gpointer'), ('gboxed'), ('gparam'), ('gvariant');


/* Type Interfaces
 *
 * Keep a list of interfaces implemented by type
 */
CREATE TABLE type_iface (
  type_id TEXT,
  iface_id TEXT REFERENCES type,
  PRIMARY KEY(type_id, iface_id)
) WITHOUT ROWID;


/* Enumerations
 *
 */
CREATE TABLE type_enum (
  type_id TEXT REFERENCES type,
  name TEXT,
  value INTEGER,
  identifier TEXT,
  doc TEXT,
  PRIMARY KEY(type_id, name)
) WITHOUT ROWID;


/* Flags
 *
 */
CREATE TABLE type_flags (
  type_id TEXT REFERENCES type,
  name TEXT,
  value INTEGER,
  identifier TEXT,
  doc TEXT,
  PRIMARY KEY(type_id, name)
) WITHOUT ROWID;


/* Type Tree
 *
 * VIEW of ancestors and ifaces by type
 */
CREATE VIEW type_tree AS
WITH RECURSIVE ancestor(type_id, generation, parent_id) AS (
  SELECT type_id, 1, parent_id FROM type
    WHERE parent_id IS NOT NULL AND
          parent_id != 'interface' AND
          parent_id != 'enum' AND
          parent_id != 'flags'
  UNION ALL
  SELECT ancestor.type_id, generation + 1, type.parent_id
    FROM type JOIN ancestor ON type.type_id = ancestor.parent_id
    WHERE type.parent_id IS NOT NULL
)
SELECT * FROM ancestor
UNION
SELECT ancestor.type_id, 0, type_iface.iface_id
  FROM ancestor JOIN type_iface
  WHERE ancestor.parent_id = type_iface.type_id
ORDER BY type_id,generation;


/* Property
 *
 */
CREATE TABLE property (
  owner_id TEXT REFERENCES type,
  property_id TEXT NOT NULL,

  type_id TEXT REFERENCES type,
  writable BOOLEAN,
  construct_only BOOLEAN,
  default_value TEXT,
  version TEXT,
  deprecated_version TEXT,
  PRIMARY KEY(owner_id, property_id)
) WITHOUT ROWID;

CREATE INDEX property_type_id_fk ON property (type_id);

/* Check property:owner_id is not fundamental */
CREATE TRIGGER on_property_before_insert_check BEFORE INSERT ON property
BEGIN
  SELECT
    CASE
      WHEN (SELECT parent_id FROM type WHERE type_id=NEW.owner_id) IS NULL THEN
            RAISE (ABORT,'owner_id is not an object type')
    END;
END;


/* Signal
 *
 */
CREATE TABLE signal (
  owner_id TEXT REFERENCES type,
  signal_id TEXT NOT NULL,

  version TEXT,
  deprecated_version TEXT,
  PRIMARY KEY(owner_id, signal_id)
) WITHOUT ROWID;

/* Check signal:owner_id is not fundamental */
CREATE TRIGGER on_signal_before_insert_check BEFORE INSERT ON signal
BEGIN
  SELECT
    CASE
      WHEN (SELECT parent_id FROM type WHERE type_id=NEW.owner_id) IS NULL THEN
            RAISE (ABORT,'owner_id is not an object type')
    END;
END;


/** Project Data Model  **/


/* UI
 *
 */
CREATE TABLE ui (
  ui_id INTEGER PRIMARY KEY AUTOINCREMENT,

  name TEXT,
  description TEXT,
  copyright TEXT,
  authors TEXT,
  license_id TEXT REFERENCES license,
  filename TEXT,
  translation_domain TEXT
);

CREATE INDEX ui_license_id_fk ON ui (license_id);

/* Object
 *
 * TODO: check type_id is an object
 */
CREATE TABLE object (
  object_id INTEGER PRIMARY KEY AUTOINCREMENT,

  type_id TEXT NOT NULL REFERENCES type,
  name TEXT,
  parent_id INTEGER REFERENCES object ON DELETE CASCADE,
  ui_id INTEGER REFERENCES ui ON DELETE CASCADE,
  CHECK (parent_id IS NULL OR ui_id IS NULL)
);

CREATE INDEX object_type_id_fk ON object (type_id);
CREATE INDEX object_ui_id_fk ON object (ui_id);


/* Object Template
 *
 * Only one template per UI is allowed
 */
CREATE TABLE object_template (
  object_id INTEGER REFERENCES object,
  ui_id INTEGER REFERENCES ui ON DELETE CASCADE,
  PRIMARY KEY (object_id, ui_id)
);


/* Object Property
 *
 * TODO: check owner_id is in object_id.type_id type tree
 */
CREATE TABLE object_property (
  object_id INTEGER REFERENCES object ON DELETE CASCADE,
  owner_id TEXT,
  property_id TEXT,

  value TEXT,
  translatable BOOLEAN,
  PRIMARY KEY(object_id, owner_id, property_id),
  FOREIGN KEY(owner_id, property_id) REFERENCES property
) WITHOUT ROWID;

CREATE INDEX object_property_property_fk ON object_property (owner_id, property_id);


/* Object Child Property
 *
 * TODO: check owner_id is in object_id.type_id type tree
 */
CREATE TABLE object_child_property (
  object_id INTEGER REFERENCES object ON DELETE CASCADE,
  child_id INTEGER REFERENCES object ON DELETE CASCADE,
  owner_id TEXT,
  property_id TEXT,

  value TEXT,
  translatable BOOLEAN,
  PRIMARY KEY(object_id, child_id, owner_id, property_id),
  FOREIGN KEY(owner_id, property_id) REFERENCES property
) WITHOUT ROWID;

CREATE INDEX object_child_property_child_property_fk ON object_child_property (owner_id, property_id);


/* Object Signal
 *
 * TODO: check owner_id is in object_id.type_id type tree
 */
CREATE TABLE object_signal (
  object_id INTEGER REFERENCES object ON DELETE CASCADE,
  owner_id TEXT,
  signal_id TEXT,

  handler TEXT NOT NULL,
  detail TEXT,
  user_data INTEGER REFERENCES object ON DELETE SET NULL,
  swap BOOLEAN,
  after BOOLEAN,
  FOREIGN KEY(owner_id, signal_id) REFERENCES signal
);

CREATE INDEX object_signal_signal_fk ON object_signal (owner_id, signal_id);


/*
 * Implement undo/redo stack with triggers
 *
 * We should be able to store the whole project history if we want to.
 *
 * history_* tables and triggers are auto generated to avoid copy/paste errors
 */

/* Main history table */

CREATE TABLE history (
  history_id INTEGER PRIMARY KEY AUTOINCREMENT,
  command TEXT NOT NULL,
  range_id INTEGER REFERENCES history,
  data TEXT
);

/* This trigger will update PUSH/POP range and data automatically on POP */
CREATE TRIGGER on_history_pop_insert AFTER INSERT ON history
WHEN
  NEW.command is 'POP'
BEGIN
/* Update range_id and data(message) from last PUSH command */
  UPDATE history
  SET (range_id, data)=(SELECT history_id, data FROM history WHERE command='PUSH' AND range_id IS NULL ORDER BY history_id DESC LIMIT 1)
  WHERE history_id = NEW.history_id;

/* Update range_id in last PUSH command */
  UPDATE history
  SET range_id=NEW.history_id
  WHERE history_id=(SELECT range_id FROM history WHERE history_id = NEW.history_id);
END;

