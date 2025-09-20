import os, requests, json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Get API key from Streamlit secrets or environment
def get_api_key():
    try:
        if hasattr(st, 'secrets') and "DEEPSEEK_API_KEY" in st.secrets:
            return st.secrets["DEEPSEEK_API_KEY"]
    except:
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
    r = requests.post(f"{BASE}/chat/completions", headers=headers, data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

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

HOOK STRATEGIES (rotate these formats):
- POV scenarios: "POV: you just subscribed and I notice your name..."
- Reverse bait: Start wholesome, add unexpected twist
- Question hooks: Ask something irresistible to answer
- Challenge/Trend hijack: Use trending formats with suggestive context
- Storytelling tease: Short narrative with cliffhanger

IMPORTANT: Make each script completely different from the others. Use different:
- Opening hooks and scenarios
- Story structures and beats
- Voice tones and styles
- Creative approaches and angles
- Hook formats (POV, question, reverse bait, etc.)

N = {n}
JSON array ONLY.
"""
    # Use slightly varied temperature for more diversity
    import random
    temperature = 0.9 + random.uniform(-0.1, 0.1)  # Random between 0.8 and 1.0
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
