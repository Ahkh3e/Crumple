FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    build-base \
    postgresql-dev \
    python3-dev \
    libffi-dev

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
# Configure Flask to listen on all interfaces
ENV HOST=0.0.0.0
ENV PORT=3000

# Add the application directory to PYTHONPATH
ENV PYTHONPATH=/app

# Run the application with uvicorn
CMD ["uvicorn", "asgi:app", "--host", "0.0.0.0", "--port", "3000", "--reload", "--log-level", "info"]
