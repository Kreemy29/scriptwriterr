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

# RAG Enhancement Models
class Embedding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    script_id: int = Field(index=True)
    part: str = Field(index=True)  # 'full', 'hook', 'beats', 'caption'
    vector: List[float] = Field(sa_column=Column(JSON))
    meta: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AutoScore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    script_id: int = Field(index=True)
    overall: float
    hook: float
    originality: float
    style_fit: float
    safety: float
    confidence: float = 0.8  # LLM judge confidence
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PolicyWeights(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    persona: str = Field(index=True)
    content_type: str = Field(index=True)
    # Retrieval weights
    semantic_weight: float = 0.45
    bm25_weight: float = 0.25
    quality_weight: float = 0.20
    freshness_weight: float = 0.10
    # Generation params
    temp_low: float = 0.4
    temp_mid: float = 0.7
    temp_high: float = 0.95
    # Performance tracking
    success_rate: float = 0.0
    total_generations: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class StyleCard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    persona: str = Field(index=True)
    content_type: str = Field(index=True)
    exemplar_hooks: List[str] = Field(sa_column=Column(JSON))
    exemplar_beats: List[str] = Field(sa_column=Column(JSON))
    exemplar_captions: List[str] = Field(sa_column=Column(JSON))
    negative_patterns: List[str] = Field(sa_column=Column(JSON))
    constraints: dict = Field(sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)