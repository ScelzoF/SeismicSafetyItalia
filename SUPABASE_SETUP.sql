-- ============================================================
-- SeismicSafetyItalia (Sismocampania) — Setup tabelle Supabase
-- Progetto: usobrbklqjwjvxesfbxk.supabase.co
-- Eseguire nel SQL Editor di Supabase
-- ============================================================

-- Tabella messaggi chat pubblica
CREATE TABLE IF NOT EXISTS chat_altro_progetto (
    id         BIGSERIAL PRIMARY KEY,
    username   TEXT,
    contenuto  TEXT NOT NULL,
    regione    TEXT DEFAULT 'Campania',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella segnalazioni eventi
CREATE TABLE IF NOT EXISTS segnalazioni_altro_progetto (
    id         BIGSERIAL PRIMARY KEY,
    username   TEXT,
    contenuto  TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Abilita accesso pubblico (RLS)
ALTER TABLE chat_altro_progetto          ENABLE ROW LEVEL SECURITY;
ALTER TABLE segnalazioni_altro_progetto  ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all" ON chat_altro_progetto;
CREATE POLICY "allow_all" ON chat_altro_progetto         FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all" ON segnalazioni_altro_progetto;
CREATE POLICY "allow_all" ON segnalazioni_altro_progetto FOR ALL USING (true) WITH CHECK (true);
