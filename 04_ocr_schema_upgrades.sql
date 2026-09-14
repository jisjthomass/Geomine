-- =====================================================================
-- 04_ocr_schema_upgrades.sql
-- Enterprise OCR Pipeline — Database Schema Upgrades
-- =====================================================================

-- 1. Relax NOT NULL constraints on historical_drilling_events
--    OCR extractions are often partial; we cannot guarantee every field.
ALTER TABLE historical_drilling_events ALTER COLUMN well_id DROP NOT NULL;
ALTER TABLE historical_drilling_events ALTER COLUMN latitude DROP NOT NULL;
ALTER TABLE historical_drilling_events ALTER COLUMN longitude DROP NOT NULL;
ALTER TABLE historical_drilling_events ALTER COLUMN event_depth DROP NOT NULL;
ALTER TABLE historical_drilling_events ALTER COLUMN event_type DROP NOT NULL;
ALTER TABLE historical_drilling_events ALTER COLUMN formation DROP NOT NULL;

-- 2. Add audit trail columns to historical_drilling_events
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='historical_drilling_events' AND column_name='source_file') THEN
        ALTER TABLE historical_drilling_events ADD COLUMN source_file TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='historical_drilling_events' AND column_name='file_hash') THEN
        ALTER TABLE historical_drilling_events ADD COLUMN file_hash VARCHAR(64);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='historical_drilling_events' AND column_name='document_class') THEN
        ALTER TABLE historical_drilling_events ADD COLUMN document_class VARCHAR(50);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='historical_drilling_events' AND column_name='extraction_confidence') THEN
        ALTER TABLE historical_drilling_events ADD COLUMN extraction_confidence DOUBLE PRECISION;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='historical_drilling_events' AND column_name='processed_at') THEN
        ALTER TABLE historical_drilling_events ADD COLUMN processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- 3. Create underground_infrastructure table (referenced but never created)
CREATE TABLE IF NOT EXISTS underground_infrastructure (
    id SERIAL PRIMARY KEY,
    infra_id VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    depth_m DOUBLE PRECISION,
    infra_type VARCHAR(100),
    source_file TEXT,
    file_hash VARCHAR(64),
    document_class VARCHAR(50),
    extraction_confidence DOUBLE PRECISION,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create processed_files table for duplicate detection
CREATE TABLE IF NOT EXISTS processed_files (
    id SERIAL PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    file_size_bytes BIGINT,
    document_class VARCHAR(50),
    event_confidence DOUBLE PRECISION,
    infra_confidence DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'PROCESSED',
    warnings TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create ocr_corrections table for feedback loop (Tier 3)
CREATE TABLE IF NOT EXISTS ocr_corrections (
    id SERIAL PRIMARY KEY,
    record_type VARCHAR(30) NOT NULL,  -- 'drilling_event' or 'infrastructure'
    record_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    corrected_by VARCHAR(100) DEFAULT 'user',
    corrected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Index for fast duplicate lookups
CREATE INDEX IF NOT EXISTS idx_processed_files_hash ON processed_files (file_hash);
CREATE INDEX IF NOT EXISTS idx_hde_source_file ON historical_drilling_events (source_file);
