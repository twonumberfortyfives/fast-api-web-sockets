#!/bin/sh

until pg_isready -h postgres -p 5432; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

# Run Alembic migrations
alembic revision --autogenerate -m "initialized"
alembic upgrade head

# Start the FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
