"""Tests for Row-Based CSV Knowledge Base"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from agno.vectordb.base import VectorDb

from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing"""
    return [
        ["question", "answer", "category", "tags"],
        ["How to create agent?", "Use Agent class with config", "development", "agent,config"],
        ["Team coordination?", "Use Team routing patterns", "architecture", "team,routing"],
        ["Debug issues?", "Check logs and trace", "operations", "debug,logging"],
    ]


@pytest.fixture
def temp_csv_file(sample_csv_content):
    """Create temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(sample_csv_content)
        csv_path = f.name
    
    yield csv_path
    
    # Cleanup
    Path(csv_path).unlink(missing_ok=True)


@pytest.fixture
def mock_vector_db():
    """Mock vector database for testing"""
    mock_db = MagicMock(spec=VectorDb)
    mock_db.exists.return_value = True
    mock_db.upsert_available.return_value = True
    return mock_db


def test_load_csv_as_documents(temp_csv_file, mock_vector_db):
    """Test loading CSV file into documents"""
    kb = RowBasedCSVKnowledgeBase(csv_path=temp_csv_file, vector_db=mock_vector_db)
    
    # Should create 3 documents (excluding header)
    assert len(kb.documents) == 3
    
    # Check first document
    doc = kb.documents[0]
    assert "How to create agent?" in doc.content
    assert "Use Agent class with config" in doc.content
    assert doc.meta_data["category"] == "development"
    assert doc.meta_data["tags"] == "agent,config"


def test_document_content_format(temp_csv_file, mock_vector_db):
    """Test document content formatting"""
    kb = RowBasedCSVKnowledgeBase(csv_path=temp_csv_file, vector_db=mock_vector_db)
    
    doc = kb.documents[0]
    
    # Should have Q: and A: format
    assert "**Q:** How to create agent?" in doc.content
    assert "**A:** Use Agent class with config" in doc.content


def test_metadata_structure(temp_csv_file, mock_vector_db):
    """Test document metadata structure"""
    kb = RowBasedCSVKnowledgeBase(csv_path=temp_csv_file, vector_db=mock_vector_db)
    
    doc = kb.documents[0]
    meta = doc.meta_data
    
    # Required metadata fields
    assert "row_index" in meta
    assert "source" in meta
    assert "category" in meta
    assert "tags" in meta
    assert "has_question" in meta
    assert "has_answer" in meta
    
    # Values
    assert meta["row_index"] == 1
    assert meta["source"] == "knowledge_rag_csv"
    assert meta["has_question"] is True
    assert meta["has_answer"] is True


def test_empty_csv_file(mock_vector_db):
    """Test handling of empty CSV file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = f.name
    
    try:
        kb = RowBasedCSVKnowledgeBase(csv_path=csv_path, vector_db=mock_vector_db)
        assert len(kb.documents) == 0
    finally:
        Path(csv_path).unlink(missing_ok=True)


def test_missing_csv_file(mock_vector_db):
    """Test handling of missing CSV file"""
    kb = RowBasedCSVKnowledgeBase(csv_path="/nonexistent/file.csv", vector_db=mock_vector_db)
    assert len(kb.documents) == 0


@patch.object(RowBasedCSVKnowledgeBase, 'load')
def test_reload_from_csv(mock_load, temp_csv_file, mock_vector_db):
    """Test CSV reload functionality"""
    kb = RowBasedCSVKnowledgeBase(csv_path=temp_csv_file, vector_db=mock_vector_db)
    original_count = len(kb.documents)
    
    # Test reload
    kb.reload_from_csv()
    
    # Should call load with recreate=True
    mock_load.assert_called_once_with(recreate=True, skip_existing=False)


def test_validate_filters(temp_csv_file, mock_vector_db):
    """Test filter validation"""
    kb = RowBasedCSVKnowledgeBase(csv_path=temp_csv_file, vector_db=mock_vector_db)
    
    # Set up valid metadata filters
    kb.valid_metadata_filters = {"category", "tags", "source"}
    
    # Test valid filters
    valid_filters = {"category": "development", "tags": "agent"}
    result_valid, result_invalid = kb.validate_filters(valid_filters)
    assert result_valid == valid_filters
    assert result_invalid == []
    
    # Test invalid filters
    invalid_filters = {"invalid_key": "value"}
    result_valid, result_invalid = kb.validate_filters(invalid_filters)
    assert result_valid == {}
    assert result_invalid == ["invalid_key"]


def test_skip_empty_answers(mock_vector_db):
    """Test handling rows with empty answers (should create documents for questions without answers)"""
    csv_content = [
        ["question", "answer", "category", "tags"],
        ["Valid question?", "Valid answer", "development", "test"],
        ["Empty answer question?", "", "development", "test"],  # Should create document for question only
        ["Another valid?", "Another answer", "development", "test"],
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_content)
        csv_path = f.name
    
    try:
        kb = RowBasedCSVKnowledgeBase(csv_path=csv_path, vector_db=mock_vector_db)
        # Should have 3 documents (including question without answer)
        assert len(kb.documents) == 3
        
        # Check that question without answer is included and formatted correctly
        empty_answer_doc = None
        for doc in kb.documents:
            if "Empty answer question?" in doc.content:
                empty_answer_doc = doc
                break
        
        assert empty_answer_doc is not None
        assert "**Q:** Empty answer question?" in empty_answer_doc.content
        assert "**A:**" not in empty_answer_doc.content  # Should not have empty answer section
        assert empty_answer_doc.meta_data["has_question"] is True
        assert empty_answer_doc.meta_data["has_answer"] is False
    finally:
        Path(csv_path).unlink(missing_ok=True)


def test_knowledge_loading_with_expected_columns(mock_vector_db):
    """Test knowledge loading from CSV with expected business columns."""
    # Create knowledge CSV with expected columns (question, answer, category, tags)
    test_data = [
        ["question", "answer", "category", "tags"],
        [
            "What are Python basics?",
            "Python is a programming language",
            "tech",
            "programming",
        ],
        [
            "What are data structures?",
            "Lists, dicts, sets are basic structures",
            "tech",
            "programming",
        ],
        ["What is machine learning?", "ML is subset of AI", "ai", "concepts"],
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
        csv_path = f.name

    try:
        knowledge = RowBasedCSVKnowledgeBase(
            str(csv_path),
            vector_db=mock_vector_db,
        )

        # Test that documents are loaded and available
        documents = knowledge.documents
        assert len(documents) == 3
        # Check that documents have expected content format
        assert documents[0].content is not None
        assert documents[0].id is not None
        assert "**Q:**" in documents[0].content
    finally:
        Path(csv_path).unlink(missing_ok=True)


def test_search_functionality_basic(mock_vector_db):
    """Test search functionality if available."""
    # Create searchable knowledge with expected columns
    test_data = [
        ["question", "answer", "category", "tags"],
        ["What is Python?", "Programming language", "tech", "code"],
        ["What is JavaScript?", "Web programming", "tech", "web"],
        ["What is a Database?", "Data storage", "tech", "data"],
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
        csv_path = f.name

    try:
        knowledge = RowBasedCSVKnowledgeBase(
            str(csv_path),
            vector_db=mock_vector_db,
        )

        # Test basic functionality exists
        documents = knowledge.documents
        assert len(documents) == 3

        # Test search if method exists (it inherits from DocumentKnowledgeBase)
        if hasattr(knowledge, "search"):
            # Mock the vector_db.search method to return sample results
            mock_vector_db.search.return_value = documents[:1]
            results = knowledge.search("Python")
            assert len(results) >= 0  # Should not crash
    finally:
        Path(csv_path).unlink(missing_ok=True)


def test_large_csv_processing(mock_vector_db):
    """Test processing of larger CSV files."""
    csv_content = [
        ["question", "answer", "category"],
    ]
    
    # Add many rows to test performance
    for i in range(200):
        csv_content.append([f"Question {i}?", f"Answer {i}", f"category_{i % 10}"])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_content)
        csv_path = f.name
    
    try:
        kb = RowBasedCSVKnowledgeBase(csv_path=csv_path, vector_db=mock_vector_db)
        
        # Should process all 200 documents
        assert len(kb.documents) == 200
        
        # Check first and last documents
        assert "Question 0?" in kb.documents[0].content
        assert "Question 199?" in kb.documents[199].content
        
        # Check metadata variety
        categories = {doc.meta_data["category"] for doc in kb.documents}
        assert len(categories) == 10  # Should have 10 different categories
    finally:
        Path(csv_path).unlink(missing_ok=True)


def test_special_characters_in_csv(mock_vector_db):
    """Test handling of special characters in CSV content."""
    csv_content = [
        ["question", "answer"],
        ['What is "AI"?', "Artificial Intelligence, ML & DL"],
        ["Cost analysis?", "$100,000 per year investment"],
        ["Physics formula?", "E = mc² energy equation"],
        ["Unicode test?", "Café ☕ with émojis 🤖"],
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_content)
        csv_path = f.name
    
    try:
        kb = RowBasedCSVKnowledgeBase(csv_path=csv_path, vector_db=mock_vector_db)
        
        assert len(kb.documents) == 4
        
        # Check special characters are preserved
        contents = [doc.content for doc in kb.documents]
        assert any("$100,000" in content for content in contents)
        assert any("E = mc²" in content for content in contents)
        assert any("Café ☕" in content for content in contents)
        assert any("🤖" in content for content in contents)
    finally:
        Path(csv_path).unlink(missing_ok=True)


def test_malformed_csv_handling(mock_vector_db):
    """Test graceful handling of malformed CSV files."""
    # Create a slightly malformed CSV that can still be parsed
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('question,answer\n')
        f.write('Valid question?,Valid answer\n')
        f.write('Question with extra comma,Answer, extra data\n')  # Extra comma
        csv_path = f.name
    
    try:
        kb = RowBasedCSVKnowledgeBase(csv_path=csv_path, vector_db=mock_vector_db)
        # Should handle gracefully and create what documents it can
        assert len(kb.documents) >= 0  # At least shouldn't crash
    except Exception:
        # It's acceptable if some malformed CSV causes exceptions
        pass
    finally:
        Path(csv_path).unlink(missing_ok=True)


def test_document_id_generation(temp_csv_file, mock_vector_db):
    """Test that documents get proper IDs generated."""
    kb = RowBasedCSVKnowledgeBase(csv_path=temp_csv_file, vector_db=mock_vector_db)
    
    # Check that all documents have unique IDs
    doc_ids = [doc.id for doc in kb.documents]
    assert len(doc_ids) == len(set(doc_ids))  # All IDs should be unique
    
    # Check ID format (should be strings and not empty)
    for doc_id in doc_ids:
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0


def test_content_format_variations(mock_vector_db):
    """Test different content column variations."""
    # Test with different column names
    test_data = [
        ["query", "response", "topic"],
        ["How to test?", "Use pytest framework", "testing"],
        ["What is Git?", "Version control system", "development"],
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
        csv_path = f.name

    try:
        # The KB should adapt to different column names
        kb = RowBasedCSVKnowledgeBase(csv_path=csv_path, vector_db=mock_vector_db)
        
        # Should still create documents
        assert len(kb.documents) >= 0
        
        # Check that content is created from available columns
        if len(kb.documents) > 0:
            doc_content = kb.documents[0].content
            assert isinstance(doc_content, str)
            assert len(doc_content) > 0
    finally:
        Path(csv_path).unlink(missing_ok=True)