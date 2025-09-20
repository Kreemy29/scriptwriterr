#!/usr/bin/env python3
"""
Simple Interactive Dataset Manager for AI Script Studio
Run this script to easily manage your dataset
"""

import os
from sqlmodel import select
from db import get_session, init_db, import_jsonl
from models import Script, Rating, Revision

def show_current_stats():
    """Show current database statistics"""
    with get_session() as ses:
        script_count = len(list(ses.exec(select(Script))))
        rating_count = len(list(ses.exec(select(Rating))))
        revision_count = len(list(ses.exec(select(Revision))))
        
        print(f"\n📊 Current Database Stats:")
        print(f"   Scripts: {script_count}")
        print(f"   Ratings: {rating_count}")
        print(f"   Revisions: {revision_count}")
        
        if script_count > 0:
            # Show breakdown by creator and content type
            scripts = list(ses.exec(select(Script)))
            creators = {}
            content_types = {}
            
            for script in scripts:
                creators[script.creator] = creators.get(script.creator, 0) + 1
                content_types[script.content_type] = content_types.get(script.content_type, 0) + 1
            
            print(f"\n👥 By Creator:")
            for creator, count in sorted(creators.items()):
                print(f"   {creator}: {count}")
            
            print(f"\n📝 By Content Type:")
            for ctype, count in sorted(content_types.items()):
                print(f"   {ctype}: {count}")

def clear_database():
    """Clear all data with confirmation"""
    show_current_stats()
    
    print(f"\n⚠️  WARNING: This will delete ALL data from your database!")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != 'DELETE':
        print("❌ Operation cancelled")
        return False
    
    with get_session() as ses:
        # Delete in dependency order
        ratings_deleted = ses.query(Rating).delete()
        revisions_deleted = ses.query(Revision).delete() 
        scripts_deleted = ses.query(Script).delete()
        ses.commit()
        
        print(f"\n✅ Database cleared successfully!")
        print(f"   Deleted: {scripts_deleted} scripts, {ratings_deleted} ratings, {revisions_deleted} revisions")
        
    return True

def import_data():
    """Import data from JSONL file"""
    print(f"\n📁 Available files in current directory:")
    jsonl_files = [f for f in os.listdir('.') if f.endswith('.jsonl')]
    
    if jsonl_files:
        for i, file in enumerate(jsonl_files, 1):
            print(f"   {i}. {file}")
        print(f"   {len(jsonl_files) + 1}. Enter custom path")
    else:
        print("   No .jsonl files found in current directory")
        print("   You'll need to enter the full path to your data file")
    
    while True:
        choice = input(f"\nEnter your choice (1-{len(jsonl_files) + 1}), file path, or 'cancel': ")
        
        if choice.lower() == 'cancel':
            return False
        
        # Try to parse as number for file selection
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(jsonl_files):
                file_path = jsonl_files[idx]
                break
            elif idx == len(jsonl_files):
                file_path = input("Enter full path to your JSONL file: ")
                break
        except ValueError:
            # Treat as direct file path
            file_path = choice
            break
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"📥 Importing from: {file_path}")
    
    try:
        count = import_jsonl(file_path)
        print(f"✅ Successfully imported {count} records!")
        show_current_stats()
        return True
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def main():
    print("🎬 AI Script Studio - Dataset Manager")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    while True:
        show_current_stats()
        
        print(f"\n🛠️  What would you like to do?")
        print("1. Clear all existing data")
        print("2. Import new data from JSONL")
        print("3. Clear data AND import new data")
        print("4. Just show stats (refresh)")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            clear_database()
        elif choice == '2':
            import_data()
        elif choice == '3':
            if clear_database():
                import_data()
        elif choice == '4':
            continue  # Will show stats at top of loop
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")
        
        input("\nPress Enter to continue...")
        print("\n" + "="*50)

if __name__ == "__main__":
    main()
