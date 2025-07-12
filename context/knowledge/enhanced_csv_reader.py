#!/usr/bin/env python3
"""
Enhanced CSV Reader for Agno Framework
Properly extracts CSV columns as document metadata for filtering
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

from agno.document import Document
from agno.document.reader.csv_reader import CSVReader


class EnhancedCSVReader(CSVReader):
    """
    Enhanced CSV Reader that properly extracts CSV columns as document metadata
    
    Unlike the default CSVReader that treats CSV as plain text, this reader:
    1. Parses CSV structure properly using csv.DictReader
    2. Creates one document per CSV row
    3. Extracts specified columns as metadata
    4. Separates content column from metadata columns
    """
    
    def __init__(
        self,
        content_column: str = "problem",
        metadata_columns: Optional[List[str]] = None,
        exclude_columns: Optional[List[str]] = None,
        encoding: str = "utf-8",
        **kwargs
    ):
        """
        Initialize Enhanced CSV Reader
        
        Args:
            content_column: Column to use as document content
            metadata_columns: Columns to extract as metadata (if None, extracts all except content)
            exclude_columns: Columns to completely ignore
            encoding: File encoding
        """
        super().__init__(**kwargs)
        self.content_column = content_column
        self.metadata_columns = metadata_columns or []
        self.exclude_columns = exclude_columns or []
        self.encoding = encoding
    
    def read(self, file: Path) -> List[Document]:
        """
        Read CSV file and return documents with proper metadata
        
        Args:
            file: Path to CSV file
            
        Returns:
            List of Document objects with CSV columns as metadata
        """
        if not file.exists():
            raise FileNotFoundError(f"CSV file not found: {file}")
        
        documents = []
        
        try:
            with open(file, 'r', encoding=self.encoding, newline='') as csvfile:
                # Use csv.DictReader for proper CSV parsing
                reader = csv.DictReader(csvfile)
                
                # Validate that content column exists
                if self.content_column not in reader.fieldnames:
                    raise ValueError(f"Content column '{self.content_column}' not found in CSV. Available columns: {reader.fieldnames}")
                
                # Determine metadata columns if not specified
                if not self.metadata_columns:
                    self.metadata_columns = [
                        col for col in reader.fieldnames 
                        if col != self.content_column and col not in self.exclude_columns
                    ]
                
                # Process each CSV row
                for row_idx, row in enumerate(reader):
                    try:
                        # Extract content
                        content = row.get(self.content_column, "")
                        if content is None:
                            print(f"Warning: None content in row {row_idx + 1}, skipping")
                            continue
                        
                        content = content.strip()
                        if not content:
                            print(f"Warning: Empty content in row {row_idx + 1}, skipping")
                            continue
                        
                        # Extract metadata
                        metadata = {}
                        for col in self.metadata_columns:
                            if col in row and row[col] is not None:
                                value = row[col].strip()
                                if value:  # Only add non-empty values
                                    metadata[col] = value
                        
                        # Create document with metadata
                        document = Document(
                            content=content,
                            meta_data=metadata,
                            id=f"csv_row_{row_idx + 1}"
                        )
                        
                        documents.append(document)
                        
                    except Exception as e:
                        print(f"Error processing CSV row {row_idx + 1}: {e}")
                        continue
        
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV file {file}: {e}")
        
        return documents
    
    def get_metadata_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get information about CSV structure and metadata extraction
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dictionary with CSV analysis information
        """
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        try:
            with open(file_path, 'r', encoding=self.encoding, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Read first few rows to analyze
                rows = list(reader)[:5]
                
                return {
                    "total_columns": len(reader.fieldnames),
                    "all_columns": reader.fieldnames,
                    "content_column": self.content_column,
                    "metadata_columns": self.metadata_columns,
                    "exclude_columns": self.exclude_columns,
                    "estimated_documents": len(rows) if len(rows) < 5 else "5+",
                    "sample_metadata": rows[0] if rows else {},
                    "encoding": self.encoding
                }
        
        except Exception as e:
            return {"error": str(e)}


def create_enhanced_csv_reader_for_pagbank() -> EnhancedCSVReader:
    """
    Create Enhanced CSV Reader specifically configured for PagBank knowledge base
    
    Configured for new 4-column CSV format:
    - problem: The customer problem/question (used as content)
    - solution: The solution/answer
    - typification: Service classification details
    - business_unit: Business unit for routing (Adquirência Web, Emissão, PagBank)
    
    Returns:
        Configured EnhancedCSVReader for new PagBank CSV structure
    """
    return EnhancedCSVReader(
        content_column="problem",  # Use problem as searchable content
        metadata_columns=[
            "business_unit",  # Essential: Business unit routing for agents
            "solution",       # Include solution in metadata for completeness
            "typification"   # Include typification for additional context
        ],
        exclude_columns=[],  # No columns to exclude in new format
        encoding="utf-8"
    )


if __name__ == "__main__":
    # Test the enhanced CSV reader
    from pathlib import Path
    
    csv_path = Path("knowledge_rag.csv")
    reader = create_enhanced_csv_reader_for_pagbank()
    
    print("🔍 Testing Enhanced CSV Reader")
    print("=" * 50)
    
    # Get metadata info
    info = reader.get_metadata_info(csv_path)
    print(f"📊 CSV Analysis:")
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    if csv_path.exists():
        print(f"\n📚 Reading documents...")
        documents = list(reader.read(csv_path))
        print(f"   Created {len(documents)} documents")
        
        if documents:
            print(f"\n🔍 Sample Document:")
            doc = documents[0]
            print(f"   Content: {doc.content[:100]}...")
            print(f"   Metadata: {doc.meta_data}")
    else:
        print(f"⚠️  CSV file not found: {csv_path}")