#!/usr/bin/env python3
"""
Complete system test for AI Script Studio with approval system
"""

import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_environment():
    """Test basic environment setup"""
    print("1. Testing Environment Setup...")
    
    try:
        # Check API key
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "your_deepseek_api_key_here":
            print("   [WARNING] DEEPSEEK_API_KEY not configured - generation tests will be limited")
            return False
        else:
            print("   [OK] API key configured")
            return True
    except Exception as e:
        print(f"   [ERROR] Environment test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n2. Testing Database...")
    
    try:
        from db import init_db, get_session, get_hybrid_refs
        from models import Script
        from sqlmodel import select, func
        
        # Initialize database
        init_db()
        print("   [OK] Database initialized")
        
        # Check current state
        with get_session() as ses:
            total = ses.exec(select(func.count(Script.id))).first()
            ref_count = ses.exec(select(func.count(Script.id)).where(Script.is_reference == True)).first()
            ai_count = ses.exec(select(func.count(Script.id)).where(Script.source == "ai")).first()
            
            print(f"   [INFO] Total scripts: {total}")
            print(f"   [INFO] Reference scripts: {ref_count}")
            print(f"   [INFO] AI scripts: {ai_count}")
            
            if ai_count == 0:
                print("   [OK] AI scripts cleared - approval system ready")
            else:
                print(f"   [WARNING] Found {ai_count} AI scripts - approval system may not be clean")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Database test failed: {e}")
        return False

def test_imports():
    """Test all critical imports"""
    print("\n3. Testing Core Imports...")
    
    try:
        from rag_integration import generate_scripts_rag, generate_scripts_fast
        print("   [OK] RAG integration imported")
        
        from deepseek_client import generate_scripts, chat
        print("   [OK] DeepSeek client functions imported")
        
        from compliance import score_script
        print("   [OK] Compliance system imported")
        
        from auto_scorer import AutoScorer
        print("   [OK] Auto scorer imported")
        
        from db import get_hybrid_refs
        print("   [OK] Reference system imported")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Import test failed: {e}")
        return False

def test_reference_system():
    """Test reference retrieval system"""
    print("\n4. Testing Reference System...")
    
    try:
        from db import get_hybrid_refs
        
        # Test reference retrieval for different creators
        test_cases = [
            ("Emily Kent", "skit"),
            ("Marcie", "thirst-trap"), 
            ("Mia", "talking-style"),
            ("Anya", "skit")
        ]
        
        for creator, content_type in test_cases:
            refs = get_hybrid_refs(creator, content_type, k=3)
            print(f"   [INFO] {creator} + {content_type}: {len(refs)} references")
            if refs:
                print(f"      Sample: {refs[0][:60]}...")
        
        print("   [OK] Reference system working")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Reference system test failed: {e}")
        return False

def test_compliance_system():
    """Test compliance checking"""
    print("\n5. Testing Compliance System...")
    
    try:
        from compliance import score_script, compliance_level
        
        # Test different compliance levels
        test_cases = [
            ("This is a safe script about fitness", "pass"),
            ("This is hot and spicy content", "warn"), 
            ("This contains explicit content", "fail"),
            ("Normal content with no issues", "pass")
        ]
        
        correct = 0
        for text, expected in test_cases:
            level, reasons = compliance_level(text)
            if level == expected:
                correct += 1
                print(f"   [OK] '{text[:30]}...' -> {level}")
            else:
                print(f"   [FAIL] '{text[:30]}...' -> {level} (expected {expected})")
        
        accuracy = correct / len(test_cases)
        print(f"   [INFO] Compliance accuracy: {accuracy:.1%}")
        
        return accuracy >= 0.75
        
    except Exception as e:
        print(f"   [ERROR] Compliance test failed: {e}")
        return False

def test_generation_system(has_api_key):
    """Test script generation system"""
    print("\n6. Testing Generation System...")
    
    if not has_api_key:
        print("   [SKIP] No API key - skipping generation tests")
        return True
    
    try:
        from rag_integration import generate_scripts_fast
        
        print("   [INFO] Testing fast generation...")
        
        # Test generation with minimal parameters
        scripts = generate_scripts_fast(
            persona="girl-next-door; playful",
            boundaries="No explicit words; suggestive only",
            content_type="skit",
            tone="playful",
            refs=["Test reference line"],
            n=2
        )
        
        if scripts and len(scripts) > 0:
            print(f"   [OK] Generated {len(scripts)} scripts")
            
            # Check script structure
            script = scripts[0]
            required_fields = ["title", "hook", "beats"]
            missing_fields = [field for field in required_fields if not script.get(field)]
            
            if missing_fields:
                print(f"   [WARNING] Missing fields: {missing_fields}")
            else:
                print("   [OK] Script structure complete")
                print(f"      Title: {script['title'][:50]}...")
                if script.get('hook'):
                    print(f"      Hook: {script['hook'][:50]}...")
            
            return True
        else:
            print("   [ERROR] Generation returned no scripts")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Generation test failed: {e}")
        return False

def test_improved_prompts():
    """Test that improved prompts are in place"""
    print("\n7. Testing Improved System Prompts...")
    
    try:
        # Check if the improved prompts are in the file
        rag_file = Path("src/rag_integration.py")
        content = rag_file.read_text(encoding='utf-8')
        
        # Look for key indicators of improved prompts
        indicators = [
            "DARK HUMOR",
            "POP CULTURE SATIRE", 
            "COLLEGE-LEVEL WIT",
            "FORBIDDEN CRINGE",
            "SOPHISTICATED"
        ]
        
        found_indicators = []
        for indicator in indicators:
            if indicator in content:
                found_indicators.append(indicator)
        
        print(f"   [INFO] Found {len(found_indicators)}/{len(indicators)} improved prompt indicators")
        for indicator in found_indicators:
            print(f"      - {indicator}")
        
        if len(found_indicators) >= 3:
            print("   [OK] Improved prompts detected")
            return True
        else:
            print("   [WARNING] Improved prompts may not be fully implemented")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Prompt test failed: {e}")
        return False

def test_app_structure():
    """Test that app has approval system structure"""
    print("\n8. Testing App Structure...")
    
    try:
        app_file = Path("src/app.py")
        content = app_file.read_text(encoding='utf-8')
        
        # Look for approval system indicators
        approval_indicators = [
            "pending_drafts",
            "Approve",
            "Reject", 
            "awaiting approval",
            "session_state"
        ]
        
        found = []
        for indicator in approval_indicators:
            if indicator in content:
                found.append(indicator)
        
        print(f"   [INFO] Found {len(found)}/{len(approval_indicators)} approval system indicators")
        
        if len(found) >= 4:
            print("   [OK] Approval system structure detected")
            return True
        else:
            print("   [WARNING] Approval system may not be fully implemented")
            return False
            
    except Exception as e:
        print(f"   [ERROR] App structure test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("AI Script Studio - Comprehensive System Test")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Database", test_database),
        ("Imports", test_imports), 
        ("Reference System", test_reference_system),
        ("Compliance System", test_compliance_system),
        ("Improved Prompts", test_improved_prompts),
        ("App Structure", test_app_structure)
    ]
    
    results = []
    has_api_key = False
    
    for test_name, test_func in tests:
        try:
            if test_name == "Environment":
                result = test_func()
                has_api_key = result
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   [ERROR] {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Run generation test if we have API key
    if has_api_key:
        try:
            gen_result = test_generation_system(True)
            results.append(("Generation System", gen_result))
        except Exception as e:
            print(f"   [ERROR] Generation test crashed: {e}")
            results.append(("Generation System", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\nSUCCESS: All systems operational!")
        print("- Database is clean with approval system ready")
        print("- Improved dark humor prompts are active") 
        print("- Reference system is working")
        print("- Compliance checking is functional")
        print("- App structure supports approval workflow")
        if has_api_key:
            print("- Script generation is working")
        
        print("\nREADY TO USE:")
        print("1. Run: streamlit run src/app.py")
        print("2. Generate scripts via sidebar")
        print("3. Review and approve scripts in main tab")
        print("4. Only approved scripts will be saved to database")
        
    else:
        print(f"\nWARNING: {total-passed} tests failed")
        print("Review the errors above and fix issues before using the system")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
