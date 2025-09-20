#!/usr/bin/env python3
"""
Data Hierarchy System for AI Script Studio
Handles primary (model-specific) and secondary (general) data retrieval
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import select, and_
from db import get_session
from models import ModelProfile, ContentTemplate, DataHierarchy, Script

class DataHierarchyManager:
    """Manages the data hierarchy system for AI training"""
    
    def __init__(self):
        self.default_weights = {
            'model_data_weight': 0.7,  # 70% model-specific data
            'general_data_weight': 0.3,  # 30% general data
            'max_model_examples': 8,
            'max_general_examples': 4
        }
    
    def get_hierarchical_references(self, niche: str, content_type: str, k: int = 12) -> List[Dict[str, Any]]:
        """
        Get references using data hierarchy:
        1. Primary: Model-specific data (70% weight)
        2. Secondary: General content data (30% weight)
        """
        with get_session() as session:
            # Get hierarchy settings
            hierarchy = self._get_hierarchy_settings(session, niche, content_type)
            
            # Get model-specific data (primary)
            model_refs = self._get_model_specific_data(session, niche, content_type, hierarchy['max_model_examples'])
            
            # Get general content data (secondary)
            general_refs = self._get_general_content_data(session, niche, content_type, hierarchy['max_general_examples'])
            
            # Combine with weights
            all_refs = []
            
            # Add model-specific refs with higher weight
            for ref in model_refs:
                ref['weight'] = hierarchy['model_data_weight']
                ref['source'] = 'model_specific'
                all_refs.append(ref)
            
            # Add general refs with lower weight
            for ref in general_refs:
                ref['weight'] = hierarchy['general_data_weight']
                ref['source'] = 'general_content'
                all_refs.append(ref)
            
            return all_refs[:k]
    
    def _get_hierarchy_settings(self, session, niche: str, content_type: str) -> Dict[str, Any]:
        """Get or create hierarchy settings for niche/content_type combination"""
        try:
            stmt = select(DataHierarchy).where(
                and_(
                    DataHierarchy.niche == niche,
                    DataHierarchy.content_type == content_type,
                    DataHierarchy.is_active == True
                )
            )
            hierarchy = session.exec(stmt).first()
        except Exception as e:
            print(f"⚠️ Hierarchy query failed, using defaults: {e}")
            hierarchy = None
        
        if not hierarchy:
            # Create default hierarchy settings
            hierarchy = DataHierarchy(
                niche=niche,
                content_type=content_type,
                **self.default_weights
            )
            session.add(hierarchy)
            session.commit()
        
        return {
            'model_data_weight': hierarchy.model_data_weight,
            'general_data_weight': hierarchy.general_data_weight,
            'max_model_examples': hierarchy.max_model_examples,
            'max_general_examples': hierarchy.max_general_examples
        }
    
    def _get_model_specific_data(self, session, niche: str, content_type: str, max_examples: int) -> List[Dict[str, Any]]:
        """Get model-specific data for the niche - prioritize exact matches but fallback for diversity"""
        # First, try to get from ModelProfile by creator name (if niche is a creator name)
        model_stmt = select(ModelProfile).where(
            and_(
                ModelProfile.model_name == niche,
                ModelProfile.is_active == True
            )
        )
        models = list(session.exec(model_stmt))
        
        # If no model found by name, try by niche
        if not models:
            model_stmt = select(ModelProfile).where(
                and_(
                    ModelProfile.niche == niche,
                    ModelProfile.is_active == True
                )
            )
            models = list(session.exec(model_stmt))
        
        model_refs = []
        
        # Get scripts from specific models
        for model in models:
            # First try exact content type match
            script_stmt = select(Script).where(
                and_(
                    Script.creator == model.model_name,
                    Script.content_type == content_type,
                    Script.is_reference == True
                )
            ).limit(max_examples // len(models) if models else max_examples)
            
            scripts = list(session.exec(script_stmt))
            
            # If not enough exact matches, get any scripts from this model for diversity
            if len(scripts) < (max_examples // len(models) if models else max_examples):
                additional_needed = (max_examples // len(models) if models else max_examples) - len(scripts)
                fallback_stmt = select(Script).where(
                    and_(
                        Script.creator == model.model_name,
                        Script.is_reference == True
                    )
                ).limit(additional_needed)
                
                fallback_scripts = list(session.exec(fallback_stmt))
                scripts.extend(fallback_scripts)
            
            for script in scripts:
                model_refs.append({
                    'title': script.title,
                    'hook': script.hook,
                    'beats': script.beats,
                    'voiceover': script.voiceover,
                    'caption': script.caption,
                    'hashtags': script.hashtags,
                    'cta': script.cta,
                    'model_name': model.model_name,
                    'brand_description': model.brand_description,
                    'content_style': model.content_style,
                    'voice_tone': model.voice_tone,
                    'content_type': script.content_type  # Include for debugging
                })
        
        return model_refs[:max_examples]
    
    def _get_general_content_data(self, session, niche: str, content_type: str, max_examples: int) -> List[Dict[str, Any]]:
        """Get general content data for the niche - prioritize diversity and creativity"""
        general_refs = []
        
        # First, try to get from ContentTemplate (exact match)
        template_stmt = select(ContentTemplate).where(
            and_(
                ContentTemplate.niche == niche,
                ContentTemplate.content_type == content_type,
                ContentTemplate.is_active == True
            )
        ).limit(max_examples // 2)  # Use half for templates
        
        templates = list(session.exec(template_stmt))
        
        for template in templates:
            template_data = template.template_data
            general_refs.append({
                'title': template_data.get('title', ''),
                'hook': template_data.get('hook', ''),
                'beats': template_data.get('beats', []),
                'voiceover': template_data.get('voiceover', ''),
                'caption': template_data.get('caption', ''),
                'hashtags': template_data.get('hashtags', []),
                'cta': template_data.get('cta', ''),
                'template_name': template.template_name,
                'source': 'general_template'
            })
        
        # Get general scripts for diversity - be more flexible with content type matching
        remaining = max_examples - len(general_refs)
        
        if remaining > 0:
            # First try exact content type match
            script_stmt = select(Script).where(
                and_(
                    Script.creator == "General Content",
                    Script.content_type == content_type,
                    Script.is_reference == True
                )
            ).limit(remaining)
            
            scripts = list(session.exec(script_stmt))
            
            # If not enough exact matches, get any general content for creativity
            if len(scripts) < remaining:
                additional_needed = remaining - len(scripts)
                fallback_stmt = select(Script).where(
                    and_(
                        Script.creator == "General Content",
                        Script.is_reference == True
                    )
                ).limit(additional_needed)
                
                fallback_scripts = list(session.exec(fallback_stmt))
                scripts.extend(fallback_scripts)
            
            for script in scripts:
                general_refs.append({
                    'title': script.title,
                    'hook': script.hook,
                    'beats': script.beats,
                    'voiceover': script.voiceover,
                    'caption': script.caption,
                    'hashtags': script.hashtags,
                    'cta': script.cta,
                    'source': 'general_script',
                    'content_type': script.content_type  # Include for debugging
                })
        
        return general_refs[:max_examples]
    
    def add_model_profile(self, model_name: str, niche: str, brand_description: str, 
                         instagram_handle: str = None, content_style: str = "", 
                         voice_tone: str = "", visual_style: str = "", 
                         target_audience: str = "", content_themes: List[str] = None) -> ModelProfile:
        """Add a new model profile to the primary data"""
        with get_session() as session:
            model = ModelProfile(
                model_name=model_name,
                niche=niche,
                brand_description=brand_description,
                instagram_handle=instagram_handle,
                content_style=content_style,
                voice_tone=voice_tone,
                visual_style=visual_style,
                target_audience=target_audience,
                content_themes=content_themes or []
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return model
    
    def add_content_template(self, template_name: str, content_type: str, niche: str, 
                           template_data: Dict[str, Any]) -> ContentTemplate:
        """Add a new content template to the secondary data"""
        with get_session() as session:
            template = ContentTemplate(
                template_name=template_name,
                content_type=content_type,
                niche=niche,
                template_data=template_data
            )
            session.add(template)
            session.commit()
            session.refresh(template)
            return template
    
    def update_hierarchy_weights(self, niche: str, content_type: str, 
                               model_data_weight: float, general_data_weight: float) -> DataHierarchy:
        """Update the data hierarchy weights"""
        with get_session() as session:
            stmt = select(DataHierarchy).where(
                and_(
                    DataHierarchy.niche == niche,
                    DataHierarchy.content_type == content_type
                )
            )
            hierarchy = session.exec(stmt).first()
            
            if hierarchy:
                hierarchy.model_data_weight = model_data_weight
                hierarchy.general_data_weight = general_data_weight
            else:
                hierarchy = DataHierarchy(
                    niche=niche,
                    content_type=content_type,
                    model_data_weight=model_data_weight,
                    general_data_weight=general_data_weight
                )
                session.add(hierarchy)
            
            session.commit()
            session.refresh(hierarchy)
            return hierarchy
    
    def get_data_stats(self) -> Dict[str, Any]:
        """Get statistics about the data hierarchy"""
        with get_session() as session:
            model_count = len(list(session.exec(select(ModelProfile))))
            template_count = len(list(session.exec(select(ContentTemplate))))
            hierarchy_count = len(list(session.exec(select(DataHierarchy))))
            
            # Get script counts by creator
            emily_scripts = len(list(session.exec(select(Script).where(Script.creator == "Emily Kent"))))
            marcie_scripts = len(list(session.exec(select(Script).where(Script.creator == "Marcie"))))
            general_scripts = len(list(session.exec(select(Script).where(Script.creator == "General Content"))))
            
            return {
                'model_profiles': model_count,
                'content_templates': template_count,
                'hierarchy_settings': hierarchy_count,
                'emily_scripts': emily_scripts,
                'marcie_scripts': marcie_scripts,
                'general_scripts': general_scripts
            }
    
    def debug_references(self, niche: str, content_type: str, k: int = 6) -> Dict[str, Any]:
        """Debug method to see what references are being retrieved"""
        with get_session() as session:
            # Get hierarchy settings
            hierarchy = self._get_hierarchy_settings(session, niche, content_type)
            
            # Get model-specific data
            model_refs = self._get_model_specific_data(session, niche, content_type, hierarchy['max_model_examples'])
            
            # Get general content data
            general_refs = self._get_general_content_data(session, niche, content_type, hierarchy['max_general_examples'])
            
            return {
                'niche': niche,
                'content_type': content_type,
                'hierarchy_settings': hierarchy,
                'model_refs_count': len(model_refs),
                'general_refs_count': len(general_refs),
                'model_refs': model_refs,
                'general_refs': general_refs,
                'total_refs': len(model_refs) + len(general_refs)
            }

# Global instance
hierarchy_manager = DataHierarchyManager()
