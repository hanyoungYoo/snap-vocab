CREATE TABLE pending_reviews (
    message_id     TEXT PRIMARY KEY,
    card_id        INT  NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    correct_answer TEXT NOT NULL,
    question       TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
