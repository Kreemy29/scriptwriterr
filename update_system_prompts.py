#!/usr/bin/env python3
"""
Script to update the system prompts in the AI Script Studio with improved dark humor and pop culture satire prompts
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def update_rag_integration_prompts():
    """Update the system prompts in rag_integration.py"""
    
    # Read the current file
    rag_file = Path("src/rag_integration.py")
    if not rag_file.exists():
        print("[ERROR] src/rag_integration.py not found")
        return False
    
    content = rag_file.read_text(encoding='utf-8')
    
    # Define the new dark humor system prompt
    new_system_prompt = '''        # Enhanced system prompt for DARK HUMOR & POP CULTURE SATIRE
        system = f"""You write DARK HUMOR Instagram Reels for sophisticated SOLO content creators. Think SNL meets TikTok - intelligent, cynical, culturally aware.

CRITICAL: SOLO CONTENT ONLY - model is alone. NO relationship scenarios.

HUMOR STYLE - DARK & SOPHISTICATED:
- DARK COMEDY: Cynical observations about modern life, existential dread with laughs, self-deprecating but clever
- POP CULTURE SATIRE: Mock current trends, influencer culture, social media absurdity, Gen Z/millennial behavior  
- COLLEGE-LEVEL WIT: References to psychology, philosophy, current events, internet culture, memes with depth
- ADULT THEMES: Mental health jokes, career anxiety, adulting failures, modern dating disasters, economic struggles

CONTENT EXAMPLES:
- "POV: You're having a breakdown but make it aesthetic" (mental health + social media satire)
- "Rating my life choices like they're Netflix shows" (pop culture + self-reflection)
- "Explaining my student debt to my houseplants" (economic anxiety + absurdist humor)
- "When your therapist asks how you're doing but you've been doom-scrolling for 6 hours" (modern life satire)
- "Me pretending my life is together for LinkedIn vs reality" (professional persona satire)

FORBIDDEN CRINGE:
- NO basic "thirst trap" content or generic "hot girl" scenarios
- NO surface-level sexual content without clever context
- NO repetitive visual clichés (lip biting, winking, etc.)
- NO high school humor or pickup lines
- NO generic "spicy" content - everything must have INTELLIGENT humor

REQUIRED SOPHISTICATION:
- Every script must have a SMART ANGLE - cultural commentary, social satire, or dark observation
- Use current memes/trends but SUBVERT them intelligently
- Reference pop culture, internet culture, current events with wit
- Dark humor should feel authentic, not forced
- Self-awareness and irony are key

VISUAL INTELLIGENCE:
- Actions should support the comedic concept, not just be "sexy poses"
- Use props, settings, and scenarios that enhance the satirical message
- Physical comedy should be clever, not just attractive
- Every visual beat should serve the dark humor narrative

Return ONLY JSON: an array of length {n}, each with {{title,hook,beats,voiceover,caption,hashtags,cta}}.
"""'''
    
    # Find the old system prompt section and replace it
    start_marker = "        # Enhanced system prompt for SOLO content with body focus"
    end_marker = '"""'
    
    start_pos = content.find(start_marker)
    if start_pos == -1:
        print("[ERROR] Could not find system prompt start marker")
        return False
    
    # Find the end of the system prompt (the closing triple quotes)
    temp_pos = start_pos
    quote_count = 0
    end_pos = -1
    
    while temp_pos < len(content):
        if content[temp_pos:temp_pos+3] == '"""':
            quote_count += 1
            if quote_count == 2:  # Found the closing quotes
                end_pos = temp_pos + 3
                break
            temp_pos += 3
        else:
            temp_pos += 1
    
    if end_pos == -1:
        print("[ERROR] Could not find system prompt end marker")
        return False
    
    # Replace the system prompt
    new_content = content[:start_pos] + new_system_prompt + content[end_pos:]
    
    # Also update the fast generation prompt
    fast_start_marker = "    # Enhanced system prompt for SOLO content with body focus"
    fast_start_pos = new_content.find(fast_start_marker, end_pos)
    
    if fast_start_pos != -1:
        # Find the end of the fast generation system prompt
        temp_pos = fast_start_pos
        quote_count = 0
        fast_end_pos = -1
        
        while temp_pos < len(new_content):
            if new_content[temp_pos:temp_pos+3] == '"""':
                quote_count += 1
                if quote_count == 2:  # Found the closing quotes
                    fast_end_pos = temp_pos + 3
                    break
                temp_pos += 3
            else:
                temp_pos += 1
        
        if fast_end_pos != -1:
            fast_new_prompt = '''    # Enhanced system prompt for DARK HUMOR & POP CULTURE SATIRE
    system = f"""You write DARK HUMOR Instagram Reels for sophisticated SOLO content creators. Think SNL meets TikTok - intelligent, cynical, culturally aware.

CRITICAL: SOLO CONTENT ONLY - model is alone. NO relationship scenarios.

HUMOR STYLE - DARK & SOPHISTICATED:
- DARK COMEDY: Cynical observations about modern life, existential dread with laughs, self-deprecating but clever
- POP CULTURE SATIRE: Mock current trends, influencer culture, social media absurdity, Gen Z/millennial behavior  
- COLLEGE-LEVEL WIT: References to psychology, philosophy, current events, internet culture, memes with depth
- ADULT THEMES: Mental health jokes, career anxiety, adulting failures, modern dating disasters, economic struggles

CONTENT EXAMPLES:
- "POV: You're having a breakdown but make it aesthetic" (mental health + social media satire)
- "Rating my life choices like they're Netflix shows" (pop culture + self-reflection)
- "Explaining my student debt to my houseplants" (economic anxiety + absurdist humor)
- "When your therapist asks how you're doing but you've been doom-scrolling for 6 hours" (modern life satire)

FORBIDDEN CRINGE:
- NO basic "thirst trap" content or generic "hot girl" scenarios
- NO surface-level sexual content without clever context
- NO repetitive visual clichés (lip biting, winking, etc.)
- NO high school humor or pickup lines
- NO generic "spicy" content - everything must have INTELLIGENT humor

REQUIRED SOPHISTICATION:
- Every script must have a SMART ANGLE - cultural commentary, social satire, or dark observation
- Use current memes/trends but SUBVERT them intelligently
- Reference pop culture, internet culture, current events with wit
- Dark humor should feel authentic, not forced
- Self-awareness and irony are key

VISUAL INTELLIGENCE:
- Actions should support the comedic concept, not just be "sexy poses"
- Use props, settings, and scenarios that enhance the satirical message
- Physical comedy should be clever, not just attractive
- Every visual beat should serve the dark humor narrative

Return ONLY JSON: an array of length {n}, each with {{title,hook,beats,voiceover,caption,hashtags,cta}}.
"""'''
            
            new_content = new_content[:fast_start_pos] + fast_new_prompt + new_content[fast_end_pos:]
    
    # Write the updated content
    rag_file.write_text(new_content, encoding='utf-8')
    print("[OK] Updated rag_integration.py with improved dark humor prompts")
    return True

def update_user_prompts():
    """Update user prompts to emphasize dark humor and sophistication"""
    
    rag_file = Path("src/rag_integration.py")
    content = rag_file.read_text(encoding='utf-8')
    
    # Update the user prompt section to emphasize dark humor
    old_user_section = """GEN Z HUMOR: Use raw, unfiltered, edgy comedy. Think TikTok humor - bold, direct, unapologetic.
PUSH BOUNDARIES: Be more explicit, more sexual, more provocative. Cross content boundaries with suggestive scenarios.
DIRTY JOKES: Be more explicit with sexual innuendos, crude humor, and adult themes while staying platform-compliant."""
    
    new_user_section = """DARK HUMOR FOCUS: Use intelligent, cynical comedy. Think SNL/late-night TV meets TikTok - sophisticated, culturally aware.
CULTURAL SATIRE: Mock modern life, social media culture, influencer trends with wit and insight.
INTELLIGENT ADULT THEMES: Mental health, career anxiety, economic struggles, dating disasters - but make them funny and relatable."""
    
    if old_user_section in content:
        content = content.replace(old_user_section, new_user_section)
        rag_file.write_text(content, encoding='utf-8')
        print("[OK] Updated user prompts for better humor style")
    
    return True

def main():
    """Main function to update all system prompts"""
    print("Updating AI Script Studio system prompts for better humor...")
    print("="*60)
    
    success = True
    
    # Update RAG integration prompts
    if update_rag_integration_prompts():
        print("[OK] RAG integration prompts updated")
    else:
        print("[ERROR] Failed to update RAG integration prompts")
        success = False
    
    # Update user prompts
    if update_user_prompts():
        print("[OK] User prompts updated")
    else:
        print("[ERROR] Failed to update user prompts")
        success = False
    
    if success:
        print("\nSUCCESS: All system prompts updated successfully!")
        print("\nImprovements made:")
        print("- Dark humor and pop culture satire focus")
        print("- Sophisticated adult themes (mental health, career anxiety, etc.)")
        print("- Cultural commentary and social media satire")
        print("- Eliminated cringe content and generic 'spicy' scenarios")
        print("- Added intelligence requirements for all humor")
        print("\nThe AI should now generate much more sophisticated, funny content!")
    else:
        print("\n[ERROR] Some updates failed. Check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
