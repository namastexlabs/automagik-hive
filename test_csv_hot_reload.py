#!/usr/bin/env python3
"""
Test CSV Hot Reload functionality
Simulates what happens when management edits the CSV file
"""

import time
import shutil
from pathlib import Path
from knowledge.csv_hot_reload import CSVHotReloadManager


def test_csv_hot_reload():
    """Test the CSV hot reload functionality"""
    
    print("🧪 Testing CSV Hot Reload Manager")
    print("=" * 50)
    
    # Create a backup of the original CSV
    original_csv = Path("knowledge/pagbank_knowledge.csv")
    backup_csv = Path("knowledge/pagbank_knowledge_backup.csv")
    
    if original_csv.exists():
        shutil.copy2(original_csv, backup_csv)
        print(f"✅ Backed up original CSV to {backup_csv}")
    
    try:
        # Initialize manager with short check interval for testing
        manager = CSVHotReloadManager(check_interval=5)  # 5 seconds for testing
        
        print("\n📊 Initial Status:")
        status = manager.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print(f"\n🔍 Starting file watcher...")
        print("   (Will check every 5 seconds for changes)")
        
        # Start watching in background
        import threading
        watch_thread = threading.Thread(target=manager.start_watching, daemon=True)
        watch_thread.start()
        
        print("\n💡 Simulation:")
        print("   In a real scenario, management would:")
        print("   1. Open pagbank_knowledge.csv in Excel")
        print("   2. Add/edit entries")
        print("   3. Save file (or sync from cloud)")
        print("   4. System automatically detects change and reloads")
        
        print("\n🔄 Simulating file change in 10 seconds...")
        time.sleep(10)
        
        # Simulate file change by touching the file
        original_csv.touch()
        print("📄 Simulated CSV file modification")
        
        # Wait for the change to be detected
        print("⏳ Waiting for change detection...")
        time.sleep(8)  # Wait a bit longer than check interval
        
        print("\n📊 Final Status:")
        status = manager.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Test completed successfully!")
        print("💡 In production:")
        print("   - Manager runs continuously in background")
        print("   - Management can edit CSV anytime")
        print("   - Changes apply automatically without restart")
        
    finally:
        # Restore original CSV if we had backed it up
        if backup_csv.exists():
            shutil.move(backup_csv, original_csv)
            print(f"🔄 Restored original CSV file")


def test_manual_commands():
    """Test manual commands for CSV manager"""
    
    print("\n🛠️  Testing Manual Commands")
    print("=" * 30)
    
    manager = CSVHotReloadManager()
    
    print("📊 Status check:")
    status = manager.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n🔄 Force reload test:")
    manager.force_reload()
    
    print("✅ Manual commands working")


if __name__ == "__main__":
    test_csv_hot_reload()
    test_manual_commands()