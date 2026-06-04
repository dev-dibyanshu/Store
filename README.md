# Store Intelligence Platform

Real-time retail analytics powered by computer vision.

## Quick Start

### Deploy with Docker

```bash
# Start all services
make deploy

# Or manually
./deploy.sh

# Load CV-generated events
make ingest-cv
```

Access:
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Server Deployment (Kubuntu)

### 1. Install Docker on Kubuntu

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Deploy Application

```bash
git clone <your-repo-url>
cd store
chmod +x deploy.sh
./deploy.sh
```

### 3. Access via Server IP

Replace `localhost` with your server IP:
- Dashboard: `http://<server-ip>:3000`
- API: `http://<server-ip>:8000`

### 4. Load Data

```bash
make ingest-cv
```

## Commands

```bash
make start       # Start services
make stop        # Stop services  
make logs        # View logs
make build       # Rebuild images
make clean       # Remove all containers
make ingest-cv   # Load CV events
```

## Features

✅ Computer vision person detection (YOLOv8)
✅ Multi-object tracking
✅ Zone engagement analysis
✅ Real-time analytics dashboard
✅ Multi-store support
✅ Auto-refresh metrics

```bash
# Start services
docker-compose up -d

# Load sample data
curl -X POST http://localhost:8000/ingest

# Access
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
```

## What It Does

- **Ingests** event streams from vision systems
- **Normalizes** inconsistent schemas 
- **Analyzes** footfall, zones, queues
- **Detects** anomalies in real-time
- **Visualizes** insights on live dashboard

## API

```bash
curl http://localhost:8000/analytics/store-summary?store_id=ST1076
curl http://localhost:8000/analytics/zones
curl http://localhost:8000/analytics/queue
curl http://localhost:8000/analytics/anomalies
```

## Commands

```bash
make start    # Start all services
make ingest   # Load sample data
make stop     # Stop services
make logs     # View logs
```
