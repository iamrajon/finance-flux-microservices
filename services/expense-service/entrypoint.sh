#!/bin/sh

# Wait for database connection
echo "Waiting for database connection at $EXPENSE_DB_HOST:$EXPENSE_DB_PORT..."
while ! nc -z "$EXPENSE_DB_HOST" "$EXPENSE_DB_PORT"; do
  sleep 0.1
done
echo "Database connected!"

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"
