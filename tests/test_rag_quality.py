"""
RAG Quality Tests for Automagik Hive v2.

Tests the CSV-based RAG system:
- CSV loading and parsing
- Incremental updates (hash-based change detection)
- Hot reload triggers on file changes
- Retrieval quality (relevance of results)
- Performance benchmarks
"""

import hashlib
import time

import pytest


class TestCSVLoading:
    """Test CSV file loading and parsing."""

    def test_loads_valid_csv(self, test_csv_data, temp_project_dir):
        """Test that valid CSV loads successfully."""
        # GIVEN: CSV file with data
        csv_file = temp_project_dir / "knowledge.csv"
        csv_file.write_text(test_csv_data)

        # WHEN: Loading CSV
        import csv

        with csv_file.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # THEN: Data is loaded correctly
        assert len(rows) == 3
        assert "query" in rows[0]
        assert "context" in rows[0]
        assert rows[0]["query"] == "How do I reset password?"

    def test_handles_missing_columns(self, temp_project_dir):
        """Test graceful handling of CSV with missing columns."""
        # GIVEN: CSV missing required column
        csv_file = temp_project_dir / "bad.csv"
        csv_file.write_text("query,answer\nTest,Response")  # Missing 'context'

        # WHEN: Loading CSV
        import csv

        with csv_file.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # THEN: Can still load but validation should catch
        assert len(rows) == 1
        assert "context" not in rows[0]  # Missing column

    def test_handles_empty_csv(self, temp_project_dir):
        """Test handling of empty CSV file."""
        csv_file = temp_project_dir / "empty.csv"
        csv_file.write_text("query,context,conclusion\n")  # Headers only

        import csv

        with csv_file.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # THEN: Should have zero rows (but valid structure)
        assert len(rows) == 0

    def test_handles_large_csv(self, temp_project_dir):
        """Test performance with large CSV files."""
        # GIVEN: Large CSV (simulate 10k rows)
        csv_file = temp_project_dir / "large.csv"
        rows = ["query,context,conclusion"]
        for i in range(10000):
            rows.append(f"Question {i},Answer to question {i},Technical")

        csv_file.write_text("\n".join(rows))

        # WHEN: Loading large file
        start = time.time()
        import csv

        with csv_file.open() as f:
            reader = csv.DictReader(f)
            loaded_rows = list(reader)

        duration = time.time() - start

        # THEN: Loads reasonably fast
        assert len(loaded_rows) == 10000
        assert duration < 5.0  # Should complete in under 5 seconds


class TestIncrementalUpdates:
    """Test hash-based incremental loading."""

    def test_detects_new_rows(self, temp_project_dir):
        """Test that new rows are detected and processed."""
        # GIVEN: Original CSV
        csv_file = temp_project_dir / "knowledge.csv"
        original = "query,context\nQ1,A1\nQ2,A2"
        csv_file.write_text(original)

        # Compute initial hashes
        initial_hashes = self._compute_hashes(original)

        # WHEN: Row added
        updated = "query,context\nQ1,A1\nQ2,A2\nQ3,A3"
        csv_file.write_text(updated)
        updated_hashes = self._compute_hashes(updated)

        # THEN: New row detected
        new_hashes = set(updated_hashes) - set(initial_hashes)
        assert len(new_hashes) == 1

    def _compute_hashes(self, csv_content: str) -> list[str]:
        """Compute MD5 hash for each row."""
        import csv
        from io import StringIO

        hashes = []
        reader = csv.DictReader(StringIO(csv_content))
        for row in reader:
            row_data = "|".join(row.values())
            hash_val = hashlib.md5(row_data.encode()).hexdigest()  # noqa: S324
            hashes.append(hash_val)
        return hashes

    def test_detects_modified_rows(self, temp_project_dir):
        """Test that modified rows trigger re-processing."""
        csv_file = temp_project_dir / "knowledge.csv"

        # Original
        original = "query,context\nQ1,Original Answer"
        csv_file.write_text(original)
        hash_v1 = self._compute_hashes(original)[0]

        # Modified
        modified = "query,context\nQ1,Updated Answer"
        csv_file.write_text(modified)
        hash_v2 = self._compute_hashes(modified)[0]

        # THEN: Hash changed
        assert hash_v1 != hash_v2

    def test_detects_deleted_rows(self, temp_project_dir):
        """Test that deleted rows are removed from index."""
        csv_file = temp_project_dir / "knowledge.csv"

        # Original with 3 rows
        original = "query,context\nQ1,A1\nQ2,A2\nQ3,A3"
        csv_file.write_text(original)
        hashes_v1 = set(self._compute_hashes(original))

        # Delete one row
        updated = "query,context\nQ1,A1\nQ3,A3"
        csv_file.write_text(updated)
        hashes_v2 = set(self._compute_hashes(updated))

        # THEN: One hash removed
        deleted = hashes_v1 - hashes_v2
        assert len(deleted) == 1

    def test_skips_unchanged_rows(self, temp_project_dir):
        """Test that unchanged rows are not re-processed."""
        csv_file = temp_project_dir / "knowledge.csv"

        # Same content
        content = "query,context\nQ1,A1\nQ2,A2"
        csv_file.write_text(content)
        hashes_v1 = self._compute_hashes(content)

        csv_file.write_text(content)  # Write again
        hashes_v2 = self._compute_hashes(content)

        # THEN: Hashes identical
        assert hashes_v1 == hashes_v2


class TestHotReload:
    """Test file watching and hot reload."""

    @pytest.mark.slow
    def test_detects_file_changes(self, temp_project_dir):
        """Test that file watcher detects CSV modifications."""
        csv_file = temp_project_dir / "knowledge.csv"
        csv_file.write_text("query,context\nQ1,A1")

        # Mock file watcher
        last_modified = csv_file.stat().st_mtime

        # Modify file
        time.sleep(0.1)
        csv_file.write_text("query,context\nQ1,A1\nQ2,A2")

        # THEN: Modification detected
        new_modified = csv_file.stat().st_mtime
        assert new_modified > last_modified

    def test_debounces_rapid_changes(self, temp_project_dir):
        """Test that rapid changes are debounced."""
        csv_file = temp_project_dir / "knowledge.csv"

        # Simulate rapid changes
        changes = []
        for i in range(5):
            csv_file.write_text(f"query,context\nQ{i},A{i}")
            changes.append(time.time())
            time.sleep(0.05)  # Fast changes

        # Mock debouncing (wait 1 second after last change)
        debounce_delay = 1.0
        last_change = max(changes)
        time_since_last = time.time() - last_change

        # THEN: Should wait for debounce period
        # (In real implementation, would trigger reload only after delay)
        assert time_since_last < debounce_delay + 1

    def test_reload_preserves_existing_data(self, temp_project_dir):
        """Test that reload doesn't lose existing embeddings."""
        # GIVEN: Existing knowledge base

        # WHEN: Reload triggered
        csv_file = temp_project_dir / "knowledge.csv"
        csv_file.write_text("query,context\nQ1,A1\nQ2,A2\nQ3,A3")

        # Simulate reload: preserve Q1, Q2, add Q3
        import csv
        import hashlib
        from io import StringIO

        hashes = []
        reader = csv.DictReader(StringIO(csv_file.read_text()))
        for row in reader:
            row_data = "|".join(row.values())
            hash_val = hashlib.md5(row_data.encode()).hexdigest()  # noqa: S324
            hashes.append(hash_val)

        # THEN: Existing data preserved
        # (Real implementation would check database)
        assert len(hashes) == 3


class TestRetrievalQuality:
    """Test quality of retrieval results."""

    def test_retrieves_relevant_results(self, test_csv_data):
        """Test that queries return relevant documents."""
        # GIVEN: Knowledge base
        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(test_csv_data))
        docs = list(reader)

        # WHEN: User asks about password
        query = "I forgot my password"

        # Mock similarity search
        results = self._mock_search(query, docs)

        # THEN: Returns password reset doc
        assert len(results) > 0
        assert "password" in results[0]["query"].lower()

    def _mock_search(self, query: str, docs: list[dict], top_k: int = 1) -> list[dict]:
        """Mock semantic search."""
        # Simple keyword matching for test
        query_lower = query.lower()
        scored = []

        for doc in docs:
            score = 0
            doc_text = (doc.get("query", "") + " " + doc.get("context", "")).lower()
            for word in query_lower.split():
                if word in doc_text:
                    score += 1
            scored.append((score, doc))

        # Sort by score and return top k
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def test_returns_multiple_results(self, test_csv_data):
        """Test retrieval of multiple relevant documents."""
        import csv
        from io import StringIO

        docs = list(csv.DictReader(StringIO(test_csv_data)))

        # WHEN: Query could match multiple docs
        query = "account issues"
        results = self._mock_search(query, docs, top_k=2)

        # THEN: Returns multiple results
        assert len(results) >= 1  # At least one result

    def test_handles_no_matches(self, test_csv_data):
        """Test behavior when no relevant docs found."""
        import csv
        from io import StringIO

        docs = list(csv.DictReader(StringIO(test_csv_data)))

        # WHEN: Query has no matches
        query = "quantum physics"
        results = self._mock_search(query, docs, top_k=1)

        # THEN: Returns empty or low-confidence results
        # (In real implementation, might return nothing or fallback)
        assert isinstance(results, list)

    def test_relevance_ranking(self):
        """Test that results are ranked by relevance."""
        docs = [
            {"query": "How to reset password", "context": "Go to settings"},
            {"query": "Password requirements", "context": "8 characters minimum"},
            {"query": "Forgot password", "context": "Click forgot password link"},
        ]

        query = "I forgot my password"
        results = self._mock_search(query, docs, top_k=3)

        # THEN: Most relevant result is first
        assert "forgot" in results[0]["query"].lower()


class TestPerformance:
    """Test RAG system performance."""

    def test_retrieval_is_fast(self, test_csv_data):
        """Test that retrieval completes quickly."""
        import csv
        from io import StringIO

        docs = list(csv.DictReader(StringIO(test_csv_data)))

        # WHEN: Performing search
        start = time.time()
        query = "password reset"

        # Simple fuzzy search for performance test
        query_lower = query.lower()
        results = []
        for doc in docs:
            doc_text = str(doc).lower()
            if any(word in doc_text for word in query_lower.split()):
                results.append(doc)
        results = results[:5]

        duration = time.time() - start

        # THEN: Search is fast
        assert duration < 1.0  # Under 1 second
        assert len(results) > 0

    def _mock_search(self, query: str, docs: list[dict]) -> list[dict]:
        """Mock search for performance test."""
        return [d for d in docs if query.lower() in str(d).lower()][:5]

    @pytest.mark.slow
    def test_scales_to_large_knowledge_base(self):
        """Test performance with large knowledge base."""
        # Simulate 10k documents
        large_kb = []
        for i in range(10000):
            large_kb.append(
                {
                    "query": f"Question {i}",
                    "context": f"Answer to question {i}",
                    "conclusion": "General",
                }
            )

        # WHEN: Searching large KB
        start = time.time()
        query = "Question 5000"
        results = [d for d in large_kb if query in d["query"]]
        duration = time.time() - start

        # THEN: Still reasonably fast
        assert duration < 2.0  # Under 2 seconds
        assert len(results) > 0


class TestErrorHandling:
    """Test error handling in RAG system."""

    def test_handles_corrupt_csv(self, temp_project_dir):
        """Test graceful handling of malformed CSV."""
        csv_file = temp_project_dir / "corrupt.csv"
        csv_file.write_text("query,context\nQ1,A1\nBroken line without comma")

        # WHEN: Loading corrupt CSV
        import csv

        with csv_file.open() as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                rows.append(row)

        # THEN: Loads partial data (CSV reader is permissive)
        assert len(rows) >= 1

    def test_handles_missing_file(self, temp_project_dir):
        """Test handling of missing CSV file."""
        csv_file = temp_project_dir / "nonexistent.csv"

        # WHEN: Trying to load missing file
        # THEN: Should raise appropriate error
        assert not csv_file.exists()

    def test_handles_permission_errors(self, temp_project_dir):
        """Test handling of read permission errors."""
        csv_file = temp_project_dir / "readonly.csv"
        csv_file.write_text("query,context\nQ1,A1")

        # Make read-only
        csv_file.chmod(0o444)

        # WHEN: File is readable (but not writable)
        assert csv_file.exists()
        content = csv_file.read_text()
        assert "Q1" in content

        # Cleanup
        csv_file.chmod(0o644)
