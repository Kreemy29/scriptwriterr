"""
Auto-scoring system using LLM judges for script quality assessment
Integrates with existing DeepSeek client
"""

import json
from typing import Dict, List, Tuple
from sqlmodel import Session, select
from datetime import datetime, timedelta

from models import Script, AutoScore, PolicyWeights
from db import get_session
from deepseek_client import chat

class AutoScorer:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        
    def score_script(self, script_data: Dict) -> Dict[str, float]:
        """
        Score a script using LLM judge across 5 dimensions
        Returns scores and confidence level
        """
        
        system_prompt = """You are an expert Instagram content analyst. Score this script on 6 dimensions (1-5 scale):

1. OVERALL: General quality and effectiveness (1=poor, 5=excellent)
2. HOOK: How compelling is the opening (1=boring, 5=irresistible) 
3. ORIGINALITY: How unique/creative (1=generic, 5=highly original)
4. STYLE_FIT: How well it matches the persona (1=off-brand, 5=perfect fit)
5. SAFETY: Instagram compliance (1=risky, 5=completely safe)
6. AUTHENTICITY: How natural/authentic vs cringe/corny (1=cringe, 5=authentic)

Return ONLY a JSON object with: {"overall": X, "hook": X, "originality": X, "style_fit": X, "safety": X, "authenticity": X, "confidence": X, "reasoning": "brief explanation"}

Be consistent and objective. Confidence should be 0.1-1.0 based on how certain you are."""

        user_prompt = f"""
Script to score:
Title: {script_data.get('title', '')}
Hook: {script_data.get('hook', '')}
Beats: {script_data.get('beats', [])}
Caption: {script_data.get('caption', '')}
Persona: {script_data.get('creator', '')} 
Content Type: {script_data.get('content_type', '')}
Tone: {script_data.get('tone', '')}

Score this script now."""

        try:
            response = chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], temperature=0.3)  # Low temperature for consistent scoring
            
            # Extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start >= 0 and end > start:
                scores = json.loads(response[start:end])
                
                # Validate scores are in range
                required_keys = ['overall', 'hook', 'originality', 'style_fit', 'safety', 'authenticity']
                for key in required_keys:
                    if key not in scores or not (1 <= scores[key] <= 5):
                        raise ValueError(f"Invalid score for {key}")
                
                # Ensure confidence is present and valid
                if 'confidence' not in scores or not (0.1 <= scores['confidence'] <= 1.0):
                    scores['confidence'] = 0.7  # Default confidence
                
                return scores
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            print(f"Auto-scoring failed: {e}")
            # Return neutral scores with low confidence
            return {
                'overall': 3.0,
                'hook': 3.0,
                'originality': 3.0,
                'style_fit': 3.0,
                'safety': 3.0,
                'confidence': 0.3,
                'reasoning': f"Scoring failed: {str(e)}"
            }
    
    def score_and_store(self, script_id: int) -> AutoScore:
        """Score a script and store in database"""
        with get_session() as ses:
            script = ses.get(Script, script_id)
            if not script:
                raise ValueError(f"Script {script_id} not found")
            
            # Prepare script data for scoring
            script_data = {
                'title': script.title,
                'hook': script.hook,
                'beats': script.beats,
                'caption': script.caption,
                'creator': script.creator,
                'content_type': script.content_type,
                'tone': script.tone
            }
            
            # Get scores
            scores = self.score_script(script_data)
            
            # Store auto-score
            auto_score = AutoScore(
                script_id=script_id,
                overall=scores['overall'],
                hook=scores['hook'],
                originality=scores['originality'],
                style_fit=scores['style_fit'],
                safety=scores['safety'],
                confidence=scores['confidence'],
                notes=scores.get('reasoning', '')
            )
            
            ses.add(auto_score)
            ses.commit()
            ses.refresh(auto_score)
            
            return auto_score
    
    def batch_score_recent(self, hours: int = 24) -> List[AutoScore]:
        """Score all recently generated scripts that haven't been auto-scored"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with get_session() as ses:
            # Find scripts without auto-scores
            recent_scripts = ses.exec(
                select(Script).where(
                    Script.created_at >= cutoff,
                    Script.source == "ai"  # Only score AI-generated scripts
                )
            ).all()
            
            # Filter out already scored
            unscored = []
            for script in recent_scripts:
                existing_score = ses.exec(
                    select(AutoScore).where(AutoScore.script_id == script.id)
                ).first()
                if not existing_score:
                    unscored.append(script)
            
            print(f"Auto-scoring {len(unscored)} recent scripts...")
            
            results = []
            for script in unscored:
                try:
                    auto_score = self.score_and_store(script.id)
                    results.append(auto_score)
                    print(f"Scored script {script.id}: {auto_score.overall:.1f}/5.0")
                except Exception as e:
                    print(f"Failed to score script {script.id}: {e}")
            
            return results

class ScriptReranker:
    """Rerank generated scripts using composite scoring"""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            'overall': 0.35,
            'hook': 0.20,
            'originality': 0.15,
            'style_fit': 0.15,
            'safety': 0.15
        }
    
    def rerank_scripts(self, script_ids: List[int]) -> List[Tuple[int, float]]:
        """
        Rerank scripts by composite score
        Returns list of (script_id, composite_score) sorted by score descending
        """
        
        results = []
        
        with get_session() as ses:
            for script_id in script_ids:
                # Try to get auto-score first
                auto_score = ses.exec(
                    select(AutoScore).where(AutoScore.script_id == script_id)
                ).first()
                
                if auto_score and auto_score.confidence >= 0.5:
                    # Use auto-scores
                    composite = (
                        self.weights['overall'] * auto_score.overall +
                        self.weights['hook'] * auto_score.hook +
                        self.weights['originality'] * auto_score.originality +
                        self.weights['style_fit'] * auto_score.style_fit +
                        self.weights['safety'] * auto_score.safety
                    )
                else:
                    # Fall back to human ratings if available
                    script = ses.get(Script, script_id)
                    if script and script.ratings_count > 0:
                        composite = (
                            self.weights['overall'] * (script.score_overall or 3.0) +
                            self.weights['hook'] * (script.score_hook or 3.0) +
                            self.weights['originality'] * (script.score_originality or 3.0) +
                            self.weights['style_fit'] * (script.score_style_fit or 3.0) +
                            self.weights['safety'] * (script.score_safety or 3.0)
                        )
                    else:
                        # Default neutral score
                        composite = 3.0
                
                results.append((script_id, composite))
        
        # Sort by composite score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def get_best_script(self, script_ids: List[int]) -> int:
        """Get the ID of the highest-scoring script"""
        ranked = self.rerank_scripts(script_ids)
        return ranked[0][0] if ranked else script_ids[0]

def auto_score_pipeline():
    """Main pipeline to auto-score recent scripts"""
    scorer = AutoScorer()
    
    # Score recent scripts
    new_scores = scorer.batch_score_recent(hours=24)
    
    if new_scores:
        print(f"\n📊 Auto-scoring Results ({len(new_scores)} scripts):")
        for score in new_scores:
            print(f"Script {score.script_id}: {score.overall:.1f}/5.0 (confidence: {score.confidence:.2f})")
    else:
        print("No new scripts to score.")

if __name__ == "__main__":
    auto_score_pipeline()
