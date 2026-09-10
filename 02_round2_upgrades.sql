-- Round 2 schema upgrades
-- These columns are queried by data_loader.py but missing from the original pg_dump
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS cause TEXT DEFAULT '';
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS mitigation TEXT DEFAULT '';
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS outcome TEXT DEFAULT '';

-- NPT Financial Engine columns
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS npt_duration_minutes INT DEFAULT 0;
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS npt_category VARCHAR(50) DEFAULT 'Unknown';
