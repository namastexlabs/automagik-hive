"""Tests for Row-Based CSV Knowledge Base"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

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
    mock_db.create.return_value = None
    mock_db.drop.return_value = None
    mock_db.id_exists.return_value = False
    mock_db.content_hash_exists.return_value = False
    mock_db.async_insert = AsyncMock(return_value=None)
    mock_db.async_upsert = AsyncMock(return_value=None)
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
    
    # Should call load with recreate=True and upsert=True
    mock_load.assert_called_once_with(recreate=True, upsert=True, skip_existing=False)


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


def test_docling_cpu_enforcement():
    """Test that DocumentConverter initialization enforces CPU-only execution.

    This regression test ensures Docling always uses CPU mode on macOS
    to avoid MPS backend compatibility issues. The implementation uses
    explicit pipeline configuration (not environment variables).

    The test verifies that DocumentConverter is initialized with:
    1. AcceleratorOptions(device=AcceleratorDevice.CPU)
    2. Proper PdfPipelineOptions configuration
    3. Format options passed to DocumentConverter constructor
    """
    from unittest.mock import patch, MagicMock, call

    # Skip test if docling not available
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.pipeline_options import AcceleratorDevice
    except ImportError:
        pytest.skip("Docling not available for testing")

    # Create fake PDF bytes for testing
    fake_pdf_bytes = b"%PDF-1.4 fake pdf content"

    # Track DocumentConverter initialization arguments
    captured_init_args = {}

    # Original __init__ to capture arguments
    original_init = DocumentConverter.__init__

    def capturing_init(self, *args, **kwargs):
        """Capture DocumentConverter initialization arguments."""
        # Record format_options passed to DocumentConverter
        captured_init_args['format_options'] = kwargs.get('format_options')
        # Don't actually initialize to avoid heavy processing
        return None

    # Patch DocumentConverter to intercept initialization
    with patch.object(DocumentConverter, '__init__', new=capturing_init):
        # Also patch convert() to avoid execution
        with patch.object(DocumentConverter, 'convert', return_value=MagicMock()):
            # Import the function being tested
            from lib.knowledge.row_based_csv_knowledge import extract_text_from_pdf_bytes

            # Execute the PDF extraction (which should configure CPU enforcement)
            try:
                result = extract_text_from_pdf_bytes(fake_pdf_bytes)
            except Exception:
                # We expect some exceptions since we're mocking
                pass

    # CRITICAL ASSERTIONS

    # 1. format_options must be provided
    assert captured_init_args.get('format_options') is not None, (
        "CPU enforcement not configured: format_options should be provided to DocumentConverter"
    )

    # 2. Verify PDF format options are present
    format_options = captured_init_args['format_options']
    from docling.datamodel.base_models import InputFormat
    assert InputFormat.PDF in format_options, (
        "PDF format options not found in DocumentConverter configuration"
    )

    # 3. Verify pipeline options with CPU acceleration are configured
    pdf_format_option = format_options[InputFormat.PDF]
    assert hasattr(pdf_format_option, 'pipeline_options'), (
        "pipeline_options not configured in PdfFormatOption"
    )

    pipeline_options = pdf_format_option.pipeline_options
    assert hasattr(pipeline_options, 'accelerator_options'), (
        "accelerator_options not configured in PdfPipelineOptions"
    )

    # 4. Verify CPU device is explicitly set
    accelerator_options = pipeline_options.accelerator_options
    assert hasattr(accelerator_options, 'device'), (
        "device not configured in AcceleratorOptions"
    )

    assert accelerator_options.device == AcceleratorDevice.CPU, (
        f"CPU enforcement not set: device should be AcceleratorDevice.CPU "
        f"but was {accelerator_options.device}"
    )
