ALTER TABLE pending_reviews
    ADD COLUMN IF NOT EXISTS question_type VARCHAR(20) NOT NULL DEFAULT 'fill_blank';
