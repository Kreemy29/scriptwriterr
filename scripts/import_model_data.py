#!/usr/bin/env python3
"""
Import Model Data for AI Script Studio
Handles importing model-specific data and general content templates
"""

import json
import sys
from typing import Dict, List, Any
from data_hierarchy import hierarchy_manager
from db import get_session, import_jsonl
from models import Script

def import_model_profile_from_json(data: Dict[str, Any]) -> None:
    """Import a model profile from JSON data"""
    try:
        model = hierarchy_manager.add_model_profile(
            model_name=data['model_name'],
            niche=data['niche'],
            brand_description=data['brand_description'],
            instagram_handle=data.get('instagram_handle'),
            content_style=data.get('content_style', ''),
            voice_tone=data.get('voice_tone', ''),
            visual_style=data.get('visual_style', ''),
            target_audience=data.get('target_audience', ''),
            content_themes=data.get('content_themes', [])
        )
        print(f"✅ Added model profile: {model.model_name}")
    except Exception as e:
        print(f"❌ Failed to add model profile {data.get('model_name', 'Unknown')}: {e}")

def import_model_scripts_from_jsonl(file_path: str, model_name: str) -> int:
    """Import scripts for a specific model from JSONL file"""
    try:
        # Import scripts and mark them as references
        count = import_jsonl(file_path)
        
        # Update the scripts to be associated with the model
        with get_session() as session:
            from sqlmodel import select, update
            scripts = list(session.exec(select(Script).where(Script.creator == model_name)))
            for script in scripts:
                script.creator = model_name
                script.is_reference = True
            session.commit()
        
        print(f"✅ Imported {count} scripts for {model_name}")
        return count
    except Exception as e:
        print(f"❌ Failed to import scripts for {model_name}: {e}")
        return 0

def import_content_templates_from_json(data: List[Dict[str, Any]]) -> None:
    """Import content templates from JSON data"""
    for template_data in data:
        try:
            template = hierarchy_manager.add_content_template(
                template_name=template_data['template_name'],
                content_type=template_data['content_type'],
                niche=template_data['niche'],
                template_data=template_data['template_data']
            )
            print(f"✅ Added content template: {template.template_name}")
        except Exception as e:
            print(f"❌ Failed to add template {template_data.get('template_name', 'Unknown')}: {e}")

def create_sample_model_data():
    """Create sample model data for testing"""
    print("🎬 Creating sample model data...")
    
    # Sample model profiles
    models = [
        {
            "model_name": "Marcie",
            "niche": "Girl-next-door",
            "brand_description": "Authentic, relatable content creator with a natural, approachable style",
            "instagram_handle": "@marcie_official",
            "content_style": "Candid lifestyle content, fitness motivation, relatable moments",
            "voice_tone": "Warm, encouraging, authentic, slightly playful",
            "visual_style": "Natural makeup, casual outfits, home/gym settings",
            "target_audience": "Young women 18-28, fitness enthusiasts, lifestyle seekers",
            "content_themes": ["fitness", "lifestyle", "motivation", "authenticity"]
        },
        {
            "model_name": "Mia",
            "niche": "Bratty tease",
            "brand_description": "Playful, teasing content with a confident, sassy attitude",
            "instagram_handle": "@mia_tease",
            "content_style": "Trendy challenges, reaction videos, playful teasing content",
            "voice_tone": "Confident, sassy, playful, slightly demanding",
            "visual_style": "Trendy outfits, bold makeup, urban settings",
            "target_audience": "Young adults 18-25, trend followers, entertainment seekers",
            "content_themes": ["trends", "comedy", "reactions", "teasing"]
        },
        {
            "model_name": "Emily",
            "niche": "Innocent but suggestive",
            "brand_description": "Sweet, innocent appearance with subtle suggestive undertones",
            "instagram_handle": "@emily_sweet",
            "content_style": "Cute lifestyle content with subtle hints, ASMR-style videos",
            "voice_tone": "Soft, sweet, innocent, slightly suggestive",
            "visual_style": "Soft makeup, cute outfits, bedroom/home settings",
            "target_audience": "Young adults 18-26, ASMR fans, lifestyle enthusiasts",
            "content_themes": ["lifestyle", "asmr", "cute", "subtle"]
        }
    ]
    
    # Import model profiles
    for model in models:
        import_model_profile_from_json(model)
    
    # Sample content templates
    templates = [
        {
            "template_name": "Fitness Motivation",
            "content_type": "lifestyle",
            "niche": "Girl-next-door",
            "template_data": {
                "title": "Morning Motivation",
                "hook": "Starting your day right",
                "beats": ["Wake up routine", "Motivational message", "Workout prep"],
                "voiceover": "Good morning! Let's start this day with positive energy",
                "caption": "New day, new opportunities 💪 #motivation #fitness",
                "hashtags": ["#motivation", "#fitness", "#lifestyle"],
                "cta": "What's your morning routine?"
            }
        },
        {
            "template_name": "Trend Challenge",
            "content_type": "skit",
            "niche": "Bratty tease",
            "template_data": {
                "title": "Trending Challenge",
                "hook": "Trying this viral trend",
                "beats": ["Setup", "Attempt", "Reaction", "Result"],
                "voiceover": "Okay, let's see if I can actually do this...",
                "caption": "This trend is harder than it looks 😅 #trending #challenge",
                "hashtags": ["#trending", "#challenge", "#viral"],
                "cta": "Try it yourself!"
            }
        }
    ]
    
    # Import content templates
    import_content_templates_from_json(templates)
    
    print("✅ Sample data created successfully!")

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python import_model_data.py sample          # Create sample data")
        print("  python import_model_data.py model <file>    # Import model profile from JSON")
        print("  python import_model_data.py scripts <file> <model_name>  # Import scripts for model")
        print("  python import_model_data.py templates <file>  # Import content templates")
        return
    
    command = sys.argv[1]
    
    if command == "sample":
        create_sample_model_data()
    
    elif command == "model" and len(sys.argv) >= 3:
        with open(sys.argv[2], 'r') as f:
            data = json.load(f)
        import_model_profile_from_json(data)
    
    elif command == "scripts" and len(sys.argv) >= 4:
        file_path = sys.argv[2]
        model_name = sys.argv[3]
        import_model_scripts_from_jsonl(file_path, model_name)
    
    elif command == "templates" and len(sys.argv) >= 3:
        with open(sys.argv[2], 'r') as f:
            data = json.load(f)
        import_content_templates_from_json(data)
    
    else:
        print("❌ Invalid command or missing arguments")

if __name__ == "__main__":
    main()
