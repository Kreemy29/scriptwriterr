#!/usr/bin/env python3
"""
Streamlit Cloud Entry Point for AI Script Studio
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables for Streamlit Cloud
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_SERVER_PORT"] = "8501"
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

# Import and run the app directly
import streamlit.web.cli as stcli

if __name__ == "__main__":
    # Run streamlit directly on the app file
    sys.argv = [
        "streamlit",
        "run", 
        "src/app.py",
        "--server.address", "0.0.0.0",
        "--server.port", "8501",
        "--server.headless", "true"
    ]
    stcli.main()
