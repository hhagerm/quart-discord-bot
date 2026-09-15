-- 
-- depends: 20260816_01_CamQ6-init

ALTER TABLE processed_events
    ADD COLUMN IF NOT EXISTS
    completed BOOLEAN NOT NULL DEFAULT FALSE;
    