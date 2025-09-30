#!/usr/bin/env python3
"""
AI Script Studio - Health Check Script
Verifies all components are working before deployment
"""

import os
import sys
import traceback
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"ERROR: Python {version.major}.{version.minor} is too old. Need Python 3.8+")
        return False
    print(f"OK: Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        "app.py",
        "src/app.py", 
        "src/db.py",
        "src/models.py",
        "requirements_streamlit.txt",
        ".streamlit/config.toml",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files present")
    return True

def check_dependencies():
    """Check if all dependencies can be imported"""
    dependencies = [
        ("streamlit", "Streamlit web framework"),
        ("sqlmodel", "Database ORM"),
        ("requests", "HTTP client"),
        ("pandas", "Data processing"),
        ("numpy", "Numerical computing"),
    ]
    
    failed_imports = []
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError as e:
            failed_imports.append((module, description, str(e)))
            print(f"❌ {module} - {description}: {e}")
    
    if failed_imports:
        print("\n💡 Install missing dependencies:")
        print("pip install -r requirements_streamlit.txt")
        return False
    
    return True

def check_database():
    """Check database connectivity"""
    try:
        # Add src to path for imports
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from db import init_db, get_session
        from models import Script
        
        # Initialize database
        init_db()
        print("✅ Database initialized successfully")
        
        # Test database connection
        with get_session() as session:
            # Simple query to test connection
            scripts = list(session.query(Script).limit(1))
            print(f"✅ Database connection works (found {len(scripts)} test records)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        traceback.print_exc()
        return False

def check_api_key():
    """Check if API key is configured"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("⚠️  DEEPSEEK_API_KEY not set in environment")
        print("   For local testing: set in .env file")
        print("   For deployment: add to platform secrets")
        return False
    
    if api_key == "your_deepseek_api_key_here":
        print("⚠️  DEEPSEEK_API_KEY is using placeholder value")
        print("   Replace with your actual API key")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️  DEEPSEEK_API_KEY doesn't look like a valid key")
        print("   Should start with 'sk-'")
        return False
    
    print("✅ API key is configured")
    return True

def check_streamlit_config():
    """Check Streamlit configuration"""
    config_path = Path(".streamlit/config.toml")
    secrets_path = Path(".streamlit/secrets.toml")
    
    if not config_path.exists():
        print("⚠️  .streamlit/config.toml not found")
        print("   Using default configuration")
    else:
        print("✅ Streamlit config found")
    
    if secrets_path.exists():
        print("✅ Local secrets file found")
        # Check if it contains placeholder
        try:
            content = secrets_path.read_text()
            if "your_deepseek_api_key_here" in content:
                print("⚠️  Secrets file contains placeholder - update with real API key")
        except Exception:
            pass
    else:
        print("⚠️  No local secrets file (okay for deployment)")
    
    return True

def check_git_status():
    """Check git status for deployment readiness"""
    try:
        import subprocess
        
        # Check if we're in a git repo
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("⚠️  Uncommitted changes found:")
            print(result.stdout)
            print("   Consider committing changes before deployment")
        else:
            print("✅ Git repository is clean")
        
        # Check for remote
        result = subprocess.run(["git", "remote", "-v"], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("✅ Git remote configured")
        else:
            print("⚠️  No git remote - add one for deployment")
        
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Git not available or not in a git repository")
        return True  # Not critical for functionality

def run_basic_app_test():
    """Test basic app functionality"""
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        # Test core imports
        from db import init_db
        from models import Script
        from deepseek_client import DeepSeekClient
        
        print("✅ Core modules import successfully")
        
        # Test database initialization
        init_db()
        print("✅ Database initialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic app test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all health checks"""
    print("AI Script Studio - Health Check")
    print("="*50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("API Key", check_api_key),
        ("Streamlit Config", check_streamlit_config),
        ("Git Status", check_git_status),
        ("Basic App Test", run_basic_app_test),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"ERROR: {name} check failed with error: {e}")
    
    print("\n" + "="*50)
    print(f"HEALTH CHECK RESULTS: {passed}/{total} passed")
    
    if passed == total:
        print("All checks passed! Ready for deployment.")
        return True
    else:
        print("Some checks failed. Review issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
