-- Restrict the public roles without changing or deleting existing messages.
-- Does not replace server-side authentication, moderation or rate limiting.
BEGIN;
ALTER TABLE public.chat_altro_progetto ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.segnalazioni_altro_progetto ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.chat_altro_progetto FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.segnalazioni_altro_progetto FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON public.chat_altro_progetto TO anon, authenticated;
GRANT SELECT, INSERT ON public.segnalazioni_altro_progetto TO anon, authenticated;
GRANT USAGE ON SEQUENCE public.chat_altro_progetto_id_seq TO anon, authenticated;
GRANT USAGE ON SEQUENCE public.segnalazioni_altro_progetto_id_seq TO anon, authenticated;
DROP POLICY IF EXISTS allow_all ON public.chat_altro_progetto;
DROP POLICY IF EXISTS allow_all ON public.segnalazioni_altro_progetto;
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
COMMIT;
