FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
# Use internal Docker network hostnames
ENV DATABASE_URL=postgresql://crumple:crumple@postgres:5432/crumple
ENV RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672

# Add the application directory to PYTHONPATH
ENV PYTHONPATH=/app

# Run the worker with app context
CMD ["python", "-c", "from app import create_app; app = create_app('production'); app.app_context().push(); from app.tasks.sync import run_sync; run_sync()"]
