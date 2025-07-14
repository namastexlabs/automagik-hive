#!/usr/bin/env python3
"""
Test script to demonstrate the fresh start fix for knowledge base reloading
"""

import os
import shutil
from pathlib import Path
from context.knowledge.smart_incremental_loader import SmartIncrementalLoader


def test_fresh_start_scenarios():
    """Test different scenarios for fresh start"""
    
    print("🧪 Testing Fresh Start Scenarios")
    print("=" * 60)
    
    # Initialize loader
    loader = SmartIncrementalLoader()
    
    # Scenario 1: Current state (should show "no changes")
    print("\n1️⃣ Current State (with cache):")
    print("-" * 30)
    
    cache_stats = loader.get_cache_stats()
    print(f"Cache exists: {cache_stats['cache_exists']}")
    print(f"Cached entries: {cache_stats['cached_entries']}")
    
    result = loader.smart_load()
    print(f"Strategy used: {result.get('strategy', 'unknown')}")
    print(f"Result: {result.get('embedding_tokens_saved', 'No token info')}")
    
    # Scenario 2: Force recreate (should rebuild everything)
    print("\n2️⃣ Force Recreate (ignores cache):")
    print("-" * 30)
    
    result = loader.smart_load(force_recreate=True)
    print(f"Strategy used: {result.get('strategy', 'unknown')}")
    print(f"Entries processed: {result.get('entries_processed', 'unknown')}")
    print(f"Load time: {result.get('load_time_seconds', 'unknown'):.2f}s")
    
    # Scenario 3: Manual cache removal (should force fresh load)
    print("\n3️⃣ Manual Cache Removal:")
    print("-" * 30)
    
    cache_path = Path("knowledge/.content_cache.json")
    if cache_path.exists():
        print(f"Removing cache file: {cache_path}")
        cache_path.unlink()
    
    # Create new loader instance (to reload empty cache)
    fresh_loader = SmartIncrementalLoader()
    
    analysis = fresh_loader.analyze_changes()
    print(f"After cache removal - New entries: {analysis.get('new_entries', 0)}")
    print(f"After cache removal - Unchanged entries: {analysis.get('unchanged_entries', 0)}")
    
    result = fresh_loader.smart_load()
    print(f"Strategy used: {result.get('strategy', 'unknown')}")
    print(f"Entries processed: {result.get('entries_processed', 'unknown')}")


def clear_cache_and_force_fresh():
    """Clear cache and force fresh reload"""
    
    print("\n🔄 SOLUTION: Clear Cache and Force Fresh Reload")
    print("=" * 60)
    
    # Remove cache file
    cache_path = Path("knowledge/.content_cache.json")
    if cache_path.exists():
        print(f"✅ Removing cache file: {cache_path}")
        cache_path.unlink()
    else:
        print("❌ Cache file not found")
    
    # Create fresh loader
    loader = SmartIncrementalLoader()
    
    # Show what will happen
    analysis = loader.analyze_changes()
    print(f"\nAfter cache removal:")
    print(f"📊 Total rows: {analysis.get('total_rows', 0)}")
    print(f"🆕 New entries: {analysis.get('new_entries', 0)}")
    print(f"🔄 Changed entries: {analysis.get('changed_entries', 0)}")
    print(f"✅ Unchanged entries: {analysis.get('unchanged_entries', 0)}")
    
    # Now do the fresh load
    print("\n🚀 Starting fresh load...")
    result = loader.smart_load()
    
    print(f"\n📋 Fresh Load Results:")
    print(f"   Strategy: {result.get('strategy', 'unknown')}")
    print(f"   Entries processed: {result.get('entries_processed', 'unknown')}")
    print(f"   Load time: {result.get('load_time_seconds', 'unknown'):.2f}s")
    print(f"   Cache updated: {result.get('cache_updated', False)}")
    
    return result


def main():
    """Main test function"""
    
    # Test scenarios
    test_fresh_start_scenarios()
    
    # Provide the solution
    clear_cache_and_force_fresh()
    
    print("\n💡 SOLUTION SUMMARY:")
    print("=" * 60)
    print("For a TRUE fresh start, use one of these approaches:")
    print()
    print("1. 🔄 Force recreate (ignores cache):")
    print("   loader.smart_load(force_recreate=True)")
    print()
    print("2. 🗑️  Manual cache removal:")
    print("   rm knowledge/.content_cache.json")
    print("   # Then run normal load")
    print()
    print("3. 🛠️  Programmatic cache clearing:")
    print("   from pathlib import Path")
    print("   Path('knowledge/.content_cache.json').unlink(missing_ok=True)")
    print()
    print("The cache prevents unnecessary re-embedding to save tokens.")
    print("For fresh starts, you need to explicitly bypass or remove it.")


if __name__ == "__main__":
    main()