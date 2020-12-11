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
);


/* Type
 *
 * Base table to keep type information
 */
CREATE TABLE type (
  type_id TEXT PRIMARY KEY,

  parent TEXT REFERENCES type,
  get_type TEXT,
  version TEXT,
  deprecated_version TEXT
);


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
);

/* Check property:owner_id is not fundamental */
CREATE TRIGGER property_check_owner_id BEFORE INSERT ON property
BEGIN
   SELECT
      CASE
          WHEN (SELECT parent FROM type WHERE type_id=NEW.owner_id) IS NULL THEN
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
);


/* Signal
 *
 * TODO: Add check to make sure signal:owner_type is not fundamental
 */
CREATE TABLE signal (
  owner_id TEXT REFERENCES type(type_id),
  signal_id TEXT NOT NULL,

  version TEXT,
  deprecated_version TEXT,
  PRIMARY KEY(owner_id, signal_id)
);


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
);


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
);


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
);


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


/* Interface Object
 *
 * TODO: check objects are toplevels (have no parent)
 */
CREATE TABLE interface_object (
  interface_id INTEGER REFERENCES interface ON DELETE CASCADE,
  object_id INTEGER REFERENCES object ON DELETE CASCADE,

  template TEXT,
  PRIMARY KEY(interface_id, object_id)
);

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
  table_name TEXT,
  column_name TEXT,
  column_value TEXT
);

