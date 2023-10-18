#!/usr/bin/env bash

#Build this .sh to develop app at locahlost, but db at render.com

# Source .env file to get environment variables
if [[ -f ./.env ]]; then
    source ./.env
else
    echo "Error: .env file not found in the root directory."
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set."
    exit 1
else
    echo "Using DATABASE_URL: $DATABASE_URL"
fi

# Parse db url wo port
regex="postgres://([^:]+):([^@]+)@([^/]+)/(.+)"

if [[ $DATABASE_URL =~ $regex ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_USER_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_NAME="${BASH_REMATCH[4]}"
    
    echo "Parsed DATABASE_URL:"
    echo "User: $DB_USER"
    echo "Host: $DB_HOST"
    echo "Database Name: $DB_NAME"
else
    echo "Error: Invalid or missing DATABASE_URL format."
    exit 1
fi

# Install app and setup the database
if make install && psql -a -d $DATABASE_URL -f database.sql; then
    echo "Database setup completed successfully."
else
    echo "Error: Failed to setup the database."
    exit 1
fi

