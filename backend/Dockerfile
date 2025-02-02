# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements/base.txt requirements/prod.txt requirements/dev.txt /app/requirements/

# Install dependencies
RUN pip install --no-cache-dir -r requirements/base.txt -r requirements/prod.txt

# Copy the rest of the application code into the container
COPY . /app

# Install the backend package in development mode
RUN pip install -e .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
