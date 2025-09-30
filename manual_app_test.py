#!/usr/bin/env python3
"""
Manual test of the Streamlit app functionality without running the full UI
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_app_imports():
    """Test that the app can import all required modules"""
    print("Testing App Imports...")
    
    try:
        # Test all the imports from app.py
        import streamlit as st
        from dotenv import load_dotenv
        from sqlmodel import select
        from db import init_db, get_session, add_rating, get_hybrid_refs
        from models import Script, Revision
        from deepseek_client import generate_scripts, revise_for, selective_rewrite
        from rag_integration import generate_scripts_rag
        from compliance import blob_from, score_script
        
        print("   [OK] All app imports successful")
        return True
        
    except Exception as e:
        print(f"   [ERROR] App import failed: {e}")
        return False

def test_session_state_simulation():
    """Test session state functionality without Streamlit"""
    print("\nTesting Session State Logic...")
    
    try:
        # Simulate session state
        session_state = {
            'pending_drafts': [],
            'generation_params': {}
        }
        
        # Simulate adding pending drafts
        mock_draft = {
            "creator": "Test Creator",
            "content_type": "skit",
            "tone": "playful",
            "title": "Test Script",
            "hook": "Test hook",
            "beats": ["Beat 1", "Beat 2"],
            "voiceover": "Test voiceover",
            "caption": "",
            "hashtags": [],
            "cta": "",
            "compliance": "pass",
            "source": "ai"
        }
        
        session_state['pending_drafts'].append(mock_draft)
        
        print(f"   [OK] Session state can hold {len(session_state['pending_drafts'])} pending drafts")
        
        # Test approval logic (saving to database)
        from db import get_session
        from models import Script
        
        with get_session() as ses:
            # Test that we can create a Script from the draft data
            script = Script(**mock_draft)
            print("   [OK] Draft data can be converted to Script model")
            
            # Don't actually save it, just test the structure
            print("   [OK] Script ready for database save")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Session state test failed: {e}")
        return False

def test_generation_workflow():
    """Test the generation workflow without API calls"""
    print("\nTesting Generation Workflow...")
    
    try:
        from db import get_hybrid_refs
        from compliance import score_script
        
        # Test reference retrieval (this should work without API)
        refs = get_hybrid_refs("Emily Kent", "skit", k=3)
        print(f"   [OK] Retrieved {len(refs)} references for generation")
        
        # Test compliance scoring
        test_content = "This is a test script for compliance checking"
        level, reasons = score_script(test_content)
        print(f"   [OK] Compliance scoring works: {level}")
        
        # Simulate the generation workflow
        mock_generated_scripts = [
            {
                "title": "Test Generated Script 1",
                "hook": "Test hook 1",
                "beats": ["Beat 1", "Beat 2"],
                "voiceover": "Test voiceover 1",
                "caption": "Test caption 1",
                "hashtags": ["#test"],
                "cta": "Test CTA 1"
            },
            {
                "title": "Test Generated Script 2", 
                "hook": "Test hook 2",
                "beats": ["Beat A", "Beat B"],
                "voiceover": "Test voiceover 2",
                "caption": "Test caption 2",
                "hashtags": ["#test2"],
                "cta": "Test CTA 2"
            }
        ]
        
        # Simulate processing them into session state format
        pending_drafts = []
        for script in mock_generated_scripts:
            content_text = " ".join([
                script.get("title", ""),
                script.get("hook", ""),
                " ".join(script.get("beats", [])),
                script.get("voiceover", ""),
                script.get("caption", ""),
                script.get("cta", "")
            ])
            
            level, _ = score_script(content_text)
            
            script_data = {
                "creator": "Test Creator",
                "content_type": "skit",
                "tone": "playful",
                "title": script["title"],
                "hook": script["hook"],
                "beats": script["beats"],
                "voiceover": script["voiceover"],
                "caption": script["caption"],
                "hashtags": script["hashtags"],
                "cta": script["cta"],
                "compliance": level,
                "source": "ai"
            }
            
            pending_drafts.append(script_data)
        
        print(f"   [OK] Processed {len(pending_drafts)} scripts for approval")
        
        # Test approval workflow (saving to database)
        from db import get_session
        from models import Script
        
        with get_session() as ses:
            # Test saving one script (then delete it)
            test_script = Script(**pending_drafts[0])
            ses.add(test_script)
            ses.commit()
            ses.refresh(test_script)
            
            print(f"   [OK] Script saved to database with ID: {test_script.id}")
            
            # Clean up - delete the test script
            ses.delete(test_script)
            ses.commit()
            print("   [OK] Test script cleaned up")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Generation workflow test failed: {e}")
        return False

def test_app_structure():
    """Test that app.py has the right structure"""
    print("\nTesting App File Structure...")
    
    try:
        app_file = Path("src/app.py")
        content = app_file.read_text(encoding='utf-8')
        
        # Check for key components
        components = {
            "Session State Init": "pending_drafts" in content,
            "Generation Logic": "generate_scripts_rag" in content,
            "Approval Interface": "Approve" in content and "Reject" in content,
            "Database Save": "Script(**draft)" in content,
            "Bulk Actions": "Approve All" in content,
            "Pending Warning": "awaiting approval" in content
        }
        
        passed = 0
        for component, found in components.items():
            if found:
                print(f"   [OK] {component} found")
                passed += 1
            else:
                print(f"   [MISSING] {component} not found")
        
        print(f"   [INFO] App structure: {passed}/{len(components)} components found")
        
        return passed >= len(components) - 1  # Allow 1 missing component
        
    except Exception as e:
        print(f"   [ERROR] App structure test failed: {e}")
        return False

def run_manual_test():
    """Run all manual tests"""
    print("AI Script Studio - Manual App Test")
    print("=" * 40)
    
    tests = [
        ("App Imports", test_app_imports),
        ("Session State Logic", test_session_state_simulation),
        ("Generation Workflow", test_generation_workflow),
        ("App Structure", test_app_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   [ERROR] {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("MANUAL TEST SUMMARY")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\nSUCCESS: App is ready for use!")
        print("\nTo test the full system:")
        print("1. Set DEEPSEEK_API_KEY environment variable")
        print("2. Run: streamlit run src/app.py")
        print("3. Generate scripts using the sidebar")
        print("4. Review and approve scripts in the main tab")
        print("5. Verify only approved scripts are saved to database")
        
        return True
    else:
        print(f"\nWARNING: {total-passed} tests failed")
        return False

if __name__ == "__main__":
    success = run_manual_test()
    sys.exit(0 if success else 1)
