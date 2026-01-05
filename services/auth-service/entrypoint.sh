#!/bin/sh

echo "Starting Django container..."

# Wait for Postgres
echo "Waiting for PostgreSQL..."
while ! nc -z "$AUTH_DB_HOST" "$AUTH_DB_PORT"; do
  sleep 1
done
echo "PostgreSQL is available!"

# Apply database migrations
echo "Applying migrations..."
python manage.py makemigrations
python manage.py migrate --noinput

# Optional: collect static files (safe in dev)
# echo "🎨 Collecting static files..."
# python manage.py collectstatic --noinput

# Start Django server
echo "Starting Django server..."
exec "$@"
