-- Semantic Search Function
-- Uses pgvector cosine similarity for semantic news search

-- Function: semantic_search
-- Find similar news articles based on embedding vector
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding vector(768),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    news_id BIGINT,
    title TEXT,
    body TEXT,
    published_at TIMESTAMPTZ,
    source VARCHAR(100),
    area VARCHAR(100),
    severity VARCHAR(20),
    tags TEXT[],
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ni.id,
        ni.title,
        ni.body,
        ni.published_at,
        ni.source,
        ni.area,
        ni.severity,
        ni.tags,
        1 - (ne.embedding <=> query_embedding) as similarity
    FROM news_embedding ne
    JOIN news_item ni ON ne.news_id = ni.id
    WHERE ni.status = 'active'
        AND 1 - (ne.embedding <=> query_embedding) > match_threshold
    ORDER BY ne.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION semantic_search IS 'Find semantically similar news articles using cosine similarity';

-- Function: semantic_search_with_filters
-- Semantic search with additional filters
CREATE OR REPLACE FUNCTION semantic_search_with_filters(
    query_embedding vector(768),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    filter_source VARCHAR(100) DEFAULT NULL,
    filter_severity VARCHAR(20) DEFAULT NULL,
    filter_area VARCHAR(100) DEFAULT NULL,
    date_from TIMESTAMPTZ DEFAULT NULL,
    date_to TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    news_id BIGINT,
    title TEXT,
    body TEXT,
    published_at TIMESTAMPTZ,
    source VARCHAR(100),
    area VARCHAR(100),
    severity VARCHAR(20),
    tags TEXT[],
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ni.id,
        ni.title,
        ni.body,
        ni.published_at,
        ni.source,
        ni.area,
        ni.severity,
        ni.tags,
        1 - (ne.embedding <=> query_embedding) as similarity
    FROM news_embedding ne
    JOIN news_item ni ON ne.news_id = ni.id
    WHERE ni.status = 'active'
        AND 1 - (ne.embedding <=> query_embedding) > match_threshold
        AND (filter_source IS NULL OR ni.source = filter_source)
        AND (filter_severity IS NULL OR ni.severity = filter_severity)
        AND (filter_area IS NULL OR ni.area = filter_area)
        AND (date_from IS NULL OR ni.published_at >= date_from)
        AND ni.published_at <= date_to
    ORDER BY ne.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION semantic_search_with_filters IS 'Semantic search with source, severity, area and date filters';

-- Function: find_similar_news
-- Find similar news to a given news_id
CREATE OR REPLACE FUNCTION find_similar_news(
    target_news_id BIGINT,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    news_id BIGINT,
    title TEXT,
    published_at TIMESTAMPTZ,
    source VARCHAR(100),
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
    target_embedding vector(768);
BEGIN
    -- Get embedding of target news
    SELECT embedding INTO target_embedding
    FROM news_embedding
    WHERE news_id = target_news_id
    LIMIT 1;

    IF target_embedding IS NULL THEN
        RAISE EXCEPTION 'No embedding found for news_id %', target_news_id;
    END IF;

    RETURN QUERY
    SELECT
        ni.id,
        ni.title,
        ni.published_at,
        ni.source,
        1 - (ne.embedding <=> target_embedding) as similarity
    FROM news_embedding ne
    JOIN news_item ni ON ne.news_id = ni.id
    WHERE ni.status = 'active'
        AND ni.id != target_news_id  -- Exclude the target itself
        AND 1 - (ne.embedding <=> target_embedding) > match_threshold
    ORDER BY ne.embedding <=> target_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION find_similar_news IS 'Find similar news articles to a given news item';

-- Function: get_news_by_tag_semantic
-- Combine tag filtering with semantic search
CREATE OR REPLACE FUNCTION get_news_by_tag_semantic(
    search_tags TEXT[],
    query_embedding vector(768) DEFAULT NULL,
    match_threshold FLOAT DEFAULT 0.6,
    match_count INT DEFAULT 20
)
RETURNS TABLE (
    news_id BIGINT,
    title TEXT,
    published_at TIMESTAMPTZ,
    tags TEXT[],
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF query_embedding IS NULL THEN
        -- Tag-only search
        RETURN QUERY
        SELECT
            ni.id,
            ni.title,
            ni.published_at,
            ni.tags,
            NULL::FLOAT as similarity
        FROM news_item ni
        WHERE ni.status = 'active'
            AND ni.tags && search_tags  -- Array overlap operator
        ORDER BY ni.published_at DESC
        LIMIT match_count;
    ELSE
        -- Hybrid: Tag filter + semantic search
        RETURN QUERY
        SELECT
            ni.id,
            ni.title,
            ni.published_at,
            ni.tags,
            1 - (ne.embedding <=> query_embedding) as similarity
        FROM news_embedding ne
        JOIN news_item ni ON ne.news_id = ni.id
        WHERE ni.status = 'active'
            AND ni.tags && search_tags
            AND 1 - (ne.embedding <=> query_embedding) > match_threshold
        ORDER BY ne.embedding <=> query_embedding
        LIMIT match_count;
    END IF;
END;
$$;

COMMENT ON FUNCTION get_news_by_tag_semantic IS 'Search news by tags with optional semantic similarity';
