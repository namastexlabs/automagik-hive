"""
Row-Based CSV Knowledge Base
Custom implementation that treats each CSV row as a separate document
"""
import csv
from typing import List, Optional
from pathlib import Path
from agno.document.base import Document
from agno.knowledge.document import DocumentKnowledgeBase
from agno.vectordb.base import VectorDb
from lib.logging import logger


class RowBasedCSVKnowledgeBase(DocumentKnowledgeBase):
    """
    CSV Knowledge Base that treats each CSV row as a separate document.
    
    Unlike the standard CSVKnowledgeBase which reads the entire CSV as one document
    and chunks it, this implementation creates one document per CSV row.
    """
    
    def __init__(self, csv_path: str, vector_db: VectorDb):
        """Initialize with CSV path and vector database."""
        # Load documents from CSV first
        csv_path_obj = Path(csv_path)
        documents = self._load_csv_as_documents(csv_path_obj)
        
        # Initialize parent DocumentKnowledgeBase with the documents
        super().__init__(documents=documents, vector_db=vector_db)
        
        # Store CSV path after parent initialization using object.__setattr__
        object.__setattr__(self, '_csv_path', csv_path_obj)
        
        logger.info("📊 Row-based CSV knowledge base initialized", 
                   csv_path=str(csv_path_obj), document_count=len(documents))
    
    def _load_csv_as_documents(self, csv_path: Path = None) -> List[Document]:
        """Load CSV file and create one document per row."""
        documents = []
        
        # Use provided path or stored path
        path_to_use = csv_path if csv_path else self._csv_path
        
        if not path_to_use.exists():
            logger.warning("📊 CSV file not found", path=str(path_to_use))
            return documents
        
        try:
            with open(path_to_use, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_index, row in enumerate(reader):
                    # Create content combining all columns with clear formatting
                    content_parts = []
                    
                    # Add problem
                    if 'problem' in row and row['problem']:
                        content_parts.append(f"**Problem:** {row['problem'].strip()}")
                    
                    # Add solution
                    if 'solution' in row and row['solution']:
                        content_parts.append(f"**Solution:** {row['solution'].strip()}")
                    
                    # Add typification
                    if 'typification' in row and row['typification']:
                        content_parts.append(f"**Typification:** {row['typification'].strip()}")
                    
                    # Add business unit
                    if 'business_unit' in row and row['business_unit']:
                        content_parts.append(f"**Business Unit:** {row['business_unit'].strip()}")
                    
                    # Create document content
                    content = "\n\n".join(content_parts)
                    
                    if content.strip():  # Only create document if there's content
                        # Create metadata for better filtering and search
                        meta_data = {
                            "row_index": row_index + 1,
                            "source": "knowledge_rag_csv",
                            "business_unit": row.get('business_unit', '').strip(),
                            "typification": row.get('typification', '').strip(),
                            "has_problem": bool(row.get('problem', '').strip()),
                            "has_solution": bool(row.get('solution', '').strip())
                        }
                        
                        # Create document with unique ID based on row index
                        doc = Document(
                            id=f"knowledge_row_{row_index + 1}",
                            content=content,
                            meta_data=meta_data
                        )
                        documents.append(doc)
            
            logger.info("📊 CSV loaded successfully", 
                       total_rows=len(documents), csv_path=str(csv_path))
                       
        except Exception as e:
            logger.error("📊 Error loading CSV file", error=str(e), csv_path=str(csv_path))
        
        return documents
    
    def reload_from_csv(self):
        """Reload documents from CSV file (for hot reload functionality)."""
        try:
            # Load new documents
            new_documents = self._load_csv_as_documents(self._csv_path)
            
            # Update the documents
            self.documents = new_documents
            
            # Reload into vector database
            self.load(recreate=True, skip_existing=False)
            
            logger.info("📊 CSV knowledge base reloaded", document_count=len(new_documents))
            
        except Exception as e:
            logger.error("📊 Error reloading CSV knowledge base", error=str(e))