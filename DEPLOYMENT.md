# 🚀 Deployment Guide - AI Script Studio

## Option 1: Streamlit Cloud (Recommended - Free)

### Step 1: Push to GitHub
1. Create a new repository on GitHub
2. Push your code:
```bash
git init
git add .
git commit -m "Initial commit - AI Script Studio"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository
5. Set main file path: `src/app.py`
6. Add your DeepSeek API key in the secrets section:
```
DEEPSEEK_API_KEY = "your_actual_api_key_here"
```
7. Click "Deploy"

### Step 3: Your App is Live!
- Your app will be available at: `https://YOUR_APP_NAME.streamlit.app`
- It runs 24/7, even when your PC is offline
- Updates automatically when you push to GitHub

## Option 2: Railway (Easy - $5/month)

### Step 1: Connect GitHub
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository

### Step 2: Configure
1. Railway will auto-detect it's a Python app
2. Add environment variable: `DEEPSEEK_API_KEY=your_key_here`
3. Railway will automatically deploy

### Step 3: Custom Domain (Optional)
1. Go to your project settings
2. Add a custom domain
3. Your app will be available at your custom URL

## Option 3: Render (Free tier)

### Step 1: Connect GitHub
1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click "New" → "Web Service"
4. Connect your repository

### Step 2: Configure
1. Build Command: `pip install -r requirements.txt`
2. Start Command: `streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0`
3. Add environment variable: `DEEPSEEK_API_KEY=your_key_here`

## Environment Variables

All platforms need this environment variable:
```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

Get your free API key at: https://platform.deepseek.com/api_keys

## Benefits of Cloud Deployment

✅ **Always Online** - Runs 24/7, even when your PC is off
✅ **Public Access** - Share with anyone, anywhere
✅ **Automatic Updates** - Deploy new features instantly
✅ **No Local Setup** - Works on any device with internet
✅ **Custom Domain** - Professional URL
✅ **Scalable** - Handles multiple users

## Recommended: Streamlit Cloud

**Why Streamlit Cloud is best:**
- ✅ Completely free
- ✅ Optimized for Streamlit apps
- ✅ Easy GitHub integration
- ✅ Automatic deployments
- ✅ Built-in secrets management
- ✅ Custom domain support
