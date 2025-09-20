from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from sqlalchemy import MetaData
from sqlalchemy.orm import clear_mappers

# Clear any existing metadata and mappers to prevent table redefinition errors
try:
    clear_mappers()
    metadata = MetaData()
    metadata.clear()
except:
    pass

class Script(SQLModel, table=True, extend_existing=True):
    __tablename__ = "script"
    __table_args__ = {'extend_existing': True}
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

class Revision(SQLModel, table=True, extend_existing=True):
    __tablename__ = "revision"
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    script_id: int = Field(index=True)
    label: str
    field: str
    before: str
    after: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# NEW: store every rating event so you keep history
class Rating(SQLModel, table=True, extend_existing=True):
    __tablename__ = "rating"
    __table_args__ = {'extend_existing': True}
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
class Embedding(SQLModel, table=True, extend_existing=True):
    __tablename__ = "embedding"
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    script_id: int = Field(index=True)
    part: str = Field(index=True)  # 'full', 'hook', 'beats', 'caption'
    vector: List[float] = Field(sa_column=Column(JSON))
    meta: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AutoScore(SQLModel, table=True, extend_existing=True):
    __tablename__ = "autoscore"
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    script_id: int = Field(index=True)
    overall: float
    hook: float
    originality: float
    style_fit: float
    safety: float
    authenticity: float  # Anti-cringe score
    confidence: float = 0.8  # LLM judge confidence
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PolicyWeights(SQLModel, table=True, extend_existing=True):
    __tablename__ = "policyweights"
    __table_args__ = {'extend_existing': True}
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

class StyleCard(SQLModel, table=True, extend_existing=True):
    __tablename__ = "stylecard"
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    persona: str = Field(index=True)
    content_type: str = Field(index=True)
    exemplar_hooks: List[str] = Field(sa_column=Column(JSON))
    exemplar_beats: List[str] = Field(sa_column=Column(JSON))
    exemplar_captions: List[str] = Field(sa_column=Column(JSON))
    negative_patterns: List[str] = Field(sa_column=Column(JSON))
    constraints: dict = Field(sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# NEW: Data Hierarchy Models
class ModelProfile(SQLModel, table=True, extend_existing=True):
    """Primary model data - specific creators like Marcie, Mia, Emily"""
    __tablename__ = "modelprofile"
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str = Field(index=True, unique=True)  # "Marcie", "Mia", "Emily"
    niche: str  # "Girl-next-door", "Bratty tease", etc.
    brand_description: str
    instagram_handle: Optional[str] = None
    content_style: str  # Description of their content style
    voice_tone: str  # How they speak/talk
    visual_style: str  # How they look/dress
    target_audience: str
    content_themes: List[str] = Field(sa_column=Column(JSON))  # ["fitness", "lifestyle", "comedy"]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContentTemplate(SQLModel, table=True, extend_existing=True):
    """Secondary general content templates and examples"""
    __tablename__ = "contenttemplate"
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    template_name: str = Field(index=True)
    content_type: str = Field(index=True)
    niche: str = Field(index=True)
    template_data: dict = Field(sa_column=Column(JSON))  # Full template structure
    usage_count: int = 0
    success_rate: float = 0.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DataHierarchy(SQLModel, table=True, extend_existing=True):
    """Controls the data hierarchy and retrieval weights"""
    __tablename__ = "datahierarchy"
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    niche: str = Field(index=True)
    content_type: str = Field(index=True)
    # Primary data weights (model-specific)
    model_data_weight: float = 0.7  # 70% weight for model-specific data
    # Secondary data weights (general content)
    general_data_weight: float = 0.3  # 30% weight for general content
    # Retrieval settings
    max_model_examples: int = 8  # Max examples from model data
    max_general_examples: int = 4  # Max examples from general data
    is_active: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)