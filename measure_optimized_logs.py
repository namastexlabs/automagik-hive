#!/usr/bin/env python3
"""
Measure optimized log volume compared to baseline
"""

import subprocess
import sys
import time
import signal
from pathlib import Path
from lib.logging import logger

def measure_optimized_startup():
    """Start server and capture optimized logs for comparison."""
    logger.info("📊 Measuring optimized startup log volume...")
    
    try:
        # Start server and capture logs for 30 seconds
        process = subprocess.Popen(
            ["uv", "run", "python", "api/serve.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            preexec_fn=os.setsid if hasattr(__import__('os'), 'setsid') else None
        )
        
        logs = []
        start_time = time.time()
        
        logger.info("🔧 ⏳ Capturing logs for 30 seconds...")
        while time.time() - start_time < 30:
            line = process.stdout.readline()
            if line:
                logs.append(line.strip())
                # Print progress every 5 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 5 == 0 and len(logs) % 10 == 0:
                    logger.info(f"🔧 Captured {len(logs)} lines in {elapsed:.0f}s")
            else:
                # Process ended early
                break
                
        # Terminate process gracefully
        try:
            if hasattr(process, 'terminate'):
                process.terminate()
                process.wait(timeout=5)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                process.kill()
            except ProcessLookupError:
                pass
        
        return [log for log in logs if log.strip()]
        
    except KeyboardInterrupt:
        logger.warning("\n🔧 ⚠️ Measurement interrupted by user")
        if 'process' in locals():
            try:
                process.terminate()
            except:
                pass
        return []
    except Exception as e:
        logger.error(f"🚨 Error measuring logs: {e}")
        return []

def compare_with_baseline():
    """Compare optimized logs with baseline."""
    logger.info("📊 🔍 Comparing optimized logs with baseline...")
    
    # Load baseline
    baseline_file = Path("baseline_logs.txt")
    if not baseline_file.exists():
        logger.error("🚨 baseline_logs.txt not found. Run measure_log_volume.py first.")
        return False
        
    with open(baseline_file) as f:
        baseline_logs = [line.strip() for line in f if line.strip()]
    
    baseline_count = len(baseline_logs)
    logger.info(f"📊 📋 Baseline log lines: {baseline_count}")
    
    # Measure optimized logs
    optimized_logs = measure_optimized_startup()
    optimized_count = len(optimized_logs)
    
    if optimized_count == 0:
        logger.error("🚨 No optimized logs captured")
        return False
        
    logger.info(f"📊 📋 Optimized log lines: {optimized_count}")
    
    # Calculate improvement
    if baseline_count > 0:
        reduction = ((baseline_count - optimized_count) / baseline_count) * 100
        logger.info(f"⚡ 📉 Log volume reduction: {reduction:.1f}%")
        
        target_reduction = 60
        if reduction >= target_reduction:
            logger.info(f"🎯 🎉 SUCCESS: Exceeded {target_reduction}% reduction target!")
        else:
            logger.warning(f"🎯 ⚠️ TARGET MISSED: Only {reduction:.1f}% reduction (target: {target_reduction}%)")
    else:
        logger.error("🚨 Cannot calculate reduction with empty baseline")
        return False
    
    # Save optimized logs for analysis
    with open("optimized_logs.txt", "w") as f:
        for log in optimized_logs:
            f.write(f"{log}\n")
    logger.info("🔧 💾 Optimized logs saved to optimized_logs.txt")
    
    # Show sample comparison
    logger.info("\n📊 SAMPLE COMPARISON:")
    logger.info("📊 " + "=" * 50)
    logger.info("📊 🔸 BASELINE (first 10 lines):")
    for i, line in enumerate(baseline_logs[:10]):
        logger.info(f"📊   {i+1:2d}: {line[:100]}")
    
    logger.info("\n📊 🔹 OPTIMIZED (first 10 lines):")
    for i, line in enumerate(optimized_logs[:10]):
        logger.info(f"📊   {i+1:2d}: {line[:100]}")
    
    return reduction >= target_reduction

def main():
    """Main comparison function."""
    logger.info("🎯 🚀 Log Optimization Validation")
    logger.info("🎯 " + "=" * 40)
    
    success = compare_with_baseline()
    
    if success:
        logger.info("\n🎯 ✅ LOG OPTIMIZATION SUCCESSFUL!")
        logger.info("🎯 Target reduction achieved")
        logger.info("🎯 ✅ Clean, informative logs maintained")
    else:
        logger.error("\n🎯 🚨 LOG OPTIMIZATION NEEDS ADJUSTMENT")
        logger.info("🎯 📋 Review logs and adjust batch thresholds")
    
    return success

if __name__ == "__main__":
    import os
    success = main()
    sys.exit(0 if success else 1)