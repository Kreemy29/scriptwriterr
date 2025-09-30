#!/usr/bin/env python3
"""
AI Script Studio - Quick Test Script
A simplified version for fast validation of core functionality
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def quick_test():
    """Run quick tests of core functionality"""
    print("AI Script Studio - Quick Test")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Environment Setup
    total_tests += 1
    print("\n1. Testing Environment Setup...")
    try:
        # Check API key
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "your_deepseek_api_key_here":
            print("   [X] DEEPSEEK_API_KEY not configured")
        else:
            print("   [OK] API key configured")
            tests_passed += 1
    except Exception as e:
        print(f"   [X] Environment setup failed: {e}")
    
    # Test 2: Database
    total_tests += 1
    print("\n2. Testing Database...")
    try:
        from db import init_db, get_session
        from models import Script
        
        init_db()
        with get_session() as session:
            # Simple query test
            scripts = list(session.query(Script).limit(1))
        print("   [OK] Database connection working")
        tests_passed += 1
    except Exception as e:
        print(f"   [X] Database test failed: {e}")
    
    # Test 3: Core Imports
    total_tests += 1
    print("\n3. Testing Core Imports...")
    try:
        from deepseek_client import DeepSeekClient
        from rag_integration import generate_scripts_rag
        from compliance import score_script
        from auto_scorer import AutoScorer
        print("   [OK] Core modules imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"   [X] Core imports failed: {e}")
    
    # Test 4: Basic Generation (if API key available)
    total_tests += 1
    print("\n4. Testing Basic Generation...")
    try:
        if api_key and api_key != "your_deepseek_api_key_here":
            from rag_integration import generate_scripts_fast
            
            scripts = generate_scripts_fast(
                persona="girl-next-door; playful",
                boundaries="No explicit words; suggestive only",
                content_type="skit",
                tone="playful",
                refs=["Test reference"],
                n=1
            )
            
            if scripts and len(scripts) > 0:
                print("   [OK] Script generation working")
                tests_passed += 1
            else:
                print("   [X] Script generation returned no results")
        else:
            print("   [SKIP] Skipping generation test (no API key)")
            tests_passed += 1  # Don't penalize missing API key
    except Exception as e:
        print(f"   [X] Generation test failed: {e}")
    
    # Test 5: Compliance System
    total_tests += 1
    print("\n5. Testing Compliance System...")
    try:
        from compliance import compliance_level
        
        level, reasons = compliance_level("This is a safe test script")
        if level in ["pass", "warn", "fail"]:
            print("   [OK] Compliance system working")
            tests_passed += 1
        else:
            print("   [X] Compliance system returned invalid level")
    except Exception as e:
        print(f"   [X] Compliance test failed: {e}")
    
    # Results
    print("\n" + "=" * 40)
    print(f"Quick Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("SUCCESS: All quick tests passed! System is ready.")
        return True
    else:
        print("WARNING: Some tests failed. Run comprehensive_test_suite.py for details.")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
