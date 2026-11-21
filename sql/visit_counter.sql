-- Run ONCE in the Supabase SQL Editor BEFORE deploying the new Python code.
-- Safe to repeat: an existing total is never replaced.
BEGIN;

CREATE TABLE IF NOT EXISTS public.visit_stats (
    id BIGINT PRIMARY KEY,
    count BIGINT NOT NULL DEFAULT 0 CHECK (count >= 0)
);
ALTER TABLE public.visit_stats ALTER COLUMN count TYPE BIGINT;
INSERT INTO public.visit_stats (id, count) VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.visit_sessions (
    visit_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.visit_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.visit_sessions ENABLE ROW LEVEL SECURITY;

-- A public client can read the total, but cannot overwrite or reset it.
REVOKE ALL ON public.visit_stats FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.visit_sessions FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.visit_stats TO anon, authenticated, service_role;
DROP POLICY IF EXISTS visit_stats_read ON public.visit_stats;
CREATE POLICY visit_stats_read ON public.visit_stats
    FOR SELECT TO anon, authenticated USING (id = 1);

CREATE OR REPLACE FUNCTION public.register_visit(p_visit_id UUID)
RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    total BIGINT;
BEGIN
    IF p_visit_id IS NULL THEN
        RAISE EXCEPTION 'visit identifier is required';
    END IF;

    INSERT INTO public.visit_sessions (visit_id) VALUES (p_visit_id)
    ON CONFLICT (visit_id) DO NOTHING;
    IF FOUND THEN
        UPDATE public.visit_stats
        SET count = GREATEST(COALESCE(count, 0), 0) + 1
        WHERE id = 1 RETURNING count INTO total;
        IF NOT FOUND THEN
            -- Roll back the session insert too, so a later retry can succeed.
            RAISE EXCEPTION 'visit counter is not initialized';
        END IF;
    ELSE
        SELECT count INTO total FROM public.visit_stats WHERE id = 1;
    END IF;
    RETURN total;
END;
$$;

REVOKE ALL ON FUNCTION public.register_visit(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.register_visit(UUID)
    TO anon, authenticated, service_role;
NOTIFY pgrst, 'reload schema';
COMMIT;
