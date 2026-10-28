-- The replayer's bookmark: which event to play next.
-- It is updated in the same transaction as each event, so a restart never repeats or skips one.

CREATE TABLE replay_state (
  id          TINYINT PRIMARY KEY,
  next_event  INT NOT NULL,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO replay_state (id, next_event) VALUES (1, 0);
