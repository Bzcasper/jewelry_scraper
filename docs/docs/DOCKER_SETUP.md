
Docker Setup
Containerizing the Jewelry Scraper application using Docker ensures consistent environments and simplifies deployment. This guide provides step-by-step instructions to set up Docker containers for both frontend and backend services.

Table of Contents
Prerequisites
Dockerfile Configuration
Docker Compose Setup
Building and Running Containers
Managing Containers
Environment Variables
Volumes and Data Persistence
Networking
Scaling Services
Troubleshooting
1. Prerequisites
Ensure the following are installed on your system:

Docker: Install Docker
Docker Compose: Install Docker Compose
2. Dockerfile Configuration
Backend Dockerfile (backend/Dockerfile)
dockerfile
Copy code
# Use official Python image as base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:8000", "app:app"]
Frontend Dockerfile (frontend/Dockerfile)
dockerfile
Copy code
# Use official Node.js image as base
FROM node:16-alpine as build

# Set work directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy project
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
3. Docker Compose Setup
The docker-compose.yml file orchestrates multiple containers for the application.

yaml
Copy code
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: jewelry_scraper_backend
    restart: always
    env_file:
      - .env
    ports:
      - "5000:5000"
    volumes:
      - ./backend:/app
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
      - db

  frontend:
    build: ./frontend
    container_name: jewelry_scraper_frontend
    restart: always
    env_file:
      - .env
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    depends_on:
      - backend

  db:
    image: postgres:13
    container_name: jewelry_scraper_db
    restart: always
    environment:
      POSTGRES_USER: yourusername
      POSTGRES_PASSWORD: yourpassword
      POSTGRES_DB: jewelry_scraper
    volumes:
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    container_name: jewelry_scraper_redis
    restart: always
    ports:
      - "6379:6379"

  prometheus:
    image: prom/prometheus
    container_name: jewelry_scraper_prometheus
    restart: always
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    container_name: jewelry_scraper_grafana
    restart: always
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  db_data:
  grafana_data:
4. Building and Running Containers
Navigate to the Project Root:

bash
Copy code
cd jewelry_scraper
Build and Start Containers:

bash
Copy code
docker-compose up -d --build
Verify Running Containers:

bash
Copy code
docker-compose ps
5. Managing Containers
Viewing Logs
Backend Logs:

bash
Copy code
docker-compose logs -f backend
Frontend Logs:

bash
Copy code
docker-compose logs -f frontend
Stopping Containers
bash
Copy code
docker-compose down
Restarting Containers
bash
Copy code
docker-compose restart
6. Environment Variables
Ensure that the .env file is correctly set up with all necessary environment variables. Docker Compose uses this file to inject variables into containers.

env
Copy code
# Example .env file

# Backend
FLASK_APP=app.py
FLASK_ENV=production
PORT=5000

# Scraping
MAX_CONCURRENT_REQUESTS=8
DOWNLOAD_DELAY=2
ROTATING_PROXY_LIST_PATH=proxies.txt

# Database
DATABASE_URL=postgresql://yourusername:yourpassword@db:5432/jewelry_scraper

# Image Storage
IMAGE_STORAGE_PATH=/app/data/images
MAX_IMAGE_SIZE=1200

# Caching
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://redis:6379/0
CACHE_DEFAULT_TIMEOUT=300
7. Volumes and Data Persistence
Database Data: Stored in the db_data Docker volume to persist PostgreSQL data.
Grafana Data: Stored in the grafana_data Docker volume to persist Grafana dashboards and configurations.
Application Data: Stored in the data/ directory to persist scraped data and backups.
Logs: Stored in the logs/ directory for persistent logging.
8. Networking
Docker Compose sets up an internal network allowing services to communicate using service names.

Backend Service: Accessible at http://backend:5000
Frontend Service: Accessible at http://localhost:3000
Prometheus: Accessible at http://localhost:9090
Grafana: Accessible at http://localhost:3001
9. Scaling Services
To scale services like the backend for handling more scraping jobs:

bash
Copy code
docker-compose up -d --scale backend=3
This command will run three instances of the backend service.

10. Troubleshooting
Common Issues
Port Conflicts: Ensure that the ports specified in docker-compose.yml are not in use by other applications.

Environment Variables Not Loaded: Verify that the .env file exists and is correctly referenced in docker-compose.yml.

Database Connection Errors: Ensure that the database service (db) is running and accessible by the backend.

Viewing Container Logs
Use Docker logs to diagnose issues.

bash
Copy code
docker-compose logs backend
docker-compose logs frontend
Rebuilding Containers
If changes are made to Dockerfiles or dependencies, rebuild the containers.

bash
Copy code
docker-compose up -d --build
End of Docker Setup Documentation 
