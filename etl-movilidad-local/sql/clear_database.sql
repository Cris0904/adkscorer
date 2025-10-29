-- Clear all data from Supabase database
-- Run this in Supabase SQL Editor to delete all news items and execution logs

-- Delete all news items
DELETE FROM news_item;

-- Delete all execution logs
DELETE FROM execution_log;

-- Reset sequences (optional - restarts IDs from 1)
ALTER SEQUENCE news_item_id_seq RESTART WITH 1;
ALTER SEQUENCE execution_log_id_seq RESTART WITH 1;

-- Verify deletion
SELECT 'News items remaining: ' || COUNT(*)::text FROM news_item
UNION ALL
SELECT 'Execution logs remaining: ' || COUNT(*)::text FROM execution_log;
