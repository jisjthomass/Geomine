-- Task 2: Embeddings Table (Round 2 RAG)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS historical_event_embeddings (
    id BIGSERIAL PRIMARY KEY,
    
    event_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    
    -- NOTE: Dimension not hard-coded yet! 
    -- If using Gemini text-embedding-004, change to VECTOR(768) before creating indexes
    embedding VECTOR,
    
    well_id TEXT,
    depth_m DOUBLE PRECISION,
    formation TEXT,
    event_type TEXT,
    
    report_id TEXT,
    document_type TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
