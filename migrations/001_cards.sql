CREATE TABLE cards (
    id            SERIAL PRIMARY KEY,
    expression    TEXT NOT NULL,
    type          VARCHAR(10) NOT NULL CHECK (type IN ('word','idiom','grammar')),
    meaning       JSONB NOT NULL,
    examples      JSONB NOT NULL,
    level         INT  NOT NULL DEFAULT 0,
    interval_days INT  NOT NULL DEFAULT 1,
    next_review   DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (expression, type)
);

CREATE INDEX idx_cards_next_review ON cards (next_review);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cards_updated_at
    BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
