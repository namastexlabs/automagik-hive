#!/usr/bin/env python3
"""
Log Volume Measurement Script for Automagik Hive Optimization
Measures startup log volume and categorizes log types.
"""

import subprocess
import sys
import time
import re
from collections import defaultdict, Counter

def measure_startup_logs():
    """Run the server briefly and capture startup logs."""
    print("📊 Measuring baseline startup log volume...")
    
    try:
        # Start server and capture logs for 30 seconds
        process = subprocess.Popen(
            ["uv", "run", "python", "api/serve.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        logs = []
        start_time = time.time()
        
        while time.time() - start_time < 30:  # Run for 30 seconds
            line = process.stdout.readline()
            if line:
                logs.append(line.strip())
            else:
                break
                
        process.terminate()
        process.wait()
        
        return logs
        
    except KeyboardInterrupt:
        print("Measurement interrupted")
        return []
    except Exception as e:
        print(f"Error measuring logs: {e}")
        return []

def analyze_log_patterns(logs):
    """Analyze log patterns and categorize by type."""
    patterns = {
        'agent_inheritance': r'Applied inheritance to agent',
        'model_resolved': r'Model resolved successfully',
        'storage_created': r'Successfully created \w+ storage for',
        'agent_created': r'Agent \w+ created with inheritance',
        'team_member_loaded': r'Loaded team member:',
        'csv_processing': r'(documents processed|CSV|knowledge base)',
        'system_init': r'(initialized|configured|started|loaded|registered)',
        'alembic_migration': r'alembic\.runtime\.migration',
        'uvicorn': r'(Will watch|Uvicorn running|Started reloader)',
        'workflow_init': r'(Workflow|Template) \w+ initialized'
    }
    
    categorized = defaultdict(list)
    pattern_counts = Counter()
    total_lines = len(logs)
    
    for line in logs:
        matched = False
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, line):
                categorized[pattern_name].append(line)
                pattern_counts[pattern_name] += 1
                matched = True
                break
        
        if not matched:
            categorized['other'].append(line)
            pattern_counts['other'] += 1
    
    return categorized, pattern_counts, total_lines

def generate_report(categorized, pattern_counts, total_lines):
    """Generate a comprehensive log analysis report."""
    print(f"\n📈 LOG VOLUME ANALYSIS REPORT")
    print("=" * 60)
    print(f"Total startup log lines: {total_lines}")
    print(f"Target reduction (60%): {total_lines * 0.6:.0f} lines")
    print(f"Optimal target: <{total_lines * 0.4:.0f} lines")
    
    print(f"\n📊 LOG PATTERN BREAKDOWN:")
    print("-" * 40)
    
    # Sort by frequency
    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
    
    for pattern_name, count in sorted_patterns:
        percentage = (count / total_lines) * 100
        print(f"{pattern_name:20} | {count:3d} lines | {percentage:5.1f}%")
    
    print(f"\n🎯 HIGH-IMPACT OPTIMIZATION TARGETS:")
    print("-" * 40)
    
    high_impact = [item for item in sorted_patterns if item[1] > 3]  # More than 3 occurrences
    for pattern_name, count in high_impact:
        examples = categorized[pattern_name][:2]  # Show first 2 examples
        print(f"\n{pattern_name.upper()} ({count} occurrences):")
        for example in examples:
            # Truncate long lines
            truncated = example[:80] + "..." if len(example) > 80 else example
            print(f"  → {truncated}")
    
    return high_impact

def main():
    """Main measurement and analysis function."""
    print("🔍 Starting Automagik Hive Log Volume Analysis")
    
    # Read baseline if it exists
    try:
        with open('baseline_logs.txt', 'r') as f:
            baseline_logs = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"📋 Using existing baseline: {len(baseline_logs)} lines")
        logs = baseline_logs
        
    except FileNotFoundError:
        print("📋 No baseline found, measuring live startup...")
        logs = measure_startup_logs()
        
        # Save the baseline
        with open('baseline_logs.txt', 'w') as f:
            for log in logs:
                f.write(f"{log}\n")
    
    if not logs:
        print("❌ No logs captured. Cannot proceed with analysis.")
        return
    
    # Analyze patterns
    categorized, pattern_counts, total_lines = analyze_log_patterns(logs)
    
    # Generate report
    high_impact = generate_report(categorized, pattern_counts, total_lines)
    
    print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
    print("-" * 40)
    print("1. Move agent_inheritance, model_resolved to DEBUG level")
    print("2. Batch storage_created messages into single summary") 
    print("3. Replace individual agent_created with batch summary")
    print("4. Consolidate CSV processing messages")
    print("5. Reduce system_init verbosity with progress indicators")
    
    # Save detailed analysis
    with open('log_analysis_report.txt', 'w') as f:
        f.write("AUTOMAGIK HIVE LOG ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total lines: {total_lines}\n")
        f.write(f"Analysis timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for pattern_name, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{pattern_name}: {count} lines\n")
            for example in categorized[pattern_name][:3]:
                f.write(f"  - {example}\n")
            f.write("\n")
    
    print(f"\n✅ Analysis complete. Detailed report saved to 'log_analysis_report.txt'")

if __name__ == "__main__":
    main()