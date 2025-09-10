# 🗃️ Dataset Import Guide

## Quick Start

I've created two scripts to help you replace your dataset:

### Option 1: Interactive Manager (Recommended)
```bash
python dataset_manager.py
```
This gives you a friendly menu to:
- See current database stats
- Clear all data with confirmation
- Import new data from JSONL files
- Do both in one go

### Option 2: Command Line Tool
```bash
# Clear all data and import new file
python clear_and_import_data.py --clear --import your_data.jsonl

# Or step by step:
python clear_and_import_data.py --clear
python clear_and_import_data.py --import your_data.jsonl
```

## Expected Data Format

Your JSONL file should contain objects like this:

```json
{
  "id": "unique_script_id",
  "model_name": "CreatorName",
  "video_type": "thirst-trap",
  "tonality": ["playful", "flirty"],
  "theme": "Script Title",
  "video_hook": "Opening hook line",
  "storyboard": ["Beat 1", "Beat 2", "Beat 3"],
  "caption_options": ["Caption option 1", "Caption option 2"],
  "hashtags": ["#fitness", "#motivation", "#lifestyle"]
}
```

## What Gets Imported

The system maps your data to these fields:
- `model_name` → `creator`
- `video_type` → `content_type`
- `tonality` → `tone` (joined with commas)
- `theme`/`id` → `title`
- `video_hook` → `hook`
- `storyboard` → `beats`
- `caption_options` → `caption` (joined with "|")
- `hashtags` → `hashtags`

All imported scripts are marked as `is_reference=True` so they'll be used for AI generation.

## Safety Notes

⚠️ **BACKUP FIRST**: The clear operation cannot be undone!

✅ **What's preserved**: Your app settings and configuration
❌ **What's deleted**: All scripts, ratings, and revision history

## After Import

1. Restart your Streamlit app: `streamlit run app.py`
2. The new scripts will appear in the analytics tab
3. They'll be used as references for AI generation
4. You can rate them to improve future AI outputs

Happy scripting! 🎬


