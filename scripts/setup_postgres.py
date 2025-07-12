#!/usr/bin/env python3
"""
Setup PostgreSQL database for PagBank Multi-Agent System
Creates only the custom tables - Agno will auto-create its own tables
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from pathlib import Path


def setup_postgres():
    """Setup PostgreSQL database with minimal schema"""
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Please set DATABASE_URL=postgresql+psycopg://ai:ai@localhost:5532/ai")
        return False
    
    # Convert SQLAlchemy URL to psycopg2 format
    if db_url.startswith("postgresql+psycopg://"):
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://")
    
    try:
        # Connect to database
        print(f"🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Read and execute minimal schema
        schema_path = Path(__file__).parent.parent / "schema" / "minimal_tables.sql"
        if not schema_path.exists():
            print(f"❌ Schema file not found: {schema_path}")
            return False
        
        print(f"📄 Reading schema from {schema_path}")
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        print("🔨 Creating tables...")
        cursor.execute(schema_sql)
        conn.commit()
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print("\n✅ Database setup complete! Tables found:")
        for table in tables:
            print(f"   - {table}")
        
        # Show Agno will create additional tables
        print("\n📝 Note: Agno will automatically create these tables on first run:")
        print("   - team_sessions (PostgresStorage)")
        print("   - agent_sessions (PostgresStorage)")
        print("   - user_memories (PostgresMemoryDb)")
        print("   - ana_user_memories (PostgresMemoryDb)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error setting up PostgreSQL: {e}")
        return False


def test_connection():
    """Test PostgreSQL connection"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return False
    
    if db_url.startswith("postgresql+psycopg://"):
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connected: {version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 PagBank PostgreSQL Setup")
    print("=" * 50)
    
    # Test connection first
    if not test_connection():
        print("\n💡 Make sure PostgreSQL is running:")
        print("   docker run -d \\")
        print("     -e POSTGRES_DB=ai \\")
        print("     -e POSTGRES_USER=ai \\")
        print("     -e POSTGRES_PASSWORD=ai \\")
        print("     -p 5532:5432 \\")
        print("     --name pgvector \\")
        print("     agno/pgvector:16")
        sys.exit(1)
    
    # Setup database
    if setup_postgres():
        print("\n🎉 Setup complete! You can now run:")
        print("   uv run python api/playground.py")
        print("   uv run python api/serve.py")
    else:
        sys.exit(1)