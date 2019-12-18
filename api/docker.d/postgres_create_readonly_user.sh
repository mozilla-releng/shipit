#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER shipituserreadonly PASSWORD 'shipitpasswordreadonly';
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO shipituserreadonly;
EOSQL
