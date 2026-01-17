# Local Print Bridge - Project Memory

## Overview
A lightweight, containerized FastAPI SSR application that bridges **Dynamics 365 (D365)** and local USB printers via WebSocket.

## Architecture Flow
```
D365 → POST /api/print-jobs → SQLite → Return {job_id, view_url}
     → Browser opens view_url → Render HTML (Jinja2 SSR)
     → JavaScript connects to ws://localhost:8765 (local bridge on user's PC)
     → Send ZPL data to USB printer
```

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, SQLite setup, API endpoints |
| `templates/print_page.html` | Jinja2 template + Tailwind CSS + WebSocket JS |
| `requirements.txt` | Python dependencies (fastapi, uvicorn, sqlalchemy, pydantic, jinja2) |
| `Dockerfile` | Python 3.9-slim container |
| `docker-compose.yml` | Service orchestration with volume persistence |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/print-jobs` | Create print job, returns `{job_id, view_url}` |
| `GET` | `/view?id={uuid}` | View print job page (SSR HTML) |
| `GET` | `/health` | Health check |

## Data Schema

### Print Job Request
```json
{
  "data": [
    {"zpl": "^XA\n^FO50,50\n^BQN,2,5\n^FDQA,HELLO WORLD^FS\n^XZ\n"}
  ]
}
```

### Database Model (SQLite)
- `PrintJob`: `id` (UUID), `data_json` (Text), `created_at` (DateTime)

## WebSocket Protocol (ws://localhost:8765)

The HTML page connects to a **local Python bridge** running on the user's PC (NOT inside Docker).

| Direction | Message Type | Payload |
|-----------|--------------|---------|
| Client → Bridge | `get_printers` | `{}` |
| Bridge → Client | `printers` | `{printers: [{name: "..."}]}` |
| Client → Bridge | `print` | `{job_id, printer, data: [...]}` |
| Bridge → Client | `print_result` | `{success: true/false, error?: "..."}` |

## Constraints & Design Decisions

1. **SQLite** - Simple, file-based DB. Single writer limitation is acceptable for print job queue.
2. **WebSocket on localhost:8765** - Must run natively on user's PC to access USB printers (Docker can't access host USB).
3. **ZPL Format** - Zebra Programming Language for thermal label printers.
4. **Tailwind via CDN** - Per user preference, using Tailwind CSS.
5. **No authentication** - Assumed to run on trusted internal network.

## Future Considerations

- [ ] Add job status tracking (pending/printed/failed)
- [ ] Add retry mechanism for failed prints
- [ ] Add print history/logs page
- [ ] Support multiple print formats (not just ZPL)
- [ ] Add authentication if exposed externally
