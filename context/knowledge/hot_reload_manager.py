#!/usr/bin/env python3
"""
Hot Reload Knowledge Manager - KISS Principle
Simple file-based knowledge management that works while application is running
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from context.knowledge.csv_knowledge_base import create_pagbank_knowledge_base


class KnowledgeHotReloadManager:
    """
    KISS Knowledge Management - Simple file-based hot reload system
    
    Usage:
    1. Drop JSON files in knowledge/updates/ folder
    2. Manager automatically picks them up and updates knowledge base
    3. Files are moved to knowledge/processed/ when done
    
    File format: {"action": "add|update|delete", "entries": [...]}
    """
    
    def __init__(self, updates_dir: str = "knowledge/updates"):
        self.updates_dir = Path(updates_dir)
        self.processed_dir = Path("knowledge/processed")
        self.kb = create_pagbank_knowledge_base()
        
        # Create directories if they don't exist
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # File watcher
        self.observer = Observer()
        self.observer.schedule(
            UpdateFileHandler(self), 
            str(self.updates_dir), 
            recursive=False
        )
        
        print(f"📁 Knowledge hot reload manager initialized")
        print(f"   Updates folder: {self.updates_dir}")
        print(f"   Drop JSON files here for automatic processing")
    
    def start_watching(self):
        """Start watching for update files"""
        self.observer.start()
        print("👀 Started watching for knowledge updates...")
        
        # Process any existing files on startup
        self._process_existing_files()
    
    def stop_watching(self):
        """Stop watching for updates"""
        self.observer.stop()
        self.observer.join()
        print("⏹️ Stopped watching for knowledge updates")
    
    def _process_existing_files(self):
        """Process any JSON files that already exist in updates folder"""
        for json_file in self.updates_dir.glob("*.json"):
            self._process_update_file(json_file)
    
    def _process_update_file(self, file_path: Path):
        """Process a single update file"""
        try:
            print(f"🔄 Processing knowledge update: {file_path.name}")
            
            # Read the update file
            with open(file_path, 'r', encoding='utf-8') as f:
                update_data = json.load(f)
            
            action = update_data.get('action', 'add')
            entries = update_data.get('entries', [])
            
            # Process based on action
            if action == 'add':
                self._add_entries(entries)
            elif action == 'update':
                self._update_entries(entries)
            elif action == 'delete':
                self._delete_entries(entries)
            else:
                print(f"❌ Unknown action: {action}")
                return
            
            # Move processed file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            processed_name = f"{timestamp}_{file_path.name}"
            processed_path = self.processed_dir / processed_name
            
            file_path.rename(processed_path)
            print(f"✅ Processed {len(entries)} entries, moved to {processed_name}")
            
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            # Move to error folder for investigation
            error_dir = self.processed_dir / "errors"
            error_dir.mkdir(exist_ok=True)
            error_path = error_dir / f"error_{file_path.name}"
            file_path.rename(error_path)
    
    def _add_entries(self, entries: List[Dict[str, Any]]):
        """Add new knowledge entries"""
        for entry in entries:
            try:
                # Format: {"content": "...", "area": "...", "tipo_produto": "...", ...}
                content = entry.get('content', '')
                metadata = {k: v for k, v in entry.items() if k != 'content'}
                
                # Add to knowledge base using upsert
                # Format compatible with CSV structure
                document_dict = {"content": content, **metadata}
                self.kb.knowledge_base.load_dict(document_dict, upsert=True)
                
            except Exception as e:
                print(f"❌ Failed to add entry: {e}")
    
    def _update_entries(self, entries: List[Dict[str, Any]]):
        """Update existing entries (same as add with upsert=True)"""
        self._add_entries(entries)
    
    def _delete_entries(self, entries: List[Dict[str, Any]]):
        """Delete entries - simplified approach: mark as deleted"""
        # For simplicity, we'll add a "deleted" metadata flag
        # Full deletion would require vector DB-specific operations
        for entry in entries:
            content = f"[DELETED] {entry.get('content', '')}"
            metadata = {**entry, "status": "deleted"}
            
            self.kb.knowledge_base.load_dict({
                "content": content,
                "metadata": metadata
            }, upsert=True)


class UpdateFileHandler(FileSystemEventHandler):
    """File system event handler for knowledge updates"""
    
    def __init__(self, manager: KnowledgeHotReloadManager):
        self.manager = manager
    
    def on_created(self, event):
        if event.is_dir:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == '.json':
            # Wait a moment for file to be fully written
            time.sleep(0.5)
            self.manager._process_update_file(file_path)


# Simple utility functions for creating update files
def create_add_update(entries: List[Dict], filename: str = None):
    """Helper to create an 'add' update file"""
    if filename is None:
        filename = f"add_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    update_data = {
        "action": "add",
        "entries": entries,
        "created_at": datetime.now().isoformat(),
        "description": f"Adding {len(entries)} new knowledge entries"
    }
    
    updates_dir = Path("knowledge/updates")
    updates_dir.mkdir(parents=True, exist_ok=True)
    
    with open(updates_dir / filename, 'w', encoding='utf-8') as f:
        json.dump(update_data, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Created update file: {filename}")


def create_quick_entry(content: str, area: str, tipo_produto: str, **kwargs):
    """Quick way to add a single knowledge entry"""
    entry = {
        "content": content,
        "area": area,
        "tipo_produto": tipo_produto,
        "tipo_informacao": kwargs.get("tipo_informacao", "beneficios"),
        "nivel_complexidade": kwargs.get("nivel_complexidade", "intermediario"),
        "publico_alvo": kwargs.get("publico_alvo", "pessoa_fisica"),
        "palavras_chave": kwargs.get("palavras_chave", ""),
        "atualizado_em": datetime.now().strftime("%Y-%m")
    }
    
    create_add_update([entry])


if __name__ == "__main__":
    # Example usage
    manager = KnowledgeHotReloadManager()
    
    try:
        manager.start_watching()
        
        # Example: Add a new knowledge entry
        create_quick_entry(
            content="Novo recurso PIX: agora é possível agendar transferências PIX para até 60 dias.",
            area="conta_digital",
            tipo_produto="pix",
            tipo_informacao="beneficios",
            palavras_chave="pix agendamento transferencia 60 dias novo recurso"
        )
        
        print("Knowledge manager running. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down knowledge manager...")
        manager.stop_watching()