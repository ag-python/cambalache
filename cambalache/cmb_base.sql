/*
 * Base Data Model for Cambalache Project
 *
 * Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
 *
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 */

/** Common Data Model **/

CREATE TABLE IF NOT EXISTS license (
  license_id TEXT PRIMARY KEY,
  name TEXT,
  license_text TEXT NOT NULL
) WITHOUT ROWID;


/* Library
 *
 * Support for different libraries
 */
CREATE TABLE IF NOT EXISTS library (
  library_id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  shared_library TEXT,
  license_id TEXT REFERENCES license,
  license_text TEXT
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS library_license_id_fk ON library (license_id);


/* Library dependecies
 *
 */
CREATE TABLE IF NOT EXISTS library_dependency (
  library_id TEXT REFERENCES library,
  dependency_id TEXT REFERENCES library,
  PRIMARY KEY(library_id, dependency_id)
) WITHOUT ROWID;


/* Library targeteable versions
 *
 */
CREATE TABLE IF NOT EXISTS library_version (
  library_id TEXT REFERENCES library,
  version TEXT,
  PRIMARY KEY(library_id, version)
) WITHOUT ROWID;


/* Type
 *
 * Base table to keep type information
 */
CREATE TABLE IF NOT EXISTS type (
  type_id TEXT PRIMARY KEY,

  parent_id TEXT REFERENCES type,
  library_id TEXT REFERENCES library,
  get_type TEXT,
  version TEXT,
  deprecated_version TEXT,
  abstract BOOLEAN,
  layout TEXT CHECK (layout IN ('container', 'manager', 'child'))
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS type_parent_id_fk ON type (parent_id);
CREATE INDEX IF NOT EXISTS type_library_id_fk ON type (library_id);

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
CREATE TABLE IF NOT EXISTS type_iface (
  type_id TEXT,
  iface_id TEXT REFERENCES type,
  PRIMARY KEY(type_id, iface_id)
) WITHOUT ROWID;


/* Enumerations
 *
 */
CREATE TABLE IF NOT EXISTS type_enum (
  type_id TEXT REFERENCES type,
  name TEXT,
  nick TEXT,
  value INTEGER,
  identifier TEXT,
  doc TEXT,
  PRIMARY KEY(type_id, name)
) WITHOUT ROWID;


/* Flags
 *
 */
CREATE TABLE IF NOT EXISTS type_flags (
  type_id TEXT REFERENCES type,
  name TEXT,
  nick TEXT,
  value INTEGER,
  identifier TEXT,
  doc TEXT,
  PRIMARY KEY(type_id, name)
) WITHOUT ROWID;


/* Type Tree
 *
 * VIEW of ancestors and ifaces by type
 */
CREATE VIEW  IF NOT EXISTS type_tree AS
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
  WHERE ancestor.type_id = type_iface.type_id
ORDER BY type_id,generation;


/* Property
 *
 */
CREATE TABLE IF NOT EXISTS property (
  owner_id TEXT REFERENCES type,
  property_id TEXT NOT NULL,

  type_id TEXT REFERENCES type,
  construct_only BOOLEAN,
  default_value TEXT,
  minimum TEXT,
  maximum TEXT,
  version TEXT,
  deprecated_version TEXT,
  PRIMARY KEY(owner_id, property_id)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS property_type_id_fk ON property (type_id);

/* Check property:owner_id is not fundamental */
CREATE TRIGGER IF NOT EXISTS on_property_before_insert_check BEFORE INSERT ON property
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
CREATE TABLE IF NOT EXISTS signal (
  owner_id TEXT REFERENCES type,
  signal_id TEXT NOT NULL,

  version TEXT,
  deprecated_version TEXT,
  detailed BOOLEAN,
  PRIMARY KEY(owner_id, signal_id)
) WITHOUT ROWID;

/* Check signal:owner_id is not fundamental */
CREATE TRIGGER IF NOT EXISTS on_signal_before_insert_check BEFORE INSERT ON signal
BEGIN
  SELECT
    CASE
      WHEN (SELECT parent_id FROM type WHERE type_id=NEW.owner_id) IS NULL THEN
            RAISE (ABORT,'owner_id is not an object type')
    END;
END;

