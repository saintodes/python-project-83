#!/usr/bin/env bash
#dev #export DATABASE_URL="postgresql://dev:devpass@127.0.0.1:5432/database"

# Parse db url
regex="postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
if [[ $DATABASE_URL =~ $regex ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_USER_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    echo "Invalid or missing DATABASE_URL"
    exit 1
fi

#Create db role, db
sudo -u postgres psql -c "CREATE ROLE $DB_USER WITH CREATEDB LOGIN PASSWORD '$DB_USER_PASSWORD';"
sudo -u postgres createdb --owner=$DB_USER $DB_NAME
make install && psql -a -d $DATABASE_URL -f database.sql