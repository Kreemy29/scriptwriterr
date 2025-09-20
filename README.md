# AI Script Studio 🎬

A powerful AI-powered script generation platform for creating engaging social media content with advanced RAG (Retrieval-Augmented Generation) capabilities.

## 🚀 Features

- **AI-Powered Script Generation**: Generate creative, spicy, and engaging scripts using DeepSeek AI
- **RAG System**: Advanced retrieval system that finds similar scripts to inspire new content
- **Model Profiles**: Support for multiple creator personas (Emily Kent, Marcie, Mia)
- **Content Types**: Generate various content types (thirst-trap, reaction-prank, skit, etc.)
- **Auto-Scoring**: LLM-based quality assessment of generated scripts
- **Multi-Armed Bandit Learning**: Optimizes generation policies based on feedback
- **Real-time Analytics**: Track script performance and compliance metrics

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kreemy29/scriptwriterr.git
   cd scriptwriterr
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp examples/secrets.toml.example .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml with your API keys
   ```

4. **Initialize database**
   ```bash
   python -c "from db import create_tables; create_tables()"
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 📁 Project Structure

```
scriptwriterr/
├── app.py                 # Main Streamlit application
├── rag_integration.py     # RAG system integration
├── rag_retrieval.py       # Script retrieval logic
├── data_hierarchy.py      # Data hierarchy management
├── models.py              # Database models
├── db.py                  # Database operations
├── deepseek_client.py     # DeepSeek API client
├── auto_scorer.py         # Auto-scoring system
├── bandit_learner.py      # Multi-armed bandit learning
├── compliance.py          # Content compliance checking
├── dataset_manager.py     # Dataset management
├── daily_maintenance.py   # Maintenance tasks
├── docs/                  # Documentation
├── examples/              # Example configurations
├── config/                # Configuration files
└── requirements.txt       # Python dependencies
```

## 🎯 Usage

### Basic Script Generation

1. **Select Creator**: Choose from Emily Kent, Marcie, Mia, or General Content
2. **Choose Content Type**: Select from thirst-trap, reaction-prank, skit, etc.
3. **Generate**: Click "Generate Scripts" to create new content
4. **Rate**: Provide feedback to improve future generations

### Advanced Features

- **RAG System**: Automatically finds similar scripts to inspire new content
- **50/50 Balance**: Configurable ratio between model-specific and general content
- **Boundary Pushing**: Enhanced prompts for creative, spicy content
- **Gen Z Humor**: Raw, unfiltered comedy style

## 🔧 Configuration

### Environment Variables

Create `.streamlit/secrets.toml`:

```toml
[api_keys]
deepseek_api_key = "your_deepseek_api_key_here"

[app_config]
default_creator = "Emily Kent"
default_content_type = "thirst-trap"
max_scripts_per_generation = 3
```

### RAG System Settings

The RAG system can be configured in `data_hierarchy.py`:

```python
default_weights = {
    'model_data_weight': 0.5,      # 50% model-specific data
    'general_data_weight': 0.5,    # 50% general data
    'max_model_examples': 8,
    'max_general_examples': 4
}
```

## 📊 Analytics

The application provides comprehensive analytics:

- **Total Scripts**: Count of all generated scripts
- **AI Generated**: Scripts created by AI vs manual
- **Compliance PASS**: Content that passes compliance checks
- **Creators**: Distribution across different creators
- **Data Breakdown**: Model vs general content usage

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Production Deployment
See `docs/DEPLOYMENT.md` for detailed deployment instructions.

### Docker Deployment
```bash
docker build -t scriptwriterr .
docker run -p 8501:8501 scriptwriterr
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` folder for detailed guides
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions

## 🔮 Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] API endpoints for external integrations
- [ ] Mobile app support
- [ ] Advanced content filtering
- [ ] Real-time collaboration features

## 🙏 Acknowledgments

- DeepSeek for AI capabilities
- Streamlit for the web framework
- The open-source community for various dependencies

---

**Made with ❤️ for content creators**