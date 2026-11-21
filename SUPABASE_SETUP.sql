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

-- Accesso pubblico limitato a lettura e inserimento.
-- Mai concedere modifica/cancellazione anonima dei messaggi.
ALTER TABLE chat_altro_progetto          ENABLE ROW LEVEL SECURITY;
ALTER TABLE segnalazioni_altro_progetto  ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all" ON chat_altro_progetto;
DROP POLICY IF EXISTS "allow_all" ON segnalazioni_altro_progetto;
REVOKE ALL ON public.chat_altro_progetto FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.segnalazioni_altro_progetto FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON public.chat_altro_progetto TO anon, authenticated;
GRANT SELECT, INSERT ON public.segnalazioni_altro_progetto TO anon, authenticated;
GRANT USAGE ON SEQUENCE public.chat_altro_progetto_id_seq TO anon, authenticated;
GRANT USAGE ON SEQUENCE public.segnalazioni_altro_progetto_id_seq TO anon, authenticated;
DROP POLICY IF EXISTS community_read ON public.chat_altro_progetto;
DROP POLICY IF EXISTS community_insert ON public.chat_altro_progetto;
DROP POLICY IF EXISTS community_read ON public.segnalazioni_altro_progetto;
DROP POLICY IF EXISTS community_insert ON public.segnalazioni_altro_progetto;
CREATE POLICY community_read ON public.chat_altro_progetto
    FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY community_insert ON public.chat_altro_progetto
    FOR INSERT TO anon, authenticated
    WITH CHECK (length(contenuto) BETWEEN 1 AND 4000 AND length(coalesce(username, '')) <= 100);
CREATE POLICY community_read ON public.segnalazioni_altro_progetto
    FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY community_insert ON public.segnalazioni_altro_progetto
    FOR INSERT TO anon, authenticated
    WITH CHECK (length(contenuto) BETWEEN 1 AND 4000 AND length(coalesce(username, '')) <= 100);

-- Contatore persistente: eseguire anche sql/visit_counter.sql.
