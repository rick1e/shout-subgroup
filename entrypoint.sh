#!/bin/sh

# Check if the first argument is 'migrate' to decide whether to run migrations
if [ "$MIGRATE" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head  # Run the Alembic migrations
fi

echo "Database migrations completed"
# When you use exec "$@" in an entrypoint script inside a Docker container:
# The script will replace itself with the application (e.g., python main.py).
# The container will now run your app as the main process, and if Docker sends signals to the container (like docker stop), they will be properly sent to the app.
# This ensures that your application runs as the main process in the container, without unnecessary intermediary processes.
exec "$@"  # Start the application
