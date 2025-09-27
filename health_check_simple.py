#!/usr/bin/env python3
"""
AI Script Studio - Simple Health Check Script
Verifies all components are working before deployment (ASCII only)
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
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("ERROR: Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("OK: All required files present")
    return True

def check_dependencies():
    """Check if all dependencies can be imported"""
    dependencies = [
        "streamlit",
        "sqlmodel", 
        "requests",
        "pandas",
        "numpy",
    ]
    
    failed_imports = []
    for module in dependencies:
        try:
            __import__(module)
            print(f"OK: {module}")
        except ImportError as e:
            failed_imports.append(module)
            print(f"ERROR: {module}: {e}")
    
    if failed_imports:
        print("\nInstall missing dependencies:")
        print("pip install -r requirements_streamlit.txt")
        return False
    
    return True

def check_api_key():
    """Check if API key is configured"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("WARNING: DEEPSEEK_API_KEY not set in environment")
        return False
    
    if api_key == "your_deepseek_api_key_here":
        print("WARNING: DEEPSEEK_API_KEY is using placeholder value")
        return False
    
    if not api_key.startswith("sk-"):
        print("WARNING: DEEPSEEK_API_KEY doesn't look like a valid key")
        return False
    
    print("OK: API key is configured")
    return True

def main():
    """Run all health checks"""
    print("AI Script Studio - Health Check")
    print("="*50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files), 
        ("Dependencies", check_dependencies),
        ("API Key", check_api_key),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"ERROR: {name} check failed: {e}")
    
    print("\n" + "="*50)
    print(f"HEALTH CHECK RESULTS: {passed}/{total} passed")
    
    if passed == total:
        print("SUCCESS: All checks passed! Ready for deployment.")
        return True
    else:
        print("WARNING: Some checks failed. Review issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
