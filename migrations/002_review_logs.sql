CREATE TABLE review_logs (
    id            SERIAL PRIMARY KEY,
    card_id       INT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    question_type VARCHAR(20) NOT NULL,
    user_answer   TEXT,
    correct       BOOLEAN NOT NULL,
    feedback      TEXT,
    reviewed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_review_logs_card ON review_logs (card_id, reviewed_at DESC);
