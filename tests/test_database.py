"""Integration tests, ONLY against a dedicated disposable local database.

TEST_DATABASE_URL must point to localhost and database seismic_test.
Requires psycopg[binary]. Never set it to a real Supabase connection.
"""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")
ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not DSN, reason="Disposable local database not configured")


@pytest.fixture
def database():
    info = psycopg.conninfo.conninfo_to_dict(DSN)
    if info.get("dbname") != "seismic_test" or info.get("host") not in ("127.0.0.1", "localhost"):
        pytest.fail("Refusing to modify anything except a disposable local seismic_test database")
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute("SET client_encoding = 'UTF8'")
        db.execute("""
            DO $$ BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                CREATE ROLE anon NOLOGIN;
              END IF;
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                CREATE ROLE authenticated NOLOGIN;
              END IF;
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
                CREATE ROLE service_role NOLOGIN;
              END IF;
            END $$;
            DROP TABLE IF EXISTS public.visit_sessions CASCADE;
            DROP TABLE IF EXISTS public.visit_stats CASCADE;
            DROP TABLE IF EXISTS public.chat_altro_progetto CASCADE;
            DROP TABLE IF EXISTS public.segnalazioni_altro_progetto CASCADE;
            GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
        """)
        yield db


def migrate(db):
    db.execute((ROOT / "sql/visit_counter.sql").read_text())


def register(token):
    with psycopg.connect(DSN) as db:
        return db.execute("SELECT public.register_visit(%s)", (token,)).fetchone()[0]


def test_migration_preserves_existing_count_and_is_repeatable(database):
    database.execute("CREATE TABLE public.visit_stats (id INT PRIMARY KEY, count INT)")
    database.execute("INSERT INTO public.visit_stats VALUES (1, 12345)")
    migrate(database)
    migrate(database)
    assert database.execute("SELECT count FROM public.visit_stats WHERE id=1").fetchone()[0] == 12345


def test_atomic_concurrent_unique_visits(database):
    migrate(database)
    tokens = [uuid4() for _ in range(60)]
    with ThreadPoolExecutor(max_workers=10) as workers:
        list(workers.map(register, tokens))
    assert database.execute("SELECT count FROM public.visit_stats WHERE id=1").fetchone()[0] == 60


def test_duplicate_concurrent_retries_only_count_once(database):
    migrate(database)
    token = uuid4()
    with ThreadPoolExecutor(max_workers=10) as workers:
        list(workers.map(register, [token] * 40))
    assert database.execute("SELECT count FROM public.visit_stats WHERE id=1").fetchone()[0] == 1


def test_public_client_cannot_reset_total(database):
    migrate(database)
    database.execute("SET ROLE anon")
    try:
        assert database.execute("SELECT public.register_visit(%s)", (uuid4(),)).fetchone()[0] == 1
        for sql in (
            "UPDATE public.visit_stats SET count=0",
            "DELETE FROM public.visit_stats",
            "INSERT INTO public.visit_stats VALUES (2,0)",
            "SELECT * FROM public.visit_sessions",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                database.execute(sql)
    finally:
        database.execute("RESET ROLE")


def test_community_can_post_but_not_overwrite_or_delete(database):
    database.execute((ROOT / "SUPABASE_SETUP.sql").read_text())
    # Simulate privileges left by the old unsafe installation too.
    database.execute("""
        CREATE POLICY allow_all ON public.chat_altro_progetto
          FOR ALL USING (true) WITH CHECK (true);
        GRANT ALL ON public.chat_altro_progetto TO anon;
    """)
    sql = (ROOT / "sql/community_permissions.sql").read_text()
    database.execute(sql)
    database.execute(sql)
    database.execute("SET ROLE anon")
    try:
        database.execute("INSERT INTO public.chat_altro_progetto (username, contenuto) VALUES ('test','valid message')")
        assert database.execute("SELECT count(*) FROM public.chat_altro_progetto").fetchone()[0] == 1
        for statement in (
            "UPDATE public.chat_altro_progetto SET contenuto='changed'",
            "DELETE FROM public.chat_altro_progetto",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                database.execute(statement)
    finally:
        database.execute("RESET ROLE")
