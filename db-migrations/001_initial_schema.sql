-- Migration 001: Initial Schema
-- ETL Movilidad Medellín
-- Date: 2024-01-15

BEGIN;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table: news_item
-- Main table for news articles
CREATE TABLE news_item (
    id BIGSERIAL PRIMARY KEY,

    -- Source information
    source VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    hash_url VARCHAR(64) UNIQUE NOT NULL,

    -- Content
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,

    -- ADK enrichment
    area VARCHAR(100),
    entities JSONB DEFAULT '[]'::jsonb,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    relevance_score DECIMAL(3,2) CHECK (relevance_score BETWEEN 0 AND 1),
    summary TEXT,

    -- Control
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'duplicate')),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for news_item
CREATE INDEX idx_news_published_at ON news_item(published_at DESC);
CREATE INDEX idx_news_source ON news_item(source);
CREATE INDEX idx_news_severity ON news_item(severity) WHERE status = 'active';
CREATE INDEX idx_news_area ON news_item(area) WHERE status = 'active';
CREATE INDEX idx_news_created_at ON news_item(created_at DESC);
CREATE INDEX idx_news_status ON news_item(status);
CREATE INDEX idx_news_tags ON news_item USING GIN(tags);

-- Table: news_embedding
-- Vector embeddings for semantic search
CREATE TABLE news_embedding (
    id BIGSERIAL PRIMARY KEY,
    news_id BIGINT NOT NULL REFERENCES news_item(id) ON DELETE CASCADE,
    embedding vector(768) NOT NULL,
    model VARCHAR(50) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for news_embedding
CREATE INDEX idx_embedding_news_id ON news_embedding(news_id);
CREATE INDEX idx_embedding_vector ON news_embedding
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Table: etl_execution_log
-- Audit trail for ETL executions
CREATE TABLE etl_execution_log (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    items_extracted INT DEFAULT 0,
    items_kept INT DEFAULT 0,
    items_discarded INT DEFAULT 0,
    items_duplicated INT DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb,
    duration_seconds INT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ
);

-- Indexes for etl_execution_log
CREATE INDEX idx_etl_log_started ON etl_execution_log(started_at DESC);
CREATE INDEX idx_etl_log_source ON etl_execution_log(source);
CREATE INDEX idx_etl_log_execution_id ON etl_execution_log(execution_id);

-- Function: update_updated_at_column
-- Automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for news_item
CREATE TRIGGER update_news_item_updated_at
BEFORE UPDATE ON news_item
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Function: generate_hash_url
-- Generate SHA256 hash for URL deduplication
CREATE OR REPLACE FUNCTION generate_hash_url(url_text TEXT)
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(digest(url_text, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Comments
COMMENT ON TABLE news_item IS 'Main table for news articles about mobility in Medellín';
COMMENT ON TABLE news_embedding IS 'Vector embeddings for semantic search';
COMMENT ON TABLE etl_execution_log IS 'Audit trail for ETL pipeline executions';

COMMENT ON COLUMN news_item.hash_url IS 'SHA256 hash of URL for deduplication';
COMMENT ON COLUMN news_item.severity IS 'Impact severity: low, medium, high, critical';
COMMENT ON COLUMN news_item.relevance_score IS 'ADK relevance score (0-1)';
COMMENT ON COLUMN news_item.entities IS 'Extracted entities (locations, organizations, dates)';
COMMENT ON COLUMN news_item.tags IS 'Classification tags (cierre_vial, accidente, etc)';

COMMIT;

-- Verify installation
DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed successfully';
    RAISE NOTICE 'Tables created: news_item, news_embedding, etl_execution_log';
    RAISE NOTICE 'Functions created: update_updated_at_column, generate_hash_url';
END $$;
