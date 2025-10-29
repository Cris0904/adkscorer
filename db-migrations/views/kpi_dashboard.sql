-- KPI Dashboard Views
-- ETL Movilidad Medellín

-- View: v_kpi_dashboard
-- Main KPI dashboard with hourly aggregations by source
CREATE OR REPLACE VIEW v_kpi_dashboard AS
WITH recent_executions AS (
    SELECT
        DATE_TRUNC('hour', started_at) as hour,
        source,
        SUM(items_extracted) as extracted,
        SUM(items_kept) as kept,
        SUM(items_discarded) as discarded,
        AVG(duration_seconds) as avg_duration,
        COUNT(*) FILTER (WHERE errors::text != '[]') as error_count,
        COUNT(*) as total_executions
    FROM etl_execution_log
    WHERE started_at > NOW() - INTERVAL '24 hours'
    GROUP BY 1, 2
)
SELECT
    hour,
    source,
    extracted,
    kept,
    discarded,
    ROUND(100.0 * kept / NULLIF(extracted, 0), 1) as keep_rate,
    ROUND(avg_duration, 2) as avg_duration,
    error_count,
    ROUND(100.0 * error_count / NULLIF(total_executions, 0), 1) as error_rate
FROM recent_executions
ORDER BY hour DESC, source;

COMMENT ON VIEW v_kpi_dashboard IS 'KPI dashboard with hourly metrics by source (last 24h)';

-- View: v_severity_distribution
-- Distribution of news by severity level (last 7 days)
CREATE OR REPLACE VIEW v_severity_distribution AS
SELECT
    severity,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM news_item
WHERE status = 'active'
    AND created_at > NOW() - INTERVAL '7 days'
    AND severity IS NOT NULL
GROUP BY severity
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END;

COMMENT ON VIEW v_severity_distribution IS 'Distribution of news by severity (last 7 days)';

-- View: v_top_areas
-- Top 10 areas with most incidents (last 7 days)
CREATE OR REPLACE VIEW v_top_areas AS
SELECT
    area,
    COUNT(*) as incident_count,
    COUNT(*) FILTER (WHERE severity IN ('high', 'critical')) as high_severity_count,
    MAX(published_at) as last_incident
FROM news_item
WHERE status = 'active'
    AND created_at > NOW() - INTERVAL '7 days'
    AND area IS NOT NULL
GROUP BY area
ORDER BY incident_count DESC
LIMIT 10;

COMMENT ON VIEW v_top_areas IS 'Top 10 areas with most mobility incidents (last 7 days)';

-- View: v_recent_news_with_embeddings
-- Recent news with embedding status
CREATE OR REPLACE VIEW v_recent_news_with_embeddings AS
SELECT
    ni.id,
    ni.source,
    ni.title,
    ni.published_at,
    ni.severity,
    ni.area,
    ni.tags,
    ni.relevance_score,
    CASE WHEN ne.id IS NOT NULL THEN true ELSE false END as has_embedding,
    ne.model as embedding_model,
    ni.created_at
FROM news_item ni
LEFT JOIN news_embedding ne ON ni.id = ne.news_id
WHERE ni.status = 'active'
    AND ni.created_at > NOW() - INTERVAL '7 days'
ORDER BY ni.published_at DESC;

COMMENT ON VIEW v_recent_news_with_embeddings IS 'Recent news with embedding generation status';

-- View: v_daily_summary
-- Daily summary of ETL performance
CREATE OR REPLACE VIEW v_daily_summary AS
SELECT
    DATE(started_at) as date,
    COUNT(DISTINCT source) as sources_processed,
    COUNT(*) as total_executions,
    SUM(items_extracted) as total_extracted,
    SUM(items_kept) as total_kept,
    SUM(items_discarded) as total_discarded,
    ROUND(100.0 * SUM(items_kept) / NULLIF(SUM(items_extracted), 0), 1) as keep_rate,
    AVG(duration_seconds) as avg_duration,
    SUM(CASE WHEN errors::text != '[]' THEN 1 ELSE 0 END) as error_count,
    ROUND(100.0 * SUM(CASE WHEN errors::text != '[]' THEN 1 ELSE 0 END) / COUNT(*), 1) as error_rate
FROM etl_execution_log
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(started_at)
ORDER BY date DESC;

COMMENT ON VIEW v_daily_summary IS 'Daily aggregated ETL performance metrics (last 30 days)';

-- View: v_embedding_coverage
-- Coverage of embeddings by day and model
CREATE OR REPLACE VIEW v_embedding_coverage AS
SELECT
    DATE(ne.created_at) as date,
    ne.model,
    COUNT(*) as embeddings_created,
    COUNT(DISTINCT ne.news_id) as unique_news_embedded
FROM news_embedding ne
WHERE ne.created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(ne.created_at), ne.model
ORDER BY date DESC, model;

COMMENT ON VIEW v_embedding_coverage IS 'Daily embedding generation statistics by model';

-- View: v_source_performance
-- Performance metrics by source (last 7 days)
CREATE OR REPLACE VIEW v_source_performance AS
WITH source_stats AS (
    SELECT
        source,
        COUNT(*) as executions,
        SUM(items_extracted) as extracted,
        SUM(items_kept) as kept,
        AVG(duration_seconds) as avg_duration,
        COUNT(*) FILTER (WHERE errors::text != '[]') as errors
    FROM etl_execution_log
    WHERE started_at > NOW() - INTERVAL '7 days'
    GROUP BY source
)
SELECT
    source,
    executions,
    extracted,
    kept,
    ROUND(100.0 * kept / NULLIF(extracted, 0), 1) as keep_rate,
    ROUND(avg_duration, 2) as avg_duration_seconds,
    errors,
    ROUND(100.0 * errors / executions, 1) as error_rate,
    -- Health score (0-100)
    ROUND(
        (
            (100.0 * kept / NULLIF(extracted, 0)) * 0.4 +  -- Keep rate (40%)
            (100 - (100.0 * errors / executions)) * 0.4 +    -- Error rate inverted (40%)
            LEAST(100, 100.0 * 60 / NULLIF(avg_duration, 0)) * 0.2  -- Speed score (20%)
        ),
        1
    ) as health_score
FROM source_stats
ORDER BY health_score DESC;

COMMENT ON VIEW v_source_performance IS 'Source performance with health score (last 7 days)';
