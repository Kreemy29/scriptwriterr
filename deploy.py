#!/usr/bin/env python3
"""
AI Script Studio - Automated Deployment Script
Prepares and deploys the app to Streamlit Cloud and other platforms
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle errors gracefully"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if git is installed
    if not run_command("git --version", "Checking Git installation"):
        print("❌ Git is not installed. Please install Git first.")
        return False
    
    # Check if we're in a git repository
    if not Path(".git").exists():
        print("⚠️  Not in a Git repository. Initializing...")
        if not run_command("git init", "Initializing Git repository"):
            return False
    
    # Check if API key is set
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your_deepseek_api_key_here":
        print("⚠️  DEEPSEEK_API_KEY not set or using placeholder")
        print("   You'll need to add this in your Streamlit Cloud secrets")
    
    return True

def prepare_deployment():
    """Prepare files for deployment"""
    print("📦 Preparing deployment files...")
    
    # Create .streamlit directory if it doesn't exist
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)
    
    # Copy production config if it doesn't exist
    prod_config = streamlit_dir / "config_production.toml"
    config_file = streamlit_dir / "config.toml"
    
    if prod_config.exists() and not config_file.exists():
        print("📋 Using production configuration")
        run_command(f"copy {prod_config} {config_file}" if os.name == 'nt' else f"cp {prod_config} {config_file}", 
                   "Copying production config")
    
    # Create .gitignore if it doesn't exist
    gitignore_content = """
# Streamlit secrets (never commit these!)
.streamlit/secrets.toml

# Database files
*.db
studio.db

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Environment
.env
.venv
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Data files (optional - uncomment if you want to exclude data)
# data/
# *.jsonl
# *.json
"""
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        print("📝 Creating .gitignore")
        gitignore_path.write_text(gitignore_content.strip())
    
    return True

def deploy_to_git():
    """Deploy to Git repository"""
    print("🚀 Deploying to Git...")
    
    # Add all files
    if not run_command("git add .", "Adding files to Git"):
        return False
    
    # Check if there are changes to commit
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("✅ No changes to commit - repository is up to date")
        return True
    
    # Commit changes
    commit_message = "Deploy AI Script Studio - Streamlit Cloud ready"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        return False
    
    # Push to remote (if remote exists)
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("📤 Pushing to remote repository...")
        run_command("git push", "Pushing to remote")
    else:
        print("⚠️  No remote repository configured")
        print("   Add a remote with: git remote add origin https://github.com/username/repo.git")
    
    return True

def show_deployment_instructions():
    """Show final deployment instructions"""
    print("\n" + "="*60)
    print("🎉 DEPLOYMENT PREPARATION COMPLETE!")
    print("="*60)
    
    print("\n📋 NEXT STEPS:")
    print("\n1. 🔗 Push to GitHub (if not done automatically):")
    print("   git remote add origin https://github.com/yourusername/ai-script-studio.git")
    print("   git push -u origin main")
    
    print("\n2. 🚀 Deploy on Streamlit Cloud:")
    print("   • Go to: https://share.streamlit.io")
    print("   • Sign in with GitHub")
    print("   • Click 'New app'")
    print("   • Select your repository")
    print("   • Set main file path: app.py")
    print("   • Add in Secrets:")
    print("     DEEPSEEK_API_KEY = \"your_actual_api_key_here\"")
    print("   • Click Deploy!")
    
    print("\n3. ✨ Your app will be live at:")
    print("   https://your-app-name.streamlit.app")
    
    print("\n📚 For detailed instructions, see: STREAMLIT_DEPLOYMENT.md")
    print("\n🎬 Happy deploying!")

def main():
    """Main deployment function"""
    print("🎬 AI Script Studio - Deployment Assistant")
    print("="*50)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Prepare deployment
    if not prepare_deployment():
        print("❌ Failed to prepare deployment")
        sys.exit(1)
    
    # Deploy to Git
    if not deploy_to_git():
        print("❌ Failed to deploy to Git")
        sys.exit(1)
    
    # Show instructions
    show_deployment_instructions()

if __name__ == "__main__":
    main()
