"""
AI Script Studio - Core Package

A powerful AI-powered script generation platform for creating engaging social media content
with advanced RAG (Retrieval-Augmented Generation) capabilities.
"""

__version__ = "1.0.0"
__author__ = "Kreemy29"
__email__ = "your.email@example.com"

# Core modules
from .models import Script, ModelProfile, Feedback
from .db import get_session, create_tables
from .rag_integration import generate_scripts_rag, generate_scripts_fast
from .rag_retrieval import RAGRetriever
from .data_hierarchy import DataHierarchyManager
from .deepseek_client import DeepSeekClient
from .auto_scorer import AutoScorer
from .bandit_learner import PolicyLearner
from .compliance import ComplianceChecker
from .dataset_manager import DatasetManager

__all__ = [
    "Script",
    "ModelProfile", 
    "Feedback",
    "get_session",
    "create_tables",
    "generate_scripts_rag",
    "generate_scripts_fast",
    "RAGRetriever",
    "DataHierarchyManager",
    "DeepSeekClient",
    "AutoScorer",
    "PolicyLearner",
    "ComplianceChecker",
    "DatasetManager",
]
