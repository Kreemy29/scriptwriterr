# 🚀 Deploy AI Script Studio to Streamlit Cloud

## Quick Deploy Guide

### 📋 Prerequisites
1. **DeepSeek API Key** - Get free at: https://platform.deepseek.com/api_keys
2. **GitHub Account** - To store your code
3. **Streamlit Cloud Account** - Free at: https://share.streamlit.io

### 🔧 Step 1: Upload to GitHub

1. **Create new GitHub repository**:
   - Go to github.com → New repository
   - Name: `ai-script-studio` (or your choice)
   - Make it **Public** (required for free Streamlit Cloud)

2. **Upload your files**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ai-script-studio.git
   git push -u origin main
   ```

   **OR drag & drop files directly on GitHub:**
   - Go to your new repo
   - Click "uploading an existing file"
   - Drag all files from your project folder

### 🚀 Step 2: Deploy on Streamlit Cloud

1. **Go to Streamlit Cloud**: https://share.streamlit.io
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Fill in**:
   - Repository: `YOUR_USERNAME/ai-script-studio`
   - Branch: `main`
   - Main file path: `app.py`
5. **Click "Deploy"** 🎉

### 🔑 Step 3: Add Your API Key

1. **In Streamlit Cloud**, go to your app
2. **Click the ⚙️ Settings** button (bottom right)
3. **Go to "Secrets"** tab
4. **Add this text**:
   ```toml
   DEEPSEEK_API_KEY = "your_actual_api_key_here"
   ```
5. **Click "Save"**

### ✅ That's It!

Your app will be live at: `https://YOUR_USERNAME-ai-script-studio-app-xyz123.streamlit.app`

## 🛠️ Troubleshooting

**Problem**: App shows API key error
- **Solution**: Check your secrets.toml format and save

**Problem**: Import errors
- **Solution**: Check requirements.txt has all dependencies

**Problem**: Database issues
- **Solution**: App auto-creates database on first run

## 🔄 Updates

When you make changes:
1. **Push to GitHub** (git commit & push)
2. **Streamlit Cloud auto-updates** in ~30 seconds

## 💡 Pro Tips

- **Custom domain**: Available with Streamlit Cloud Pro
- **Password protection**: Use Streamlit Cloud Pro features
- **Analytics**: Check your app usage in Streamlit Cloud dashboard
- **Sharing**: Send your live URL to anyone!

---

🎬 **Your AI Script Studio is now live for the world to use!** ✨
