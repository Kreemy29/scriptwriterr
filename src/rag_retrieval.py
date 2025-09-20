"""
Enhanced RAG retrieval system for AI Script Studio
Extends the existing hybrid reference system with semantic search and policy learning
"""

import numpy as np
import math
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from datetime import datetime, timedelta

from models import Script, Embedding, AutoScore, PolicyWeights, StyleCard
from db import get_session

class RAGRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with lightweight but effective embedding model"""
        self.encoder = SentenceTransformer(model_name)
        self.tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def generate_embeddings(self, script: Script) -> List[Embedding]:
        """Generate embeddings for different parts of a script"""
        parts = {
            'full': self._get_full_text(script),
            'hook': script.hook or '',
            'beats': ' '.join(script.beats or []),
            'caption': script.caption or ''
        }
        
        embeddings = []
        for part, text in parts.items():
            if text.strip():  # Only embed non-empty parts
                vector = self.encoder.encode(text).tolist()
                meta = {
                    'creator': script.creator,
                    'content_type': script.content_type,
                    'tone': script.tone,
                    'quality_score': script.score_overall or 0.0,
                    'compliance': script.compliance
                }
                embeddings.append(Embedding(
                    script_id=script.id,
                    part=part,
                    vector=vector,
                    meta=meta
                ))
        return embeddings
    
    def _get_full_text(self, script: Script) -> str:
        """Combine all script parts into full text"""
        parts = [
            script.title,
            script.hook or '',
            ' '.join(script.beats or []),
            script.voiceover or '',
            script.caption or '',
            script.cta or ''
        ]
        return ' '.join(p for p in parts if p.strip())
    
    def hybrid_retrieve(self, 
                       query_text: str,
                       persona: str,
                       content_type: str,
                       k: int = 6,
                       global_quality_mean: float = 4.2,
                       shrinkage_alpha: float = 10.0,
                       freshness_tau_days: float = 28.0) -> List[Dict]:
        """
        Production-grade hybrid retrieval with proper score normalization:
        - Semantic similarity (cosine normalized to [0,1])
        - BM25/TF-IDF similarity (min-max normalized per query)  
        - Quality scores (Bayesian shrinkage)
        - Freshness boost (exponential decay)
        - Policy-learned weights
        """
        
        # Get policy weights for this persona/content_type
        weights = self._get_policy_weights(persona, content_type)
        
        with get_session() as ses:
            # Get all relevant scripts
            scripts = list(ses.exec(
                select(Script).where(
                    Script.creator == persona,
                    Script.content_type == content_type,
                    Script.is_reference == True,
                    Script.compliance != "fail"
                )
            ))
            
            if not scripts:
                return []
            
            # Get embeddings for semantic similarity
            embeddings = list(ses.exec(
                select(Embedding).join(Script, Embedding.script_id == Script.id).where(
                    Embedding.part == 'full',
                    Script.creator == persona,
                    Script.content_type == content_type,
                    Script.is_reference == True,
                    Script.compliance != "fail"
                )
            ))
            
            # Pre-calculate all raw scores for normalization
            raw_scores = []
            query_embedding = self.encoder.encode(query_text)
            now = datetime.utcnow()
            
            for script in scripts:
                # Find matching embedding
                script_embedding = next(
                    (e for e in embeddings if e.script_id == script.id), 
                    None
                )
                
                # 1. Raw semantic similarity (cosine returns [-1,1])
                if script_embedding:
                    raw_cosine = cosine_similarity(
                        [query_embedding], 
                        [script_embedding.vector]
                    )[0][0]
                else:
                    raw_cosine = -1.0  # Worst case for missing embeddings
                
                # 2. Raw BM25/TF-IDF similarity
                script_text = self._get_full_text(script)
                raw_bm25 = self._calculate_tfidf_similarity(query_text, script_text)
                
                raw_scores.append({
                    'script': script,
                    'raw_cosine': raw_cosine,
                    'raw_bm25': raw_bm25
                })
            
            # Normalize BM25 scores (min-max normalization across this query's candidates)
            bm25_scores = [s['raw_bm25'] for s in raw_scores]
            min_bm25 = min(bm25_scores)
            max_bm25 = max(bm25_scores) 
            bm25_range = max_bm25 - min_bm25 + 1e-9  # Avoid division by zero
            
            # Calculate final normalized scores
            results = []
            
            for raw_score in raw_scores:
                script = raw_score['script']
                scores = {}
                
                # 1. Semantic similarity: normalize cosine [-1,1] → [0,1]
                scores['semantic'] = (raw_score['raw_cosine'] + 1.0) / 2.0
                
                # 2. BM25: min-max normalize within this query's candidate set
                scores['bm25'] = (raw_score['raw_bm25'] - min_bm25) / bm25_range
                
                # 3. Quality: Bayesian shrinkage toward global mean
                n_ratings = script.ratings_count or 0
                local_quality = script.score_overall or global_quality_mean
                
                # Shrinkage: blend local mean with global mean based on sample size
                shrunk_quality = (
                    (n_ratings / (n_ratings + shrinkage_alpha)) * local_quality +
                    (shrinkage_alpha / (n_ratings + shrinkage_alpha)) * global_quality_mean
                )
                
                # Normalize to [0,1] (assuming 1-5 rating scale)
                scores['quality'] = max(0.0, min(1.0, (shrunk_quality - 1) / 4))
                
                # 4. Freshness: exponential decay (smoother than linear)
                days_old = max(0, (now - script.created_at).days)
                scores['freshness'] = math.exp(-days_old / freshness_tau_days)
                
                # Combined score using policy weights
                combined_score = (
                    weights.semantic_weight * scores['semantic'] +
                    weights.bm25_weight * scores['bm25'] +
                    weights.quality_weight * scores['quality'] +
                    weights.freshness_weight * scores['freshness']
                )
                
                results.append({
                    'script': script,
                    'score': combined_score,
                    'component_scores': scores,
                    # Debug info
                    '_debug': {
                        'n_ratings': n_ratings,
                        'raw_quality': local_quality,
                        'shrunk_quality': shrunk_quality,
                        'days_old': days_old
                    }
                })
            
            # Sort by combined score and return top k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:k]
    
    def _calculate_tfidf_similarity(self, query: str, doc: str) -> float:
        """Calculate TF-IDF similarity between query and document"""
        try:
            tfidf_matrix = self.tfidf.fit_transform([query, doc])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except:
            return 0.0
    
    def _get_policy_weights(self, persona: str, content_type: str) -> PolicyWeights:
        """Get learned policy weights or create defaults"""
        with get_session() as ses:
            weights = ses.exec(
                select(PolicyWeights).where(
                    PolicyWeights.persona == persona,
                    PolicyWeights.content_type == content_type
                )
            ).first()
            
            if not weights:
                # Create default weights
                weights = PolicyWeights(
                    persona=persona,
                    content_type=content_type
                )
                ses.add(weights)
                ses.commit()
                ses.refresh(weights)
            
            return weights
    
    def build_dynamic_few_shot_pack(self, 
                                  persona: str,
                                  content_type: str,
                                  query_context: str = "") -> Dict:
        """Build dynamic few-shot examples pack optimized for this request"""
        
        # Get best references via hybrid retrieval
        references = self.hybrid_retrieve(
            query_text=query_context or f"{persona} {content_type}",
            persona=persona,
            content_type=content_type,
            k=6
        )
        
        if not references:
            return {"style_card": "", "examples": [], "constraints": {}}
        
        # Extract best examples by type
        best_hooks = []
        best_beats = []
        best_captions = []
        
        for ref in references[:4]:  # Use top 4 references
            script = ref['script']
            if script.hook and len(best_hooks) < 2:
                best_hooks.append(script.hook)
            if script.beats and len(best_beats) < 1:
                best_beats.extend(script.beats[:2])  # First 2 beats
            if script.caption and len(best_captions) < 1:
                best_captions.append(script.caption)
        
        # Get or create style card
        style_card = self._get_style_card(persona, content_type)
        
        return {
            "style_card": f"Persona: {persona} | Content: {content_type}",
            "best_hooks": best_hooks[:2],
            "best_beats": best_beats[:3],
            "best_captions": best_captions[:1],
            "constraints": {
                "max_length": "15-25 seconds",
                "compliance": "Instagram-safe",
                "tone": references[0]['script'].tone if references else "playful"
            },
            "negative_patterns": style_card.negative_patterns if style_card else []
        }
    
    def _get_style_card(self, persona: str, content_type: str) -> Optional[StyleCard]:
        """Get existing style card or return None"""
        with get_session() as ses:
            return ses.exec(
                select(StyleCard).where(
                    StyleCard.persona == persona,
                    StyleCard.content_type == content_type
                )
            ).first()
    
    def detect_copying(self, 
                      generated_content: Dict, 
                      reference_texts: List[str],
                      similarity_threshold: float = 0.92) -> Dict:
        """
        Detect if generated content is too similar to reference material.
        Returns detection results with flagged content and similarity scores.
        
        Args:
            generated_content: Dict with keys like 'hook', 'caption', 'beats', etc.
            reference_texts: List of reference text snippets to compare against
            similarity_threshold: Cosine similarity threshold (0.92 recommended)
        
        Returns:
            Dict with detection results and recommendations
        """
        
        detection_results = {
            'is_copying': False,
            'flagged_fields': [],
            'max_similarity': 0.0,
            'rewrite_recommendations': []
        }
        
        if not reference_texts:
            return detection_results
        
        # Encode all reference texts
        reference_embeddings = self.encoder.encode(reference_texts)
        
        # Fields to check for copying
        fields_to_check = ['hook', 'caption', 'cta']
        
        for field in fields_to_check:
            if field in generated_content and generated_content[field]:
                generated_text = str(generated_content[field])
                
                # Skip very short texts (less than 10 characters)
                if len(generated_text.strip()) < 10:
                    continue
                
                # Encode generated text
                generated_embedding = self.encoder.encode([generated_text])
                
                # Calculate similarity to all reference texts
                similarities = cosine_similarity(generated_embedding, reference_embeddings)[0]
                max_sim = float(np.max(similarities))
                
                # Update overall max similarity
                detection_results['max_similarity'] = max(detection_results['max_similarity'], max_sim)
                
                # Check if similarity exceeds threshold
                if max_sim >= similarity_threshold:
                    detection_results['is_copying'] = True
                    detection_results['flagged_fields'].append({
                        'field': field,
                        'text': generated_text,
                        'similarity': max_sim,
                        'similar_reference': reference_texts[int(np.argmax(similarities))]
                    })
                    
                    # Generate rewrite recommendation
                    if max_sim >= 0.95:
                        urgency = "CRITICAL"
                        action = "Completely rewrite this content"
                    elif max_sim >= 0.92:
                        urgency = "HIGH" 
                        action = "Significantly rephrase this content"
                    else:
                        urgency = "MEDIUM"
                        action = "Minor rewording may be needed"
                    
                    detection_results['rewrite_recommendations'].append({
                        'field': field,
                        'urgency': urgency,
                        'action': action,
                        'original': generated_text
                    })
        
        return detection_results
    
    def auto_rewrite_similar_content(self, 
                                   generated_content: Dict,
                                   detection_results: Dict,
                                   rewrite_instruction: str = "Rewrite to be more original while keeping the same intent") -> Dict:
        """
        Automatically rewrite content that's too similar to references.
        
        Args:
            generated_content: The original generated content
            detection_results: Results from detect_copying()
            rewrite_instruction: Instructions for how to rewrite
        
        Returns:
            Rewritten content dict
        """
        
        if not detection_results['is_copying']:
            return generated_content
        
        rewritten_content = generated_content.copy()
        
        for flag in detection_results['flagged_fields']:
            field = flag['field']
            original_text = flag['text']
            
            # Simple rewrite strategy: add instruction to modify the text
            # In a production system, you'd call the LLM to rewrite
            rewrite_prompt = f"""
            Original: {original_text}
            
            This text is too similar to existing reference material. 
            Please rewrite it to be more original while keeping the same intent and tone.
            Make it clearly different from the reference but equally engaging.
            
            Rewritten version:
            """
            
            # For now, add a flag that this needs rewriting
            # In production, you'd call your LLM API here
            rewritten_content[field] = f"[NEEDS_REWRITE] {original_text}"
            
            # Log the issue
            print(f"🚨 Anti-copy detection: {field} flagged (similarity: {flag['similarity']:.3f})")
            print(f"   Original: {original_text[:60]}...")
            print(f"   Similar to: {flag['similar_reference'][:60]}...")
        
        return rewritten_content

def index_all_scripts():
    """Utility function to generate embeddings for all existing scripts"""
    retriever = RAGRetriever()
    
    with get_session() as ses:
        scripts = list(ses.exec(select(Script)))
        
        for script in scripts:
            # Check if embeddings already exist
            existing = ses.exec(
                select(Embedding).where(Embedding.script_id == script.id)
            ).first()
            
            if not existing:
                embeddings = retriever.generate_embeddings(script)
                for embedding in embeddings:
                    ses.add(embedding)
                
                print(f"Generated embeddings for script {script.id}")
        
        ses.commit()
        print(f"Indexing complete! Processed {len(scripts)} scripts.")

if __name__ == "__main__":
    # Run this to index your existing scripts
    index_all_scripts()
