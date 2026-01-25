-- One-time setup for local Postgres (no Docker).
-- Run: psql -d postgres -f scripts/init-local-db.sql
-- On some systems: psql -U postgres -d postgres -f scripts/init-local-db.sql
-- If user/db already exist, you'll see errors; that's ok.

CREATE USER spreads WITH PASSWORD 'spreads';
CREATE DATABASE spreads OWNER spreads;
