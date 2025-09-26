#!/usr/bin/env python3
"""
Dataset Export Script for AI Script Studio
Usage: python export_dataset.py [--output filename.jsonl] [--format jsonl|json] [--include-ratings]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add src to path to import our modules
sys.path.append('src')

from db import get_session, init_db
from models import Script, Rating, Revision
from sqlmodel import select, text

def script_to_export_dict(script: Script, include_ratings: bool = False) -> Dict[str, Any]:
    """Convert script to export-friendly dictionary"""
    
    # Base script data
    data = {
        "id": f"{script.creator.lower()}-{script.title.lower().replace(' ', '-')}",
        "model_name": script.creator,
        "video_type": script.content_type,
        "tonality": [t.strip() for t in script.tone.split(',')] if script.tone else [],
        "theme": script.title,
        "video_hook": script.hook,
        "storyboard": script.beats or [],
        "caption_options": [script.caption] if script.caption else [],
        "hashtags": script.hashtags or [],
        "voiceover": script.voiceover,
        "cta": script.cta,
        "compliance": script.compliance,
        "source": script.source,
        "is_reference": script.is_reference,
        "created_at": script.created_at.isoformat() if script.created_at else None,
        "updated_at": script.updated_at.isoformat() if script.updated_at else None,
        
        # Video production fields (from rich format)
        "date_iso": script.date_iso,
        "video_length_s": script.video_length_s,
        "cuts": script.cuts,
        "lighting": script.lighting or [],
        "concept": script.concept,
        "retention_strategy": script.retention_strategy,
        "key_shots": script.key_shots or [],
        "text_overlay_lines": script.text_overlay_lines or [],
        "setting": script.setting or [],
        "wardrobe": script.wardrobe or [],
        "equipment": script.equipment or [],
        "list_of_shots": script.list_of_shots or [],
        "camera_direction": script.camera_direction or [],
        "risk_level": script.risk_level,
    }
    
    # Add scoring data if available
    if script.score_overall is not None:
        data["scores"] = {
            "overall": script.score_overall,
            "hook": script.score_hook,
            "originality": script.score_originality,
            "style_fit": script.score_style_fit,
            "safety": script.score_safety,
            "ratings_count": script.ratings_count
        }
    
    # Add ratings if requested
    if include_ratings:
        with get_session() as ses:
            ratings = list(ses.exec(
                select(Rating).where(Rating.script_id == script.id)
            ))
            if ratings:
                data["ratings"] = [
                    {
                        "overall": r.overall,
                        "hook": r.hook,
                        "originality": r.originality,
                        "style_fit": r.style_fit,
                        "safety": r.safety,
                        "notes": r.notes,
                        "rater": r.rater,
                        "created_at": r.created_at.isoformat() if r.created_at else None
                    }
                    for r in ratings
                ]
    
    return data

def export_to_jsonl(output_file: str, include_ratings: bool = False) -> int:
    """Export all scripts to JSONL format"""
    print(f"📤 Exporting dataset to {output_file}...")
    
    init_db()
    count = 0
    
    with get_session() as ses:
        # Get all scripts ordered by creation date
        scripts = list(ses.exec(
            select(Script).order_by(Script.created_at.asc())
        ))
        
        if not scripts:
            print("❌ No scripts found in database")
            return 0
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for script in scripts:
                export_data = script_to_export_dict(script, include_ratings)
                f.write(json.dumps(export_data, ensure_ascii=False) + '\n')
                count += 1
        
        print(f"✅ Successfully exported {count} scripts")
        
        # Show summary by creator
        creators = {}
        for script in scripts:
            creator = script.creator
            creators[creator] = creators.get(creator, 0) + 1
        
        print("\n📊 Export Summary:")
        for creator, script_count in creators.items():
            print(f"   {creator}: {script_count} scripts")
    
    return count

def export_to_json(output_file: str, include_ratings: bool = False) -> int:
    """Export all scripts to JSON format"""
    print(f"📤 Exporting dataset to {output_file}...")
    
    init_db()
    
    with get_session() as ses:
        # Get all scripts ordered by creation date
        scripts = list(ses.exec(
            select(Script).order_by(Script.created_at.asc())
        ))
        
        if not scripts:
            print("❌ No scripts found in database")
            return 0
        
        # Convert all scripts to export format
        export_data = {
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_scripts": len(scripts),
                "include_ratings": include_ratings
            },
            "scripts": []
        }
        
        for script in scripts:
            script_data = script_to_export_dict(script, include_ratings)
            export_data["scripts"].append(script_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully exported {len(scripts)} scripts")
        
        # Show summary by creator
        creators = {}
        for script in scripts:
            creator = script.creator
            creators[creator] = creators.get(creator, 0) + 1
        
        print("\n📊 Export Summary:")
        for creator, script_count in creators.items():
            print(f"   {creator}: {script_count} scripts")
    
    return len(scripts)

def show_database_stats():
    """Show current database statistics"""
    print("📊 Current Database Statistics:")
    print("=" * 40)
    
    init_db()
    
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
        for creator, count in creators.items():
            print(f"   {creator}: {count}")
        
        # Scripts by content type
        content_types = {}
        for script in ses.exec(select(Script)):
            ctype = script.content_type
            content_types[ctype] = content_types.get(ctype, 0) + 1
        
        print(f"\nScripts by Content Type:")
        for ctype, count in content_types.items():
            print(f"   {ctype}: {count}")
        
        # Reference scripts
        ref_scripts = len(list(ses.exec(select(Script).where(Script.is_reference == True))))
        print(f"\nReference Scripts: {ref_scripts}")
        
        # Scripts with ratings
        rated_scripts = len(list(ses.exec(select(Rating.script_id).distinct())))
        print(f"Scripts with Ratings: {rated_scripts}")

def main():
    parser = argparse.ArgumentParser(description="Export AI Script Studio dataset")
    parser.add_argument("--output", "-o", default="exported_dataset.jsonl", 
                       help="Output filename (default: exported_dataset.jsonl)")
    parser.add_argument("--format", "-f", choices=["jsonl", "json"], default="jsonl",
                       help="Export format (default: jsonl)")
    parser.add_argument("--include-ratings", action="store_true",
                       help="Include rating data in export")
    parser.add_argument("--stats", action="store_true",
                       help="Show database statistics only")
    
    args = parser.parse_args()
    
    if args.stats:
        show_database_stats()
        return
    
    # Determine output file extension if not provided
    if not args.output.endswith(('.jsonl', '.json')):
        if args.format == 'json':
            args.output += '.json'
        else:
            args.output += '.jsonl'
    
    # Export data
    if args.format == 'jsonl':
        count = export_to_jsonl(args.output, args.include_ratings)
    else:
        count = export_to_json(args.output, args.include_ratings)
    
    if count > 0:
        print(f"\n🎉 Export complete! File saved as: {args.output}")
        print(f"📁 File size: {os.path.getsize(args.output) / 1024:.1f} KB")
        
        if args.include_ratings:
            print("📊 Ratings included in export")
        else:
            print("💡 Use --include-ratings to include rating data")
    else:
        print("❌ No data exported")

if __name__ == "__main__":
    main()
