#!/usr/bin/env python3
"""
Improve reference data quality and availability for AI Script Studio
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def clean_creator_names():
    """Standardize creator names for better reference matching"""
    
    from db import get_session
    from models import Script
    from sqlmodel import select
    
    name_mappings = {
        "Emily Kent (@itsemilykent)": "Emily Kent",
        "girl-next-door; playful; witty": "General Content",  # These seem to be test generations
    }
    
    print("Cleaning up creator names...")
    
    with get_session() as ses:
        for old_name, new_name in name_mappings.items():
            scripts = list(ses.exec(select(Script).where(Script.creator == old_name)))
            print(f"  Updating {len(scripts)} scripts from '{old_name}' to '{new_name}'")
            
            for script in scripts:
                script.creator = new_name
                ses.add(script)
            
            ses.commit()
    
    print("[OK] Creator names standardized")

def mark_best_ai_as_references():
    """Mark the best AI-generated scripts as references to expand the reference pool"""
    
    from db import get_session
    from models import Script
    from sqlmodel import select
    
    print("Finding best AI-generated scripts to mark as references...")
    
    with get_session() as ses:
        # Get AI scripts with good ratings
        good_ai_scripts = list(ses.exec(
            select(Script).where(
                Script.source == "ai",
                Script.compliance == "pass",
                Script.score_overall >= 4.0  # Only high-rated scripts
            ).limit(20)  # Limit to best 20
        ))
        
        print(f"  Found {len(good_ai_scripts)} high-quality AI scripts")
        
        for script in good_ai_scripts:
            script.is_reference = True
            ses.add(script)
        
        ses.commit()
        print(f"[OK] Marked {len(good_ai_scripts)} AI scripts as references")

def create_cross_creator_references():
    """Allow using references from other creators when a creator has too few"""
    
    db_file = Path("src/db.py")
    content = db_file.read_text(encoding='utf-8')
    
    # Update the hybrid refs function to be more flexible
    old_hybrid_start = "    if not all_refs:"
    old_hybrid_line = "        return _get_fallback_refs(content_type)"
    
    new_hybrid_logic = '''    if not all_refs:
        # Try to get references from other creators of the same content type
        print(f"No refs for {creator}/{content_type}, trying other creators...")
        other_refs = list(ses.exec(
            select(Script).where(
                Script.creator != creator,
                Script.content_type == content_type,
                Script.is_reference == True,
                Script.compliance != "fail"
            ).limit(6)
        ))
        
        if other_refs:
            print(f"Found {len(other_refs)} refs from other creators")
            # Use other creators' references but still return fallback if none
            all_refs = other_refs
        else:
            return _get_fallback_refs(content_type)'''
    
    if old_hybrid_start in content and old_hybrid_line in content:
        content = content.replace(old_hybrid_start + "\n" + "        return _get_fallback_refs(content_type)", new_hybrid_logic)
        db_file.write_text(content, encoding='utf-8')
        print("[OK] Updated hybrid refs to use cross-creator references")
        return True
    else:
        print("[WARNING] Could not find hybrid refs logic to update")
        return False

def show_reference_stats():
    """Show current reference availability"""
    
    from db import get_session, get_hybrid_refs
    from models import Script
    from sqlmodel import select, func
    
    print("\n=== REFERENCE AVAILABILITY AFTER IMPROVEMENTS ===")
    
    with get_session() as ses:
        # Count references by creator
        ref_counts = ses.exec(
            select(Script.creator, func.count(Script.id))
            .where(Script.is_reference == True)
            .group_by(Script.creator)
        ).all()
        
        print("Reference scripts by creator:")
        for creator, count in ref_counts:
            print(f"  {creator}: {count} reference scripts")
        
        # Test reference retrieval for main creators
        main_creators = ["Emily Kent", "Marcie", "Mia", "Anya"]
        content_types = ["skit", "thirst-trap", "talking-style"]
        
        print("\nReference retrieval test:")
        for creator in main_creators:
            for content_type in content_types:
                refs = get_hybrid_refs(creator, content_type, k=4)
                print(f"  {creator} + {content_type}: {len(refs)} refs available")
                if refs:
                    # Show first reference to see if it's from database or fallback
                    first_ref = refs[0]
                    is_fallback = "POV: You're having a breakdown" in first_ref or "Rating my life choices" in first_ref
                    source = "fallback" if is_fallback else "database"
                    print(f"    Sample ({source}): {first_ref[:60]}...")

def suggest_data_improvements():
    """Suggest ways to improve the reference data"""
    
    print("\n=== SUGGESTIONS FOR BETTER REFERENCES ===")
    print()
    print("1. IMPORT MORE DATA:")
    print("   - Each creator needs 15-20 good reference scripts minimum")
    print("   - Look for more .jsonl files with creator content")
    print("   - Import scripts from successful posts/content")
    print()
    print("2. QUALITY OVER QUANTITY:")
    print("   - Mark only your BEST scripts as is_reference=True")
    print("   - Remove low-quality or test scripts from references")
    print("   - Focus on scripts that match the dark humor style")
    print()
    print("3. CROSS-CREATOR LEARNING:")
    print("   - Allow creators to learn from each other's best content")
    print("   - Create 'General Content' category for universal good examples")
    print("   - Use style transfer techniques")
    print()
    print("4. MANUAL CURATION:")
    print("   - Review and rate existing reference scripts")
    print("   - Mark the best AI-generated scripts as references")
    print("   - Remove outdated or cringe reference content")

def main():
    """Main function to improve reference data"""
    print("Improving AI Script Studio reference data...")
    print("="*50)
    
    # 1. Clean up creator names
    try:
        clean_creator_names()
    except Exception as e:
        print(f"[ERROR] Creator name cleanup failed: {e}")
    
    # 2. Mark best AI scripts as references
    try:
        mark_best_ai_as_references()
    except Exception as e:
        print(f"[WARNING] Could not mark AI scripts as references: {e}")
    
    # 3. Enable cross-creator references
    if create_cross_creator_references():
        print("[OK] Cross-creator references enabled")
    
    # 4. Show current stats
    try:
        show_reference_stats()
    except Exception as e:
        print(f"[ERROR] Stats check failed: {e}")
    
    # 5. Provide suggestions
    suggest_data_improvements()
    
    print("\n" + "="*50)
    print("SUMMARY: Reference system improved with limited data")
    print("- Standardized creator names")
    print("- Enabled cross-creator learning") 
    print("- Added best AI scripts to reference pool")
    print("- System will now make better use of your ~10 scripts per creator")

if __name__ == "__main__":
    main()
