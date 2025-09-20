"""
Tests for the RAG integration module
"""

import pytest
from unittest.mock import Mock, patch
from src.rag_integration import generate_scripts_rag, generate_scripts_fast


class TestRAGIntegration:
    """Test cases for RAG integration"""
    
    @patch('src.rag_integration.DeepSeekClient')
    def test_generate_scripts_rag(self, mock_client):
        """Test script generation with RAG"""
        # Mock the client response
        mock_client.return_value.generate_scripts.return_value = [
            {
                "title": "Test Script",
                "hook": "Test hook",
                "beats": "Test beat",
                "voiceover": "Test voiceover",
                "caption": "Test caption",
                "hashtags": "test hashtag",
                "cta": "Test CTA"
            }
        ]
        
        # Test the function
        result = generate_scripts_rag(
            persona="test-persona",
            content_type="test-type",
            n=1,
            refs=["test reference"]
        )
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Script"
    
    @patch('src.rag_integration.DeepSeekClient')
    def test_generate_scripts_fast(self, mock_client):
        """Test fast script generation"""
        # Mock the client response
        mock_client.return_value.generate_scripts.return_value = [
            {
                "title": "Fast Script",
                "hook": "Fast hook",
                "beats": "Fast beat",
                "voiceover": "Fast voiceover",
                "caption": "Fast caption",
                "hashtags": "fast hashtag",
                "cta": "Fast CTA"
            }
        ]
        
        # Test the function
        result = generate_scripts_fast(
            persona="test-persona",
            content_type="test-type",
            n=1,
            refs=["test reference"]
        )
        
        assert len(result) == 1
        assert result[0]["title"] == "Fast Script"
