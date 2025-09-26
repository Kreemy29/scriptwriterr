#!/usr/bin/env python3
"""
Comprehensive Re-import Script for AI Script Studio
Re-imports all dataset files with proper field mapping and organization
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.append('src')

from db import get_session, init_db, import_jsonl
from models import Script, Rating, Revision
from sqlmodel import select

def clear_all_data():
    """Clear all existing data from database"""
    print("🗑️  Clearing all existing data...")
    
    with get_session() as ses:
        # Delete in order to respect foreign key constraints
        ratings_deleted = ses.query(Rating).delete()
        revisions_deleted = ses.query(Revision).delete()
        scripts_deleted = ses.query(Script).delete()
        
        ses.commit()
        
        print(f"✅ Cleared data:")
        print(f"   - {scripts_deleted} scripts")
        print(f"   - {ratings_deleted} ratings") 
        print(f"   - {revisions_deleted} revisions")
    
    return scripts_deleted + ratings_deleted + revisions_deleted

def import_dataset_file(file_path: str, expected_creator: str = None) -> int:
    """Import a single dataset file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return 0
    
    print(f"📥 Importing: {os.path.basename(file_path)}")
    
    try:
        count = import_jsonl(file_path)
        print(f"✅ Successfully imported {count} records")
        
        # Verify creator if specified
        if expected_creator:
            with get_session() as ses:
                creator_count = len(list(ses.exec(
                    select(Script).where(Script.creator == expected_creator)
                )))
                print(f"   📊 {expected_creator} scripts in database: {creator_count}")
        
        return count
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return 0

def organize_data_by_creator():
    """Organize data by creator type"""
    print("\n📊 Organizing data by creator...")
    
    with get_session() as ses:
        # Get all scripts
        all_scripts = list(ses.exec(select(Script)))
        
        # Define creator categories
        model_creators = ["Emily Kent", "Marcie", "Mia"]
        general_creators = ["General Content", "Anya"]
        
        # Count by category
        model_count = 0
        general_count = 0
        other_count = 0
        
        for script in all_scripts:
            if script.creator in model_creators:
                model_count += 1
            elif script.creator in general_creators:
                general_count += 1
            else:
                other_count += 1
                print(f"   ⚠️  Unknown creator: {script.creator}")
        
        print(f"📈 Data Organization:")
        print(f"   🎭 Model-specific data: {model_count} scripts")
        print(f"   🌐 General content data: {general_count} scripts")
        print(f"   ❓ Other/Unknown: {other_count} scripts")

def show_final_stats():
    """Show final database statistics"""
    print("\n📊 Final Database Statistics:")
    print("=" * 50)
    
    with get_session() as ses:
        # Total scripts
        total_scripts = len(list(ses.exec(select(Script))))
        print(f"Total Scripts: {total_scripts}")
        
        if total_scripts == 0:
            print("❌ No scripts found in database")
            return
        
        # Scripts by creator
        creators = {}
        for script in ses.exec(select(Script)):
            creator = script.creator
            creators[creator] = creators.get(creator, 0) + 1
        
        print(f"\nScripts by Creator:")
        for creator, count in sorted(creators.items()):
            print(f"   {creator}: {count}")
        
        # Scripts with rich data
        rich_data_count = 0
        for script in ses.exec(select(Script)):
            if script.concept or script.lighting or script.camera_direction:
                rich_data_count += 1
        
        print(f"\nScripts with Rich Production Data: {rich_data_count}")
        print(f"Reference Scripts: {len(list(ses.exec(select(Script).where(Script.is_reference == True))))}")

def main():
    print("🚀 AI Script Studio - Comprehensive Data Re-import")
    print("=" * 60)
    
    # Dataset files to import (from D:\work\nidhal\dataset\models)
    dataset_files = [
        # Model-specific data
        ("../dataset/models/emily_briefs_2025_1-10.jsonl", "Emily Kent"),
        ("../dataset/models/marcie_briefs_1-7.jsonl", "Marcie"),
        ("../dataset/models/mia_briefs_2025_1-10.jsonl", "Mia"),
        
        # General content data
        ("../dataset/models/trend_reels_1to10.jsonl", "General Content"),
        ("../dataset/models/trend_reels_11to20_fixed.jsonl", "General Content"),
        ("../dataset/models/trend_reels_21to30.jsonl", "General Content"),
        ("../dataset/models/trend_reels_31to40.jsonl", "General Content"),
        
        # Keep existing Anya data (if it exists)
        ("anya_scripts.jsonl", "Anya"),
    ]
    
    # Initialize database
    init_db()
    
    # Clear existing data
    confirm = input("⚠️  Clear all existing data and re-import? This cannot be undone! (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    clear_all_data()
    
    # Import all dataset files
    total_imported = 0
    successful_imports = 0
    
    for file_path, expected_creator in dataset_files:
        if os.path.exists(file_path):
            count = import_dataset_file(file_path, expected_creator)
            if count > 0:
                total_imported += count
                successful_imports += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n📈 Import Summary:")
    print(f"   ✅ Successfully imported {successful_imports} files")
    print(f"   📊 Total records imported: {total_imported}")
    
    # Organize and show final stats
    organize_data_by_creator()
    show_final_stats()
    
    print(f"\n🎉 Re-import complete!")
    print(f"💡 Your database now has all the rich video production details!")
    print(f"🔄 Restart your Streamlit app to see the updated data")

if __name__ == "__main__":
    main()
