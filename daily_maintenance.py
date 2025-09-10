#!/usr/bin/env python3
"""
Daily maintenance script for AI Script Studio RAG system
Run this daily to keep your system learning and improving

Usage:
    python daily_maintenance.py                    # Interactive mode
    python daily_maintenance.py --auto             # Automatic mode  
    python daily_maintenance.py --score-only       # Just auto-scoring
    python daily_maintenance.py --learn-only       # Just policy learning
"""

import argparse
from datetime import datetime, timedelta

from auto_scorer import auto_score_pipeline
from rag_retrieval import index_all_scripts

# Safe import of policy learning (optional component)
try:
    from bandit_learner import run_policy_learning as _run_policy_learning
    def run_policy_learning():
        return _run_policy_learning()
except ImportError:
    def run_policy_learning():
        print("ℹ️ Policy learning skipped (bandit_learner not available)")
        return True
from db import get_session
from models import Script, AutoScore, PolicyWeights, Embedding
from sqlmodel import select

def get_system_stats():
    """Get current system statistics"""
    with get_session() as ses:
        scripts = list(ses.exec(select(Script)))
        auto_scores = list(ses.exec(select(AutoScore)))
        embeddings = list(ses.exec(select(Embedding)))
        policies = list(ses.exec(select(PolicyWeights)))
        
        # Recent activity (last 24h)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_scripts = [s for s in scripts if s.created_at >= cutoff]
        recent_scores = [s for s in auto_scores if s.created_at >= cutoff]
        
        return {
            'total_scripts': len(scripts),
            'total_auto_scores': len(auto_scores),
            'total_embeddings': len(embeddings),
            'total_policies': len(policies),
            'recent_scripts_24h': len(recent_scripts),
            'recent_scores_24h': len(recent_scores)
        }

def print_stats(stats):
    """Print system statistics"""
    print("📊 System Statistics")
    print("=" * 40)
    print(f"📝 Total Scripts: {stats['total_scripts']}")
    print(f"🤖 Auto-scored Scripts: {stats['total_auto_scores']}")
    print(f"🧠 Vector Embeddings: {stats['total_embeddings']}")
    print(f"⚙️  Policy Configurations: {stats['total_policies']}")
    print(f"🆕 New Scripts (24h): {stats['recent_scripts_24h']}")
    print(f"📊 New Scores (24h): {stats['recent_scores_24h']}")
    print()

def run_auto_scoring():
    """Run the auto-scoring pipeline"""
    print("🤖 Running Auto-Scoring Pipeline...")
    print("-" * 40)
    
    try:
        auto_score_pipeline()
        print("✅ Auto-scoring completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Auto-scoring failed: {e}")
        return False

def run_policy_learning():
    """Run the policy learning system"""
    print("🧠 Running Policy Learning...")
    print("-" * 40)
    
    try:
        run_policy_learning()
        print("✅ Policy learning completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Policy learning failed: {e}")
        return False

def index_new_scripts():
    """Index any new scripts that don't have embeddings"""
    print("🔍 Checking for new scripts to index...")
    
    with get_session() as ses:
        # Find scripts without embeddings
        scripts = list(ses.exec(select(Script)))
        embedded_script_ids = set(
            ses.exec(select(Embedding.script_id).distinct())
        )
        
        new_scripts = [s for s in scripts if s.id not in embedded_script_ids]
        
        if new_scripts:
            print(f"🆕 Found {len(new_scripts)} new scripts to index")
            
            from rag_retrieval import RAGRetriever
            retriever = RAGRetriever()
            
            for script in new_scripts:
                try:
                    embeddings = retriever.generate_embeddings(script)
                    for embedding in embeddings:
                        ses.add(embedding)
                    print(f"✅ Indexed script {script.id}: {script.title[:40]}...")
                except Exception as e:
                    print(f"❌ Failed to index script {script.id}: {e}")
            
            ses.commit()
            print(f"✅ Indexing completed! Processed {len(new_scripts)} scripts.")
        else:
            print("✅ All scripts are already indexed!")

def interactive_mode():
    """Interactive maintenance mode"""
    print("🔧 AI Script Studio - Daily Maintenance")
    print("=" * 50)
    
    stats = get_system_stats()
    print_stats(stats)
    
    print("What would you like to do?")
    print("1. Run full maintenance (auto-score + policy learning + indexing)")
    print("2. Auto-score recent scripts only")
    print("3. Run policy learning only") 
    print("4. Index new scripts only")
    print("5. Show statistics only")
    print("6. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            print("\n🚀 Running full maintenance...")
            index_new_scripts()
            run_auto_scoring()
            run_policy_learning()
            break
        elif choice == '2':
            run_auto_scoring()
            break
        elif choice == '3':
            run_policy_learning()
            break
        elif choice == '4':
            index_new_scripts()
            break
        elif choice == '5':
            stats = get_system_stats()
            print_stats(stats)
            continue
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")

def automatic_mode():
    """Automatic maintenance mode"""
    print("🤖 Running automatic maintenance...")
    
    stats = get_system_stats()
    print_stats(stats)
    
    # Always index new scripts first
    index_new_scripts()
    
    # Run auto-scoring if there are recent scripts
    if stats['recent_scripts_24h'] > 0:
        run_auto_scoring()
    else:
        print("ℹ️  No new scripts to score")
    
    # Run policy learning if there's enough data
    if stats['total_scripts'] >= 10:
        run_policy_learning()
    else:
        print("ℹ️  Need at least 10 scripts for policy learning")
    
    print("🎉 Automatic maintenance completed!")

def main():
    parser = argparse.ArgumentParser(description="Daily maintenance for AI Script Studio")
    parser.add_argument("--auto", action="store_true", help="Run automatic maintenance")
    parser.add_argument("--score-only", action="store_true", help="Run auto-scoring only")
    parser.add_argument("--learn-only", action="store_true", help="Run policy learning only")
    parser.add_argument("--index-only", action="store_true", help="Index new scripts only")
    
    args = parser.parse_args()
    
    if args.auto:
        automatic_mode()
    elif args.score_only:
        run_auto_scoring()
    elif args.learn_only:
        run_policy_learning()
    elif args.index_only:
        index_new_scripts()
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
