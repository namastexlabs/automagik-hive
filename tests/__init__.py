"""
Tests package initialization for Automagik Hive.

This module ensures that all tests have access to the project modules by
adding the project root to the Python path early in the import process.
"""

import sys
from pathlib import Path

# Add project root to Python path to fix module import issues
# This needs to be done at the package level to ensure it's applied 
# before any test modules attempt to import project code
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
