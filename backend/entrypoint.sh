#!/bin/sh

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! python -c "import psycopg2; psycopg2.connect(host='db', dbname='${POSTGRES_DB}', user='${POSTGRES_USER}', password='${POSTGRES_PASSWORD}')" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start server
echo "Starting server..."
exec "$@"