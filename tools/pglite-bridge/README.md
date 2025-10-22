# PGlite Bridge

PostgreSQL-compatible HTTP bridge for PGlite (WebAssembly PostgreSQL).

## Overview

The PGlite Bridge provides a lightweight HTTP server that exposes PGlite's WebAssembly PostgreSQL implementation through a simple REST API, enabling psycopg3 compatibility for Automagik Hive.

## Features

- ✅ HTTP/JSON query interface
- ✅ PGlite WebAssembly backend
- ✅ pgvector extension support
- ✅ Graceful shutdown handling
- ✅ Health check endpoint
- ✅ Persistent data storage

## Requirements

- Node.js >= 18.0.0
- npm or yarn

## Installation

```bash
cd tools/pglite-bridge
npm install
```

## Usage

### Start Server

```bash
./start.sh
```

Or manually:

```bash
node server.js
```

### Stop Server

```bash
./stop.sh
```

### Health Check

```bash
./health.sh
```

Or manually:

```bash
curl http://127.0.0.1:5532/health
```

## API Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "pglite": "ready"
}
```

### POST /query

Execute SQL query.

**Request:**
```json
{
  "sql": "SELECT * FROM users WHERE id = $1",
  "params": [123]
}
```

**Response (Success):**
```json
{
  "success": true,
  "rows": [...],
  "rowCount": 1,
  "fields": [...]
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "relation \"users\" does not exist",
  "code": "42P01"
}
```

## Configuration

Environment variables:

- `PGLITE_PORT` - Server port (default: 5532)
- `PGLITE_DATA_DIR` - Data directory (default: ./pglite-data)

## Integration with Automagik Hive

The bridge is automatically managed by the `PGliteBackend` provider:

```python
from lib.database import get_database_backend, DatabaseBackendType

# Get PGlite backend
backend = get_database_backend(DatabaseBackendType.PGLITE)

# Start bridge
await backend.initialize()

# Backend handles HTTP queries transparently
result = await backend.fetch_one("SELECT 1 as test")
print(result)  # {'test': 1}

# Stop bridge
await backend.close()
```

## Architecture

```
┌─────────────────┐
│  Python App     │
│  (psycopg3)     │
└────────┬────────┘
         │ HTTP/JSON
         ↓
┌─────────────────┐
│ PGlite Bridge   │
│  (Node.js)      │
└────────┬────────┘
         │ WASM
         ↓
┌─────────────────┐
│    PGlite       │
│  (PostgreSQL)   │
└─────────────────┘
```

## Limitations

- HTTP overhead vs native PostgreSQL wire protocol
- Single connection (no pooling needed for WASM)
- Not suitable for high-concurrency production use
- Limited to PGlite-supported PostgreSQL features

## Troubleshooting

### Bridge won't start

Check Node.js version:
```bash
node --version  # Should be >= 18.0.0
```

Check logs:
```bash
cat pglite-bridge.log
```

### Health check fails

Verify port is available:
```bash
lsof -i :5532
```

Check process:
```bash
cat pglite-bridge.pid
ps -p $(cat pglite-bridge.pid)
```

### Dependencies missing

Reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

## Development

Run in foreground with logs:
```bash
node server.js
```

Test query endpoint:
```bash
curl -X POST http://127.0.0.1:5532/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT 1 as test"}'
```

## License

MIT - See root LICENSE file
