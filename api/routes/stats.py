from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from api.db import acquire
from api.deps import verify_api_key

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary")
async def summary(_: None = Depends(verify_api_key)) -> dict:
    async with acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM cards")
        due_today = await conn.fetchval(
            "SELECT COUNT(*) FROM cards WHERE next_review <= CURRENT_DATE"
        )
        accuracy_7d = await conn.fetchval(
            """SELECT COALESCE(AVG(correct::int)::float, 0)
               FROM review_logs WHERE reviewed_at >= NOW() - INTERVAL '7 days'"""
        )
        new_7d = await conn.fetchval(
            "SELECT COUNT(*) FROM cards WHERE created_at >= NOW() - INTERVAL '7 days'"
        )
        levels = await conn.fetch(
            "SELECT level, COUNT(*) AS n FROM cards GROUP BY level ORDER BY level"
        )

    return {
        "total": total,
        "due_today": due_today,
        "accuracy_7d": round((accuracy_7d or 0) * 100, 1),
        "new_7d": new_7d,
        "levels": [{"level": r["level"], "n": r["n"]} for r in levels],
    }


@router.get("/timeseries")
async def timeseries(
    _: None = Depends(verify_api_key),
    days: int = Query(default=30, ge=1, le=180),
) -> dict:
    async with acquire() as conn:
        rows = await conn.fetch(
            f"""SELECT
                  d::date AS day,
                  COALESCE(r.reviews, 0) AS reviews,
                  COALESCE(r.correct, 0) AS correct
                FROM generate_series(
                       CURRENT_DATE - INTERVAL '{days - 1} days',
                       CURRENT_DATE,
                       INTERVAL '1 day'
                     ) d
                LEFT JOIN (
                  SELECT date_trunc('day', reviewed_at)::date AS day,
                         COUNT(*) AS reviews,
                         SUM(correct::int) AS correct
                  FROM review_logs
                  WHERE reviewed_at >= CURRENT_DATE - INTERVAL '{days - 1} days'
                  GROUP BY 1
                ) r ON r.day = d::date
                ORDER BY day"""
        )

    points = []
    for r in rows:
        reviews = r["reviews"]
        correct = r["correct"]
        accuracy = round(correct / reviews * 100, 1) if reviews else None
        points.append(
            {
                "day": r["day"].isoformat(),
                "reviews": reviews,
                "correct": correct,
                "accuracy": accuracy,
            }
        )
    return {"points": points}


@router.get("/streak")
async def streak(_: None = Depends(verify_api_key)) -> dict:
    async with acquire() as conn:
        rows = await conn.fetch(
            """SELECT DISTINCT date_trunc('day', reviewed_at)::date AS day
               FROM review_logs
               ORDER BY day DESC"""
        )

    days = {r["day"] for r in rows}
    current = 0
    cursor = date.today()
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)

    longest = 0
    if days:
        sorted_days = sorted(days)
        run = 1
        best = 1
        for i in range(1, len(sorted_days)):
            if sorted_days[i] - sorted_days[i - 1] == timedelta(days=1):
                run += 1
                best = max(best, run)
            else:
                run = 1
        longest = best

    return {"current_streak": current, "longest_streak": longest}


@router.get("/upcoming")
async def upcoming(
    _: None = Depends(verify_api_key),
    days: int = Query(default=60, ge=7, le=180),
) -> dict:
    async with acquire() as conn:
        rows = await conn.fetch(
            """SELECT next_review::date AS day, COUNT(*) AS n
               FROM cards
               WHERE next_review::date BETWEEN CURRENT_DATE AND CURRENT_DATE + $1::int
               GROUP BY 1
               ORDER BY 1""",
            days,
        )
    return {"points": [{"day": r["day"].isoformat(), "n": r["n"]} for r in rows]}
