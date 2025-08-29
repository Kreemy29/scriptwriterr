import os, requests, json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Get API key from Streamlit secrets or environment
def get_api_key():
    if hasattr(st, 'secrets') and "DEEPSEEK_API_KEY" in st.secrets:
        return st.secrets["DEEPSEEK_API_KEY"]
    return os.getenv("DEEPSEEK_API_KEY")

DEEPSEEK_API_KEY = get_api_key()
BASE = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

def chat(messages, model="deepseek-chat", temperature=0.9):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature}
    r = requests.post(f"{BASE}/chat/completions", headers=headers, data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def generate_scripts(persona, boundaries, content_type, tone, refs, n=6):
    system = (
        "You write Instagram-compliant, suggestive-but-not-explicit Reels briefs. "
        "Use tight hooks, concrete visual beats, clear CTAs. Avoid explicit sexual terms. "
        "Return ONLY JSON: an array of length N, each with {title,hook,beats,voiceover,caption,hashtags,cta}."
    )
    user = f"""
Persona: {persona}
Boundaries: {boundaries}
Content type: {content_type} | Tone: {tone} | Duration: 15–25s
Reference snippets (inspire, don't copy):
{chr(10).join(f"- {r}" for r in refs)}

N = {n}
JSON array ONLY.
"""
    out = chat([{"role":"system","content":system},{"role":"user","content":user}])
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
