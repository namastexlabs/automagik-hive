#!/bin/bash
set -e

# Initialize PostgreSQL database if not exists
if [ ! -f /var/lib/postgresql/data/pgdata/PG_VERSION ]; then
    echo "Initializing PostgreSQL database..."
    
    # Initialize PostgreSQL data directory
    /usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/data/pgdata --locale=C.UTF-8 --encoding=UTF8
    
    # Start PostgreSQL temporarily for setup
    /usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data/pgdata -w start
    
    # Create database user and database
    createuser --superuser hive
    createdb -O hive hive_genie
    psql -c "ALTER USER hive PASSWORD 'genie_secure_password';"
    psql -d hive_genie -c "CREATE EXTENSION IF NOT EXISTS vector;"
    
    # Stop PostgreSQL  
    /usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data/pgdata stop
    
    echo "PostgreSQL database initialized successfully"
fi

# Execute the main command
exec "$@"