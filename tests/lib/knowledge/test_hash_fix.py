#!/usr/bin/env python3
"""
Simple test to force repopulate database hashes and verify the fix.
"""

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
import yaml
from sqlalchemy import create_engine, text


def test_hash_consistency():
    """Test hash consistency between CSV and database"""

    # Read CSV file (adjust path for tests directory)
    csv_path = Path(__file__).parent.parent.parent.parent / "lib" / "knowledge" / "knowledge_rag.csv"
    if not csv_path.exists():
        return False

    df = pd.read_csv(csv_path)

    # Load config to get column configuration
    config_path = Path(__file__).parent.parent.parent.parent / "lib" / "knowledge" / "config.yaml"
    try:
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except Exception:
        return False

    csv_config = config.get("knowledge", {}).get("csv_reader", {})
    content_column = csv_config.get("content_column", "answer")
    metadata_columns = csv_config.get("metadata_columns", ["question"])

    # Compute hash for first row
    if len(df) == 0:
        return False

    first_row = df.iloc[0]

    # Build content string using same algorithm as _hash_row
    content_parts = []

    # Add first metadata column (question)
    if metadata_columns:
        content_parts.append(str(first_row.get(metadata_columns[0], "")))

    # Add content column (answer)
    content_parts.append(str(first_row.get(content_column, "")))

    # Add remaining metadata columns
    for col in metadata_columns[1:]:
        content_parts.append(str(first_row.get(col, "")))

    content = "".join(content_parts)
    csv_hash = hashlib.md5(content.encode("utf-8")).hexdigest()  # noqa: S324 - Content hashing, not cryptographic

    # Connect to database and check
    db_url = "postgresql://hive:hive_automagik_password@localhost:5532/automagik_hive"

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Get database entry for same question
            query = """
                SELECT content_hash, LEFT(content, 100) as content_preview 
                FROM agno.knowledge_base 
                WHERE content LIKE :pattern 
                LIMIT 1
            """
            question_start = str(first_row.get("question", ""))[:30]
            result = conn.execute(text(query), {"pattern": f"%{question_start}%"})
            db_row = result.fetchone()

            if db_row:
                if csv_hash == db_row.content_hash:
                    return True
                else:
                    return False
            else:
                return False

    except Exception:
        return False


def force_repopulate_hashes():
    """Force repopulate all database hashes with correct algorithm"""

    # Load config
    config_path = Path(__file__).parent.parent.parent.parent / "lib" / "knowledge" / "config.yaml"
    try:
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except Exception:
        return False

    csv_config = config.get("knowledge", {}).get("csv_reader", {})
    content_column = csv_config.get("content_column", "answer")
    metadata_columns = csv_config.get("metadata_columns", ["question"])

    # Read CSV file
    csv_path = Path(__file__).parent.parent.parent.parent / "lib" / "knowledge" / "knowledge_rag.csv"
    if not csv_path.exists():
        return False

    df = pd.read_csv(csv_path)

    # Connect to database
    db_url = "postgresql://hive:hive_automagik_password@localhost:5532/automagik_hive"

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            updated_count = 0

            for idx, row in df.iterrows():
                # Compute correct hash
                content_parts = []

                # Add first metadata column (question)
                if metadata_columns:
                    content_parts.append(str(row.get(metadata_columns[0], "")))

                # Add content column (answer)
                content_parts.append(str(row.get(content_column, "")))

                # Add remaining metadata columns
                for col in metadata_columns[1:]:
                    content_parts.append(str(row.get(col, "")))

                content = "".join(content_parts)
                correct_hash = hashlib.md5(content.encode("utf-8")).hexdigest()  # noqa: S324 - Content hashing, not cryptographic

                # Update database with correct hash
                question_text = str(row.get(metadata_columns[0], "")) if metadata_columns else ""
                if question_text:
                    update_query = """
                        UPDATE agno.knowledge_base
                        SET content_hash = :hash
                        WHERE content LIKE :problem_pattern
                    """
                    result = conn.execute(
                        text(update_query),
                        {
                            "hash": correct_hash,
                            "problem_pattern": f"%{question_text[:50]}%",
                        },
                    )

                    if result.rowcount > 0:
                        updated_count += 1
                        if idx % 10 == 0:  # Progress indicator
                            pass

            conn.commit()
            return True

    except Exception:
        return False


def test_analyze_changes():
    """Test the analyze_changes method to see what it actually reports"""

    # Set up environment for SmartIncrementalLoader
    os.environ["HIVE_DATABASE_URL"] = "postgresql://hive:hive_automagik_password@localhost:5532/automagik_hive"

    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))

        from lib.knowledge.smart_incremental_loader import SmartIncrementalLoader

        # Initialize loader
        loader = SmartIncrementalLoader()

        # Run analyze_changes
        result = loader.analyze_changes()

        # Print results
        for key, _value in result.items():
            if key in ["new_rows", "changed_rows", "removed_rows"]:
                pass
            else:
                pass

        # If there are changed rows, this confirms the hash mismatch issue
        if "changed_rows" in result and len(result["changed_rows"]) > 0:
            return result
        else:
            return result

    except Exception:
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--analyze":
        # Test the analyze_changes method
        test_analyze_changes()
    elif len(sys.argv) > 1 and sys.argv[1] == "--fix":
        # Force repopulate hashes
        success = force_repopulate_hashes()
        if success:
            test_hash_consistency()
    else:
        # Just test current state
        consistent = test_hash_consistency()
        if not consistent:
            pass
        else:
            pass
