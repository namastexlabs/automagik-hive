#!/usr/bin/env python3
"""Test PostgreSQL connection with PgVector extension."""

import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def test_postgres_connection():
    """Test PostgreSQL connection and PgVector extension."""
    connection_string = "postgresql+psycopg://ai:ai@localhost:5532/ai"
    
    try:
        # Parse connection string for psycopg2
        conn_params = {
            'host': 'localhost',
            'port': 5532,
            'database': 'ai',
            'user': 'ai',
            'password': 'ai'
        }
        
        print("Testing PostgreSQL connection...")
        print(f"Connection parameters: {dict(conn_params, password='***')}")
        
        # Test basic connection
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        print("✓ PostgreSQL connection successful")
        
        # Test PgVector extension
        cursor = conn.cursor()
        
        # Check if pgvector extension exists
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
        if cursor.fetchone():
            print("✓ PgVector extension is installed")
        else:
            print("⚠ PgVector extension not found, attempting to install...")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✓ PgVector extension installed successfully")
            except Exception as e:
                print(f"✗ Failed to install PgVector extension: {e}")
                return False
        
        # Test basic vector operations
        cursor.execute("SELECT vector_dims(vector '[1,2,3]');")
        result = cursor.fetchone()
        if result and result[0] == 3:
            print("✓ PgVector operations working correctly")
        else:
            print("✗ PgVector operations failed")
            return False
        
        cursor.close()
        conn.close()
        
        print("\n✓ All database tests passed!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"✗ Connection failed: {e}")
        print("Make sure PostgreSQL is running on localhost:5532")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)