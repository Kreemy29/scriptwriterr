# db.py
import os, json, random
from contextlib import contextmanager
from typing import List, Iterable, Tuple, Optional
from sqlmodel import SQLModel, create_engine, Session, select, delete
from datetime import datetime

# ---- Configure DB ----
# For cloud deployment, ensure database persists in the correct location
DB_URL = os.environ.get("DB_URL", "sqlite:///studio.db")

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
    SQLModel.metadata.create_all(engine)

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
def extract_snippets_from_script(s: Script, max_lines: int = 3) -> List[str]:
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
    
    # Filter out garbage snippets (too short, metadata fragments, etc.)
    clean_snippets = []
    for sn in snippets:
        if (len(sn.strip()) > 15 and 
            len(sn.strip()) < 200 and 
            not any(x in sn.lower() for x in ["brand fit", "tl;dr", "meta", "accessibility", "quick text beats", "beat (00:00"]) and
            not sn.strip().startswith(";") and
            not sn.strip().startswith(":")):
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
    """Provide high-quality fallback references when database refs are poor"""
    fallback_refs = {
        "skit": [
            "POV: When he says he's good with his hands but you're about to test his skills",
            "Shot of feet dangling in pool, toes pointed, gently swirling water", 
            "Quick cut to sunscreen bottle being squeezed with excessive force",
            "Close-up on pool floatie with 'Queen' text partially deflated",
            "When the 'deep end' of his skills turns out to be three feet max",
            "Comment 'POOL' if you'd test these waters",
            "Tag your summer fling (and lifeguard)",
            "Save for your next poolside mood"
        ],
        "thirst-trap": [
            "POV: When you catch him staring but he thinks you don't notice",
            "Shot of slow hair flip with knowing smile",
            "Quick cut to adjusting jewelry while maintaining eye contact", 
            "Close-up on lip bite with raised eyebrow",
            "When the confidence is higher than your standards",
            "Comment 'NOTICED' if you've been there",
            "Tag someone who needs to work on their subtlety",
            "Save for your next confidence boost"
        ],
        "reaction-prank": [
            "POV: When you prank him but his reaction is better than expected",
            "Shot of him jumping back with exaggerated surprise",
            "Quick cut to him trying to play it cool but failing",
            "Close-up on his face going from shock to laughter",
            "When the prank backfires in the best way possible",
            "Comment 'PRANKED' if you've been there",
            "Tag your favorite prank victim",
            "Save for your next harmless chaos"
        ]
    }
    
    return fallback_refs.get(content_type, fallback_refs["skit"])
