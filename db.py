# db.py
import os, json, random
from contextlib import contextmanager
from typing import List, Iterable, Tuple, Optional
from sqlmodel import SQLModel, create_engine, Session, select
from datetime import datetime

# ---- Configure DB ----
DB_URL = os.environ.get("DB_URL", "sqlite:///studio.db")
engine = create_engine(DB_URL, echo=False)

# ---- Models ----
from models import Script, Rating  # make sure Script has: is_reference: bool, plus the other fields

# ---- Init / Session ----
def init_db() -> None:
    SQLModel.metadata.create_all(engine)

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

    payload = dict(
        # core identity
        creator=row.get("model_name", "Unknown"),
        content_type=(row.get("video_type", "") or "talking_style").lower(),
        tone=tone,
        title=external_id or row.get("theme", "") or "Imported Script",
        hook=row.get("video_hook", ""),

        # structured fields
        beats=row.get("storyboard", []) or [],
        voiceover="",
        caption=caption,
        hashtags=row.get("hashtags", []) or [],
        cta="",

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
        return []

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
    # dedupe again and cap ~8 lines
    seen, out = set(), []
    for sn in snippets:
        if sn not in seen:
            out.append(sn); seen.add(sn)
    return out[:8]
