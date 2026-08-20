-- Phase 5: Update Reading Plans Table for 365-day M'Cheyne Schedule

ALTER TABLE reading_plans 
ADD COLUMN IF NOT EXISTS scheduled_date DATE,
ADD COLUMN IF NOT EXISTS scripture_reference TEXT;

-- Reload the PostgREST schema cache so the API recognizes the new columns immediately
NOTIFY pgrst, 'reload schema';
