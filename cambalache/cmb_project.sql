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
  template_id INTEGER,

  name TEXT UNIQUE,
  filename TEXT UNIQUE,
  description TEXT,
  copyright TEXT,
  authors TEXT,
  license_id TEXT REFERENCES license,
  translation_domain TEXT,
  FOREIGN KEY(ui_id, template_id) REFERENCES object(ui_id, object_id) ON DELETE SET NULL
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
  ui_id INTEGER REFERENCES ui ON DELETE CASCADE,
  object_id INTEGER,

  type_id TEXT NOT NULL REFERENCES type,
  name TEXT,
  parent_id INTEGER,
  PRIMARY KEY(ui_id, object_id),
  FOREIGN KEY(ui_id, parent_id) REFERENCES object(ui_id, object_id) ON DELETE CASCADE
) WITHOUT ROWID;

CREATE INDEX object_type_id_fk ON object (type_id);
CREATE INDEX object_parent_id_fk ON object (ui_id, parent_id);


/* Object Property
 *
 * TODO: check owner_id is in object_id.type_id type tree
 */
CREATE TABLE object_property (
  ui_id INTEGER REFERENCES ui ON DELETE CASCADE,
  object_id INTEGER,
  owner_id TEXT,
  property_id TEXT,

  value TEXT,
  translatable BOOLEAN,
  PRIMARY KEY(ui_id, object_id, owner_id, property_id),
  FOREIGN KEY(ui_id, object_id) REFERENCES object(ui_id, object_id) ON DELETE CASCADE,
  FOREIGN KEY(owner_id, property_id) REFERENCES property
) WITHOUT ROWID;

CREATE INDEX object_property_object_fk ON object_property (ui_id, object_id);
CREATE INDEX object_property_property_fk ON object_property (owner_id, property_id);


/* Object Child Property
 *
 * TODO: check owner_id is in object_id.type_id type tree
 */
CREATE TABLE object_layout_property (
  ui_id INTEGER REFERENCES ui ON DELETE CASCADE,
  object_id INTEGER,
  child_id INTEGER,
  owner_id TEXT,
  property_id TEXT,

  value TEXT,
  translatable BOOLEAN,
  PRIMARY KEY(ui_id, object_id, child_id, owner_id, property_id),
  FOREIGN KEY(ui_id, object_id) REFERENCES object ON DELETE CASCADE,
  FOREIGN KEY(ui_id, child_id) REFERENCES object(ui_id, object_id) ON DELETE CASCADE,
  FOREIGN KEY(owner_id, property_id) REFERENCES property
) WITHOUT ROWID;

CREATE INDEX object_layout_property_child_property_fk ON object_layout_property (owner_id, property_id);


/* Object Signal
 *
 * TODO: check owner_id is in object_id.type_id type tree
 */
CREATE TABLE object_signal (
  ui_id INTEGER REFERENCES ui ON DELETE CASCADE,
  object_id INTEGER,
  owner_id TEXT,
  signal_id TEXT,

  handler TEXT NOT NULL,
  detail TEXT,
  user_data INTEGER,
  swap BOOLEAN,
  after BOOLEAN,
  FOREIGN KEY(ui_id, object_id) REFERENCES object ON DELETE CASCADE,
  FOREIGN KEY(ui_id, user_data) REFERENCES object(ui_id, object_id) ON DELETE SET NULL,
  FOREIGN KEY(owner_id, signal_id) REFERENCES signal
);

CREATE INDEX object_signal_signal_fk ON object_signal (owner_id, signal_id);

