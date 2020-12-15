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
  deprecated_version TEXT
) WITHOUT ROWID;

CREATE INDEX type_parent_id_fk ON type (parent_id);
CREATE INDEX type_catalog_id_fk ON type (catalog_id);


/* Add fundamental types */
INSERT INTO type (type_id) VALUES
 ('char'), ('uchar'), ('boolean'), ('int'), ('uint'), ('long'), ('ulong'),
 ('int64'), ('uint64'), ('enum'), ('flags'), ('float'), ('double'), ('string'),
 ('pointer'), ('boxed'), ('param'), ('object'), ('gtype'), ('variant');


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


/* Child Property
 *
 */
CREATE TABLE child_property (
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

CREATE INDEX child_property_type_id_fk ON child_property (type_id);


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

/* Object
 *
 */
CREATE TABLE object (
  object_id INTEGER PRIMARY KEY AUTOINCREMENT,

  type_id TEXT NOT NULL REFERENCES type,
  name TEXT UNIQUE,
  parent_id INTEGER REFERENCES object
);

CREATE INDEX object_type_id_fk ON object (type_id);


/* Object Property
 *
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
 */
CREATE TABLE object_child_property (
  object_id INTEGER REFERENCES object ON DELETE CASCADE,
  child_id INTEGER REFERENCES object ON DELETE CASCADE,
  owner_id TEXT,
  property_id TEXT,

  value TEXT,
  translatable BOOLEAN,
  PRIMARY KEY(object_id, child_id, owner_id, property_id),
  FOREIGN KEY(owner_id, property_id) REFERENCES child_property
) WITHOUT ROWID;

CREATE INDEX object_child_property_child_property_fk ON object_child_property (owner_id, property_id);


/* Object Signal
 *
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
  PRIMARY KEY(object_id, owner_id, signal_id),
  FOREIGN KEY(owner_id, signal_id) REFERENCES signal
) WITHOUT ROWID;

CREATE INDEX object_signal_signal_fk ON object_signal (owner_id, signal_id);


/* Interface
 *
 */
CREATE TABLE interface (
  interface_id INTEGER PRIMARY KEY AUTOINCREMENT,

  name TEXT,
  description TEXT,
  copyright TEXT,
  authors TEXT,
  license_id TEXT REFERENCES license,
  filename TEXT,
  translation_domain TEXT
);

CREATE INDEX interface_license_id_fk ON interface (license_id);


/* Interface Object
 *
 */
CREATE TABLE interface_object (
  interface_id INTEGER REFERENCES interface ON DELETE CASCADE,
  object_id INTEGER REFERENCES object ON DELETE CASCADE,

  template TEXT,
  PRIMARY KEY(interface_id, object_id)
) WITHOUT ROWID;

/* Check objects are toplevels (have no parent) */
CREATE TRIGGER on_interface_object_before_insert_check BEFORE INSERT ON interface_object
BEGIN
  SELECT
    CASE
      WHEN (SELECT parent_id FROM object WHERE object_id=NEW.object_id) IS NOT NULL THEN
            RAISE (ABORT,'owner_id is not an object type')
    END;
END;


/*
 * Implement undo/redo stack with triggers
 *
 * We should be able to store the whole project history if we want to.
 *
 * history_* tables and triggers are auto generated to avoid copy/paste errors
 */

/* Main history tables */

CREATE TABLE history_group (
  history_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
  done BOOLEAN,
  description TEXT
);

CREATE TABLE history (
  history_id INTEGER PRIMARY KEY AUTOINCREMENT,
  history_group_id INTEGER REFERENCES history_group,
  command TEXT,
  table_name TEXT
);

CREATE INDEX history_history_group_id_fk ON history (history_group_id);
