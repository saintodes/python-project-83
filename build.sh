#!/usr/bin/env bash

#Build this .sh while deploying on render.com

if [[ -f ./.env ]]; then
    source ./.env
else
    echo "Invalid or missing DATABASE_URL"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set."
    exit 1
else
    echo "Using DATABASE_URL."
fi

# Install app and setup the database
if make install && psql -a -d $DATABASE_URL -f database.sql; then
    echo "Database setup completed successfully."
else
    echo "Error: Failed to setup the database or make install."
    exit 1
fi

