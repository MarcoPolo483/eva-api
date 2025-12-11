# Minimal startup file for Azure App Service
# This ensures PYTHONPATH is set correctly for the src/ structure

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the app
from eva_api.main import app
