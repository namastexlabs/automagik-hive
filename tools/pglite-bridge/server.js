/**
 * PGlite Bridge Server
 *
 * Provides a PostgreSQL-compatible interface over HTTP for PGlite (WebAssembly PostgreSQL).
 * Simplified bridge focusing on compatibility with psycopg3 async patterns.
 */

const { PGlite } = require('@electric-sql/pglite');
const { Pool } = require('pg');
const http = require('http');

// Configuration
const PORT = process.env.PGLITE_PORT || 5532;
const DATA_DIR = process.env.PGLITE_DATA_DIR || './pglite-data';

// PGlite instance (singleton)
let db = null;

/**
 * Initialize PGlite database instance
 */
async function initDatabase() {
  if (db) return db;

  console.log(`[PGlite Bridge] Initializing database at ${DATA_DIR}...`);

  try {
    db = new PGlite({
      dataDir: DATA_DIR,
      // Enable pgvector extension support
      extensions: {
        vector: require('@electric-sql/pglite/vector').vector
      }
    });

    await db.waitReady;
    console.log('[PGlite Bridge] Database initialized successfully');

    // Create pgvector extension if not exists
    try {
      await db.exec('CREATE EXTENSION IF NOT EXISTS vector;');
      console.log('[PGlite Bridge] pgvector extension ready');
    } catch (err) {
      console.warn('[PGlite Bridge] pgvector extension warning:', err.message);
    }

    return db;
  } catch (error) {
    console.error('[PGlite Bridge] Failed to initialize database:', error);
    throw error;
  }
}

/**
 * Execute SQL query via PGlite
 */
async function executeQuery(sql, params = []) {
  const database = await initDatabase();

  try {
    const result = await database.query(sql, params);
    return {
      success: true,
      rows: result.rows || [],
      rowCount: result.affectedRows || result.rows?.length || 0,
      fields: result.fields || []
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      code: error.code || 'PGLITE_ERROR'
    };
  }
}

/**
 * HTTP request handler
 */
async function handleRequest(req, res) {
  // CORS headers for development
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Health check endpoint
  if (req.method === 'GET' && req.url === '/health') {
    try {
      await initDatabase();
      const result = await executeQuery('SELECT 1 as health');

      if (result.success) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'healthy', pglite: 'ready' }));
      } else {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'unhealthy', error: result.error }));
      }
    } catch (error) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'unhealthy', error: error.message }));
    }
    return;
  }

  // Query execution endpoint
  if (req.method === 'POST' && req.url === '/query') {
    let body = '';

    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', async () => {
      try {
        const { sql, params } = JSON.parse(body);

        if (!sql) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Missing sql parameter' }));
          return;
        }

        const result = await executeQuery(sql, params || []);

        res.writeHead(result.success ? 200 : 500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });

    return;
  }

  // Default response
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Endpoint not found. Use /health or /query' }));
}

/**
 * Start HTTP server
 */
async function startServer() {
  const server = http.createServer(handleRequest);

  server.listen(PORT, '127.0.0.1', async () => {
    console.log(`[PGlite Bridge] Server listening on http://127.0.0.1:${PORT}`);
    console.log(`[PGlite Bridge] Health check: http://127.0.0.1:${PORT}/health`);
    console.log(`[PGlite Bridge] Query endpoint: http://127.0.0.1:${PORT}/query`);

    // Initialize database on startup
    try {
      await initDatabase();
      console.log('[PGlite Bridge] Ready to accept connections');
    } catch (error) {
      console.error('[PGlite Bridge] Startup failed:', error);
      process.exit(1);
    }
  });

  // Graceful shutdown
  process.on('SIGTERM', async () => {
    console.log('[PGlite Bridge] Shutting down gracefully...');
    server.close(async () => {
      if (db) {
        await db.close();
        console.log('[PGlite Bridge] Database closed');
      }
      process.exit(0);
    });
  });

  process.on('SIGINT', async () => {
    console.log('[PGlite Bridge] Interrupted, shutting down...');
    server.close(async () => {
      if (db) {
        await db.close();
        console.log('[PGlite Bridge] Database closed');
      }
      process.exit(0);
    });
  });
}

// Start server if run directly
if (require.main === module) {
  startServer().catch(error => {
    console.error('[PGlite Bridge] Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { initDatabase, executeQuery, startServer };
