#!/usr/bin/env python3
"""
Streamlit Cloud Entry Point for AI Script Studio
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the Streamlit app
import streamlit as st
from src.app import main

if __name__ == "__main__":
    main()
