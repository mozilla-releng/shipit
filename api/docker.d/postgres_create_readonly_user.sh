#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER shipituserreadonly PASSWORD 'shipitpasswordreadonly';
    ALTER DEFAULT PRIVILEGES FOR USER $POSTGRES_USER IN SCHEMA public GRANT SELECT ON TABLES TO shipituserreadonly;
EOSQL
