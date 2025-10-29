-- Maintenance Scripts
-- ETL Movilidad Medellín

-- Script: Archive Old News
-- Archives news items older than 90 days
-- Should be run daily via maintenance workflow

DO $$
DECLARE
    archived_count INT;
BEGIN
    UPDATE news_item
    SET status = 'archived'
    WHERE status = 'active'
        AND published_at < NOW() - INTERVAL '90 days';

    GET DIAGNOSTICS archived_count = ROW_COUNT;
    RAISE NOTICE 'Archived % news items older than 90 days', archived_count;
END $$;

-- Script: Delete Old Execution Logs
-- Removes execution logs older than 30 days
-- Keeps database size manageable

DO $$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM etl_execution_log
    WHERE started_at < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % execution log entries older than 30 days', deleted_count;
END $$;

-- Script: Mark Duplicates
-- Identifies and marks duplicate entries based on hash_url
-- Keeps only the oldest entry as active

DO $$
DECLARE
    marked_count INT;
BEGIN
    UPDATE news_item
    SET status = 'duplicate'
    WHERE id IN (
        SELECT id
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY hash_url ORDER BY created_at) as rn
            FROM news_item
            WHERE status = 'active'
        ) t
        WHERE rn > 1
    );

    GET DIAGNOSTICS marked_count = ROW_COUNT;
    RAISE NOTICE 'Marked % duplicate entries', marked_count;
END $$;

-- Script: Vacuum and Analyze
-- Optimizes tables and updates statistics
-- Should be run weekly or after large deletions

VACUUM ANALYZE news_item;
VACUUM ANALYZE news_embedding;
VACUUM ANALYZE etl_execution_log;

-- Script: Delete Orphaned Embeddings
-- Removes embeddings without corresponding news items
-- Should not happen with CASCADE, but useful as safeguard

DO $$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM news_embedding
    WHERE news_id NOT IN (SELECT id FROM news_item);

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % orphaned embeddings', deleted_count;
END $$;

-- Script: Rebuild Vector Index
-- Rebuilds IVFFLAT index for better performance
-- Run if search becomes slow

REINDEX INDEX CONCURRENTLY idx_embedding_vector;

-- Script: Database Statistics
-- Shows current database usage and health
-- Useful for capacity planning

SELECT
    'news_item' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE status = 'active') as active_rows,
    COUNT(*) FILTER (WHERE status = 'archived') as archived_rows,
    COUNT(*) FILTER (WHERE status = 'duplicate') as duplicate_rows,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as last_7d,
    pg_size_pretty(pg_total_relation_size('news_item')) as table_size
FROM news_item
UNION ALL
SELECT
    'news_embedding',
    COUNT(*),
    COUNT(*),
    NULL,
    NULL,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days'),
    pg_size_pretty(pg_total_relation_size('news_embedding'))
FROM news_embedding
UNION ALL
SELECT
    'etl_execution_log',
    COUNT(*),
    COUNT(*),
    NULL,
    NULL,
    COUNT(*) FILTER (WHERE started_at > NOW() - INTERVAL '24 hours'),
    COUNT(*) FILTER (WHERE started_at > NOW() - INTERVAL '7 days'),
    pg_size_pretty(pg_total_relation_size('etl_execution_log'))
FROM etl_execution_log;

-- Script: Check for Missing Embeddings
-- Identifies active news items without embeddings

SELECT
    ni.id,
    ni.title,
    ni.source,
    ni.created_at,
    EXTRACT(EPOCH FROM (NOW() - ni.created_at))/3600 as hours_since_creation
FROM news_item ni
LEFT JOIN news_embedding ne ON ni.id = ne.news_id
WHERE ni.status = 'active'
    AND ne.id IS NULL
    AND ni.created_at > NOW() - INTERVAL '7 days'
ORDER BY ni.created_at DESC
LIMIT 20;

-- Script: Severity Distribution Check
-- Verifies reasonable distribution of severity levels
-- Alert if too many criticals or too few total

WITH severity_stats AS (
    SELECT
        severity,
        COUNT(*) as count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
    FROM news_item
    WHERE status = 'active'
        AND created_at > NOW() - INTERVAL '7 days'
        AND severity IS NOT NULL
    GROUP BY severity
)
SELECT
    severity,
    count,
    percentage || '%' as percentage,
    CASE
        WHEN severity = 'critical' AND percentage > 20 THEN '⚠️ Too many criticals'
        WHEN severity = 'low' AND percentage > 60 THEN '⚠️ Too many low severity'
        ELSE '✓ OK'
    END as status
FROM severity_stats
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END;

-- Script: Index Health Check
-- Verifies index usage and suggests missing indexes

SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND (tablename = 'news_item' OR tablename = 'news_embedding' OR tablename = 'etl_execution_log')
ORDER BY idx_scan DESC;
