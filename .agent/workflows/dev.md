---
description: Run the application in local development mode with hot-reload
---

# Local Development

## Prerequisites
- Python 3.9+
- pip

## Steps

1. Navigate to project directory:
```bash
cd /Volumes/ExternalSSD/Project/web-print-client
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create data directory:
```bash
mkdir -p data
```

// turbo
5. Run with hot-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server available at: http://localhost:8000
