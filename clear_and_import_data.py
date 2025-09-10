#!/usr/bin/env python3
"""
Dataset Management Script for AI Script Studio
Usage: python clear_and_import_data.py [--clear] [--import path/to/data.jsonl]
"""

import argparse
import os
import sys
from db import get_session, init_db, import_jsonl
from models import Script, Rating, Revision

def clear_all_data():
    """Clear all data from the database tables"""
    print("🗑️  Clearing all existing data...")
    
    with get_session() as ses:
        # Delete in order to respect foreign key constraints
        # First delete ratings and revisions (they reference scripts)
        ratings_deleted = ses.query(Rating).delete()
        revisions_deleted = ses.query(Revision).delete()
        
        # Then delete scripts
        scripts_deleted = ses.query(Script).delete()
        
        ses.commit()
        
        print(f"✅ Cleared data:")
        print(f"   - {scripts_deleted} scripts")
        print(f"   - {ratings_deleted} ratings") 
        print(f"   - {revisions_deleted} revisions")
    
    return scripts_deleted + ratings_deleted + revisions_deleted

def import_new_data(file_path: str):
    """Import new data from JSONL file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return 0
    
    print(f"📥 Importing data from: {file_path}")
    
    try:
        count = import_jsonl(file_path)
        print(f"✅ Successfully imported {count} records")
        return count
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Manage AI Script Studio dataset")
    parser.add_argument("--clear", action="store_true", help="Clear all existing data")
    parser.add_argument("--import", dest="import_file", help="Import data from JSONL file")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    if not args.clear and not args.import_file:
        parser.print_help()
        return
    
    # Initialize database
    init_db()
    
    # Clear data if requested
    if args.clear:
        if not args.force:
            confirm = input("⚠️  Are you sure you want to delete ALL data? This cannot be undone! (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Operation cancelled")
                return
        
        clear_all_data()
    
    # Import new data if provided
    if args.import_file:
        import_new_data(args.import_file)
    
    print("🎉 Dataset management complete!")

if __name__ == "__main__":
    main()


