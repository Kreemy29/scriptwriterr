#!/usr/bin/env python3
"""
AI Script Studio - Streamlit Cloud Entry Point
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import modules directly
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Now execute the src/app.py file directly
with open("src/app.py", "r") as f:
    exec(f.read())