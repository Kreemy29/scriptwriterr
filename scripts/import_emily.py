#!/usr/bin/env python3
"""
Import Emily's data for testing the new hierarchy system
"""

import json
from data_hierarchy import hierarchy_manager
from db import get_session, import_jsonl
from models import Script
from sqlmodel import select

def create_emily_profile():
    """Create Emily's model profile"""
    print("👤 Creating Emily's model profile...")
    
    emily_profile = {
        "model_name": "Emily Kent",
        "niche": "Artistic Sensual",
        "brand_description": "Sophisticated, artistic creator with a mysterious allure. British accent, ginger hair, intelligent and creative personality with a sensual edge. Focuses on artistic expression, travel, and sophisticated storytelling.",
        "instagram_handle": "@itsemilykent",
        "content_style": "Artistic travel content, sophisticated pool/beach settings, creative storytelling, adventure narratives, boyfriend POV with artistic flair",
        "voice_tone": "Sophisticated, artistic, mysterious, sensual, British accent, intelligent and creative",
        "visual_style": "Ginger hair, artistic makeup, elegant swimwear/activewear, travel settings, pool/beach locations with artistic composition",
        "target_audience": "Young adults 18-30, art enthusiasts, travel lovers, sophisticated content consumers, creative minds",
        "content_themes": ["artistic", "travel", "sophisticated", "creative", "sensual", "storytelling", "adventure", "artistic_expression"]
    }
    
    try:
        model = hierarchy_manager.add_model_profile(
            model_name=emily_profile["model_name"],
            niche=emily_profile["niche"],
            brand_description=emily_profile["brand_description"],
            instagram_handle=emily_profile["instagram_handle"],
            content_style=emily_profile["content_style"],
            voice_tone=emily_profile["voice_tone"],
            visual_style=emily_profile["visual_style"],
            target_audience=emily_profile["target_audience"],
            content_themes=emily_profile["content_themes"]
        )
        print(f"✅ Created Emily's profile: {model.model_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to create Emily's profile: {e}")
        return False

def import_emily_scripts():
    """Import Emily's scripts from JSONL"""
    print("📥 Importing Emily's scripts...")
    
    try:
        # Import the scripts
        count = import_jsonl("D:/work/nidhal/dataset/models/emily_briefs_2025_1-10.jsonl")
        print(f"✅ Imported {count} scripts from Emily's file")
        
        # Update scripts to be associated with Emily and mark as references
        with get_session() as session:
            # Get all scripts that were just imported
            scripts = list(session.exec(select(Script).where(Script.creator == "Emily Kent (@itsemilykent)")))
            
            for script in scripts:
                # Update creator name to match our model profile
                script.creator = "Emily Kent"
                script.is_reference = True
                # Map video_type to content_type
                if script.content_type == "skit":
                    script.content_type = "skit"
            
            session.commit()
            print(f"✅ Updated {len(scripts)} scripts for Emily")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import Emily's scripts: {e}")
        return False

def create_emily_content_templates():
    """Create content templates for Emily's niche"""
    print("📝 Creating content templates for Emily's niche...")
    
    templates = [
        {
            "template_name": "Artistic Pool Story",
            "content_type": "storytelling",
            "niche": "Artistic Sensual",
            "template_data": {
                "title": "The Art of Understanding",
                "hook": "If I book the hotel with the pool view...",
                "beats": ["Artistic setup at pool edge", "Slow, sensual turn to camera", "Mysterious reveal", "Elegant smile and landscape"],
                "voiceover": "If I book the hotel with the pool view... I hope you understand the assignment",
                "caption": "Pool view = assignment. Comment 'assignment' if you get it 😉",
                "hashtags": ["#artistic", "#travel", "#villa", "#infinitypool", "#assignment", "#reels", "#fyp"],
                "cta": "Comment 'assignment' if you'd book this view"
            }
        },
        {
            "template_name": "Adventure Narrative",
            "content_type": "storytelling", 
            "niche": "Artistic Sensual",
            "template_data": {
                "title": "The Art of Adventure",
                "hook": "POV: your GF swore she 'knows how to ride' 😅",
                "beats": ["Artistic POV angle on ATV", "Dramatic lurch and fall", "Muddy aftermath with artistic composition", "Stand up with elegant smile"],
                "voiceover": "POV: your GF insisted she 'knew how to ride'... (She was not okay... broke 3 toes)",
                "caption": "We live & we learn 😂 Mud: 1 — Me: 0. (I'm okay now)",
                "hashtags": ["#artistic", "#atv", "#adventuredate", "#mudlife", "#bfpov", "#fails", "#reels"],
                "cta": "Comment 'MUD' if you've had an adventure date go sideways"
            }
        },
        {
            "template_name": "Creative Travel Story",
            "content_type": "storytelling",
            "niche": "Artistic Sensual", 
            "template_data": {
                "title": "The Art of Travel",
                "hook": "Looking for a bf — must be good with a camera + able to travel the world with me",
                "beats": ["Artistic back-facing at pool edge", "Hold pose with scenic composition", "Slow, elegant head turn", "Mysterious look to camera"],
                "voiceover": "Looking for a bf — must be good with a camera + able to travel the world with me",
                "caption": "Serious inquiries only: camera skills, passport, and patience for chaos. Comment 'camera'",
                "hashtags": ["#artistic", "#traveller", "#contentcreator", "#dating", "#bfpov", "#reels", "#fyp"],
                "cta": "Comment 'camera' if you'd apply"
            }
        }
    ]
    
    for template_data in templates:
        try:
            template = hierarchy_manager.add_content_template(
                template_name=template_data["template_name"],
                content_type=template_data["content_type"],
                niche=template_data["niche"],
                template_data=template_data["template_data"]
            )
            print(f"✅ Created template: {template.template_name}")
        except Exception as e:
            print(f"❌ Failed to create template {template_data['template_name']}: {e}")

def main():
    """Main function to import all Emily data"""
    print("🎬 Importing Emily's data for testing...")
    print("=" * 50)
    
    # Step 1: Create Emily's model profile
    if create_emily_profile():
        print("✅ Emily's profile created successfully")
    else:
        print("❌ Failed to create Emily's profile")
        return
    
    # Step 2: Import Emily's scripts
    if import_emily_scripts():
        print("✅ Emily's scripts imported successfully")
    else:
        print("❌ Failed to import Emily's scripts")
        return
    
    # Step 3: Create content templates
    create_emily_content_templates()
    
    # Step 4: Show stats
    stats = hierarchy_manager.get_data_stats()
    print("\n📊 Final Stats:")
    print(f"Model Profiles: {stats['model_profiles']}")
    print(f"Content Templates: {stats['content_templates']}")
    print(f"Hierarchy Settings: {stats['hierarchy_settings']}")
    
    print("\n🎉 Emily's data import complete! Ready to test the new system.")

if __name__ == "__main__":
    main()
