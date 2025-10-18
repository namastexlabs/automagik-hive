#!/usr/bin/env python3
"""
Change Analyzer Service - Change detection and orphan analysis logic
Extracted from SmartIncrementalLoader for better separation of concerns.
Keeps orphan detection exactly as-is from the original implementation.
"""

from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.engine import Connection


class ChangeAnalyzer:
    """Service for analyzing changes between CSV data and database state."""

    def __init__(self, config: dict[str, Any], repository: Any) -> None:
        self.config = config
        self.repository = repository

    def analyze_changes(
        self,
        csv_rows: list[dict[str, Any]],
        db_connection: Connection,
    ) -> dict[str, Any]:
        """Analyze what needs to be loaded by checking specific content vs PostgreSQL - EXTRACTED from SmartIncrementalLoader.analyze_changes"""
        try:
            _csv_hashes = {row["hash"] for row in csv_rows}

            # Check which CSV rows are new or changed
            new_rows = []
            changed_rows = []
            existing_count = 0

            for row in csv_rows:
                # Use configured column names consistently
                csv_config = self.config.get("knowledge", {}).get("csv_reader", {})
                metadata_columns = csv_config.get("metadata_columns", ["question"])
                question_col = metadata_columns[0]  # First metadata column for search

                question_text = row["data"].get(question_col, "")[:100]  # First 100 chars

                # First check if a row with this question exists and get its hash
                query = """
                    SELECT content_hash FROM agno.knowledge_base 
                    WHERE content LIKE :question_pattern
                    LIMIT 1
                """
                result = db_connection.execute(text(query), {"question_pattern": f"%{question_text}%"})

                db_row = result.fetchone()

                if db_row is None:
                    # Row doesn't exist - it's new
                    new_rows.append(row)
                else:
                    # Row exists - check if hash matches
                    db_hash = cast(str, db_row[0])
                    csv_hash = row["hash"]

                    # Debug: Show first row comparison at DEBUG level only
                    if row["index"] == 0:
                        from lib.logging import logger

                        logger.debug(
                            "First row comparison debug",
                            question_preview=question_text[:50],
                            db_hash=db_hash,
                            csv_hash=csv_hash,
                            hashes_match=(db_hash == csv_hash),
                        )

                    if db_hash != csv_hash:
                        # Content has changed!
                        changed_rows.append(row)
                    else:
                        # Content unchanged
                        existing_count += 1

            # Now check for orphaned rows in DB that aren't in CSV - KEEP EXACT ORIGINAL LOGIC
            # First, let's understand what IDs we expect from the CSV
            # The IDs should be content hashes based on the CSV data

            # Get all document IDs from database
            result = db_connection.execute(
                text("""
                SELECT id FROM agno.knowledge_base
                WHERE id IS NOT NULL
            """)
            )
            db_ids = {row[0] for row in result.fetchall()}

            # Calculate the total count that SHOULD be in the DB
            # This is the number of valid CSV rows
            expected_count = len(csv_rows)

            # If DB has more documents than CSV rows, we have orphans
            orphaned_ids = []
            if len(db_ids) > expected_count:
                # We need a better way to identify orphans
                # Let's check which DB rows don't match ANY CSV content

                # Get config for column names
                csv_config = self.config.get("knowledge", {}).get("csv_reader", {})
                content_column = csv_config.get("content_column", "answer")

                for db_id in db_ids:
                    # For each DB ID, check if it corresponds to a CSV row
                    query = """
                        SELECT content FROM agno.knowledge_base 
                        WHERE id = :id
                    """
                    result = db_connection.execute(text(query), {"id": db_id})
                    content = result.fetchone()

                    if content:
                        content_text = cast(str, content[0])
                        # Check if this content matches any CSV row
                        found_match = False
                        for csv_row in csv_rows:
                            question = csv_row["data"].get(question_col, "")
                            answer = csv_row["data"].get(content_column, "")
                            # Check if DB content contains this CSV Q&A
                            if question in content_text or answer[:100] in content_text:
                                found_match = True
                                break

                        if not found_match:
                            # This DB row doesn't match any CSV content - it's orphaned
                            orphaned_ids.append(db_id)

            removed_count = len(orphaned_ids)
            needs_processing = len(new_rows) > 0 or len(changed_rows) > 0 or removed_count > 0

            from lib.logging import logger

            logger.debug(
                "Analysis complete", new_rows=len(new_rows), changed_rows=len(changed_rows), removed_rows=removed_count
            )

            # Build structured status payload with Agno v2 metadata
            csv_config = self.config.get("knowledge", {}).get("csv_reader", {})
            status_payload: dict[str, Any] = {
                "component": "change_analyzer",
                "mode": "agno_native_incremental",
                "config": {
                    "csv_reader": {
                        "content_column": csv_config.get("content_column", "answer"),
                        "metadata_columns": csv_config.get("metadata_columns", ["question"]),
                    }
                },
                "db": {
                    "schema": "agno",
                    "table_name": "knowledge_base",
                },
                "results": {
                    "csv_total_rows": len(csv_rows),
                    "existing_vector_rows": existing_count,
                    "new_rows_count": len(new_rows),
                    "changed_rows_count": len(changed_rows),
                    "removed_rows_count": removed_count,
                },
            }

            return {
                "csv_total_rows": len(csv_rows),
                "existing_vector_rows": existing_count,
                "new_rows_count": len(new_rows),
                "changed_rows_count": len(changed_rows),
                "removed_rows_count": removed_count,
                "new_rows": new_rows,
                "changed_rows": changed_rows,
                "removed_hashes": orphaned_ids,
                "potential_removals": orphaned_ids,  # alias for observability consumers
                "needs_processing": needs_processing,
                "status": "up_to_date" if not needs_processing else "incremental_update_required",
                "status_payload": status_payload,
            }

        except Exception as e:
            return {"error": str(e)}
