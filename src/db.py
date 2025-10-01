# db.py
import os, json, random
from contextlib import contextmanager
from typing import List, Iterable, Tuple, Optional
from sqlmodel import SQLModel, create_engine, Session, select, delete
from datetime import datetime

# ---- Configure DB ----
# For cloud deployment, use in-memory database to avoid file system issues
import streamlit as st

# Check if running on Streamlit Cloud (more accurate detection)
if os.environ.get('STREAMLIT_CLOUD') or (hasattr(st, 'secrets') and hasattr(st.secrets, '_file_paths')):
    # Use in-memory database for Streamlit Cloud
    DB_URL = "sqlite:///:memory:"
    print("Using in-memory database for Streamlit Cloud deployment")
else:
    # Use file-based database for local development
    DB_URL = os.environ.get("DB_URL", "sqlite:///studio.db")
    print(f"Using database: {DB_URL}")

# Cloud deployment optimizations
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,  # Verify connections before use
    "pool_recycle": 300,    # Recycle connections every 5 minutes
}

# SQLite-specific optimizations for cloud deployment
if DB_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {
            "check_same_thread": False,  # Allow multi-threading
            "timeout": 20,               # 20 second timeout
        }
    })

engine = create_engine(DB_URL, **engine_kwargs)

# ---- Models ----
from models import Script, Rating  # make sure Script has: is_reference: bool, plus the other fields

# ---- Init / Session ----
def init_db() -> None:
    """Initialize database"""
    try:
        SQLModel.metadata.create_all(engine)
        print("Database initialized successfully")
        
        # For in-memory database (Streamlit Cloud), add some sample data
        if DB_URL == "sqlite:///:memory:":
            _add_sample_data()
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise e  # Re-raise the error so the app can handle it

def _add_sample_data():
    """Add sample data for in-memory database"""
    try:
        from models import Script
        with get_session() as session:
            # Check if we already have data
            existing = session.exec(select(Script)).first()
            if existing:
                return  # Data already exists
                
            # Add a few sample scripts for reference
            sample_scripts = [
                Script(
                    title="Sample Workout Tease",
                    hook="Watch my ass bounce during this 'workout'",
                    beats=["Stretching in tight leggings", "Squats facing away from camera", "Wink at camera"],
                    voiceover="",
                    caption="Just a casual workout session 😉",
                    hashtags=["#workout", "#fitness", "#tease"],
                    cta="Follow for more workouts",
                    creator="Sample",
                    content_type="thirst-trap",
                    persona="confident",
                    is_reference=True
                )
            ]
            
            for script in sample_scripts:
                session.add(script)
            session.commit()
            print("Sample data added successfully")
    except Exception as e:
        print(f"Error adding sample data: {e}")

def clear_all_data() -> None:
    """Clear all data from the database"""
    from models import Script, Embedding, AutoScore, PolicyWeights
    with get_session() as ses:
        # Clear all tables
        ses.exec(delete(Script))
        ses.exec(delete(Embedding))
        ses.exec(delete(AutoScore))
        ses.exec(delete(PolicyWeights))
        ses.commit()

@contextmanager
def get_session():
    with Session(engine) as ses:
        yield ses

# ---- Helpers for import ----

def _payload_from_jsonl_row(row: dict) -> Tuple[dict, str, str]:
    """
    Map a JSONL row (the file I generated for you) into Script columns.
    Returns (payload, dedupe_key_title, dedupe_key_creator).
    You can also add 'external_id' to Script model and dedupe on that.
    """
    # Prefer using the JSON 'id' as an external identifier:
    external_id = row.get("id", "")

    # Tone could be an array; flatten for now
    tone = ", ".join(row.get("tonality", [])) or "playful"

    # Compact caption: use caption options line as a quick reference
    caption = " | ".join(row.get("caption_options", []))[:180]

    # Create unique title by combining id with concept or theme
    base_title = external_id or row.get("theme", "") or "Imported Script"
    concept = row.get("concept", "")
    if concept:
        # Use first part of concept as unique identifier
        concept_words = concept.split()[:3]  # First 3 words
        unique_title = f"{base_title}-{'-'.join(concept_words)}"
    else:
        unique_title = base_title

    # Extract actual script content from the rich fields
    # Hook: look for hook options in the content
    hook = ""
    setting_content = row.get("setting", [])
    if setting_content:
        # Look for hook-like content - prefer shorter, punchier content
        for item in setting_content:
            if "POV:" in item and len(item) < 150:
                # Extract just the hook part
                if "POV:" in item:
                    hook_part = item.split("POV:")[1].split(".")[0].strip()
                    if hook_part and len(hook_part) < 100:
                        hook = f"POV: {hook_part}"
                        break
    
    # Beats: extract clean, actionable script beats
    beats = []
    for field_name in ["setting", "wardrobe", "list_of_shots", "camera_direction"]:
        field_content = row.get(field_name, [])
        if field_content:
            for item in field_content:
                if item.strip():
                    # Look for time-based beats (00:00-00:02 format)
                    if "00:" in item and len(item) < 200:
                        beats.append(item.strip())
                    # Look for short, actionable content
                    elif len(item.strip()) > 20 and len(item.strip()) < 150 and not any(x in item.lower() for x in ["brand fit", "tl;dr", "meta", "accessibility"]):
                        beats.append(item.strip())
    
    # Voiceover: look for audio/voiceover content
    voiceover = ""
    for field_name in ["setting", "wardrobe"]:
        field_content = row.get(field_name, [])
        if field_content:
            for item in field_content:
                if "trending vo:" in item.lower() or "audio" in item.lower():
                    # Extract the actual audio text
                    if "trending vo:" in item.lower():
                        vo_part = item.lower().split("trending vo:")[1].split(".")[0].strip()
                        if vo_part and len(vo_part) < 200:
                            voiceover = vo_part
                            break
    
    # CTA: look for CTA content
    cta = ""
    for field_name in ["setting", "wardrobe"]:
        field_content = row.get(field_name, [])
        if field_content:
            for item in field_content:
                if "comment" in item.lower() and len(item) < 100:
                    cta = item.strip()
                    break

    payload = dict(
        # core identity
        creator=row.get("model_name", "Unknown"),
        content_type=(row.get("video_type", "") or "talking_style").lower(),
        tone=tone,
        title=unique_title,
        hook=hook,

        # structured fields
        beats=beats[:5],  # Limit to 5 beats to avoid too much content
        voiceover=voiceover,
        caption=caption,
        hashtags=row.get("hashtags", []) or [],
        cta=cta,

        # video production fields (from rich original format)
        date_iso=row.get("date_iso"),
        video_length_s=row.get("video_length_s"),
        cuts=row.get("cuts"),
        lighting=row.get("lighting", []) or [],
        concept=row.get("concept"),
        retention_strategy=row.get("retention_strategy"),
        key_shots=row.get("key_shots", []) or [],
        text_overlay_lines=row.get("text_overlay_lines", []) or [],
        setting=row.get("setting", []) or [],
        wardrobe=row.get("wardrobe", []) or [],
        equipment=row.get("equipment", []) or [],
        list_of_shots=row.get("list_of_shots", []) or [],
        camera_direction=row.get("camera_direction", []) or [],
        risk_level=row.get("risk_level"),

        # flags
        source="import",
        is_reference=True,          # mark imported examples as references
        compliance="pass",          # we'll score again after save if you want
    )
    return payload, payload["title"], payload["creator"]

def _score_and_update_compliance(s: Script) -> None:
    """Optional: score compliance using your simple rule-checker."""
    try:
        from compliance import blob_from, score_script
        lvl, _ = score_script(blob_from(s.dict()))
        s.compliance = lvl
    except Exception:
        # If no compliance module or error, keep default
        pass

def _iter_jsonl(path: str) -> Iterable[dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

# ---- Public: Importer ----
def import_jsonl(path: str) -> int:
    """
    Import (upsert) scripts from a JSONL file produced earlier.
    Dedupe by (creator, title). Returns count of upserted rows.
    """
    init_db()
    count = 0
    with get_session() as ses:
        for row in _iter_jsonl(path):
            payload, key_title, key_creator = _payload_from_jsonl_row(row)

            existing = ses.exec(
                select(Script).where(
                    Script.title == key_title,
                    Script.creator == key_creator
                )
            ).first()

            if existing:
                # Update all fields
                for k, v in payload.items():
                    setattr(existing, k, v)
                _score_and_update_compliance(existing)
                existing.updated_at = datetime.utcnow()
                ses.add(existing)
            else:
                obj = Script(**payload)
                _score_and_update_compliance(obj)
                ses.add(obj)

            count += 1
        ses.commit()
    return count

# ---- Ratings API ----
def add_rating(script_id: int,
               overall: float,
               hook: Optional[float] = None,
               originality: Optional[float] = None,
               style_fit: Optional[float] = None,
               safety: Optional[float] = None,
               notes: Optional[str] = None,
               rater: str = "human") -> None:
    with get_session() as ses:
        # store rating event
        ses.add(Rating(
            script_id=script_id, overall=overall, hook=hook,
            originality=originality, style_fit=style_fit, safety=safety,
            notes=notes, rater=rater
        ))
        ses.commit()
        # recompute cached aggregates on Script
        _recompute_script_aggregates(ses, script_id)
        ses.commit()

def _recompute_script_aggregates(ses: Session, script_id: int) -> None:
    rows = list(ses.exec(select(Rating).where(Rating.script_id == script_id)))
    if not rows:
        return
    def avg(field): 
        vals = [getattr(r, field) for r in rows if getattr(r, field) is not None]
        return round(sum(vals)/len(vals), 3) if vals else None
    s: Script = ses.get(Script, script_id)
    s.score_overall = avg("overall")
    s.score_hook = avg("hook")
    s.score_originality = avg("originality")
    s.score_style_fit = avg("style_fit")
    s.score_safety = avg("safety")
    s.ratings_count = len(rows)
    s.updated_at = datetime.utcnow()
    ses.add(s)

# ---- Public: Reference retrieval for generation ----
def extract_snippets_from_script(s: Script, max_lines: int = 4) -> List[str]:
    items: List[str] = []
    
    # Prioritize hook content (most important)
    if s.hook and len(s.hook.strip()) > 10:
        items.append(s.hook.strip())
    
    # Add video_hook if different from hook
    if hasattr(s, 'video_hook') and s.video_hook and s.video_hook != s.hook:
        if len(s.video_hook.strip()) > 10:
            items.append(s.video_hook.strip())
    
    # Add concept content (THIS WAS MISSING!)
    if hasattr(s, 'concept') and s.concept and len(s.concept.strip()) > 20:
        concept = s.concept.strip()
        # Clean up concept content
        if concept.lower().startswith('meta'):
            concept = concept[4:].strip()  # Remove "Meta" prefix
        items.append(concept[:200])  # Cap at 200 chars
    
    # Add best beats (filter out technical beats more aggressively)
    if s.beats:
        good_beats = []
        for beat in s.beats[:4]:  # Check first 4 beats
            beat = beat.strip()
            if (len(beat) > 20 and 
                not beat.lower().startswith(('shot of', 'cut to', 'close-up', 'wide shot', '; quick', 'beat (')) and
                not any(x in beat.lower() for x in ['00:', 'camera', 'lighting', 'audio', 'trending vo:', 'text overlay:'])):
                good_beats.append(beat)
        items.extend(good_beats[:2])  # Take best 2 beats
    
    # Add caption if it's substantial
    if s.caption and len(s.caption.strip()) > 20:
        items.append(s.caption.strip()[:150])
    
    # Add retention_strategy if available (good for variety)
    if hasattr(s, 'retention_strategy') and s.retention_strategy and len(s.retention_strategy.strip()) > 30:
        items.append(s.retention_strategy.strip()[:150])
    
    # Add voiceover content if meaningful (handle Unicode issues)
    if s.voiceover and len(s.voiceover.strip()) > 20:
        try:
            voiceover = s.voiceover.strip()[:150]
            # Clean up common Unicode issues
            voiceover = voiceover.replace('�', "'")
            items.append(voiceover)
        except:
            pass  # Skip if Unicode issues
    
    # If we don't have enough content, create snippets from title
    if len(items) < 2 and s.title:
        title = s.title.replace('-', ' ').replace('_', ' ')
        # Remove creator prefix
        for prefix in ['emily-brief-', 'marcie-brief-', 'mia-brief-', 'anya-brief-']:
            if title.lower().startswith(prefix):
                title = title[len(prefix):]
                break
        
        if len(title) > 10:
            # Create content-style snippets from titles
            if 'pov' in title.lower():
                items.append(f"POV: {title.replace('pov', '').replace('POV', '').strip()}")
            elif any(word in title.lower() for word in ['rating', 'explaining', 'trying']):
                items.append(f"{title.strip()}")
            else:
                items.append(f"Content concept: {title.strip()}")
    
    # Dedupe while preserving order
    seen, uniq = set(), []
    for it in items:
        if it and it not in seen and len(it.strip()) > 15:
            uniq.append(it); seen.add(it)
    
    return uniq[:max_lines]

def get_library_refs(creator: str, content_type: str, k: int = 6) -> List[str]:
    with get_session() as ses:
        rows = list(ses.exec(
            select(Script)
            .where(
                Script.creator == creator,
                Script.content_type == content_type,
                Script.is_reference == True,
                Script.compliance != "fail"
            )
            .order_by(Script.created_at.desc())
        ))[:k]

    snippets: List[str] = []
    for r in rows:
        snippets.extend(extract_snippets_from_script(r))
    # final dedupe
    seen, uniq = set(), []
    for s in snippets:
        if s not in seen:
            uniq.append(s); seen.add(s)
    return uniq[:8]

# ---- HYBRID reference retrieval ----
def get_hybrid_refs(creator: str, content_type: str, k: int = 6,
                    top_n: int = 3, explore_n: int = 2, newest_n: int = 1) -> List[str]:
    """
    Mix of:
      - top_n best scored references (exploit)
      - explore_n random references (explore)
      - newest_n most recent references (freshness)
    Returns flattened snippet list (cap ~8 to keep prompt lean).
    """
    import random
    import time
    
    with get_session() as ses:
        all_refs = list(ses.exec(
            select(Script).where(
                Script.creator == creator,
                Script.content_type == content_type,
                Script.is_reference == True,
                Script.compliance != "fail"
            )
        ))

    if not all_refs:
        return _get_fallback_refs(content_type)

    # sort by score_overall (fallback to 0) and pick top_n
    scored = sorted(all_refs, key=lambda s: (s.score_overall or 0.0), reverse=True)
    best = scored[:top_n]

    # newest by created_at
    newest = sorted(all_refs, key=lambda s: s.created_at, reverse=True)[:newest_n]

    # explore = random sample from the remainder
    remainder = [r for r in all_refs if r not in best and r not in newest]
    explore = random.sample(remainder, min(explore_n, len(remainder))) if remainder else []

    # merge (preserve order, dedupe)
    chosen_scripts = []
    seen_ids = set()
    for bucket in (best, explore, newest):
        for s in bucket:
            if s.id not in seen_ids:
                chosen_scripts.append(s)
                seen_ids.add(s.id)

    # cut to k scripts
    chosen_scripts = chosen_scripts[:k]

    # flatten snippets and cap to keep prompt compact
    snippets: List[str] = []
    for s in chosen_scripts:
        snippets.extend(extract_snippets_from_script(s))
    
    # Filter out garbage snippets and prioritize quality content
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
            # Accept hook-like content or any substantial content
            ("pov:" in sn.lower() or 
             "when " in sn.lower() or 
             "me " in sn.lower() or
             "rating " in sn.lower() or
             "explaining " in sn.lower() or
             "content concept:" in sn.lower() or
             "caption" in sn.lower() or
             "fail" in sn.lower() or
             "reveal" in sn.lower() or
             "comedy" in sn.lower() or
             "trending" in sn.lower() or
             len(sn.strip()) > 25)):  # Or longer content (reduced from 30)
            clean_snippets.append(sn.strip())
    
    # If we don't have enough clean snippets, use fallback
    if len(clean_snippets) < 3:
        return _get_fallback_refs(content_type)
    
    # dedupe and cap ~8 lines
    seen, out = set(), []
    for sn in clean_snippets:
        if sn not in seen:
            out.append(sn); seen.add(sn)
    
    # Shuffle the snippets to add more diversity in the order they appear
    # Use timestamp-based seed for more variation
    random.seed(int(time.time() * 1000) % 10000)
    random.shuffle(out)
    
    return out[:8]

def _get_fallback_refs(content_type: str) -> List[str]:
    """Provide dark humor and satirical fallback references with college-level wit"""
    fallback_refs = {
        "skit": [
            "POV: You're trying to be productive but then remember we live in a capitalist hellscape",
            "Rating my life choices by how much they disappoint my parents - spoiler: it's all of them",
            "When you realize your 'self-care' routine is just avoiding responsibilities with extra steps",
            "My morning routine but make it existential dread and caffeine dependency",
            "Starting to explain adulting tips but it turns into a masterclass in barely functioning",
            "When someone asks about my five-year plan and I can barely plan five minutes ahead",
            "POV: You're trying to budget but then remember inflation exists and cry instead",
            "Rating my cooking skills but it's really just rating my ability to not burn down the apartment",
            "My skincare routine but every step reminds me that I'm aging and time is meaningless",
            "POV: You're at a family gathering explaining why you're still single and broke",
            "When I pretend to have my life together but really I'm just winging it like everyone else",
            "My cleaning routine but it's really just moving mess from one room to another",
            "POV: You're job hunting but every posting wants 5 years experience for an 'entry-level' position",
            "Rating my social skills by how awkward I make normal conversations",
            "My bedtime routine but it's really just scrolling until I hate myself",
            "POV: You're trying to be healthy but then remember vegetables are expensive",
            "When I'm 'meal prepping' but it's really just eating cereal for the third day straight",
            "My workout routine that's really just walking to the fridge and calling it cardio",
            "POV: You're trying to save money but then remember you need to eat to survive",
            "Rating my life decisions by how much they would horrify my past self"
        ],
        "thirst-trap": [
            "POV: You start confident but then slowly realize exactly what you're doing to them - and it turns you on even more",
            "Rating my outfits by how hard they make you, starting innocent then escalating to the ones that make you lose control",
            "When you think you're taking a 'casual' selfie but then catch yourself being absolutely sinful in the mirror", 
            "My mirror knows all my dirty secrets and so do you now - watch as I slowly reveal why that's so fucking dangerous",
            "The art of looking effortless while being absolutely intentional - a masterclass in making men desperate for you",
            "When your curves start doing all the talking and making men beg for more - and you love every second of it",
            "Comment 'OBSESSED' if you've been staring and can't look away from this slow seduction",
            "Save this for your next confidence boost - but warning: it might make you too confident and too fucking irresistible"
        ],
        "talking-style": [
            "Let me explain why this trend is actually a symptom of late-stage capitalism",
            "The psychology behind why we're all pretending to be okay - spoiler: we're not",
            "Rating my coping mechanisms by how healthy they are - spoiler: they're all terrible", 
            "Why I'm the reason your screen time is embarrassingly high - and why that's concerning",
            "The science of procrastination: a masterclass in avoiding adult responsibilities",
            "Breaking down why our generation is obsessed with documenting everything instead of living it",
            "Let me tell you about the time I realized I'm becoming my parents and had an existential crisis",
            "Here's why I dress like I have my life together when I absolutely do not",
            "The difference between self-care and self-destruction - and why I can't tell them apart anymore",
            "Why I love making small talk awkward - and the psychological reasons behind it",
            "Let me explain what I'm really thinking when I say 'I'm fine' - hint: it's not fine",
            "The art of pretending to be an adult - and why I'm failing spectacularly at it",
            "Here's what I notice about people that makes me lose faith in humanity",
            "Why social media is a dystopian nightmare - and why I can't stop scrolling",
            "Let me break down exactly how this app is destroying our attention spans",
            "The real reason I make these videos - and it's definitely concerning"
        ],
        "reaction-prank": [
            "POV: You try to act unaffected but your body language gives you away",
            "Rating men's reactions to my content by how obvious they are",
            "When you think you're being subtle but I notice everything", 
            "My favorite game: seeing how long you can maintain eye contact",
            "The moment you realize I'm doing this on purpose",
            "When your poker face fails and I catch you looking",
            "Comment 'GUILTY' if I caught you",
            "Tag someone who needs to work on their subtlety"
        ],
        "lifestyle": [
            "My self-care routine: skincare, yoga, and looking absolutely stunning",
            "Rating my daily activities by how much they'd interest you",
            "POV: Your idea of productivity is watching me be productive", 
            "My morning routine but make it seductive",
            "The art of looking good while doing absolutely nothing",
            "When your lifestyle is your brand and your brand is irresistible",
            "Comment what part of my routine you'd want to join",
            "Save this for motivation to upgrade your own routine"
        ]
    }
    
    return fallback_refs.get(content_type, fallback_refs["skit"])
