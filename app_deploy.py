import os, streamlit as st
from dotenv import load_dotenv
from sqlmodel import select
from db import init_db, get_session, add_rating
from models import Script, Revision
from deepseek_client import generate_scripts, revise_for, selective_rewrite
import time

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="🎬 AI Script Studio", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def script_to_json_dict(script):
    """Convert script to JSON-serializable dictionary"""
    data = script.model_dump()
    # Remove datetime fields that cause JSON serialization issues
    data.pop('created_at', None)
    data.pop('updated_at', None)
    return data

# Load environment - works both locally and on Streamlit Cloud
load_dotenv()

# Initialize database with error handling
try:
    init_db()
    db_initialized = True
except Exception as e:
    st.error(f"Database initialization failed: {e}")
    db_initialized = False

# Check for API key in Streamlit secrets or environment
api_key = st.secrets.get("DEEPSEEK_API_KEY") if hasattr(st, 'secrets') and "DEEPSEEK_API_KEY" in st.secrets else os.getenv("DEEPSEEK_API_KEY")

# DEBUG INFO - remove after fixing
if hasattr(st, 'secrets'):
    st.sidebar.write("🔍 DEBUG: Secrets available")
    if "DEEPSEEK_API_KEY" in st.secrets:
        st.sidebar.write("✅ DEEPSEEK_API_KEY found in secrets")
        st.sidebar.write(f"🔑 Key length: {len(st.secrets['DEEPSEEK_API_KEY'])}")
        st.sidebar.write(f"🔑 Key starts with: {st.secrets['DEEPSEEK_API_KEY'][:10]}...")
    else:
        st.sidebar.write("❌ DEEPSEEK_API_KEY NOT in secrets")
        st.sidebar.write(f"Available secrets: {list(st.secrets.keys())}")
else:
    st.sidebar.write("❌ No secrets available")

if not api_key:
    st.error("🔑 **DeepSeek API Key Required**")
    st.markdown("""
    **For Local Development:**
    - Create a `.env` file and add: `DEEPSEEK_API_KEY=your_key_here`
    
    **For Streamlit Cloud:**
    - Go to your app settings → Secrets
    - Add: `DEEPSEEK_API_KEY = "your_key_here"`
    
    Get your free API key at: https://platform.deepseek.com/api_keys
    """)
    st.stop()
else:
    st.sidebar.write("✅ API key loaded successfully")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .step-container {
        border: 2px solid #e1e1e1;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
    }
    .draft-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 0.5rem;
        background: white;
        transition: all 0.2s ease;
    }
    .draft-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎬 AI Script Studio</h1>
    <p>Generate Instagram-ready scripts with AI • Powered by DeepSeek</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'generation_step' not in st.session_state:
    st.session_state.generation_step = 'setup'
if 'generated_count' not in st.session_state:
    st.session_state.generated_count = 0

# Sidebar - Generation Controls
with st.sidebar:
    st.header("🎯 Script Generation")
    
    # Step 1: Basic Settings
    with st.expander("📝 Step 1: Basic Settings", expanded=True):
        # Simplified creator selection for deployment
        creator = st.selectbox(
            "Creator Name",
            ["Anya", "Emily", "Ava", "Sophie", "Zoe"],
            help="Select the creator persona for script generation"
        )
        
        content_type = st.selectbox(
            "Content Type",
            ["thirst-trap", "lifestyle", "comedy", "prank", "trend-adaptation"],
            help="Choose the type of content to generate"
        )
        
        tone_options = ["playful", "confident", "flirty", "comedic", "wholesome"]
        selected_tones = st.multiselect(
            "Tone/Vibe (select multiple)",
            tone_options,
            default=["playful"],
            help="Select the mood and tone for your scripts"
        )
        
        num_drafts = st.slider(
            "Number of drafts",
            min_value=1,
            max_value=10,
            value=3,
            help="How many script variations to generate"
        )
    
    # Step 2: Advanced Options (Simplified for deployment)
    with st.expander("⚙️ Step 2: Advanced Options"):
        hook_style = st.selectbox(
            "Hook Style",
            ["Auto", "Question", "Statement", "Tease", "Story"],
            help="Style of opening hook"
        )
        
        length = st.selectbox(
            "Target Length",
            ["Auto", "Short (15-30s)", "Medium (30-60s)", "Long (60s+)"],
            help="Preferred video length"
        )
        
        retention = st.selectbox(
            "Retention Strategy",
            ["Auto", "Quick Hook", "Story Arc", "Visual Tease", "Trending"],
            help="Strategy to keep viewers watching"
        )
    
    # Manual References (Simplified)
    with st.expander("📚 Step 3: Reference Examples"):
        st.write("Add your own reference examples (optional):")
        refs_text = st.text_area(
            "Reference Examples",
            placeholder="Enter example hooks, captions, or scripts...\nOne per line",
            height=100,
            help="Provide examples of the style you want"
        )
    
    # Generation Button
    if not db_initialized:
        st.error("⚠️ Database not available - using simplified mode")
        st.info("Some features may be limited in deployment mode")
    
    generate_button = st.button(
        "🚀 Generate Scripts", 
        type="primary",
        use_container_width=True
    )

# Main Content Area
if generate_button:
    if not api_key:
        st.error("Please configure your DeepSeek API key first!")
    else:
        with st.spinner("🧠 AI is creating your scripts..."):
            try:
                # Simplified generation without RAG for deployment
                tone_str = ", ".join(selected_tones) if selected_tones else "playful"
                
                # Build prompt
                prompt = f"""
Generate {num_drafts} Instagram script variations for:
- Creator: {creator}
- Content Type: {content_type}
- Tone: {tone_str}
- Hook Style: {hook_style}
- Length: {length}
- Retention: {retention}

Format each script as JSON with: title, hook, beats (array), caption, hashtags (array), cta
Make each script unique and engaging for Instagram Reels.
"""
                
                if refs_text.strip():
                    prompt += f"\nReference examples:\n{refs_text}"
                
                # Generate scripts using simple method
                scripts_data = generate_scripts(prompt, num_drafts)
                
                if scripts_data:
                    st.success(f"✅ Generated {len(scripts_data)} scripts!")
                    
                    # Display scripts
                    for i, script_data in enumerate(scripts_data, 1):
                        with st.expander(f"📝 Script {i}: {script_data.get('title', 'Untitled')}", expanded=True):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write("**Hook:**")
                                st.write(script_data.get('hook', 'No hook provided'))
                                
                                st.write("**Beats:**")
                                beats = script_data.get('beats', [])
                                if beats:
                                    for beat in beats:
                                        st.write(f"• {beat}")
                                else:
                                    st.write("No beats provided")
                                
                                st.write("**Caption:**")
                                st.write(script_data.get('caption', 'No caption provided'))
                            
                            with col2:
                                st.write("**Hashtags:**")
                                hashtags = script_data.get('hashtags', [])
                                if hashtags:
                                    hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                                    st.write(hashtag_text)
                                else:
                                    st.write("No hashtags provided")
                                
                                st.write("**CTA:**")
                                st.write(script_data.get('cta', 'No CTA provided'))
                                
                                # Simple rating system
                                st.write("**Rate this script:**")
                                rating = st.slider(f"Quality (1-5)", 1, 5, 3, key=f"rating_{i}")
                                
                                if st.button(f"Save Rating", key=f"save_{i}"):
                                    st.success(f"Rated {rating}/5 - Thank you for feedback!")
                else:
                    st.error("Failed to generate scripts. Please try again.")
                    
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
                st.write("This might be due to API limits or network issues. Please try again.")

else:
    # Welcome message
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>Ready to Create Amazing Scripts?</h2>
        <p style="font-size: 1.2rem; color: #666;">
            👈 Use the sidebar to generate your first batch of AI scripts<br>
            🤖 The AI will create engaging Instagram content<br>
            ✨ Then review and perfect your scripts here
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 10px;">
        <p><strong>AI Script Studio</strong> • Built with Streamlit & DeepSeek AI</p>
        <p><em>Tip: Generate scripts in batches, then refine with AI tools for best results.</em></p>
    </div>
    """, unsafe_allow_html=True)
