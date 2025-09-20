# 🚀 Hugging Face Spaces Deployment Checklist

## ✅ Files to Upload

### Core Application Files:
- [ ] `app.py` - Main Streamlit application
- [ ] `requirements.txt` - Python dependencies
- [ ] `README.md` - Space configuration
- [ ] `packages.txt` - System packages (ffmpeg only)
- [ ] `.gitignore` - Hide sensitive files

### Python Modules:
- [ ] `models.py` - Database models
- [ ] `db.py` - Database functions
- [ ] `deepseek_client.py` - AI client
- [ ] `rag_integration.py` - RAG system
- [ ] `rag_retrieval.py` - Retrieval functions
- [ ] `auto_scorer.py` - Auto-scoring system
- [ ] `bandit_learner.py` - Learning system
- [ ] `compliance.py` - Compliance checking

## ❌ Files to EXCLUDE (Don't Upload):
- [ ] `.streamlit/secrets.toml` - Contains API key
- [ ] `.env` - Environment variables
- [ ] `*.db` - Database files
- [ ] `__pycache__/` - Python cache
- [ ] `studio.db` - Local database

## 🔑 After Upload:
1. Go to Space Settings
2. Add Repository Secret: `DEEPSEEK_API_KEY`
3. Set value to your actual API key
4. Save and restart the space

## 🎯 Expected Result:
- Full RAG system with multi-armed bandit learning
- Auto-scoring and rating system
- 83 scripts in database for reference
- All advanced features working
