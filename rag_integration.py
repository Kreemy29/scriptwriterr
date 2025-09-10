"""
Integration layer between the existing system and new RAG capabilities
Shows how to plug the enhanced system into the current workflow
"""

from typing import List, Dict, Any, Optional
import json
from sqlmodel import Session
from datetime import datetime

from models import Script, Embedding, AutoScore, PolicyWeights
from db import get_session, init_db
from deepseek_client import chat, get_api_key
from rag_retrieval import RAGRetriever
from auto_scorer import AutoScorer, ScriptReranker
from bandit_learner import PolicyLearner

class EnhancedScriptGenerator:
    """
    Enhanced version of script generation with RAG + policy learning
    Drop-in replacement for the existing generate_scripts function
    """
    
    def __init__(self):
        self.retriever = RAGRetriever()
        self.scorer = AutoScorer()
        self.reranker = ScriptReranker()
        self.policy_learner = PolicyLearner()
        
        # Verify we have API key
        if not get_api_key():
            raise ValueError("DeepSeek API key not found!")
    
    def generate_scripts_enhanced(self,
                                persona: str,
                                boundaries: str, 
                                content_type: str,
                                tone: str,
                                manual_refs: List[str] = None,
                                n: int = 6) -> List[Dict]:
        """
        Enhanced script generation with:
        1. RAG-based reference selection
        2. Policy-optimized parameters  
        3. Auto-scoring and reranking
        4. Online learning feedback
        """
        
        print(f"🤖 Enhanced generation: {persona} × {content_type} × {n} scripts")
        
        # Step 1: Get optimized policy for this persona/content_type
        policy_arm = self.policy_learner.get_optimized_policy(persona, content_type)
        
        # Step 2: Build dynamic few-shot pack using RAG
        query_context = f"{persona} {content_type} {tone}"
        few_shot_pack = self.retriever.build_dynamic_few_shot_pack(
            persona=persona,
            content_type=content_type, 
            query_context=query_context
        )
        
        # Step 3: Combine RAG refs with manual refs
        rag_refs = (
            few_shot_pack.get('best_hooks', []) +
            few_shot_pack.get('best_beats', []) +
            few_shot_pack.get('best_captions', [])
        )
        all_refs = (manual_refs or []) + rag_refs
        
        print(f"📚 Using {len(rag_refs)} RAG refs + {len(manual_refs or [])} manual refs")
        
        # Step 4: Enhanced generation with policy-optimized parameters
        drafts = self._generate_with_policy(
            persona=persona,
            boundaries=boundaries,
            content_type=content_type, 
            tone=tone,
            refs=all_refs,
            policy_arm=policy_arm,
            n=n,
            few_shot_pack=few_shot_pack
        )
        
        # Step 5: Anti-copying detection and cleanup
        print(f"🛡️ Checking for similarity to reference content...")
        
        # Extract reference texts for copying detection
        reference_texts = rag_refs
        cleaned_drafts = []
        
        for draft in drafts:
            # Check for copying
            detection_results = self.retriever.detect_copying(
                generated_content=draft,
                reference_texts=reference_texts,
                similarity_threshold=0.92
            )
            
            if detection_results['is_copying']:
                print(f"⚠️ Anti-copy triggered for draft: {draft.get('title', 'Untitled')[:30]}")
                print(f"   Max similarity: {detection_results['max_similarity']:.3f}")
                
                # Auto-rewrite similar content
                cleaned_draft = self.retriever.auto_rewrite_similar_content(
                    generated_content=draft,
                    detection_results=detection_results
                )
                cleaned_drafts.append(cleaned_draft)
            else:
                cleaned_drafts.append(draft)
        
        # Step 6: Auto-score all generated drafts
        script_ids = self._save_drafts_to_db(cleaned_drafts, persona, content_type, tone)
        auto_scores = [self.scorer.score_and_store(sid) for sid in script_ids]
        
        print(f"📊 Auto-scored {len(auto_scores)} drafts")
        
        # Step 7: Rerank by composite score
        ranked_script_ids = self.reranker.rerank_scripts(script_ids)
        
        # Step 8: Policy learning feedback
        self.policy_learner.learn_from_generation_batch(
            persona=persona,
            content_type=content_type,
            generated_script_ids=script_ids,
            selected_arm=policy_arm
        )
        
        # Return drafts in ranked order with scores
        return self._format_enhanced_results(ranked_script_ids, cleaned_drafts)
    
    def _generate_with_policy(self,
                            persona: str,
                            boundaries: str,
                            content_type: str,
                            tone: str,
                            refs: List[str],
                            policy_arm: Any,  # BanditArm
                            n: int,
                            few_shot_pack: Dict) -> List[Dict]:
        """Generate scripts using policy-optimized parameters"""
        
        # Enhanced system prompt with few-shot pack context
        system = f"""You write Instagram-compliant, suggestive-but-not-explicit Reels briefs.
        
STYLE CONTEXT: {few_shot_pack.get('style_card', '')}

BEST PATTERNS TO EMULATE:
Hooks: {json.dumps(few_shot_pack.get('best_hooks', []))}  
Beats: {json.dumps(few_shot_pack.get('best_beats', []))}
Captions: {json.dumps(few_shot_pack.get('best_captions', []))}

AVOID THESE PATTERNS: {json.dumps(few_shot_pack.get('negative_patterns', []))}

Use tight hooks, concrete visual beats, clear CTAs. Avoid explicit sexual terms.
Return ONLY JSON: an array of length {n}, each with {{title,hook,beats,voiceover,caption,hashtags,cta}}.
"""
        
        user = f"""
Persona: {persona}
Boundaries: {boundaries}
Content type: {content_type} | Tone: {tone}
Constraints: {json.dumps(few_shot_pack.get('constraints', {}))}

Reference snippets (inspire, don't copy):
{chr(10).join(f"- {r}" for r in refs[:8])}  # Limit to top 8 refs

Generate {n} unique variations. JSON array ONLY.
"""
        
        # Generate with multiple temperatures (policy-optimized)
        variants = []
        temps = [policy_arm.temp_low, policy_arm.temp_mid, policy_arm.temp_high]
        scripts_per_temp = max(1, n // len(temps))
        
        for i, temp in enumerate(temps):
            batch_size = scripts_per_temp
            if i == len(temps) - 1:  # Last batch gets remainder
                batch_size = n - len(variants)
            
            if batch_size <= 0:
                break
                
            try:
                out = chat([
                    {"role": "system", "content": system},
                    {"role": "user", "content": user.replace(f"Generate {n}", f"Generate {batch_size}")}
                ], temperature=temp)
                
                # Extract JSON
                start = out.find("[")
                end = out.rfind("]")
                if start >= 0 and end > start:
                    batch_variants = json.loads(out[start:end+1])
                    variants.extend(batch_variants[:batch_size])
                    print(f"✨ Generated {len(batch_variants)} scripts at temp={temp}")
                    
            except Exception as e:
                print(f"❌ Generation failed at temp={temp}: {e}")
        
        return variants[:n]  # Ensure we don't exceed requested count
    
    def _save_drafts_to_db(self, 
                          drafts: List[Dict], 
                          persona: str, 
                          content_type: str, 
                          tone: str) -> List[int]:
        """Save generated drafts to database and return script IDs"""
        
        script_ids = []
        
        with get_session() as ses:
            for draft in drafts:
                try:
                    # Calculate basic compliance
                    from compliance import score_script, blob_from
                    content_blob = blob_from(draft)
                    compliance_level, _ = score_script(content_blob)
                    
                    script = Script(
                        creator=persona,
                        content_type=content_type,
                        tone=tone,
                        title=draft.get("title", "Generated Script"),
                        hook=draft.get("hook", ""),
                        beats=draft.get("beats", []),
                        voiceover=draft.get("voiceover", ""),
                        caption=draft.get("caption", ""),
                        hashtags=draft.get("hashtags", []),
                        cta=draft.get("cta", ""),
                        compliance=compliance_level,
                        source="ai"
                    )
                    
                    ses.add(script)
                    ses.commit()
                    ses.refresh(script)
                    
                    script_ids.append(script.id)
                    
                    # Generate embeddings for new script
                    embeddings = self.retriever.generate_embeddings(script)
                    for embedding in embeddings:
                        ses.add(embedding)
                    
                except Exception as e:
                    print(f"❌ Failed to save draft: {e}")
                    continue
            
            ses.commit()
        
        return script_ids
    
    def _format_enhanced_results(self, 
                               ranked_script_ids: List[tuple], 
                               original_drafts: List[Dict]) -> List[Dict]:
        """Format results with ranking and score information"""
        
        # Create a lookup for original drafts by content
        draft_lookup = {}
        for i, draft in enumerate(original_drafts):
            key = draft.get("title", "") + draft.get("hook", "")
            draft_lookup[key] = draft
        
        results = []
        
        with get_session() as ses:
            for script_id, composite_score in ranked_script_ids:
                script = ses.get(Script, script_id)
                if script:
                    # Convert back to the expected format
                    result = {
                        "title": script.title,
                        "hook": script.hook,
                        "beats": script.beats,
                        "voiceover": script.voiceover,
                        "caption": script.caption,
                        "hashtags": script.hashtags,
                        "cta": script.cta,
                        # Enhanced metadata
                        "_enhanced_score": round(composite_score, 3),
                        "_script_id": script_id,
                        "_compliance": script.compliance
                    }
                    results.append(result)
        
        return results

# Backward compatibility wrapper
def generate_scripts_rag(persona: str,
                        boundaries: str,
                        content_type: str,
                        tone: str,
                        refs: List[str],
                        n: int = 6) -> List[Dict]:
    """
    Drop-in replacement for existing generate_scripts function
    Uses enhanced RAG system while maintaining API compatibility
    """
    generator = EnhancedScriptGenerator()
    return generator.generate_scripts_enhanced(
        persona=persona,
        boundaries=boundaries,
        content_type=content_type,
        tone=tone,
        manual_refs=refs,
        n=n
    )

def setup_rag_system():
    """One-time setup to initialize the RAG system"""
    print("🔧 Setting up RAG system...")
    
    # Initialize database with new tables
    init_db()
    print("✅ Database initialized")
    
    # Generate embeddings for existing scripts
    from rag_retrieval import index_all_scripts
    index_all_scripts()
    print("✅ Existing scripts indexed")
    
    # Auto-score recent scripts
    scorer = AutoScorer()
    recent_scores = scorer.batch_score_recent(hours=24*7)  # Last week
    print(f"✅ Auto-scored {len(recent_scores)} recent scripts")
    
    print("🎉 RAG system setup complete!")

if __name__ == "__main__":
    # Demo the enhanced system
    setup_rag_system()
    
    # Test generation
    generator = EnhancedScriptGenerator()
    results = generator.generate_scripts_enhanced(
        persona="Anya",
        boundaries="Instagram-safe; suggestive but not explicit",
        content_type="thirst-trap",
        tone="playful, flirty",
        manual_refs=["Just a quick workout session", "Getting ready for the day"],
        n=3
    )
    
    print(f"\n🎬 Generated {len(results)} enhanced scripts:")
    for i, script in enumerate(results, 1):
        score = script.get('_enhanced_score', 0)
        compliance = script.get('_compliance', 'unknown')
        print(f"{i}. {script['title']} (score: {score}, compliance: {compliance})")
        print(f"   Hook: {script['hook'][:60]}...")
