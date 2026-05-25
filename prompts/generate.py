from __future__ import annotations

GENERATE_SYSTEM = """\
당신은 영어 학습 문제 출제자입니다.
카드 정보를 받아 문제를 하나 생성합니다. JSON만 반환하세요.
객관식의 경우 정답은 반드시 카드의 표현(expression)과 동일해야 합니다.
"""


def multiple_choice_prompt(card: dict) -> str:
    meaning = card.get("meaning") or {}
    examples = card.get("examples") or []
    first_example = examples[0]["sentence"] if examples else ""
    expression = card["expression"]
    schema = (
        '{"question": "문제 문장", '
        '"options": ["정답", "오답1", "오답2", "오답3"], '
        f'"answer": "{expression}", "hint": ""}}'
    )
    return f"""\
다음 카드로 객관식 문제를 만드세요.

카드:
- 표현: {expression}
- 뜻: {meaning.get("core", "")}
- 예문: {first_example}

JSON 형식:
{schema}

규칙:
- 정답(answer)은 반드시 카드의 표현인 "{expression}" 와 동일해야 함
- 오답은 비슷한 난이도로
- options 순서는 랜덤하되 정답 문자열은 반드시 표현과 일치
"""


def fill_blank_prompt(card: dict) -> str:
    examples = card.get("examples") or []
    example_sentences = "\n".join(
        f"  - {e['sentence']}" for e in examples if isinstance(e, dict) and "sentence" in e
    )
    return f"""\
다음 카드로 빈칸 채우기 문제를 만드세요.

카드:
- 표현: {card["expression"]}
- 뜻: {(card.get("meaning") or {}).get("core", "")}
- 예문들:\n{example_sentences}

JSON 형식:
{{"question": "빈칸이 있는 문장 (___ 표시)", "answer": "{card["expression"]}", "hint": ""}}

규칙:
- 예문을 활용하되 그대로 쓰지 말고 변형
- 정답이 유일하게 결정되어야 함
"""
