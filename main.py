#!/usr/bin/env python3
"""
AI Script Studio - Main Entry Point

This is the main entry point for the AI Script Studio application.
It can be used to run the Streamlit app or perform other operations.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def run_app():
    """Run the Streamlit application"""
    import streamlit.web.cli as stcli
    import sys
    
    # Set up the command line arguments for Streamlit
    sys.argv = [
        "streamlit",
        "run",
        "src/app.py",
        "--server.address", "0.0.0.0",
        "--server.port", "8501"
    ]
    
    # Run Streamlit
    stcli.main()

def init_database():
    """Initialize the database"""
    from src.db import create_tables
    print("Initializing database...")
    create_tables()
    print("Database initialized successfully!")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Script Studio")
    parser.add_argument(
        "command", 
        choices=["run", "init-db", "help"],
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_app()
    elif args.command == "init-db":
        init_database()
    elif args.command == "help":
        print("""
AI Script Studio Commands:
  run      - Start the Streamlit application
  init-db  - Initialize the database
  help     - Show this help message

Examples:
  python main.py run
  python main.py init-db
        """)

if __name__ == "__main__":
    main()
