# Use a Python slim image as the base
FROM python:3.9-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app_root 

# Install system dependencies that might be needed for building Python packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file from your specified location into the container's WORKDIR
COPY splitWiseBackendNew/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY splitWiseBackendNew/app ./app

# Create a directory for the SQLite database if it doesn't exist.
# This path is relative to the WORKDIR.
RUN mkdir -p ./data

# Set default environment variables for the application.
ENV PROJECT_NAME="Splitwise API (Docker Single Stage)"
ENV API_V1_STR="/api/v1"
ENV DATABASE_URL="sqlite:///./data/app_database.db" 
ENV SECRET_KEY="default_docker_secret_key_please_override_at_runtime_single_stage"
ENV ALGORITHM="HS256"
ENV ACCESS_TOKEN_EXPIRE_MINUTES="1440"
ENV REDIS_HOST="redis-server" 
ENV REDIS_PORT="6379"
ENV REDIS_DB="0"
ENV CACHE_EXPIRATION_SECONDS="300"

# Expose the port the application will run on
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]