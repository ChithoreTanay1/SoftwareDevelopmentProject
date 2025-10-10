-- PostgreSQL Configuration for Quiz Game
-- Run these commands in psql as superuser

-- Enable performance extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Set optimal parameters for quiz game workload
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Connection settings
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET superuser_reserved_connections = 3;

-- WAL settings for performance
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET max_wal_size = '1GB';
ALTER SYSTEM SET min_wal_size = '80MB';

-- Reload configuration
SELECT pg_reload_conf();

-- Grant necessary permissions to quiz_user
GRANT pg_read_all_stats TO quiz_user;