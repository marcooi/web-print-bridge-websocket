---
description: Test the API endpoints manually with curl
---

# Test API

## Prerequisites
- Server running at http://localhost:8000

## Steps

// turbo
1. Create a print job:
```bash
curl -X POST http://localhost:8000/api/print-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"zpl": "^XA\n^FO50,50\n^BQN,2,5\n^FDQA,HELLO WORLD^FS\n^XZ\n"}
    ]
  }'
```

Expected response:
```json
{"job_id": "uuid", "view_url": "http://localhost:8000/view?id=uuid"}
```

2. Open the `view_url` in browser to see the print page

// turbo
3. Test health endpoint:
```bash
curl http://localhost:8000/health
```

// turbo
4. Test error handling (invalid ID):
```bash
curl http://localhost:8000/view?id=invalid-uuid
```
