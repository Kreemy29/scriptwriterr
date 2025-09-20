"""
Tests for the models module
"""

import pytest
from src.models import Script, ModelProfile, Feedback


class TestScript:
    """Test cases for Script model"""
    
    def test_script_creation(self):
        """Test creating a script"""
        script = Script(
            title="Test Script",
            hook="Test hook",
            beats="Test beat",
            voiceover="Test voiceover",
            caption="Test caption",
            hashtags="test hashtag",
            cta="Test CTA",
            creator="Test Creator",
            content_type="test-type"
        )
        assert script.title == "Test Script"
        assert script.creator == "Test Creator"
    
    def test_script_validation(self):
        """Test script validation"""
        with pytest.raises(ValueError):
            Script()  # Should raise error for missing required fields


class TestModelProfile:
    """Test cases for ModelProfile model"""
    
    def test_model_profile_creation(self):
        """Test creating a model profile"""
        profile = ModelProfile(
            model_name="Test Model",
            niche="test-niche",
            description="Test description"
        )
        assert profile.model_name == "Test Model"
        assert profile.niche == "test-niche"


class TestFeedback:
    """Test cases for Feedback model"""
    
    def test_feedback_creation(self):
        """Test creating feedback"""
        feedback = Feedback(
            script_id=1,
            overall_score=4.5,
            hook_clarity=4.0,
            originality=5.0,
            style_fit=4.0,
            safety=5.0
        )
        assert feedback.overall_score == 4.5
        assert feedback.script_id == 1
