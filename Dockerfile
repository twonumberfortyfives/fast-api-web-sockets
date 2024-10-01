# Use an official Python runtime as a parent image
FROM python:3.10-slim

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

# Run the application using pg_isready to wait for PostgreSQL
CMD ["sh", "-c", "until pg_isready -h postgres -p 5432; do echo waiting for postgres; sleep 2; done; uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
