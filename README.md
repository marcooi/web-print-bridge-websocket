# Local Print Bridge

A lightweight, containerized application that bridges **Dynamics 365 (D365)** and local USB printers using FastAPI and Server-Side Rendering.

## Architecture

```
┌─────────────┐     POST /api/print-jobs     ┌─────────────────┐
│ Dynamics 365│ ──────────────────────────► │ FastAPI Server  │
│             │ ◄────────────────────────── │ (Docker)        │
└─────────────┘     { job_id, view_url }     │                 │
                                             │ SQLite DB       │
       ┌───────────────────────────────────► │ Jinja2 SSR      │
       │  Open view_url in browser           └────────┬────────┘
       │                                              │
┌──────┴──────┐                              ┌────────▼────────┐
│   Browser   │ ◄──────── HTML Page ──────── │  /view?id=uuid  │
│             │                              └─────────────────┘
│  JavaScript │ ──── WebSocket ────┐
└─────────────┘                    │
                                   ▼
                          ┌─────────────────┐
                          │ Local WS Bridge │  ws://localhost:5001/printers
                          │ (User's PC)     │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │   USB Printer   │
                          └─────────────────┘
```

## Tech Stack

- **Backend:** Python FastAPI
- **Database:** SQLite + SQLAlchemy
- **Templating:** Jinja2 SSR
- **Frontend:** HTML5 + Tailwind CSS (CDN) + Vanilla JS
- **Deployment:** Docker / Docker Compose

## Quick Start

### 1. Build & Run (Docker)

```bash
# Clone or navigate to project
cd web-print-client

# Build and start container
docker-compose up --build -d

# Check logs
docker-compose logs -f print-bridge

# Stop
docker-compose down
```

### 2. Local Development (Without Docker)

```bash
# Navigate to project
cd web-print-client

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Run with hot-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000` with auto-reload on code changes.

### 3. Test API

```bash
# Create a print job with ZPL data
curl -X POST http://localhost:8000/api/print-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"zpl": "^XA\n^FO50,50\n^BQN,2,5\n^FDQA,HELLO WORLD^FS\n^XZ\n"},
      {"zpl": "^XA\n^FO50,50\n^BQN,2,5\n^FDQA,SECOND LABEL^FS\n^XZ\n"}
    ]
  }'
```

**Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "view_url": "http://localhost:8000/view?id=a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 4. Open View URL

Open the `view_url` in a browser to see the print page with:
- Job details and ZPL preview
- Printer selection dropdown
- Print button to send data via WebSocket

## API Endpoints

| `GET` | `/` | Landing page with API info |
| `POST` | `/api/print-jobs` | Create print job, returns `job_id` and `view_url` |
| `GET` | `/view?id={uuid}` | View print job page (SSR HTML) |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/docs` | Swagger API documentation |

### Request Body Schema

```json
{
  "data": [
    { "zpl": "^XA...^XZ" },
    { "zpl": "^XA...^XZ" }
  ]
}
```

## File Structure

```
web-print-client/
├── .agent/
│   ├── memory.md            # Project context for AI assistants
│   └── workflows/
│       ├── dev.md           # Local development workflow
│       ├── deploy.md        # Docker deployment workflow
│       └── test.md          # API testing workflow
├── templates/
│   ├── index.html           # Landing page
│   └── print_page.html      # Jinja2 template with WebSocket JS
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Deployment orchestration
├── .gitignore               # Git ignore rules
├── .dockerignore            # Docker build ignore rules
└── app_data/                # SQLite database (auto-created, volume mount)
    └── printjobs.db
```

## Local WebSocket Bridge

The HTML page connects to `ws://localhost:5001/printers` to communicate with a **local C# WebSocket server** running on the user's PC. This bridge handles:

1. Listing available printers
2. Receiving ZPL data from the browser
3. Sending print commands to USB printers

> **Note:** The local WebSocket bridge is NOT included in this Docker container. It must run natively on the user's machine to access USB printers.

### Expected WebSocket Protocol

**Get Printers Request:**
```
get
```

**Get Printers Response:**
```json
["Printer1", "Printer2", "Zebra ZD420"]
```

**Print Request (sent for each item):**
```json
{
  "printer_name": "Zebra ZD420",
  "label_qty": 1,
  "data": "^XA...^XZ"
}
```

### Features
- Auto-selects first printer from the list
- Sends each print item separately
- Auto-closes tab after successful print

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Ensure real-time logging |

## Data Persistence

SQLite database is stored at `/app/data/printjobs.db` inside the container.

The `docker-compose.yml` mounts `./app_data` to `/app/data`, ensuring data persists across container restarts.

## AI Development

This project includes `.agent/memory.md` for AI context. Example prompts:

**Features:**
- "Add job status tracking (pending/printed/failed)"
- "Add a print history page at `/history`"
- "Support PDF format in addition to ZPL"

**Fixes:**
- "The WebSocket disconnects after 30 seconds, add heartbeat"
- "Handle duplicate print job submissions"

**DevOps:**
- "Add health check for database connection"
- "Add environment variable for WebSocket URL"

**Workflows:**
- `/dev` - Run locally
- `/deploy` - Deploy with Docker
- `/test` - Test API endpoints

## License

MIT
