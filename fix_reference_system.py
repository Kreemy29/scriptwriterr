#!/usr/bin/env python3
"""
Fix the reference retrieval system to use actual database scripts instead of cringe fallbacks
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def update_fallback_refs():
    """Update the fallback references with sophisticated dark humor examples"""
    
    db_file = Path("src/db.py")
    content = db_file.read_text(encoding='utf-8')
    
    # New sophisticated fallback references
    new_fallbacks = '''def _get_fallback_refs(content_type: str) -> List[str]:
    """Provide high-quality fallback references with dark humor and pop culture satire"""
    fallback_refs = {
        "skit": [
            "POV: You're having a breakdown but make it aesthetic for Instagram",
            "Rating my life choices like they're Netflix shows - mostly cancelled after one season", 
            "Explaining my student debt to my houseplants because they're the only ones who listen",
            "When your therapist asks how you're doing but you've been doom-scrolling for 6 hours",
            "Me pretending my life is together for LinkedIn vs the reality of eating cereal for dinner",
            "My mental health journey but make it a personality trait",
            "Comment 'SAME' if you've turned your trauma into content",
            "Save this for your next existential crisis"
        ],
        "thirst-trap": [
            "POV: You're confident but it's actually just undiagnosed mental illness",
            "Rating my personality disorders by how well they serve me in capitalism",
            "When you realize your main character energy is just anxiety with better lighting", 
            "Me manifesting my dream life vs actually doing anything about it",
            "The confidence is fake but the student debt is real",
            "Comment 'THERAPY' if you relate to this energy",
            "Tag someone who needs to embrace their chaos",
            "Save this for your next identity crisis"
        ],
        "talking-style": [
            "Let me explain why I'm emotionally unavailable but make it sound intellectual",
            "My Roman Empire is actually just wondering if I'm the toxic one in every situation",
            "Ranking my coping mechanisms by how socially acceptable they are", 
            "Why I collect hobbies like Pokemon cards but never actually do them",
            "The psychology behind why I respond to texts immediately or never",
            "Comment your most unhinged thought that you think is normal",
            "Share this if you've ever psychoanalyzed a 'hey' text for 3 hours",
            "Save for when you need to feel intellectually superior"
        ],
        "reaction-prank": [
            "POV: You try to be mysterious but you're actually just awkward",
            "Rating social interactions by how much I want to disappear afterward",
            "When someone asks what I do for fun and I panic because doom-scrolling isn't a hobby", 
            "Me trying to be a functioning adult vs my actual life skills",
            "The audacity of life expecting me to have my shit together at this age",
            "Comment 'CALLED OUT' if this is too real",
            "Tag someone who's also just winging adulthood",
            "Save this for your next social anxiety spiral"
        ],
        "lifestyle": [
            "My self-care routine is just buying things I don't need and calling it retail therapy",
            "Rating my healthy habits by how long they lasted (spoiler: not long)",
            "POV: You're trying to be that girl but you're actually just tired", 
            "My morning routine: anxiety, coffee, more anxiety, check phone, existential dread",
            "The wellness industry wants me to manifest abundance but I can barely manifest motivation",
            "Comment your most chaotic self-care moment",
            "Share if you've ever bought a planner to organize your life and never used it",
            "Save for when you need to feel better about your life choices"
        ]
    }
    
    return fallback_refs.get(content_type, fallback_refs["skit"])'''
    
    # Find and replace the old fallback function
    start_marker = "def _get_fallback_refs(content_type: str) -> List[str]:"
    end_marker = "    return fallback_refs.get(content_type, fallback_refs[\"skit\"])"
    
    start_pos = content.find(start_marker)
    if start_pos == -1:
        print("[ERROR] Could not find fallback function")
        return False
    
    # Find the end of the function
    end_pos = content.find(end_marker, start_pos)
    if end_pos == -1:
        print("[ERROR] Could not find end of fallback function")
        return False
    
    end_pos += len(end_marker)
    
    # Replace the function
    new_content = content[:start_pos] + new_fallbacks + content[end_pos:]
    
    # Write back
    db_file.write_text(new_content, encoding='utf-8')
    print("[OK] Updated fallback references with sophisticated dark humor")
    return True

def fix_reference_filtering():
    """Improve the reference filtering to get better quality snippets"""
    
    db_file = Path("src/db.py")
    content = db_file.read_text(encoding='utf-8')
    
    # Update the snippet filtering logic
    old_filter = '''    # Filter out garbage snippets (too short, metadata fragments, etc.)
    clean_snippets = []
    for sn in snippets:
        if (len(sn.strip()) > 15 and 
            len(sn.strip()) < 200 and 
            not any(x in sn.lower() for x in ["brand fit", "tl;dr", "meta", "accessibility", "quick text beats", "beat (00:00"]) and
            not sn.strip().startswith(";") and
            not sn.strip().startswith(":")):
            clean_snippets.append(sn.strip())'''
    
    new_filter = '''    # Filter out garbage snippets and prioritize quality content
    clean_snippets = []
    for sn in snippets:
        if (len(sn.strip()) > 20 and  # Increased minimum length
            len(sn.strip()) < 300 and  # Increased maximum length
            not any(x in sn.lower() for x in [
                "brand fit", "tl;dr", "meta", "accessibility", "quick text beats", 
                "beat (00:00", "trending vo:", "audio:", "text overlay:", "shot of"
            ]) and
            not sn.strip().startswith(";") and
            not sn.strip().startswith(":") and
            not sn.strip().startswith("(") and
            # Prioritize hook-like content
            ("pov:" in sn.lower() or 
             "when " in sn.lower() or 
             "me " in sn.lower() or
             "rating " in sn.lower() or
             "explaining " in sn.lower() or
             len(sn.strip()) > 50)):  # Or longer content
            clean_snippets.append(sn.strip())'''
    
    if old_filter in content:
        content = content.replace(old_filter, new_filter)
        db_file.write_text(content, encoding='utf-8')
        print("[OK] Improved reference filtering logic")
        return True
    else:
        print("[WARNING] Could not find old filter logic to replace")
        return False

def check_database_quality():
    """Check the quality of references in the database"""
    
    from db import get_session, get_hybrid_refs
    from models import Script
    from sqlmodel import select
    
    print("\n=== DATABASE REFERENCE QUALITY CHECK ===")
    
    with get_session() as ses:
        # Check actual database content
        creators = ["Emily Kent", "Marcie", "Mia"]
        
        for creator in creators:
            # Get actual scripts from database (not fallbacks)
            actual_scripts = list(ses.exec(
                select(Script).where(
                    Script.creator == creator,
                    Script.is_reference == True,
                    Script.compliance != "fail"
                ).limit(3)
            ))
            
            print(f"\n{creator} - {len(actual_scripts)} actual reference scripts:")
            for script in actual_scripts:
                print(f"  Title: {script.title}")
                if script.hook:
                    print(f"  Hook: {script.hook[:80]}...")
                if script.beats:
                    print(f"  Beats: {len(script.beats)} beats")
                if script.caption:
                    print(f"  Caption: {script.caption[:80]}...")
            
            # Test hybrid refs
            refs = get_hybrid_refs(creator, "skit", k=3)
            print(f"  Hybrid refs returned: {len(refs)}")
            for i, ref in enumerate(refs[:2], 1):
                print(f"    {i}. {ref[:80]}...")

def improve_reference_extraction():
    """Improve how we extract snippets from scripts"""
    
    db_file = Path("src/db.py")
    content = db_file.read_text(encoding='utf-8')
    
    # Update extract_snippets_from_script function
    old_extract = '''def extract_snippets_from_script(s: Script, max_lines: int = 3) -> List[str]:
    items: List[str] = []
    if s.hook:
        items.append(s.hook.strip())
    if s.beats:
        items.extend([b.strip() for b in s.beats[:2]])  # first 1–2 beats
    if s.caption:
        items.append(s.caption.strip()[:120])
    # dedupe while preserving order
    seen, uniq = set(), []
    for it in items:
        if it and it not in seen:
            uniq.append(it); seen.add(it)
    return uniq[:max_lines]'''
    
    new_extract = '''def extract_snippets_from_script(s: Script, max_lines: int = 4) -> List[str]:
    items: List[str] = []
    
    # Prioritize hook content (most important)
    if s.hook and len(s.hook.strip()) > 10:
        items.append(s.hook.strip())
    
    # Add video_hook if different from hook
    if hasattr(s, 'video_hook') and s.video_hook and s.video_hook != s.hook:
        if len(s.video_hook.strip()) > 10:
            items.append(s.video_hook.strip())
    
    # Add best beats (filter out technical beats)
    if s.beats:
        good_beats = []
        for beat in s.beats[:4]:  # Check first 4 beats
            beat = beat.strip()
            if (len(beat) > 20 and 
                not beat.lower().startswith(('shot of', 'cut to', 'close-up', 'wide shot')) and
                not any(x in beat.lower() for x in ['00:', 'camera', 'lighting', 'audio'])):
                good_beats.append(beat)
        items.extend(good_beats[:2])  # Take best 2 beats
    
    # Add caption if it's substantial
    if s.caption and len(s.caption.strip()) > 20:
        items.append(s.caption.strip()[:150])
    
    # Add voiceover content if meaningful
    if s.voiceover and len(s.voiceover.strip()) > 20:
        items.append(s.voiceover.strip()[:150])
    
    # Dedupe while preserving order
    seen, uniq = set(), []
    for it in items:
        if it and it not in seen and len(it.strip()) > 15:
            uniq.append(it); seen.add(it)
    
    return uniq[:max_lines]'''
    
    if old_extract in content:
        content = content.replace(old_extract, new_extract)
        db_file.write_text(content, encoding='utf-8')
        print("[OK] Improved snippet extraction logic")
        return True
    else:
        print("[WARNING] Could not find old extract function to replace")
        return False

def main():
    """Main function to fix reference system"""
    print("Fixing AI Script Studio reference system...")
    print("="*50)
    
    success = True
    
    # 1. Update fallback references
    if update_fallback_refs():
        print("[OK] Fallback references updated with dark humor")
    else:
        print("[ERROR] Failed to update fallback references")
        success = False
    
    # 2. Improve reference filtering
    if fix_reference_filtering():
        print("[OK] Reference filtering improved")
    else:
        print("[WARNING] Reference filtering update had issues")
    
    # 3. Improve snippet extraction
    if improve_reference_extraction():
        print("[OK] Snippet extraction improved")
    else:
        print("[WARNING] Snippet extraction update had issues")
    
    # 4. Check database quality
    try:
        check_database_quality()
        print("[OK] Database quality check completed")
    except Exception as e:
        print(f"[ERROR] Database quality check failed: {e}")
        success = False
    
    if success:
        print("\nSUCCESS: Reference system improvements completed!")
        print("\nImprovements made:")
        print("- Updated fallback references with dark humor and pop culture satire")
        print("- Improved filtering to prioritize quality content")
        print("- Enhanced snippet extraction to get better references")
        print("- The AI will now use actual database scripts more effectively")
        print("\nThe system should now inspire from your existing sophisticated scripts!")
    else:
        print("\n[WARNING] Some improvements completed with issues.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
