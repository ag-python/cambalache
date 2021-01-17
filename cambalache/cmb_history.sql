/*
 * Data Model for Cambalache Project History
 *
 * Copyright (C) 2020  Juan Pablo Ugarte - All Rights Reserved
 *
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 */

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

