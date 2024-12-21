# File: /backend/Dockerfile

FROM python:3.10-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    chromium-driver \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/images logs

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_DRIVER_PATH=/usr/bin/chromedriver

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:5000", "--worker-class=uvicorn.workers.UvicornWorker", "api.app:app"]