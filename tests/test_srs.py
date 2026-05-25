from bot.srs import MAX_INTERVAL_DAYS, calculate_next_review, get_question_type


def test_calculate_next_review_correct_doubles_interval():
    new_level, new_interval = calculate_next_review(level=1, correct=True, current_interval_days=2)
    assert new_level == 2
    assert new_interval == 4


def test_calculate_next_review_correct_caps_at_max():
    new_level, new_interval = calculate_next_review(
        level=10, correct=True, current_interval_days=400
    )
    assert new_level == 11
    assert new_interval == MAX_INTERVAL_DAYS


def test_calculate_next_review_wrong_resets():
    new_level, new_interval = calculate_next_review(level=3, correct=False, current_interval_days=8)
    assert new_level == 2
    assert new_interval == 1


def test_calculate_next_review_wrong_floors_at_zero():
    new_level, new_interval = calculate_next_review(level=0, correct=False, current_interval_days=1)
    assert new_level == 0
    assert new_interval == 1


def test_get_question_type_boundaries():
    assert get_question_type(0) == "multiple_choice"
    assert get_question_type(2) == "multiple_choice"
    assert get_question_type(3) == "fill_blank"
    assert get_question_type(5) == "fill_blank"
    assert get_question_type(6) == "composition"
