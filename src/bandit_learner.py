"""
Multi-armed bandit learning system for optimizing generation policies
Learns which retrieval weights and generation parameters work best for each persona/content_type
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlmodel import Session, select

from models import Script, AutoScore, PolicyWeights, Rating
from db import get_session

@dataclass
class BanditArm:
    """Represents one configuration of parameters to test"""
    name: str
    semantic_weight: float
    bm25_weight: float
    quality_weight: float  
    freshness_weight: float
    temp_low: float
    temp_mid: float
    temp_high: float
    
    def __post_init__(self):
        # Ensure weights sum to 1.0
        total = self.semantic_weight + self.bm25_weight + self.quality_weight + self.freshness_weight
        if total != 1.0:
            self.semantic_weight /= total
            self.bm25_weight /= total
            self.quality_weight /= total
            self.freshness_weight /= total

class PolicyBandit:
    """Multi-armed bandit for learning optimal generation policies"""
    
    def __init__(self, epsilon: float = 0.15, decay_rate: float = 0.99):
        self.epsilon = epsilon  # Exploration rate
        self.decay_rate = decay_rate  # Epsilon decay over time
        self.min_epsilon = 0.05
        
        # Define arms (different parameter configurations)
        self.arms = [
            # Current default
            BanditArm("balanced", 0.45, 0.25, 0.20, 0.10, 0.4, 0.7, 0.95),
            
            # Semantic-heavy (focus on meaning)
            BanditArm("semantic_heavy", 0.60, 0.15, 0.15, 0.10, 0.4, 0.7, 0.95),
            
            # Quality-focused (use only best examples)
            BanditArm("quality_focused", 0.35, 0.20, 0.35, 0.10, 0.3, 0.6, 0.85),
            
            # Fresh-focused (prioritize recent trends)
            BanditArm("fresh_focused", 0.40, 0.20, 0.15, 0.25, 0.5, 0.8, 1.0),
            
            # Conservative (lower temperatures)
            BanditArm("conservative", 0.45, 0.25, 0.20, 0.10, 0.3, 0.5, 0.7),
            
            # Creative (higher temperatures)  
            BanditArm("creative", 0.45, 0.25, 0.20, 0.10, 0.6, 0.9, 1.2),
            
            # Text-match heavy (traditional keyword matching)
            BanditArm("text_heavy", 0.25, 0.45, 0.20, 0.10, 0.4, 0.7, 0.95)
        ]
        
        # Initialize arm statistics
        self.arm_counts = {arm.name: 0 for arm in self.arms}
        self.arm_rewards = {arm.name: 0.0 for arm in self.arms}
    
    def select_arm(self, persona: str, content_type: str) -> BanditArm:
        """Select arm using epsilon-greedy with UCB bias"""
        
        # Load existing policy weights to initialize arm stats
        self._load_arm_stats(persona, content_type)
        
        # Decay epsilon over time
        current_epsilon = max(self.min_epsilon, self.epsilon * (self.decay_rate ** sum(self.arm_counts.values())))
        
        if random.random() < current_epsilon:
            # Explore: random arm
            selected_arm = random.choice(self.arms)
            print(f"🔄 Exploring with {selected_arm.name} policy (ε={current_epsilon:.3f})")
        else:
            # Exploit: best arm with UCB confidence bounds
            selected_arm = self._select_best_arm_ucb()
            print(f"⭐ Exploiting with {selected_arm.name} policy")
        
        return selected_arm
    
    def _select_best_arm_ucb(self) -> BanditArm:
        """Select arm using Upper Confidence Bound"""
        total_counts = sum(self.arm_counts.values())
        if total_counts == 0:
            return self.arms[0]  # Default to first arm
        
        best_arm = None
        best_score = float('-inf')
        
        for arm in self.arms:
            count = self.arm_counts[arm.name]
            if count == 0:
                return arm  # Always try unplayed arms first
            
            # UCB score = average reward + confidence interval
            avg_reward = self.arm_rewards[arm.name] / count
            confidence = np.sqrt(2 * np.log(total_counts) / count)
            ucb_score = avg_reward + confidence
            
            if ucb_score > best_score:
                best_score = ucb_score
                best_arm = arm
        
        return best_arm or self.arms[0]
    
    def _load_arm_stats(self, persona: str, content_type: str):
        """Load historical performance for this persona/content_type"""
        with get_session() as ses:
            policy = ses.exec(
                select(PolicyWeights).where(
                    PolicyWeights.persona == persona,
                    PolicyWeights.content_type == content_type
                )
            ).first()
            
            if policy:
                # Find matching arm and update stats
                for arm in self.arms:
                    if self._arm_matches_policy(arm, policy):
                        self.arm_counts[arm.name] = policy.total_generations
                        self.arm_rewards[arm.name] = policy.success_rate * policy.total_generations
                        break
    
    def _arm_matches_policy(self, arm: BanditArm, policy: PolicyWeights, tolerance: float = 0.05) -> bool:
        """Check if an arm matches the stored policy within tolerance"""
        return (
            abs(arm.semantic_weight - policy.semantic_weight) < tolerance and
            abs(arm.bm25_weight - policy.bm25_weight) < tolerance and
            abs(arm.quality_weight - policy.quality_weight) < tolerance and
            abs(arm.freshness_weight - policy.freshness_weight) < tolerance
        )
    
    def update_reward(self, 
                     arm: BanditArm, 
                     reward: float, 
                     persona: str, 
                     content_type: str,
                     script_id: int):
        """Update arm performance with new reward signal"""
        
        # Update in-memory stats
        self.arm_counts[arm.name] += 1
        self.arm_rewards[arm.name] += reward
        
        # Update database policy
        self._update_policy_weights(arm, reward, persona, content_type)
        
        print(f"📈 Updated {arm.name}: reward={reward:.3f}, avg={self.arm_rewards[arm.name]/self.arm_counts[arm.name]:.3f}")
    
    def _update_policy_weights(self, 
                             arm: BanditArm, 
                             reward: float, 
                             persona: str, 
                             content_type: str):
        """Update policy weights in database"""
        with get_session() as ses:
            policy = ses.exec(
                select(PolicyWeights).where(
                    PolicyWeights.persona == persona,
                    PolicyWeights.content_type == content_type
                )
            ).first()
            
            if not policy:
                # Create new policy
                policy = PolicyWeights(
                    persona=persona,
                    content_type=content_type,
                    semantic_weight=arm.semantic_weight,
                    bm25_weight=arm.bm25_weight,
                    quality_weight=arm.quality_weight,
                    freshness_weight=arm.freshness_weight,
                    temp_low=arm.temp_low,
                    temp_mid=arm.temp_mid,
                    temp_high=arm.temp_high,
                    total_generations=1,
                    success_rate=reward
                )
            else:
                # Update existing policy with exponential moving average
                alpha = 0.1  # Learning rate
                policy.success_rate = (1 - alpha) * policy.success_rate + alpha * reward
                policy.total_generations += 1
                
                # If this arm is performing well, shift weights toward it
                if reward > policy.success_rate:
                    shift = 0.05  # Small shift toward better performing arm
                    policy.semantic_weight = (1 - shift) * policy.semantic_weight + shift * arm.semantic_weight
                    policy.bm25_weight = (1 - shift) * policy.bm25_weight + shift * arm.bm25_weight
                    policy.quality_weight = (1 - shift) * policy.quality_weight + shift * arm.quality_weight
                    policy.freshness_weight = (1 - shift) * policy.freshness_weight + shift * arm.freshness_weight
                    
                    policy.temp_low = (1 - shift) * policy.temp_low + shift * arm.temp_low
                    policy.temp_mid = (1 - shift) * policy.temp_mid + shift * arm.temp_mid
                    policy.temp_high = (1 - shift) * policy.temp_high + shift * arm.temp_high
            
            policy.updated_at = datetime.utcnow()
            ses.add(policy)
            ses.commit()
    
    def calculate_reward(self, script_id: int) -> float:
        """
        Calculate reward signal from script performance
        Combines auto-scores and human ratings when available
        """
        reward_components = []
        
        with get_session() as ses:
            # Get auto-score
            auto_score = ses.exec(
                select(AutoScore).where(AutoScore.script_id == script_id)
            ).first()
            
            if auto_score and auto_score.confidence > 0.5:
                # Weighted composite of auto-scores
                auto_reward = (
                    0.35 * auto_score.overall +
                    0.20 * auto_score.hook +
                    0.15 * auto_score.originality +
                    0.15 * auto_score.style_fit +
                    0.15 * auto_score.safety
                ) / 5.0  # Normalize to 0-1
                
                reward_components.append(('auto', auto_reward, auto_score.confidence))
            
            # Get human ratings
            script = ses.get(Script, script_id)
            if script and script.ratings_count > 0:
                human_reward = script.score_overall / 5.0  # Normalize to 0-1
                confidence = min(1.0, script.ratings_count / 3.0)  # More ratings = higher confidence
                reward_components.append(('human', human_reward, confidence))
        
        if not reward_components:
            return 0.5  # Neutral reward if no scores available
        
        # Weighted average of reward components by confidence
        total_weight = sum(confidence for _, _, confidence in reward_components)
        weighted_reward = sum(
            reward * confidence for _, reward, confidence in reward_components
        ) / total_weight
        
        return weighted_reward

class PolicyLearner:
    """Main interface for policy learning"""
    
    def __init__(self):
        self.bandit = PolicyBandit()
    
    def learn_from_generation_batch(self, 
                                  persona: str,
                                  content_type: str,
                                  generated_script_ids: List[int],
                                  selected_arm: BanditArm):
        """Learn from a batch of generated scripts"""
        
        if not generated_script_ids:
            return
        
        # Calculate average reward from the batch
        rewards = [self.bandit.calculate_reward(sid) for sid in generated_script_ids]
        avg_reward = sum(rewards) / len(rewards)
        
        # Update bandit with average performance
        self.bandit.update_reward(
            selected_arm, 
            avg_reward, 
            persona, 
            content_type,
            generated_script_ids[0]  # Representative script ID
        )
        
        print(f"🧠 Policy learning: {persona}/{content_type} → {avg_reward:.3f} reward")
    
    def get_optimized_policy(self, persona: str, content_type: str) -> BanditArm:
        """Get the current best policy for this persona/content_type"""
        return self.bandit.select_arm(persona, content_type)
    
    def run_learning_cycle(self):
        """Run a learning cycle on recent generations"""
        print("🔄 Starting policy learning cycle...")
        
        # Find recent AI-generated scripts by persona/content_type
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        with get_session() as ses:
            recent_scripts = list(ses.exec(
                select(Script).where(
                    Script.created_at >= cutoff,
                    Script.source == "ai"
                )
            ))
        
        # Group by persona/content_type
        groups = {}
        for script in recent_scripts:
            key = (script.creator, script.content_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(script.id)
        
        # Learn from each group
        for (persona, content_type), script_ids in groups.items():
            if len(script_ids) >= 3:  # Need minimum batch size
                # For now, assume they used the balanced policy
                # In practice, you'd track which policy was used for each generation
                balanced_arm = next(arm for arm in self.bandit.arms if arm.name == "balanced")
                self.learn_from_generation_batch(persona, content_type, script_ids, balanced_arm)

def run_policy_learning():
    """Main entry point for policy learning"""
    learner = PolicyLearner()
    learner.run_learning_cycle()

if __name__ == "__main__":
    run_policy_learning()


