#!/usr/bin/env python3
"""
Streamlit Cloud Entry Point for AI Script Studio
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the Streamlit app - this will execute all the app logic
import src.app
