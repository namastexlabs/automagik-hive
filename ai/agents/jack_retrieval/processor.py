"""CTE and MINUTA File Processor

Python code handles file processing and database insertion.
The agent does NOT process files - only Python code does.

Implementation approach - Python code handles file processing, not the agent:
- Read and parse CTE and MINUTA JSON files
- Extract order/CNPJ data and insert into PostgreSQL
- Handle errors gracefully with logging
- Use direct database connections, not agent MCP tools
"""

import json
import glob
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
            database_url: PostgreSQL connection URL (psycopg format: postgresql://)
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
    # ========== MINUTA PROCESSING METHODS ==========

    async def process_minuta_directory(self, directory_path: str) -> int:
        """
        Process all MINUTA JSON files in directory and sync to database.

        Args:
            directory_path: Path to directory containing MINUTA JSON files

        Returns:
            Total number of CNPJ groups processed
        """
        directory = Path(directory_path)

        if not directory.exists():
            logger.warning(f"MINUTA directory does not exist: {directory_path}")
            return 0

        json_files = glob.glob(f"{directory_path}/minutas_*.json")

        if not json_files:
            logger.info(f"No MINUTA JSON files found in {directory_path}")
            return 0

        logger.info(f"Processing {len(json_files)} MINUTA JSON files from {directory_path}")

        total_groups = 0
        for json_file in json_files:
            groups_processed = await self.process_minuta_file(json_file)
            total_groups += groups_processed

        logger.info(f"✅ Synced {total_groups} MINUTA CNPJ groups to database")
        return total_groups

    async def process_minuta_file(self, file_path: str) -> int:
        """
        Process single MINUTA JSON file and upsert CNPJ groups to database.

        Args:
            file_path: Path to the MINUTA JSON file

        Returns:
            Number of CNPJ groups processed from this file
        """
        try:
            # Read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract CNPJ groups
            cnpj_groups = data.get('cnpj_groups', [])

            if not cnpj_groups:
                logger.info(f"No CNPJ groups found in {Path(file_path).name}")
                return 0

            # Process CNPJ groups via database connection
            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    # Ensure hive schema exists
                    await cur.execute("CREATE SCHEMA IF NOT EXISTS hive;")

                    # Batch insert/update CNPJ groups
                    for cnpj_group in cnpj_groups:
                        await self._upsert_minuta_group(cur, cnpj_group, Path(file_path).name)

                    await conn.commit()

            logger.info(f"Processed {len(cnpj_groups)} CNPJ groups from {Path(file_path).name}")
            return len(cnpj_groups)

        except Exception as e:
            error_msg = f"Error processing MINUTA file {file_path}: {e}"
            logger.error(error_msg)
            return 0

    async def _upsert_minuta_group(self, cursor, cnpj_group: Dict[str, Any], source_file: str) -> None:
        """
        Insert/update a single MINUTA CNPJ group in the database.

        Args:
            cursor: Database cursor
            cnpj_group: CNPJ group data dictionary
            source_file: Name of the source JSON file
        """
        # Create table if not exists
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hive.minuta_data (
                id BIGSERIAL PRIMARY KEY,
                cnpj_claro VARCHAR(20) UNIQUE NOT NULL,
                cnpj_formatted VARCHAR(25),
                empresa_origem VARCHAR(255),
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                city VARCHAR(100),
                state VARCHAR(100),
                municipio VARCHAR(100),
                uf VARCHAR(2),
                minuta_count INTEGER DEFAULT 0,
                total_value DECIMAL(12,2) NOT NULL DEFAULT 0.00,
                po_list JSONB,
                minutas JSONB,
                start_date VARCHAR(20),
                end_date VARCHAR(20),
                protocol_number VARCHAR(50),
                requires_regional BOOLEAN DEFAULT FALSE,
                regional_type VARCHAR(20),
                pdf_files JSONB,
                source_file VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Create indexes if not exist
        await cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_minuta_data_cnpj ON hive.minuta_data(cnpj_claro);
        """)
        await cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_minuta_data_status ON hive.minuta_data(status);
        """)
        await cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_minuta_data_uf ON hive.minuta_data(uf);
        """)

        # Upsert MINUTA CNPJ group data
        await cursor.execute("""
            INSERT INTO hive.minuta_data
            (cnpj_claro, cnpj_formatted, empresa_origem, status, city, state,
             municipio, uf, minuta_count, total_value, po_list, minutas,
             start_date, end_date, protocol_number, requires_regional,
             regional_type, pdf_files, source_file)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cnpj_claro) DO UPDATE SET
                cnpj_formatted = EXCLUDED.cnpj_formatted,
                empresa_origem = EXCLUDED.empresa_origem,
                status = EXCLUDED.status,
                city = EXCLUDED.city,
                state = EXCLUDED.state,
                municipio = EXCLUDED.municipio,
                uf = EXCLUDED.uf,
                minuta_count = EXCLUDED.minuta_count,
                total_value = EXCLUDED.total_value,
                po_list = EXCLUDED.po_list,
                minutas = EXCLUDED.minutas,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                protocol_number = EXCLUDED.protocol_number,
                requires_regional = EXCLUDED.requires_regional,
                regional_type = EXCLUDED.regional_type,
                pdf_files = EXCLUDED.pdf_files,
                source_file = EXCLUDED.source_file,
                last_updated = NOW()
        """, (
            cnpj_group.get('cnpj_claro'),
            cnpj_group.get('cnpj_claro_formatted'),
            cnpj_group.get('empresa_origem'),
            cnpj_group.get('status', 'PENDING'),
            cnpj_group.get('city'),
            cnpj_group.get('state'),
            cnpj_group.get('municipio'),
            cnpj_group.get('uf'),
            cnpj_group.get('minuta_count', 0),
            float(cnpj_group.get('total_value', 0.0)),
            json.dumps(cnpj_group.get('po_list', [])),
            json.dumps(cnpj_group.get('minutas', [])),
            cnpj_group.get('start_date'),
            cnpj_group.get('end_date'),
            cnpj_group.get('protocol_number'),
            cnpj_group.get('requires_regional', False),
            cnpj_group.get('regional_type'),
            json.dumps(cnpj_group.get('pdf_files', {})),
            source_file
        ))

    async def get_minuta_count(self) -> int:
        """
        Get total count of MINUTA CNPJ groups in database.

        Returns:
            Total number of CNPJ groups
        """
        try:
            async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT COUNT(*) FROM hive.minuta_data")
                    result = await cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting MINUTA count: {e}")
            return 0
