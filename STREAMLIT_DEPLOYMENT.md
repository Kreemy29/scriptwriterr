# 🚀 AI Script Studio - Streamlit Cloud Deployment Guide

## Quick Start (5-Minute Deploy)

### Prerequisites
- GitHub account
- DeepSeek API key ([Get free key](https://platform.deepseek.com/api_keys))

### 1. Push to GitHub
```bash
git add .
git commit -m "Deploy AI Script Studio to Streamlit Cloud"
git push origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set **Main file path**: `app.py`
6. Click "Advanced settings"
7. Add in **Secrets**:
```toml
DEEPSEEK_API_KEY = "your_actual_api_key_here"
```
8. Click "Deploy!"

### 3. Your App is Live! 🎉
- URL: `https://your-app-name.streamlit.app`
- Updates automatically when you push to GitHub
- Runs 24/7 for free

---

## Platform Options

### 🥇 Streamlit Cloud (Recommended - FREE)
**Best for**: Free hosting, automatic deployments, optimized for Streamlit

**Pros:**
- ✅ Completely free
- ✅ Automatic GitHub deployments
- ✅ Built-in secrets management
- ✅ Custom domains available
- ✅ Optimized for Streamlit apps

**Setup:**
1. Push code to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add `DEEPSEEK_API_KEY` in secrets
4. Deploy!

**Configuration:**
- Main file: `app.py`
- Requirements: `requirements_streamlit.txt`
- Python version: 3.11

---

### 🥈 Railway ($5/month)
**Best for**: Custom domains, more control, faster builds

**Pros:**
- ✅ Fast deployment
- ✅ Custom domains included
- ✅ More compute resources
- ✅ Database persistence

**Setup:**
1. Connect GitHub at [railway.app](https://railway.app)
2. Add environment variable: `DEEPSEEK_API_KEY`
3. Deploy automatically

**Configuration:**
```bash
# Build Command (auto-detected)
pip install -r requirements_streamlit.txt

# Start Command
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

### 🥉 Render (Free tier available)
**Best for**: Free alternative with good performance

**Setup:**
1. Connect GitHub at [render.com](https://render.com)
2. Create new "Web Service"
3. Build Command: `pip install -r requirements_streamlit.txt`
4. Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. Add environment variable: `DEEPSEEK_API_KEY`

---

## Environment Variables

### Required
```bash
DEEPSEEK_API_KEY=your_api_key_here
```

### Optional
```bash
DB_URL=sqlite:///production.db  # Custom database location
```

---

## Database Configuration

The app uses SQLite by default, which works perfectly for cloud deployment:

- **Local**: `studio.db` in project root
- **Cloud**: Persistent SQLite file in app directory
- **Scaling**: Can easily switch to PostgreSQL with `DB_URL` env var

### For High Traffic (Optional)
```bash
# PostgreSQL example
DB_URL=postgresql://user:pass@host:5432/dbname

# MySQL example  
DB_URL=mysql://user:pass@host:3306/dbname
```

---

## Performance Optimization

### Memory Usage
- Uses CPU-only PyTorch for smaller footprint
- Optimized sentence-transformers for cloud deployment
- Efficient SQLite database with proper indexing

### Loading Speed
- Lazy imports for faster startup
- Cached model loading
- Optimized requirements for cloud deployment

---

## Troubleshooting

### Common Issues

**1. "Module not found" errors**
- Solution: Use `requirements_streamlit.txt` instead of `requirements.txt`
- This file is optimized for cloud deployment

**2. "API key not found"**
- Solution: Add `DEEPSEEK_API_KEY` in your platform's secrets/environment variables
- Don't commit API keys to GitHub

**3. "Database errors"**
- Solution: The app automatically creates SQLite database on first run
- Database persists between deployments on all platforms

**4. "Memory limit exceeded"**
- Solution: The app is optimized for 1GB RAM limit
- Uses CPU-only models to reduce memory usage

### Performance Tips

1. **Use the optimized requirements file:**
   ```bash
   # Use this for deployment
   requirements_streamlit.txt
   
   # Not this (too heavy for cloud)
   requirements.txt
   ```

2. **Enable caching:**
   - App uses Streamlit's built-in caching
   - Models are cached after first load
   - Database queries are optimized

3. **Monitor usage:**
   - Streamlit Cloud shows app analytics
   - Monitor memory and CPU usage
   - Optimize if needed

---

## Security Best Practices

### API Key Security
- ✅ Store API keys in platform secrets (never in code)
- ✅ Use environment variables
- ✅ Don't commit `.streamlit/secrets.toml` to Git

### Database Security
- ✅ SQLite is secure for single-user apps
- ✅ No external database connections needed
- ✅ Data stays within your app instance

---

## Advanced Configuration

### Custom Domain Setup

**Streamlit Cloud:**
1. Go to app settings
2. Add custom domain
3. Update DNS CNAME record
4. SSL automatically configured

**Railway/Render:**
1. Add domain in project settings
2. Update DNS records as instructed
3. SSL automatically configured

### Scaling Considerations

**Single User (Current Setup):**
- SQLite database
- Local file storage
- Perfect for personal use

**Multi User (Future):**
- Add PostgreSQL database
- Add Redis for caching
- Add user authentication

---

## Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] DeepSeek API key obtained
- [ ] Platform account created (Streamlit Cloud recommended)
- [ ] Repository connected to platform
- [ ] API key added to secrets/environment variables
- [ ] App deployed successfully
- [ ] Database initialized (happens automatically)
- [ ] Basic functionality tested

---

## Support

### Getting Help
- Check Streamlit Cloud logs for deployment issues
- Verify API key is correctly set in secrets
- Ensure `requirements_streamlit.txt` is used for deployment

### Updates
- Push to GitHub to automatically update deployed app
- No downtime during updates
- Database persists through updates

---

**🎬 Your AI Script Studio is now ready for the world!**

Share your app URL with anyone - it runs 24/7 and handles multiple users simultaneously.
