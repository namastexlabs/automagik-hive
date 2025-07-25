"""Registry test fixtures."""

import sys
from pathlib import Path

# Add fixtures directory to path
fixtures_dir = Path(__file__).parent.parent / "fixtures"
sys.path.insert(0, str(fixtures_dir))

# Import all fixtures
from config_fixtures import *
from service_fixtures import *