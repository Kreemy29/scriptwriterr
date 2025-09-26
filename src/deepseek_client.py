import os, requests, json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Get API key from Streamlit secrets or environment
def get_api_key():
    try:
        if hasattr(st, 'secrets') and "DEEPSEEK_API_KEY" in st.secrets:
            return st.secrets["DEEPSEEK_API_KEY"]
    except Exception as e:
        # Streamlit secrets might not be available in all contexts
        pass
    return os.getenv("DEEPSEEK_API_KEY")

# Don't call get_api_key() at import time - call it when needed
DEEPSEEK_API_KEY = None
BASE = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

def chat(messages, model="deepseek-chat", temperature=0.9):
    api_key = get_api_key()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found. Please set it in Hugging Face Space secrets or environment variables.")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature}
    r = requests.post(f"{BASE}/chat/completions", headers=headers, data=json.dumps(payload), timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def generate_scripts_template(persona, boundaries, content_type, tone, refs, n=6):
    """
    Generate scripts using the new template format with conditional script generation
    """
    # Map content types to video types
    video_type_mapping = {
        "talking-style": "talking",
        "skit": "skit", 
        "fake-podcast": "fake_podcast",
        "reaction-prank": "prank",
        "lifestyle": "candid_interaction",
        "thirst-trap": "thirst_trap"
    }
    
    video_type = video_type_mapping.get(content_type, "skit")
    
    # Determine if script should be included based on video type
    script_rules = {
        "talking": "always",           # Always include script
        "skit": "conditional",         # Include script OR voiceover based on context
        "fake_podcast": "always",      # Always include script
        "prank": "always",             # Always include script
        "candid_interaction": "conditional",  # Include script OR none based on context
        "thirst_trap": "never"         # Never include script/voiceover
    }
    
    script_rule = script_rules.get(video_type, "conditional")
    
    # Build system prompt based on video type and script requirements
    system = f"""You are a professional video content planner creating Instagram Reels scripts.

VIDEO TYPE: {video_type.upper()}
SCRIPT REQUIREMENT: {script_rule.upper()}

Create {n} video planning templates with this EXACT JSON structure:
{{
  "model_name": "{persona}",
  "date": "2025-09-24",
  "video_type": "{video_type}",
  "video_length": "15-25s",
  "cut_lengths": "Quick cuts",
  "video_hook": "[Text overlay on screen - POV scenario or caption, can be empty if no text needed]",
  "lighting": "Natural lighting",
  "main_idea": "[Brief concept description]",
  "action_scenes": ["Detailed scene 1 with specific actions, expressions, and timing", "Detailed scene 2 with specific actions, expressions, and timing", "Detailed scene 3 with specific actions, expressions, and timing"],
  "script_guidance": "[Script content or empty string]",
  "storyboard_notes": ["Location", "Wardrobe", "Shot type", "Focus points"],
  "list_of_shots": ["Wide shot", "Close-up", "Medium shot"],
  "intro_hook": "[ACTUAL HOOK: visual/audio attention-grabber for first 0.3 seconds - camera shake, boobs shaking, unique angle, weird audio, voice cadence change]",
  "outro_hook": "[REWARD: visual payoff, audio reward, satisfying conclusion]"
}}

DETAILED REQUIREMENTS:

HOOKS (video_hook, intro_hook, outro_hook):
- Be SPECIFIC and DETAILED, not generic
- video_hook: TEXT OVERLAY on screen (POV scenario, caption, or empty if no text needed)
- intro_hook: ACTUAL HOOK - VISUAL/AUDIO attention-grabber for first 0.3 seconds (camera shake, boobs shaking, unique angle, weird audio, voice cadence change)
- outro_hook: REWARD for watching - satisfying conclusion (visual payoff, audio reward, call-to-action)

IMPORTANT: Text overlay (video_hook) and actual hook (intro_hook) are DIFFERENT:
- Text overlay = what appears as text on screen (sometimes)
- Actual hook = the visual/audio element that grabs attention (always)

ACTION SCENES:
- Each scene must be DETAILED with specific actions, expressions, timing
- Include: What the person does, how they move, facial expressions, timing
- Example: "Person looks confused, then realization hits, points at camera with 'aha!' expression, holds for 2 seconds"
- NOT generic like "Scene 1" - be specific about the actual content

SCRIPT GUIDANCE RULES:
- TALKING videos: Always include detailed script content - SINGLE SHOT, DIRECT TO CAMERA (like realcarlyjane/realmarciereeves), NO storylines, NO cringe content
- SKIT videos: Include script if it's a talking skit, empty if it's visual comedy
- FAKE PODCAST: Always include script content
- PRANK videos: Always include script content  
- CANDID INTERACTION: Include script if there's talking, empty if it's just actions
- THIRST TRAP: Always empty (no script/voiceover)

IMPORTANT VIDEO TYPE RULES:
- TALKING videos: Model talks DIRECTLY TO CAMERA, single continuous shot, no cuts, no storylines, no boyfriend mentions, authentic direct communication
- SKIT videos: Can be visual comedy or talking skits, include appropriate script content
- AVOID: Excessive boyfriend mentions, cringe storylines, overly complex narratives

Return ONLY JSON array with {n} complete templates."""

    user = f"""
Persona: {persona}
Content Type: {content_type} | Video Type: {video_type}
Tone: {tone}
Boundaries: {boundaries}

Reference examples (use for style inspiration):
{chr(10).join(f"- {r}" for r in refs[:4])}

Create {n} COMPLETELY DIFFERENT video planning templates. Each must be:

HOOKS - Be SPECIFIC and DETAILED:
- video_hook: TEXT OVERLAY on screen (POV scenario, caption, or empty if no text needed)
- intro_hook: ACTUAL HOOK - VISUAL/AUDIO attention-grabber for first 0.3 seconds (camera shake, boobs shaking, unique angle, weird audio, voice cadence change)
- outro_hook: REWARD for watching - satisfying conclusion (visual payoff, audio reward, call-to-action)

REMEMBER: Text overlay and actual hook are DIFFERENT things!

ACTION SCENES - Be DETAILED with specific actions:
- Include: exact movements, facial expressions, timing, camera interactions
- Example: "Person looks confused for 1 second, then realization hits, points at camera with 'aha!' expression, holds for 2 seconds"
- NOT generic like "Scene 1" - describe the actual specific content

SCRIPT GUIDANCE:
- TALKING videos: SINGLE SHOT, DIRECT TO CAMERA, NO storylines, NO boyfriend mentions, authentic direct communication
- SKIT videos: Include script if talking, empty if visual comedy
- Other types: Appropriate based on video type

PRODUCTION DETAILS:
- Detailed storyboard_notes with specific locations, wardrobe, shot types
- Professional shot list with specific camera angles and movements

AVOID: Excessive boyfriend mentions, cringe storylines, overly complex narratives

JSON array ONLY.
"""

    # Use consistent temperature for template generation
    temperature = 0.8
    
    try:
        out = chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ], temperature=temperature)
        
        # Extract JSON
        start = out.find("[")
        end = out.rfind("]")
        if start >= 0 and end > start:
            json_str = out[start:end+1]
            print(f"🔍 Raw JSON output: {json_str[:200]}...")
            try:
                templates = json.loads(json_str)
                print(f"✨ Generated {len(templates)} video templates for {video_type}")
                return templates[:n]
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"🔍 Problematic JSON: {json_str}")
                return []
        else:
            print(f"❌ Failed to find JSON array in output")
            print(f"🔍 Raw output: {out[:200]}...")
            return []
            
    except Exception as e:
        print(f"❌ Template generation failed: {e}")
        return []

def generate_scripts(persona, boundaries, content_type, tone, refs, n=6):
    # Determine content style based on boundaries and tone
    is_spicy = "spicy" in boundaries.lower() or "adult" in boundaries.lower() or "explicit" in boundaries.lower() or "bold" in boundaries.lower()
    is_funny = "funny" in tone.lower() or "comedy" in tone.lower() or "humor" in tone.lower() or "witty" in tone.lower()
    is_creative = "creative" in tone.lower() or "artistic" in tone.lower() or "unique" in tone.lower()
    
    if is_spicy and is_funny:
        system = (
            "You are a creative adult content writer specializing in funny, sexy, and entertaining scenarios. "
            "Create engaging content that combines humor, creativity, and sexual themes in a fun and playful way. "
            "Use clever wordplay, funny situations, and creative sexual scenarios that make people laugh while being turned on. "
            "Focus on humor, creativity, and sexual content that's entertaining and memorable. "
            "Use creative language, funny metaphors, and explore themes of desire, humor, and human connection. "
            "AUTHENTICITY RULES: Sound like a real person, not a copywriter. Use natural language, avoid corporate speak, "
            "and make it feel like authentic social media content. Subtext > explicitness - be suggestive, not obvious. "
            "Return ONLY JSON: an array of length N, each with {title,hook,beats,voiceover,caption,hashtags,cta}."
        )
    elif is_spicy:
        system = (
            "You are a creative adult content writer specializing in sexy, creative, and engaging scenarios. "
            "Create content that is explicit, creative, and entertaining. Focus on sexual themes, desire, and human connection. "
            "Use creative language, interesting scenarios, and explore themes of intimacy and passion. "
            "Make it sexy, creative, and engaging without being crude or vulgar. "
            "AUTHENTICITY RULES: Sound like a real person, not a copywriter. Use natural language, avoid corporate speak, "
            "and make it feel like authentic social media content. Subtext > explicitness - be suggestive, not obvious. "
            "Return ONLY JSON: an array of length N, each with {title,hook,beats,voiceover,caption,hashtags,cta}."
        )
    elif is_funny:
        system = (
            "You are a creative content writer specializing in funny, entertaining, and engaging content. "
            "Create content that is hilarious, creative, and memorable. Focus on humor, wit, and entertaining storytelling. "
            "Use clever wordplay, funny situations, and creative scenarios that make people laugh. "
            "Avoid clichés and generic content - instead create unique, funny, and engaging scenarios. "
            "AUTHENTICITY RULES: Sound like a real person, not a copywriter. Use natural language, avoid corporate speak, "
            "and make it feel like authentic social media content. Focus on entertainment first, not selling. "
            "Return ONLY JSON: an array of length N, each with {title,hook,beats,voiceover,caption,hashtags,cta}."
        )
    else:
        system = (
            "You are a creative content writer specializing in engaging, creative, and entertaining content. "
            "Create content that is fresh, original, and avoids clichés. Focus on creativity, humor, and engaging storytelling. "
            "Use creative language, unique perspectives, and explore interesting themes. "
            "Make it creative, entertaining, and memorable. "
            "AUTHENTICITY RULES: Sound like a real person, not a copywriter. Use natural language, avoid corporate speak, "
            "and make it feel like authentic social media content. Focus on entertainment first, not selling. "
            "Return ONLY JSON: an array of length N, each with {title,hook,beats,voiceover,caption,hashtags,cta}."
        )
    
    user = f"""
Persona: {persona}
Boundaries: {boundaries}
Content type: {content_type} | Tone: {tone} | Duration: 15–25s

Reference snippets (inspire, don't copy - use for style and approach):
{chr(10).join(f"- {r}" for r in refs)}

Create {n} COMPLETELY DIFFERENT, unique, creative, and engaging scripts. Each script must be:
- TOTALLY UNIQUE from the others (different scenarios, hooks, approaches)
- Creative and entertaining storytelling
- Humor and wit
- Sexual themes and desire (if appropriate)
- Unique perspectives and fresh ideas
- Engaging and memorable scenarios
- Avoiding clichés and generic content
- VARIED in style, tone, and approach
- BODY-FOCUSED: Include tasteful references to the model's physical features and attractiveness
- PHYSICAL APPEAL: Use body language, curves, and physical comedy as central elements
- VISUAL ENGAGEMENT: Create scenarios that showcase the model's figure in engaging ways
- NO RELATIONSHIP CONTENT: Avoid boyfriend, girlfriend, partner, dating scenarios
- SOLO FOCUS: Model alone, interacting with objects, situations, or audience directly
- FORBIDDEN WORDS: "we", "us", "together", "couple", "partner", "boyfriend", "girlfriend"
- REQUIRED LANGUAGE: Use "I", "me", "my", "myself", "alone", "solo" instead

HOOK STRATEGIES (rotate these formats):
- POV scenarios: "POV: you just subscribed and I notice your name..."
- Reverse bait: Start wholesome, add unexpected twist
- Question hooks: Ask something irresistible to answer
- Challenge/Trend hijack: Use trending formats with suggestive context
- Storytelling tease: Short narrative with cliffhanger

SOLO CONTENT EXAMPLES (avoid relationship themes):
- Lifestyle scenarios: getting ready, working out, cooking, shopping
- Challenge content: trying trends, reactions, transformations
- POV scenarios: talking directly to audience, sharing thoughts
- Object interactions: playing with props, trying products, demonstrating things
- Situational comedy: awkward moments, funny observations, relatable experiences

IMPORTANT: Make each script completely different from the others. Use different:
- Opening hooks and scenarios
- Story structures and beats
- Voice tones and styles
- Creative approaches and angles
- Hook formats (POV, question, reverse bait, etc.)

CRITICAL LANGUAGE RULES:
- NEVER use "we", "us", "together", "couple", "partner", "boyfriend", "girlfriend"
- ALWAYS use "I", "me", "my", "myself", "alone", "solo" instead
- Focus on the model as a solo individual, not part of a relationship

N = {n}
JSON array ONLY.
"""
    # Use more varied temperature for maximum diversity
    import random
    import time
    random.seed(int(time.time() * 1000) % 10000)  # Use current time as seed
    temperature = 0.8 + random.uniform(0.0, 0.4)  # Random between 0.8 and 1.2
    out = chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=temperature)
    # Be lenient if model wraps JSON with text
    start = out.find("[")
    end = out.rfind("]")
    return json.loads(out[start:end+1])

def revise_for(prompt_label, draft: dict, guidance: str):
    system = f"You revise scripts to {prompt_label}. Keep intent; return ONLY JSON with the same schema."
    user = json.dumps({"draft": draft, "guidance": guidance})
    out = chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0.6)
    start = out.find("{")
    end = out.rfind("}")
    return json.loads(out[start:end+1])

def selective_rewrite(draft: dict, field: str, snippet: str, prompt: str):
    system = "You rewrite only the targeted snippet inside the specified field. Keep style. Return ONLY JSON."
    user = json.dumps({"field": field, "snippet": snippet, "prompt": prompt, "draft": draft})
    out = chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0.7)
    start = out.find("{")
    end = out.rfind("}")
    return json.loads(out[start:end+1])
