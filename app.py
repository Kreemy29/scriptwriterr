import os, streamlit as st
from dotenv import load_dotenv
from sqlmodel import select
from db import init_db, get_session, add_rating
from models import Script, Revision
from deepseek_client import generate_scripts, revise_for, selective_rewrite
from rag_integration import generate_scripts_rag
from compliance import blob_from, score_script
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
init_db()

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
        # Clean creator dropdown - only show our 4 main creators
        creator_options = ["Emily Kent", "Marcie", "Mia", "General Content"]
        creator = st.selectbox(
            "Creator Name", 
            creator_options,
            help="Choose from existing creators or your imported scripts"
        )
        
        # Expanded content types
        content_type = st.selectbox(
            "Content Type", 
            ["thirst-trap", "skit", "reaction-prank", "talking-style", "lifestyle", "fake-podcast", "dance-trend", "voice-tease-asmr"],
            help="Choose the type of content you want to create"
        )
        
        # Multi-select tones
        tone_options = ["naughty", "playful", "suggestive", "funny", "flirty", "bratty", "teasing", "intimate", "witty", "comedic", "confident", "wholesome", "asmr-voice"]
        selected_tones = st.multiselect(
            "Tone/Vibe (select multiple)", 
            tone_options,
            default=["playful"],
            help="Choose one or more tones - scripts often blend 2-3 vibes"
        )
        tone = ", ".join(selected_tones) if selected_tones else "playful"
        
        n = st.slider(
            "Number of drafts", 
            min_value=1, 
            max_value=20, 
            value=6,
            help="How many script variations to generate"
        )
    
    # Step 2: Persona & Style
    with st.expander("👤 Step 2: Persona & Style", expanded=True):
        # Persona presets
        persona_presets = {
            "Girl-next-door": "girl-next-door; playful; witty; approachable",
            "Bratty tease": "bratty; teasing; demanding; playful attitude",
            "Dominant/In control": "confident; in control; commanding; assertive",
            "Innocent but suggestive": "innocent; sweet; accidentally suggestive; naive charm",
            "Party girl": "outgoing; fun; social; party vibes; energetic",
            "Gym fitspo": "fitness focused; motivational; athletic; body confident",
            "ASMR/Voice fetish": "soft spoken; intimate; soothing; sensual voice",
            "Girlfriend experience": "loving; intimate; caring; relationship vibes",
            "Funny meme-style": "comedic; meme references; internet culture; quirky",
            "Candid/Lifestyle": "authentic; relatable; everyday life; natural"
        }
        
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            persona_preset = st.selectbox(
                "Persona Preset", 
                ["Custom"] + list(persona_presets.keys()),
                help="Choose a preset or use custom"
            )
        
        with col2:
            if persona_preset != "Custom":
                if st.button("📋 Use Preset", use_container_width=True):
                    st.session_state.persona_text = persona_presets[persona_preset]
        
        persona = st.text_area(
            "Persona Description", 
            value=st.session_state.get('persona_text', "girl-next-door; playful; witty"),
            help="Describe the character/personality for the scripts"
        )
        
        # Compliance/Boundaries presets
        boundary_presets = {
            "Safe IG mode": "No explicit words; no sexual acts; suggestive only; no banned IG terms; keep it flirty but clean",
            "Spicy mode": "Innuendos allowed; suggestive language OK; no explicit acts; can be naughty but not graphic", 
            "Brand-safe": "No swearing; no sex references; just flirty and fun; wholesome with hint of tease",
            "Mild NSFW": "Moaning sounds OK; wet references allowed; squirt innuendo OK; suggestive but not explicit",
            "Platform optimized": "Avoid flagged keywords; use creative euphemisms; suggestive storytelling style"
        }
        
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            boundary_preset = st.selectbox(
                "Compliance Preset", 
                ["Custom"] + list(boundary_presets.keys()),
                help="Choose platform-appropriate safety rules"
            )
        
        with col2:
            if boundary_preset != "Custom":
                if st.button("🛡️ Use Preset", use_container_width=True):
                    st.session_state.boundaries_text = boundary_presets[boundary_preset]
        
        boundaries = st.text_area(
            "Content Boundaries", 
            value=st.session_state.get('boundaries_text', "No explicit words; no solicitation; no age refs"),
            help="What should the AI avoid? Set your safety guidelines here"
        )
    
    # Step 3: Advanced Options
    with st.expander("⚡ Step 3: Advanced Options", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Hook style
            hook_style = st.selectbox(
                "Hook Style",
                ["Auto", "Question", "Confession", "Contrarian", "PSA", "Tease", "Command", "Shock"],
                help="How should the hook start?"
            )
            
            # Length
            length = st.selectbox(
                "Target Length",
                ["Auto", "Short (5-7s)", "Medium (8-12s)", "Longer (13-20s)"],
                help="How long should the script be?"
            )
            
            # Risk level
            risk_level = st.slider(
                "Risk Level",
                min_value=1,
                max_value=5,
                value=3,
                help="1=Safe, 3=Suggestive, 5=Spicy"
            )
        
        with col2:
            # Retention gimmick
            retention = st.selectbox(
                "Retention Hook",
                ["Auto", "Twist ending", "Shock reveal", "Naughty payoff", "Innocent→dirty flip", "Cliffhanger"],
                help="How to keep viewers watching?"
            )
            
            # Shot type
            shot_type = st.selectbox(
                "Shot Type",
                ["Auto", "POV", "Selfie cam", "Tripod", "Over-the-shoulder", "Mirror shot"],
                help="Camera angle/perspective"
            )
            
            # Wardrobe
            wardrobe = st.selectbox(
                "Wardrobe/Setting",
                ["Auto", "Gym fit", "Bikini", "Bed outfit", "Towel", "Dress", "Casual", "Kitchen", "Car"],
                help="Setting or outfit context"
            )
    
    # Step 4: Optional References
    with st.expander("📚 Step 4: Extra References (Optional)", expanded=False):
        st.info("💡 The AI automatically uses your database references, but you can add more here")
        refs_text = st.text_area(
            "Additional Reference Lines", 
            value="",
            height=100,
            help="Add extra inspiration lines (one per line)"
        )
    
    # Generation Button
    st.markdown("---")
    
    # Show reference count
    from db import get_hybrid_refs
    
    # Map new content types to existing database types for compatibility
    content_type_mapping = {
        "thirst-trap": "talking_style / thirst_trap",
        "skit": "comedy",
        "reaction-prank": "prank", 
        "talking-style": "talking_style",
        "lifestyle": "lifestyle",
        "fake-podcast": "fake-podcast",
        "dance-trend": "trend-adaptation",
        "voice-tease-asmr": "talking_style"
    }
    
    mapped_content_type = content_type_mapping.get(content_type, content_type)
    ref_count = len(get_hybrid_refs("Emily", mapped_content_type, k=6))
    
    st.info(f"🤖 AI will use {ref_count} database references + your extras")
    
    generate_button = st.button(
        "🚀 Generate Scripts", 
        type="primary",
        use_container_width=True
    )
    
    # Generation Process
    if generate_button:
        with st.spinner("🧠 AI is creating your scripts..."):
            try:
                # Get manual refs from text area
                manual_refs = [x.strip() for x in refs_text.split("\n") if x.strip()]
                
                # Get automatic refs from Emily scripts in database using content type mapping
                auto_refs = get_hybrid_refs("Emily", mapped_content_type, k=6)
                
                # Combine both
                all_refs = manual_refs + auto_refs
                
                # Progress indicator
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔍 Analyzing references...")
                progress_bar.progress(25)
                time.sleep(0.5)
                
                status_text.text("🧠 RAG system selecting optimal references...")
                progress_bar.progress(40)
                time.sleep(0.3)
                
                status_text.text("✨ Generating enhanced content with AI learning...")
                progress_bar.progress(60)
                
                # Build enhanced prompt from advanced options
                advanced_prompt = ""
                if hook_style != "Auto":
                    advanced_prompt += f"Hook style: {hook_style}. "
                if length != "Auto":
                    advanced_prompt += f"Target length: {length}. "
                if retention != "Auto":
                    advanced_prompt += f"Retention strategy: {retention}. "
                if shot_type != "Auto":
                    advanced_prompt += f"Shot type: {shot_type}. "
                if wardrobe != "Auto":
                    advanced_prompt += f"Setting/wardrobe: {wardrobe}. "
                if risk_level != 3:
                    risk_desc = {1: "very safe", 2: "mild", 3: "suggestive", 4: "spicy", 5: "very spicy"}
                    advanced_prompt += f"Risk level: {risk_desc[risk_level]}. "
                
                # Enhance boundaries with advanced prompt
                enhanced_boundaries = boundaries
                if advanced_prompt:
                    enhanced_boundaries += f"\n\nADVANCED GUIDANCE: {advanced_prompt}"
                
                # Generate scripts with enhanced RAG system
                drafts = generate_scripts_rag(persona, enhanced_boundaries, content_type, tone, all_refs, n=n)
                
                progress_bar.progress(75)
                status_text.text("💾 Saving to database...")
                
                # Save to database
                with get_session() as ses:
                    for d in drafts:
                        lvl, _ = score_script(" ".join([d.get("title",""), d.get("hook",""), *d.get("beats",[]), d.get("voiceover",""), d.get("caption",""), d.get("cta","")]))
                        s = Script(
                            creator=creator, content_type=content_type, tone=tone,
                            title=d["title"], hook=d["hook"], beats=d["beats"],
                            voiceover=d["voiceover"], caption=d["caption"],
                            hashtags=d.get("hashtags",[]), cta=d.get("cta",""),
                            compliance=lvl, source="ai"
                        )
                        ses.add(s)
                    ses.commit()
                
                progress_bar.progress(100)
                status_text.text("")
                progress_bar.empty()
                
                st.session_state.generated_count += len(drafts)
                st.success(f"🎉 Generated {len(drafts)} scripts successfully!")
                
                # Show which refs were used and advanced options
                col1, col2 = st.columns(2)
                with col1:
                    if auto_refs:
                        st.markdown("**🤖 Hybrid refs used this run:**")
                        for line in auto_refs[:3]:  # Show first 3
                            st.write(f"• {line}")
                
                with col2:
                    if advanced_prompt:
                        st.markdown("**⚡ Advanced options applied:**")
                        st.write(f"• {advanced_prompt[:100]}...")
                    st.write(f"**📊 Settings:** {tone} • {content_type}")
                
                st.balloons()
                
                # Auto-refresh to show new drafts
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Generation failed: {str(e)}")
                st.write("💡 Try adjusting your parameters or check your API key")
    
    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("🗑️ Clear All", use_container_width=True, help="Delete all your generated scripts"):
            if st.session_state.get('confirm_clear'):
                with get_session() as ses:
                    scripts_to_delete = list(ses.exec(select(Script).where(Script.creator == creator, Script.source == "ai")))
                    for script in scripts_to_delete:
                        ses.delete(script)
                    ses.commit()
                st.success("🗑️ All drafts cleared!")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm deletion!")

# Main Area
tab1, tab2, tab3 = st.tabs(["📝 Draft Review", "🎯 Filters", "📊 Analytics"])

with tab1:
    # Load drafts
    with get_session() as ses:
        q = select(Script).where(Script.creator == creator, Script.source == "ai")
        all_drafts = list(ses.exec(q))
    
    if not all_drafts:
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <h3>🎬 Ready to Create Amazing Scripts?</h3>
            <p style="font-size: 1.2rem; color: #666;">
                👈 Use the sidebar to generate your first batch of AI scripts<br>
                🤖 The AI will learn from successful examples in the database<br>
                ✨ Then review, edit, and perfect your scripts here
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.generated_count > 0:
            st.info(f"🎉 You've generated {st.session_state.generated_count} scripts so far! Use filters to find them.")
    else:
        # Draft management
        col1, col2 = st.columns([0.4, 0.6], gap="large")
        
        with col1:
            st.subheader(f"📋 Your Drafts ({len(all_drafts)})")
            
            # Quick filters
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                compliance_filter = st.selectbox(
                    "Compliance", 
                    ["All", "PASS", "WARN", "FAIL"],
                    key="compliance_filter"
                )
            with filter_col2:
                sort_by = st.selectbox(
                    "Sort by", 
                    ["Newest", "Oldest", "Title"],
                    key="sort_filter"
                )
            
            # Apply filters
            filtered_drafts = all_drafts
            if compliance_filter != "All":
                filtered_drafts = [d for d in filtered_drafts if d.compliance.upper() == compliance_filter]
            
            # Apply sorting
            if sort_by == "Newest":
                filtered_drafts.sort(key=lambda x: x.created_at, reverse=True)
            elif sort_by == "Oldest":
                filtered_drafts.sort(key=lambda x: x.created_at)
            else:  # Title
                filtered_drafts.sort(key=lambda x: x.title)
            
            # Draft cards
            selected_id = st.session_state.get("selected_id")
            
            for draft in filtered_drafts:
                # Compliance color coding
                compliance_color = {
                    "pass": "🟢",
                    "warn": "🟡", 
                    "fail": "🔴"
                }.get(draft.compliance, "⚪")
                
                # Create card
                with st.container(border=True):
                    if st.button(
                        f"{compliance_color} {draft.title}",
                        key=f"select-{draft.id}",
                        use_container_width=True
                    ):
                        st.session_state["selected_id"] = draft.id
                        selected_id = draft.id
                    
                    st.caption(f"🎭 {draft.tone} • 📅 {draft.created_at.strftime('%m/%d %H:%M')}")
                    
                    # Preview hook
                    if draft.hook:
                        st.markdown(f"*{draft.hook[:80]}{'...' if len(draft.hook) > 80 else ''}*")
        
        with col2:
            st.subheader("✏️ Script Editor")
            
            if not filtered_drafts:
                st.info("No drafts match your filters. Try adjusting the filter settings.")
            else:
                # Auto-select first draft if none selected
                if not selected_id or selected_id not in [d.id for d in filtered_drafts]:
                    selected_id = filtered_drafts[0].id
                    st.session_state["selected_id"] = selected_id
                
                # Get current draft
                current = next((x for x in filtered_drafts if x.id == selected_id), filtered_drafts[0])
                
                # Editor tabs
                edit_tab1, edit_tab2, edit_tab3 = st.tabs(["📝 Edit", "🛠️ AI Tools", "📜 History"])
                
                with edit_tab1:
                    # Main editing fields
                    with st.form("edit_script"):
                        title = st.text_input("Title", value=current.title)
                        hook = st.text_area("Hook", value=current.hook or "", height=80)
                        beats_text = st.text_area("Beats (one per line)", value="\n".join(current.beats or []), height=120)
                        voiceover = st.text_area("Voiceover", value=current.voiceover or "", height=80)
                        caption = st.text_area("Caption", value=current.caption or "", height=100)
                        # Clean up hashtags display - remove commas, show as space-separated 
                        current_hashtags = current.hashtags or []
                        hashtags_display = " ".join(current_hashtags) if current_hashtags else ""
                        hashtags = st.text_input("Hashtags (space separated)", value=hashtags_display, help="Enter hashtags like: #gym #fitness #workout")
                        cta = st.text_input("Call to Action", value=current.cta or "")
                        
                        # Submit button
                        if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                            with get_session() as ses:
                                dbs = ses.get(Script, current.id)
                                dbs.title = title
                                dbs.hook = hook
                                dbs.beats = [x.strip() for x in beats_text.split("\n") if x.strip()]
                                dbs.voiceover = voiceover
                                dbs.caption = caption
                                # Parse hashtags from space-separated input
                                dbs.hashtags = [x.strip() for x in hashtags.split() if x.strip()]
                                dbs.cta = cta
                                
                                # Update compliance
                                lvl, _ = score_script(blob_from(dbs.model_dump()))
                                dbs.compliance = lvl
                                
                                ses.add(dbs)
                                ses.commit()
                            
                            st.success("✅ Script saved successfully!")
                            time.sleep(1)
                            st.rerun()
                    
                    # Rating widget
                    st.markdown("### Rate this script (feeds future generations)")
                    
                    # Show current ratings if any
                    if current.ratings_count > 0:
                        st.info(f"📊 Current ratings ({current.ratings_count} ratings): Overall: {current.score_overall:.1f}/5.0, Hook: {current.score_hook:.1f}/5.0, Originality: {current.score_originality:.1f}/5.0")
                    
                    with st.form("rate_script"):
                        colA, colB, colC, colD, colE = st.columns(5)
                        overall = colA.slider("Overall", 1.0, 5.0, 4.0, 0.5)
                        hook_s = colB.slider("Hook clarity", 1.0, 5.0, 4.0, 0.5)
                        orig_s = colC.slider("Originality", 1.0, 5.0, 4.0, 0.5)
                        fit_s  = colD.slider("Style fit", 1.0, 5.0, 4.0, 0.5)
                        safe_s = colE.slider("Safety", 1.0, 5.0, 4.0, 0.5)
                        notes  = st.text_input("Notes (optional)")
                        
                        if st.form_submit_button("💫 Save rating", type="secondary", use_container_width=True):
                            add_rating(
                                script_id=current.id,
                                overall=overall, hook=hook_s, originality=orig_s,
                                style_fit=fit_s, safety=safe_s, notes=notes, rater="human"
                            )
                            st.success("Rating saved. Future generations will weigh this higher.")
                            time.sleep(1)
                            st.rerun()
                
                with edit_tab2:
                    st.write("🤖 **AI-Powered Improvements**")
                    
                    # Quick AI actions
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🛡️ Make Safer", use_container_width=True):
                            with st.spinner("Making content safer..."):
                                revised = revise_for("be Instagram-compliant and safer", script_to_json_dict(current), "Remove risky phrases; keep intent and beat order.")
                                with get_session() as ses:
                                    dbs = ses.get(Script, current.id)
                                    before = dbs.caption
                                    dbs.caption = revised.get("caption", dbs.caption)
                                    lvl, _ = score_script(blob_from(revised))
                                    dbs.compliance = lvl
                                    ses.add(dbs)
                                    ses.commit()
                                    ses.add(Revision(script_id=dbs.id, label="Auto safer", field="caption", before=before, after=dbs.caption))
                                    ses.commit()
                                st.success("✅ Content made safer!")
                                st.rerun()
                        
                        if st.button("✨ More Playful", use_container_width=True):
                            with st.spinner("Adding playful vibes..."):
                                revised = revise_for("be more playful (keep safe)", script_to_json_dict(current), "Increase playful tone without adding risk.")
                                with get_session() as ses:
                                    dbs = ses.get(Script, current.id)
                                    before = dbs.hook
                                    dbs.hook = revised.get("hook", dbs.hook)
                                    ses.add(dbs)
                                    ses.commit()
                                    ses.add(Revision(script_id=dbs.id, label="More playful", field="hook", before=before, after=dbs.hook))
                                    ses.commit()
                                st.success("✨ Added playful energy!")
                                st.rerun()
                    
                    with col2:
                        if st.button("✂️ Shorter Hook", use_container_width=True):
                            with st.spinner("Tightening hook..."):
                                revised = revise_for("shorten the hook to <= 8 words", script_to_json_dict(current), "Shorten only the hook, keep intent.")
                                with get_session() as ses:
                                    dbs = ses.get(Script, current.id)
                                    before = dbs.hook
                                    dbs.hook = revised.get("hook", dbs.hook)
                                    ses.add(dbs)
                                    ses.commit()
                                    ses.add(Revision(script_id=dbs.id, label="Shorter hook", field="hook", before=before, after=dbs.hook))
                                    ses.commit()
                                st.success("✂️ Hook tightened!")
                                st.rerun()
                        
                        if st.button("🇬🇧 Localize (UK)", use_container_width=True):
                            with st.spinner("Localizing content..."):
                                revised = revise_for("localize to UK English", script_to_json_dict(current), "Adjust spelling/phrasing to UK without changing content.")
                                with get_session() as ses:
                                    dbs = ses.get(Script, current.id)
                                    before = dbs.caption
                                    dbs.caption = revised.get("caption", dbs.caption)
                                    ses.add(dbs)
                                    ses.commit()
                                    ses.add(Revision(script_id=dbs.id, label="Localize UK", field="caption", before=before, after=dbs.caption))
                                    ses.commit()
                                st.success("🇬🇧 Localized to UK!")
                                st.rerun()
                    
                    # Custom rewrite section
                    st.markdown("---")
                    st.write("🎯 **Custom Rewrite**")
                    
                    with st.form("custom_rewrite"):
                        rewrite_col1, rewrite_col2 = st.columns([0.6, 0.4])
                        
                        with rewrite_col1:
                            field = st.selectbox("Field to Edit", ["title","hook","voiceover","caption","cta","beats"])
                            snippet = st.text_input("Exact text you want to change")
                        
                        with rewrite_col2:
                            prompt = st.text_input("How to rewrite it")
                        
                        if st.form_submit_button("🪄 Rewrite", use_container_width=True):
                            if snippet and prompt:
                                with st.spinner("AI is rewriting..."):
                                    draft = script_to_json_dict(current)
                                    revised = selective_rewrite(draft, field, snippet, prompt)
                                    with get_session() as ses:
                                        dbs = ses.get(Script, current.id)
                                        before = getattr(dbs, field)
                                        setattr(dbs, field, revised.get(field, before))
                                        lvl, _ = score_script(blob_from(dbs.model_dump()))
                                        dbs.compliance = lvl
                                        ses.add(dbs)
                                        ses.commit()
                                        ses.add(Revision(script_id=dbs.id, label="Custom rewrite", field=field, before=str(before), after=str(getattr(dbs, field))))
                                        ses.commit()
                                    st.success("🪄 Rewrite complete!")
                                    st.rerun()
                            else:
                                st.error("Please fill in both the text and rewrite instructions")
                
                with edit_tab3:
                    st.write("📜 **Revision History**")
                    
                    with get_session() as ses:
                        revisions = list(ses.exec(
                            select(Revision).where(Revision.script_id==current.id).order_by(Revision.created_at.desc())
                        ))
                    
                    if not revisions:
                        st.info("No revisions yet. Make some changes to see the history!")
                    else:
                        for rev in revisions:
                            with st.expander(f"🔄 {rev.label} • {rev.field} • {rev.created_at.strftime('%m/%d %H:%M')}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Before:**")
                                    st.code(rev.before)
                                with col2:
                                    st.write("**After:**")
                                    st.code(rev.after)

with tab2:
    st.subheader("🎯 Advanced Filters & Search")
    
    # Advanced filtering interface
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        creator_filter = st.selectbox("Creator", ["All"] + ["Creator A", "Emily"])
        content_filter = st.selectbox("Content Type", ["All"] + ["thirst-trap", "lifestyle", "comedy", "prank", "fake-podcast", "trend-adaptation"])
    
    with filter_col2:
        compliance_filter_adv = st.selectbox("Compliance Status", ["All", "PASS", "WARN", "FAIL"])
        source_filter = st.selectbox("Source", ["All", "AI Generated", "Imported", "Manual"])
    
    with filter_col3:
        date_filter = st.selectbox("Date Range", ["All Time", "Today", "This Week", "This Month"])
        search_text = st.text_input("🔍 Search in titles/content")
    
    # Apply advanced filters and show results
    with get_session() as ses:
        query = select(Script)
        
        # Apply filters
        if creator_filter != "All":
            query = query.where(Script.creator == creator_filter)
        if content_filter != "All":
            query = query.where(Script.content_type == content_filter)
        if compliance_filter_adv != "All":
            query = query.where(Script.compliance == compliance_filter_adv.lower())
        
        filtered_results = list(ses.exec(query))
        
        # Search in text
        if search_text:
            filtered_results = [
                r for r in filtered_results 
                if search_text.lower() in r.title.lower() or 
                   search_text.lower() in (r.hook or "").lower() or
                   search_text.lower() in (r.caption or "").lower()
            ]
    
    st.write(f"**Found {len(filtered_results)} scripts**")
    
    # Display filtered results
    if filtered_results:
        for script in filtered_results[:10]:  # Show first 10
            with st.expander(f"{script.compliance.upper()} • {script.title} • {script.creator}"):
                st.write(f"**Hook:** {script.hook}")
                st.write(f"**Type:** {script.content_type} • **Tone:** {script.tone}")
                st.write(f"**Created:** {script.created_at.strftime('%Y-%m-%d %H:%M')}")

with tab3:
    st.subheader("📊 Script Analytics")
    
    # Get all scripts for analytics
    with get_session() as ses:
        all_scripts = list(ses.exec(select(Script)))
    
    if all_scripts:
        # Create metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Scripts", len(all_scripts))
        
        with col2:
            ai_generated = len([s for s in all_scripts if s.source == "ai"])
            st.metric("AI Generated", ai_generated)
        
        with col3:
            passed_compliance = len([s for s in all_scripts if s.compliance == "pass"])
            st.metric("Compliance PASS", passed_compliance)
        
        with col4:
            unique_creators = len(set(s.creator for s in all_scripts))
            st.metric("Creators", unique_creators)
        
        # Charts and insights
        st.markdown("### 📈 Content Insights")
        
        # Compliance distribution
        compliance_counts = {}
        for script in all_scripts:
            compliance_counts[script.compliance] = compliance_counts.get(script.compliance, 0) + 1
        
        if compliance_counts:
            st.bar_chart(compliance_counts)
        
        # Content type distribution
        type_counts = {}
        for script in all_scripts:
            type_counts[script.content_type] = type_counts.get(script.content_type, 0) + 1
        
        if type_counts:
            st.bar_chart(type_counts)
    
    else:
        st.info("📊 Generate some scripts to see analytics!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🎬 AI Script Studio • Built with Streamlit & DeepSeek AI<br>
    💡 Tip: Generate scripts in batches, then refine with AI tools for best results
</div>
""", unsafe_allow_html=True)