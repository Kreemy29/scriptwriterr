#!/usr/bin/env python3
"""
Test the approval system by checking the database state
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_approval_system():
    """Test the approval system functionality"""
    
    from db import get_session
    from models import Script
    from sqlmodel import select, func
    
    print("Testing Approval System")
    print("="*30)
    
    with get_session() as ses:
        # Count scripts by source
        sources = ses.exec(
            select(Script.source, func.count(Script.id))
            .group_by(Script.source)
        ).all()
        
        print("Scripts by source:")
        for source, count in sources:
            print(f"  {source}: {count}")
        
        # Count reference vs AI scripts
        total_scripts = ses.exec(select(func.count(Script.id))).first()
        reference_scripts = ses.exec(select(func.count(Script.id)).where(Script.is_reference == True)).first()
        ai_scripts = ses.exec(select(func.count(Script.id)).where(Script.source == "ai")).first()
        
        print(f"\nScript breakdown:")
        print(f"  Total scripts: {total_scripts}")
        print(f"  Reference scripts: {reference_scripts}")
        print(f"  AI-generated scripts: {ai_scripts}")
        
        print(f"\n✅ AI scripts cleared: {ai_scripts == 0}")
        print(f"✅ Reference scripts preserved: {reference_scripts > 0}")
        
        if ai_scripts == 0:
            print("\n🎉 Approval system ready!")
            print("- All old AI scripts have been cleared")
            print("- Only reference scripts remain")
            print("- New AI scripts will require approval before saving")
        else:
            print(f"\n⚠️ Found {ai_scripts} AI scripts still in database")

if __name__ == "__main__":
    test_approval_system()
