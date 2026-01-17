---
description: Deploy the application using Docker Compose
---

# Deploy with Docker

## Prerequisites
- Docker
- Docker Compose

## Steps

1. Navigate to project directory:
```bash
cd /Volumes/ExternalSSD/Project/web-print-client
```

// turbo
2. Build and start container:
```bash
docker-compose up --build -d
```

// turbo
3. Check logs:
```bash
docker-compose logs -f print-bridge
```

// turbo
4. Verify health:
```bash
curl http://localhost:8000/health
```

## Stop

```bash
docker-compose down
```

## Data Persistence
SQLite database is persisted in `./app_data/printjobs.db`
