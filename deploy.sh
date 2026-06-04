#!/bin/bash

echo "=========================================="
echo "Store Intelligence Platform - Deployment"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Stop existing containers
echo ""
echo "Stopping existing containers..."
docker-compose down

# Build and start containers
echo ""
echo "Building Docker images..."
docker-compose build --no-cache

echo ""
echo "Starting containers..."
docker-compose up -d

# Wait for services to start
echo ""
echo "Waiting for services to start..."
sleep 10

# Check if services are running
echo ""
echo "Checking service status..."
docker-compose ps

# Check backend health
echo ""
echo "Checking backend health..."
curl -s http://localhost:8000/health || echo "Backend not responding yet"

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo "Backend API: http://localhost:8000"
echo "Dashboard: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo "=========================================="
