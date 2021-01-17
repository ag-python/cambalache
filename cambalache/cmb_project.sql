/*
 * Data Model for Cambalache Project
 *
 * Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
 *
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 */


/* UI
 *
 */
CREATE TABLE ui (
  ui_id INTEGER PRIMARY KEY AUTOINCREMENT,

  name TEXT UNIQUE,
  filename TEXT UNIQUE,
  description TEXT,
  copyright TEXT,
  authors TEXT,
  license_id TEXT REFERENCES license,
  translation_domain TEXT
);

CREATE INDEX ui_license_id_fk ON ui (license_id);


/* UI library version target
 *
 */
CREATE TABLE ui_library (
  ui_id INTEGER REFERENCES ui ON DELETE CASCADE,
  library_id TEXT,
  version TEXT,
  PRIMARY KEY(ui_id, library_id),
  FOREIGN KEY(library_id, version) REFERENCES library_version
) WITHOUT ROWID;


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

