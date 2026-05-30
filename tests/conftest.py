import os

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://snap:snap@localhost:15433/snap_vocab_test",
)
os.environ.setdefault("API_SECRET_KEY", "test-secret")

MIGRATIONS = [
    "migrations/001_cards.sql",
    "migrations/002_review_logs.sql",
    "migrations/003_pending_reviews.sql",
    "migrations/004_pending_reviews_question_type.sql",
]


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_pool():
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=5)
    async with pool.acquire() as conn:
        for path in MIGRATIONS:
            sql = open(path).read()
            await conn.execute(sql)
    yield pool
    async with pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS pending_reviews, review_logs, cards CASCADE")
        await conn.execute("DROP FUNCTION IF EXISTS set_updated_at CASCADE")
    await pool.close()


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def clean_tables(db_pool):
    yield
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE cards, review_logs, pending_reviews RESTART IDENTITY CASCADE")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client(db_pool):
    import api.db as db_module

    db_module._pool = db_pool

    from api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
