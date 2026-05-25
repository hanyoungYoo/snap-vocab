from __future__ import annotations

GRADE_SYSTEM = """\
당신은 영어 학습 채점자입니다.
사용자 답변을 채점하고 간결한 피드백을 줍니다. JSON만 반환하세요.
"""


def grade_prompt(card: dict, question: str, correct_answer: str, user_answer: str) -> str:
    return f"""\
채점하세요.

표현: {card["expression"]}
문제: {question}
정답: {correct_answer}
사용자 답변: {user_answer}

JSON 형식:
{{"correct": true|false, "feedback": "2~3줄 피드백 (한국어)", "better_expression": ""}}

규칙:
- 유사 정답(철자 오류, 시제 변형 등)은 correct: true
- feedback은 간결, 왜 맞았는지/틀렸는지 + 팁
"""
