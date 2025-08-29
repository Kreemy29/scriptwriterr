from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

class Script(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creator: str
    content_type: str
    tone: str
    title: str
    hook: str
    beats: List[str] = Field(sa_column=Column(JSON))
    voiceover: str
    caption: str
    hashtags: List[str] = Field(sa_column=Column(JSON))
    cta: str
    compliance: str = "pass"   # pass | warn | fail
    source: str = "ai"         # ai | manual | import
    is_reference: bool = False  # mark imported examples as references
    
    # --- NEW: cached aggregates from ratings (all optional) ---
    score_overall: Optional[float] = None         # 1..5 (avg)
    score_hook: Optional[float] = None            # 1..5 (avg)
    score_originality: Optional[float] = None     # 1..5 (avg)
    score_style_fit: Optional[float] = None       # 1..5 (avg)
    score_safety: Optional[float] = None          # 1..5 (avg)
    ratings_count: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Revision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    script_id: int = Field(index=True)
    label: str
    field: str
    before: str
    after: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# NEW: store every rating event so you keep history
class Rating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    script_id: int = Field(index=True)
    rater: str = "human"   # optional: store user/email
    overall: float         # 1..5
    hook: Optional[float] = None
    originality: Optional[float] = None
    style_fit: Optional[float] = None
    safety: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
