from __future__ import annotations

MAX_INTERVAL_DAYS = 365


def calculate_next_review(
    level: int, correct: bool, current_interval_days: int
) -> tuple[int, int]:
    """Return (new_level, new_interval_days)."""
    if correct:
        new_level = level + 1
        new_interval = min(current_interval_days * 2, MAX_INTERVAL_DAYS)
    else:
        new_level = max(0, level - 1)
        new_interval = 1
    return new_level, new_interval


def get_question_type(level: int) -> str:
    if level <= 2:
        return "multiple_choice"
    if level <= 5:
        return "fill_blank"
    return "composition"
