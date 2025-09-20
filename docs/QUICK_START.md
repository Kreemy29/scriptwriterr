# Quick Start Guide 🚀

Get your AI Script Studio up and running in minutes!

## Prerequisites
- Python 3.9+
- Git
- DeepSeek API key

## 1. Clone & Setup
```bash
git clone https://github.com/Kreemy29/scriptwriterr.git
cd scriptwriterr
pip install -r requirements.txt
```

## 2. Configure API Keys
```bash
# Create secrets file
mkdir -p .streamlit
cp examples/secrets.toml.example .streamlit/secrets.toml

# Edit with your API key
# Add your DeepSeek API key to .streamlit/secrets.toml
```

## 3. Initialize Database
```bash
python -c "from db import create_tables; create_tables()"
```

## 4. Run the App
```bash
streamlit run app.py
```

## 5. Access Your App
- Local: http://localhost:8501
- External: Use ngrok for public access

## First Steps
1. **Import Data**: Use the data import tools to add your reference scripts
2. **Configure Models**: Set up your creator profiles (Emily Kent, Marcie, Mia)
3. **Generate Scripts**: Start creating content with the AI
4. **Rate & Improve**: Provide feedback to enhance future generations

## Troubleshooting
- **Database Issues**: Delete `studio.db` and reinitialize
- **API Errors**: Check your DeepSeek API key in secrets.toml
- **Import Errors**: Ensure your JSON/JSONL files are properly formatted

## Need Help?
- Check the full documentation in `docs/`
- Review example configurations in `examples/`
- Open an issue on GitHub for support

Happy script writing! 🎬✨
