# Use an official Python runtime as a parent image
FROM python:3.10-slim


RUN apt-get update && apt-get install -y curl wget && rm -rf /var/lib/apt/lists/*


# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install PostgreSQL client for pg_isready
RUN apt-get update && apt-get install -y postgresql-client

# Copy the current directory contents into the container at /app
COPY . .

# Run Alembic migrations and start the FastAPI application
CMD ["sh", "-c", "until pg_isready -h postgres -p 5432; do echo 'Waiting for PostgreSQL...'; sleep 2; done; alembic upgrade head; uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
