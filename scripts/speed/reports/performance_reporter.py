#!/usr/bin/env python3
"""
Genie Speed Optimization Framework - Performance Reporter
Generates comprehensive optimization reports with visualization
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import traceback
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from jinja2 import Template
import markdown

# Add project root to path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))


class PerformanceReporter:
    """
    Generates comprehensive performance optimization reports
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.data_dir = project_root / "data" / "speed_optimization"
        self.reports_dir = project_root / "reports" / "speed_optimization"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[{level}] {message}")
    
    def load_optimization_history(self) -> Dict[str, Any]:
        """Load optimization history data"""
        history_file = self.data_dir / "optimization_history.json"
        
        if not history_file.exists():
            return {
                "total_optimizations": 0,
                "cumulative_improvement": 0,
                "last_updated": datetime.now().isoformat(),
                "optimizations": []
            }
        
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Error loading optimization history: {e}", "ERROR")
            return {"total_optimizations": 0, "optimizations": []}
    
    def load_revert_history(self) -> Dict[str, Any]:
        """Load revert history data"""
        history_file = self.data_dir / "revert_history.json"
        
        if not history_file.exists():
            return {
                "total_reverts": 0,
                "last_updated": datetime.now().isoformat(),
                "revert_counts": {},
                "reverts": []
            }
        
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Error loading revert history: {e}", "ERROR")
            return {"total_reverts": 0, "reverts": []}