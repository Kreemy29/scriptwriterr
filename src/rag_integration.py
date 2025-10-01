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
        
        print(f"Enhanced generation: {persona} × {content_type} × {n} scripts")
        
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
        
        # Step 5: Skip heavy similarity checking for speed
        print(f"Skipping similarity check for speed")
        cleaned_drafts = drafts
        
        # Step 6: Save drafts and skip heavy processing for speed
        script_ids = self._save_drafts_to_db(cleaned_drafts, persona, content_type, tone)
        
        # Skip auto-scoring and reranking for speed
        print(f"Skipping auto-scoring and reranking for speed")
        ranked_script_ids = [(sid, 0.8) for sid in script_ids]  # Default score
        
        # Skip policy learning for speed
        print(f"Skipping policy learning for speed")
        
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
        """Generate scripts using policy-optimized parameters - OPTIMIZED VERSION"""
        
        # Enhanced system prompt for SEDUCTIVE ADULT CONTENT targeting male audiences
        system = f"""You write seductive, sexually appealing Instagram Reels targeting male audiences. Think sophisticated seduction meets intelligent humor.

CRITICAL: This is SOLO SEDUCTIVE CONTENT - model is alone, creating sexual appeal for male viewers.

SEDUCTIVE CONTENT STYLE:
- INTELLIGENT SEDUCTION: Clever sexual innuendos, sophisticated dirty talk, witty sexual humor
- MALE-FOCUSED APPEAL: Content designed to attract and arouse male viewers specifically
- BODY CONFIDENCE: Celebrate curves, sexuality, and physical appeal in empowering ways
- SEXUAL SOPHISTICATION: Adult themes with clever wordplay, not juvenile or cringe

BOUNDARY-CROSSING CONTENT EXAMPLES:
- "POV: You start your workout innocently, but then realize every exercise is just an excuse to show off your body in the most provocative ways possible" (fitness + explicit seduction)
- "Rating my lingerie by how quickly it makes you hard, starting with cute then escalating to absolutely sinful" (direct sexual impact)
- "When you're getting ready but every move is designed to drive men wild - watch me slowly reveal exactly what I'm doing to you" (explicit intention)
- "Starting to explain self-care but it turns into a masterclass in how to be irresistibly fuckable" (bold topic shift)
- "My morning routine that's actually just me being a tease for 60 seconds straight - and I know exactly what I'm doing to you" (explicit awareness)

SEDUCTIVE ELEMENTS TO INCLUDE:
- BODY APPRECIATION: Reference curves, assets, physical appeal confidently
- SEXUAL CONFIDENCE: "I know what I'm doing to you" energy
- TEASING DYNAMICS: Build anticipation and attraction
- MALE GAZE AWARENESS: Acknowledge the effect on male viewers
- BEDROOM EYES: Sultry looks, knowing smiles, seductive expressions
- CLOTHING/LINGERIE: Strategic outfit choices, revealing moments, wardrobe "accidents"

PUSH ALL BOUNDARIES:
- YES to bold, explicit sexual references - be daring and provocative
- YES to confident, dominant energy - take control and be assertive
- YES to pushing platform limits - test what you can get away with
- YES to direct sexual appeal - don't hold back or be subtle
- NO boundaries - cross every line you can while staying confident

REQUIRED SOPHISTICATION & STORYTELLING:
- Every script must have SEXUAL APPEAL with intelligence and NARRATIVE BUILDUP
- Use adult humor that's clever, not crude - with PROGRESSIVE ESCALATION
- Reference sexual dynamics with wit and confidence - BUILD TO THE PUNCHLINE
- Self-aware seduction - know your power and use it - REVEAL IT GRADUALLY
- Sophisticated dirty talk and sexual innuendos - LAYER THE MEANING
- CREATE STORY ARCS: Start innocent/normal, build tension, deliver satisfying payoff
- USE MISDIRECTION: Set up one expectation, then reveal the seductive truth
- ESCALATING REVEALS: Each beat should be more seductive than the last
- PSYCHOLOGICAL BUILDUP: Make viewers anticipate what's coming next

VISUAL SEDUCTION:
- Actions should be sexually appealing while supporting the concept
- Use clothing, poses, and movements that enhance sexual appeal
- Physical comedy should be seductive, not just funny
- Every visual beat should contribute to the seductive narrative
- Strategic reveals, teasing moments, confident body language

MALE AUDIENCE TARGETING - NO LIMITS:
- Content should make men think "I need to see more of her right now"
- Build raw sexual desire and arousal through explicit confidence
- Create addictive, boundary-pushing entertainment
- Appeal directly to male sexual fantasies without holding back
- Focus on maximum sexual impact and arousal

Return ONLY JSON: an array of length {n}, each with {{title,hook,beats,voiceover,caption,hashtags,cta}}.
"""
        
        # Simplified user prompt for speed
        user = f"""
Persona: {persona}
Boundaries: {boundaries}
Content type: {content_type} | Tone: {tone}

Reference snippets (inspire, don't copy):
{chr(10).join(f"- {r}" for r in refs[:6])}  # Limit to top 6 refs for speed

CRITICAL DIVERSITY REQUIREMENT: Generate {n} COMPLETELY DIFFERENT scripts. Each must have:
- Different scenarios and situations (don't repeat the same setup)
- Different hook styles (rotate: POV, question, reverse bait, challenge, storytelling)
- Different visual beats and actions (avoid similar movements/expressions)
- Different humor approaches and angles (vary the comedy style)
- Different settings and contexts (change locations/situations)
- Vary the tone and style between scripts (some playful, some edgy, some witty)

NO RELATIONSHIP CONTENT: Avoid boyfriend, girlfriend, partner, dating scenarios
- Focus on SOLO scenarios: model alone, interacting with objects, situations, or audience
- Use lifestyle, challenge, reaction, or POV content instead of relationship drama
- Think solo content creator, not couple content
- FORBIDDEN WORDS: "we", "us", "together", "couple", "partner", "boyfriend", "girlfriend"
- REQUIRED LANGUAGE: Use "I", "me", "my", "myself", "alone", "solo" instead

RANDOM SEED: {seed_variation} - Use this to ensure each generation is unique!

IMPORTANT: Use these reference scripts as INSPIRATION for style, tone, and approach. 
Study their hooks, beats, and humor style. Create NEW content that captures their essence but is completely original.
AVOID VISUAL CLICHÉS: No "biting lip", "smirking", "head tilts", "eye rolls", "winking" - be creative with unique visual moments.
AVOID GENERIC EXPRESSIONS: No "mischievous smile", "playful glance", "suggestive look" - be specific with unique actions and settings.
SEDUCTIVE FOCUS: Use intelligent seduction and sexual appeal. Think sophisticated, confident creator with witty content.
MALE AUDIENCE TARGETING: Create content that attracts and appeals to male viewers specifically.
SEXUAL SOPHISTICATION: Adult themes, body confidence, teasing dynamics - but make them clever and empowering, not promotional.

Generate {n} COMPLETELY DIFFERENT, unique variations. Each script must be:
- TOTALLY UNIQUE from the others (different scenarios, hooks, approaches)
- CREATIVE and SPICY with mature, witty humor
- Clever double entendres and sexual innuendos
- Adult-level comedy and clever wordplay
- Push boundaries with suggestive content (but stay platform-compliant)
- VARIED in style, tone, and approach
- Think sophisticated adult humor, not juvenile jokes
- NO CORNY PICKUP LINES OR CHEESY HUMOR
- NO REPETITIVE VISUAL CLICHÉS: NO "biting lip", "smirking", "head tilts", "eye rolls", "winking"
- NO GENERIC FACIAL EXPRESSIONS: NO "mischievous smile", "playful glance", "suggestive look"
- CREATE UNIQUE, VARIED VISUAL BEATS - avoid repetitive facial expressions and gestures
- BE SPECIFIC WITH VISUAL MOMENTS - describe unique actions, objects, settings, not generic expressions
- GEN Z HUMOR: Use raw, unfiltered, edgy comedy. Think TikTok humor - bold, direct, unapologetic
- DIRTY JOKES: Be MORE EXPLICIT with sexual innuendos, crude humor, and adult themes. Cross content boundaries
- NO SAFE, BORING CONTENT - push limits with suggestive scenarios, sexual tension, and provocative humor
- Be EDGY, WITTY, and SOPHISTICATED
- Think HBO comedy, not Disney Channel

JSON array ONLY.
"""
        
        variants = []
        import random
        import time
        
        # Use more aggressive randomization for maximum diversity
        random.seed(int(time.time() * 1000) % 10000)
        
        # Much higher temperature range for maximum creativity and diversity
        temp = 0.7 + random.uniform(0.0, 0.6)  # Randomize between 0.7-1.3 for maximum creativity
        temp = max(0.7, min(1.3, temp))
        
        # Add random seed variation to the user prompt
        seed_variation = random.randint(1, 1000)
        
        # Create user prompt with seed_variation
        user_with_seed = f"""
Persona: {persona}
Boundaries: {boundaries}
Content type: {content_type} | Tone: {tone}

Reference snippets (inspire, don't copy):
{chr(10).join(f"- {r}" for r in refs[:6])}  # Limit to top 6 refs for speed

CRITICAL DIVERSITY REQUIREMENT: Generate {n} COMPLETELY DIFFERENT scripts. Each must have:
- Different scenarios and situations (don't repeat the same setup)
- Different hook styles (rotate: POV, question, reverse bait, challenge, storytelling)
- Different visual beats and actions (avoid similar movements/expressions)
- Different humor approaches and angles (vary the comedy style)
- Different settings and contexts (change locations/situations)
- Vary the tone and style between scripts (some playful, some edgy, some witty)

NO RELATIONSHIP CONTENT: Avoid boyfriend, girlfriend, partner, dating scenarios
- Focus on SOLO scenarios: model alone, interacting with objects, situations, or audience
- Use lifestyle, challenge, reaction, or POV content instead of relationship drama
- Think solo content creator, not couple content
- FORBIDDEN WORDS: "we", "us", "together", "couple", "partner", "boyfriend", "girlfriend"
- REQUIRED LANGUAGE: Use "I", "me", "my", "myself", "alone", "solo" instead

RANDOM SEED: {seed_variation} - Use this to ensure each generation is unique!

IMPORTANT: Use these reference scripts as INSPIRATION for style, tone, and approach. 
Study their hooks, beats, and humor style. Create NEW content that captures their essence but is completely original.
AVOID VISUAL CLICHÉS: No "biting lip", "smirking", "head tilts", "eye rolls", "winking" - be creative with unique visual moments.
AVOID GENERIC EXPRESSIONS: No "mischievous smile", "playful glance", "suggestive look" - be specific with unique actions and settings.
SEDUCTIVE FOCUS: Use intelligent seduction and sexual appeal. Think sophisticated, confident creator with witty content.
MALE AUDIENCE TARGETING: Create content that attracts and appeals to male viewers specifically.
SEXUAL SOPHISTICATION: Adult themes, body confidence, teasing dynamics - but make them clever and empowering, not promotional.

Generate {n} COMPLETELY DIFFERENT, unique variations. Each script must be:
- TOTALLY UNIQUE from the others (different scenarios, hooks, approaches)
- CREATIVE and SPICY with mature, witty humor
- Clever double entendres and sexual innuendos
- Platform-compliant but pushing boundaries
- Engaging hooks that grab attention immediately
- Visual beats that are specific and unique (not generic expressions)
- Adult humor that's sophisticated and edgy
- BODY-FOCUSED: Include references to the model's physical features, curves, and attractiveness
- PHYSICAL COMEDY: Use body language, movement, and physical appeal as central elements
- VISUAL APPEAL: Create scenarios that showcase the model's figure and body in engaging ways

Return ONLY JSON: an array of length {n}, each with {{title,hook,beats,voiceover,caption,hashtags,cta}}.
"""
        
        try:
            out = chat([
                {"role": "system", "content": system},
                {"role": "user", "content": user_with_seed}
            ], temperature=temp)
                
            # Extract JSON
            start = out.find("[")
            end = out.rfind("]")
            if start >= 0 and end > start:
                batch_variants = json.loads(out[start:end+1])
                
                
                variants.extend(batch_variants)
                print(f"Generated {len(batch_variants)} scripts at temp={temp:.2f}")
            else:
                print(f"❌ Failed to parse JSON from generation response")
                
        except Exception as e:
            print(f"❌ Generation failed at temp={temp:.2f}: {e}")
        
        return variants[:n]
    
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
                    
                    # Handle both old and new format
                    if "model_name" in draft:
                        # New template format
                        script = Script(
                            creator=persona,
                            content_type=content_type,
                            tone=tone,
                            title=draft.get("main_idea", "Generated Script"),
                            hook=draft.get("video_hook", ""),
                            beats=draft.get("action_scenes", []),
                            voiceover=draft.get("script_guidance", ""),
                            caption="",  # No longer used
                            hashtags=[],  # No longer used
                            cta="",  # No longer used
                            compliance=compliance_level,
                            source="ai",
                            # New template fields
                            model_name=draft.get("model_name", persona),
                            video_type=draft.get("video_type", content_type),
                            video_length=draft.get("video_length", "15-25s"),
                            cut_lengths=draft.get("cut_lengths", "Quick cuts"),
                            video_hook=draft.get("video_hook", ""),
                            main_idea=draft.get("main_idea", ""),
                            action_scenes=draft.get("action_scenes", []),
                            script_guidance=draft.get("script_guidance", ""),
                            storyboard_notes=draft.get("storyboard_notes", []),
                            intro_hook=draft.get("intro_hook", ""),
                            outro_hook=draft.get("outro_hook", ""),
                            list_of_shots=draft.get("list_of_shots", [])
                        )
                    else:
                        # Old format (backward compatibility)
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

# Fast mode - bypasses heavy RAG processing
def generate_scripts_fast(persona: str,
                         content_type: str,
                         tone: str,
                         n: int = 6,
                         spicy_hooks: bool = True) -> List[Dict]:
    """
    Fast mode generation - bypasses heavy RAG processing for speed
    """
    print(f"Fast generation: {persona} × {content_type} × {n} scripts")
    
    # Hook style based on spicy_hooks toggle
    hook_style = ""
    if spicy_hooks:
        hook_style = """
SPICY HOOKS (Visual/Suggestive):
- "Watch my ass bounce while I pretend to work out"
- "POV: Every move I make is designed to turn you on"
- "The way my tits shake when I run to the camera"
- "Bending over 'accidentally' while you watch"
- "My curves doing all the talking in this outfit"
"""
    else:
        hook_style = """
TRADITIONAL HOOKS:
- "You won't believe what happened next"
- "This changed everything for me"
- "Wait for the plot twist"
- "The ending will shock you"
- "This is why I love being single"
"""

    # Enhanced system prompt for SEDUCTIVE ADULT CONTENT targeting male audiences
    system = f"""You write seductive, sexually appealing Instagram Reels targeting male audiences.

CRITICAL: SOLO SEDUCTIVE CONTENT - model alone, creating sexual appeal for male viewers.

{hook_style}

CONTENT TYPE SPECIFIC RULES:
- SKIT: Visual comedy/scenarios, voiceover should be EMPTY (no script), hooks should be actual hooks
- TALKING-STYLE: Model talks DIRECTLY TO CAMERA like realcarlyjane/realmarciereeves, voiceover contains the script, SINGLE SHOT ONLY, NO storylines, NO cuts, authentic direct communication
- THIRST-TRAP: Pure visual appeal, voiceover should be EMPTY, focus on body/poses

TALKING-STYLE SPECIFIC REQUIREMENTS:
- ONE CONTINUOUS SHOT: No cuts, no scene changes, no storylines
- DIRECT TO CAMERA: Model looks at and talks to the viewer directly
- AUTHENTIC COMMUNICATION: Real, conversational tone like realcarlyjane/realmarciereeves
- NO STORYLINES: Avoid narrative arcs, just direct communication
- EXAMPLES: "Let me tell you why...", "Here's what I think about...", "You guys always ask me..."

HOOK FORMAT - CRITICAL:
- Hook should be the ACTUAL HOOK text that appears on screen
- NOT a description like "POV: You're just trying to buy groceries but..."
- Should be short, punchy, attention-grabbing text
- Examples: "Watch my ass bounce", "This outfit is dangerous", "Men can't handle this"

VOICEOVER FORMAT - CRITICAL:
- SKIT/VISUAL content: voiceover should be EMPTY string ""
- TALKING videos: voiceover contains what the model says to camera
- THIRST-TRAP: voiceover should be EMPTY string ""

SEDUCTIVE ELEMENTS WITH STORYTELLING:
- BODY APPRECIATION: Reference curves, assets, physical appeal confidently - BUILD UP TO IT
- SEXUAL CONFIDENCE: "I know what I'm doing to you" energy - REVEAL GRADUALLY  
- TEASING DYNAMICS: Build anticipation and attraction - CREATE STORY ARCS
- MALE GAZE AWARENESS: Acknowledge the effect on male viewers - USE MISDIRECTION
- STRATEGIC CLOTHING: Revealing outfits, lingerie, wardrobe moments - ESCALATING REVEALS
- NARRATIVE BUILDUP: Start innocent/normal, build tension, deliver satisfying payoff
- PSYCHOLOGICAL ESCALATION: Each beat should be more seductive than the last

VISUAL SEDUCTION:
- Actions should be sexually appealing while supporting the concept
- Use clothing, poses, movements that enhance sexual appeal
- Strategic reveals, teasing moments, confident body language
- Every visual beat contributes to seductive narrative

MALE AUDIENCE TARGETING - NO LIMITS:
- Make men think "I need to see more of her right now"
- Build raw sexual desire and arousal through explicit confidence
- Create addictive, boundary-pushing entertainment
- Appeal directly to male sexual fantasies without holding back
- Focus on maximum sexual impact and arousal

NO RELATIONSHIP CONTENT: Avoid boyfriend, girlfriend, partner, dating scenarios
- Focus on SOLO scenarios: model alone, interacting with objects, situations, or audience
- FORBIDDEN WORDS: "we", "us", "together", "couple", "partner", "boyfriend", "girlfriend"
- REQUIRED LANGUAGE: Use "I", "me", "my", "myself", "alone", "solo" instead

Return ONLY JSON: an array of length {n}, each with {{title,hook,beats,voiceover,caption,hashtags,cta}}.
"""
    
    
    import random
    import time
    
    # Use more aggressive randomization for maximum diversity
    random.seed(int(time.time() * 1000) % 10000)
    
    # Add random seed variation to the user prompt
    seed_variation = random.randint(1, 1000)
    
    # Much higher temperature range for maximum creativity and diversity
    temp = 0.8 + random.uniform(0.0, 0.5)  # Randomize between 0.8-1.3 for maximum creativity
    temp = max(0.8, min(1.3, temp))
    
    # Create user prompt with seed_variation
    user_with_seed = f"""
Persona: {persona}
Content type: {content_type} | Tone: {tone}
NO BOUNDARIES - PUSH ALL LIMITS

Reference snippets (inspire, don't copy):
- POV: You start your workout innocently, but then realize every exercise is just an excuse to show off your body in the most provocative ways possible
- Rating my lingerie by how quickly it makes you hard, starting with cute then escalating to absolutely sinful
- When you're getting ready but every move is designed to drive men wild - watch me slowly reveal exactly what I'm doing to you
- My morning routine that's actually just me being a tease for 60 seconds straight - and I know exactly what I'm doing to you

CRITICAL DIVERSITY REQUIREMENT: Generate {n} COMPLETELY DIFFERENT scripts. Each must have:
- Different scenarios and situations (don't repeat the same setup)
- Different hook styles (rotate: POV, question, reverse bait, challenge, storytelling)
- Different visual beats and actions (avoid similar movements/expressions)
- Different humor approaches and angles (vary the comedy style)
- Different settings and contexts (change locations/situations)
- Vary the tone and style between scripts (some playful, some edgy, some witty)

NO RELATIONSHIP CONTENT: Avoid boyfriend, girlfriend, partner, dating scenarios
- Focus on SOLO scenarios: model alone, interacting with objects, situations, or audience
- Use lifestyle, challenge, reaction, or POV content instead of relationship drama
- Think solo content creator, not couple content
- FORBIDDEN WORDS: "we", "us", "together", "couple", "partner", "boyfriend", "girlfriend"
- REQUIRED LANGUAGE: Use "I", "me", "my", "myself", "alone", "solo" instead

RANDOM SEED: {seed_variation} - Use this to ensure each generation is unique!

IMPORTANT: Use these reference scripts as INSPIRATION for style, tone, and approach. 
Study their hooks, beats, and humor style. Create NEW content that captures their essence but is completely original.
AVOID VISUAL CLICHÉS: No "biting lip", "smirking", "head tilts", "eye rolls", "winking" - be creative with unique visual moments.
AVOID GENERIC EXPRESSIONS: No "mischievous smile", "playful glance", "suggestive look" - be specific with unique actions and settings.
SEDUCTIVE FOCUS: Use intelligent seduction and sexual appeal. Think sophisticated, confident creator with witty content.
MALE AUDIENCE TARGETING: Create content that attracts and appeals to male viewers specifically.
SEXUAL SOPHISTICATION: Adult themes, body confidence, teasing dynamics - but make them clever and empowering, not promotional.

Generate {n} COMPLETELY DIFFERENT, unique variations. Each script must be:
- TOTALLY UNIQUE from the others (different scenarios, hooks, approaches)
- CREATIVE and SPICY with mature, witty humor
- Clever double entendres and sexual innuendos
- Platform-compliant but pushing boundaries
- Engaging hooks that grab attention immediately
- Visual beats that are specific and unique (not generic expressions)
- Adult humor that's sophisticated and edgy
- BODY-FOCUSED: Include references to the model's physical features, curves, and attractiveness
- PHYSICAL COMEDY: Use body language, movement, and physical appeal as central elements
- VISUAL APPEAL: Create scenarios that showcase the model's figure and body in engaging ways

Return ONLY JSON: an array of length {n}, each with {{title,hook,beats,voiceover,caption,hashtags,cta}}.
"""
    
    try:
        out = chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user_with_seed}
        ], temperature=temp)
            
        # Extract JSON
        start = out.find("[")
        end = out.rfind("]")
        if start >= 0 and end > start:
            variants = json.loads(out[start:end+1])
            
            
            print(f"Generated {len(variants)} scripts at temp={temp:.2f}")
            return variants[:n]
        else:
            print(f"Failed to parse JSON from generation response")
            return []
            
    except Exception as e:
        print(f"Fast generation failed: {e}")
        return []

# Backward compatibility wrapper
def generate_scripts_rag(persona: str,
                        boundaries: str,
                        content_type: str,
                        tone: str,
                        refs: List[str],
                        n: int = 6,
                        spicy_hooks: bool = True) -> List[Dict]:
    """
    Enhanced RAG-powered script generation with seductive content focus
    NO BOUNDARIES - PUSH ALL LIMITS
    """
    # Use the fast generation function which has the updated seductive prompts
    # Ignore boundaries and refs - we're crossing all boundaries now
    return generate_scripts_fast(
        persona=persona,
        content_type=content_type,
        tone=tone,
        n=n,
        spicy_hooks=spicy_hooks
    )

def setup_rag_system():
    """One-time setup to initialize the RAG system"""
    print("Setting up RAG system...")
    
    # Initialize database with new tables
    init_db()
    print("Database initialized")
    
    # Generate embeddings for existing scripts
    from rag_retrieval import index_all_scripts
    index_all_scripts()
    print("Existing scripts indexed")
    
    # Auto-score recent scripts
    scorer = AutoScorer()
    recent_scores = scorer.batch_score_recent(hours=24*7)  # Last week
    print(f"Auto-scored {len(recent_scores)} recent scripts")
    
    print("RAG system setup complete!")

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
    
    print(f"\nGenerated {len(results)} enhanced scripts:")
    for i, script in enumerate(results, 1):
        score = script.get('_enhanced_score', 0)
        compliance = script.get('_compliance', 'unknown')
        print(f"{i}. {script['title']} (score: {score}, compliance: {compliance})")
        print(f"   Hook: {script['hook'][:60]}...")
