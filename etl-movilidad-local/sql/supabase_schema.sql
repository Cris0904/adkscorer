-- Supabase Schema for ETL Movilidad Medellín
-- Run this in Supabase SQL Editor to create the database schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main news table
CREATE TABLE IF NOT EXISTS news_item (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    hash_url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- ADK enrichment fields
    severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')),
    tags JSONB DEFAULT '[]',
    area TEXT,
    entities JSONB DEFAULT '[]',
    summary TEXT,
    relevance_score REAL,

    -- Status and metadata
    status TEXT DEFAULT 'active',
    alerted BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Execution log table
CREATE TABLE IF NOT EXISTS execution_log (
    id BIGSERIAL PRIMARY KEY,
    execution_time TIMESTAMP WITH TIME ZONE NOT NULL,
    news_extracted INTEGER DEFAULT 0,
    news_deduplicated INTEGER DEFAULT 0,
    news_scored INTEGER DEFAULT 0,
    news_kept INTEGER DEFAULT 0,
    news_discarded INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    duration_seconds REAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_news_hash_url ON news_item(hash_url);
CREATE INDEX IF NOT EXISTS idx_news_published_at ON news_item(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_severity ON news_item(severity);
CREATE INDEX IF NOT EXISTS idx_news_source ON news_item(source);
CREATE INDEX IF NOT EXISTS idx_news_created_at ON news_item(created_at DESC);

-- Create index on JSONB fields for better query performance
CREATE INDEX IF NOT EXISTS idx_news_tags ON news_item USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_news_entities ON news_item USING GIN (entities);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to call the function before update
CREATE TRIGGER update_news_item_updated_at
    BEFORE UPDATE ON news_item
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE news_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_log ENABLE ROW LEVEL SECURITY;

-- Create policies for read access (anyone can read)
CREATE POLICY "Enable read access for all users" ON news_item
    FOR SELECT USING (true);

CREATE POLICY "Enable read access for execution logs" ON execution_log
    FOR SELECT USING (true);

-- Create policies for insert/update/delete (only service role)
-- Note: Use service_role key for write operations from your ETL pipeline
CREATE POLICY "Enable insert for service role only" ON news_item
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for service role only" ON news_item
    FOR UPDATE USING (true);

CREATE POLICY "Enable insert for execution logs" ON execution_log
    FOR INSERT WITH CHECK (true);

-- Create a view for public API consumption (optional)
CREATE OR REPLACE VIEW public_news AS
SELECT
    id,
    source,
    url,
    title,
    summary,
    severity,
    tags,
    area,
    entities,
    relevance_score,
    published_at,
    created_at
FROM news_item
WHERE status = 'active'
ORDER BY published_at DESC;

-- Grant access to the view
GRANT SELECT ON public_news TO anon, authenticated;

-- Create a function to get recent high severity news
CREATE OR REPLACE FUNCTION get_high_severity_news(limit_count INTEGER DEFAULT 20)
RETURNS TABLE (
    id BIGINT,
    source TEXT,
    url TEXT,
    title TEXT,
    summary TEXT,
    severity TEXT,
    tags JSONB,
    area TEXT,
    published_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.source,
        n.url,
        n.title,
        n.summary,
        n.severity,
        n.tags,
        n.area,
        n.published_at
    FROM news_item n
    WHERE n.severity IN ('high', 'critical')
    AND n.status = 'active'
    ORDER BY n.published_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get statistics
CREATE OR REPLACE FUNCTION get_news_stats()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_news', (SELECT COUNT(*) FROM news_item WHERE status = 'active'),
        'by_severity', (
            SELECT json_object_agg(COALESCE(severity, 'unknown'), count)
            FROM (
                SELECT severity, COUNT(*) as count
                FROM news_item
                WHERE status = 'active'
                GROUP BY severity
            ) s
        ),
        'by_source', (
            SELECT json_object_agg(source, count)
            FROM (
                SELECT source, COUNT(*) as count
                FROM news_item
                WHERE status = 'active'
                GROUP BY source
            ) src
        ),
        'recent_executions', (
            SELECT COUNT(*)
            FROM execution_log
            WHERE created_at > NOW() - INTERVAL '7 days'
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE news_item IS 'Stores news items extracted and scored by the ETL pipeline';
COMMENT ON TABLE execution_log IS 'Logs each execution of the ETL pipeline';
COMMENT ON COLUMN news_item.hash_url IS 'SHA256 hash of URL for deduplication';
COMMENT ON COLUMN news_item.tags IS 'JSON array of tags extracted by ADK';
COMMENT ON COLUMN news_item.entities IS 'JSON array of entities extracted by ADK';
COMMENT ON COLUMN news_item.relevance_score IS 'Relevance score from 0.0 to 1.0';
