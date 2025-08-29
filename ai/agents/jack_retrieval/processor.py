"""CTE File Processor

Python code handles file processing and database insertion.
The agent does NOT process files - only Python code does.

Implementation approach - Python code handles file processing, not the agent:
- Read and parse CTE JSON files
- Extract order data and insert into PostgreSQL
- Handle errors gracefully with logging
- Use direct database connections, not agent MCP tools
"""

import json
import asyncio
import psycopg
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class CTEProcessor:
    """Process CTE JSON files and insert into database."""
    
    def __init__(self, database_url: str):
        """
        Initialize CTE processor.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
    
    async def process_cte_file(self, file_path: str) -> None:
        """
        Process CTE JSON file and insert into database.
        
        Args:
            file_path: Path to the CTE JSON file
        """
        try:
            # Read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract orders
            orders = data.get('orders', [])
            
            if not orders:
                logger.info(f"No orders found in {Path(file_path).name}")
                return
            
            # Process orders via database connection
            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # Ensure hive schema exists
                    await cur.execute("CREATE SCHEMA IF NOT EXISTS hive;")
                    
                    # Batch insert/update orders
                    for order in orders:
                        await self._insert_order(cur, order, Path(file_path).name)
                    
                    await conn.commit()
            
            print(f"✅ Processados {len(orders)} pedidos de {Path(file_path).name}")
            logger.info(f"Processed {len(orders)} orders from {Path(file_path).name}")
            
        except Exception as e:
            error_msg = f"❌ Erro processando {file_path}: {e}"
            print(error_msg)
            logger.error(error_msg)
    
    async def _insert_order(self, cursor, order: Dict[str, Any], source_file: str) -> None:
        """
        Insert/update a single order in the database.
        
        Args:
            cursor: Database cursor
            order: Order data dictionary
            source_file: Name of the source JSON file
        """
        # Create table if not exists
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hive.cte_data (
                id BIGSERIAL PRIMARY KEY,
                po_number VARCHAR(15) UNIQUE NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                po_total_value DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                cte_count INTEGER DEFAULT 0,
                start_date DATE,
                end_date DATE,
                source_file VARCHAR(100),
                batch_id VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create indexes if not exist
        await cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cte_data_po_number ON hive.cte_data(po_number);
        """)
        await cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cte_data_status ON hive.cte_data(status);
        """)
        
        # Upsert order data
        await cursor.execute("""
            INSERT INTO hive.cte_data 
            (po_number, status, po_total_value, cte_count, source_file, batch_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (po_number) DO UPDATE SET
                status = EXCLUDED.status,
                po_total_value = EXCLUDED.po_total_value,
                cte_count = EXCLUDED.cte_count,
                source_file = EXCLUDED.source_file,
                batch_id = EXCLUDED.batch_id,
                last_updated = NOW()
        """, (
            order.get('po_number'),
            order.get('status', 'PENDING'),
            float(order.get('po_total_value', 0.0)),
            order.get('cte_count', 0),
            source_file,
            order.get('batch_id')
        ))
    
    async def process_directory(self, directory_path: str) -> None:
        """
        Process all JSON files in a directory.
        
        Args:
            directory_path: Path to directory containing CTE JSON files
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory_path}")
            return
        
        json_files = list(directory.glob("*.json"))
        
        if not json_files:
            logger.info(f"No JSON files found in {directory_path}")
            return
        
        logger.info(f"Processing {len(json_files)} JSON files from {directory_path}")
        
        for json_file in json_files:
            await self.process_cte_file(str(json_file))
    
    async def get_order_count(self) -> int:
        """
        Get total count of orders in database.
        
        Returns:
            Total number of orders
        """
        try:
            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT COUNT(*) FROM hive.cte_data")
                    result = await cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting order count: {e}")
            return 0