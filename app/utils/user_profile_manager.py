"""
User Profile Manager - Track user characteristics for personalization
Learns user skill level, preferences, device type, and time availability
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class SkillLevel(str, Enum):
    """User technical skill levels"""
    NEWBIE = "newbie"              # Can't troubleshoot, needs detailed steps
    INTERMEDIATE = "intermediate"  # Can follow technical instructions
    ADVANCED = "advanced"          # Can troubleshoot themselves
    EXPERT = "expert"              # Rarely needs help


class TimeAvailability(str, Enum):
    """User's time constraints"""
    URGENT = "urgent"              # < 5 minutes, on the road
    SHORT = "short"                # 5-15 minutes, has some time
    FLEXIBLE = "flexible"          # 15+ minutes, can wait


class UserProfile:
    """
    Comprehensive user profile for personalization.
    Learns from interaction history and adapts response style.
    """
    
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.created_at = datetime.utcnow()
        self.last_interaction = datetime.utcnow()
        
        # Technical capability
        self.skill_level = SkillLevel.NEWBIE  # Default to newbie
        self.technical_vocabulary = 0.0       # 0-1, grows with interactions
        self.device_type: Optional[str] = None
        self.device_specs: Dict[str, str] = {}
        
        # Availability & preferences
        self.time_availability = TimeAvailability.SHORT
        self.preferred_explanation = "step_by_step"  # step_by_step, detailed, simple
        self.language_preference = "id"
        
        # Issue history
        self.issue_history: List[Dict[str, Any]] = []
        self.previous_failed_solutions: List[str] = []
        self.previously_resolved_categories: List[str] = []
        
        # Interaction metrics
        self.total_interactions = 0
        self.successful_resolutions = 0
        self.escalations = 0
        self.satisfaction_ratings: List[float] = []
        
        # Communication style
        self.average_response_length = 0
        self.frustration_indicators = 0
        self.is_frustrated = False
    
    def update_from_message(self, message: str, context: Optional[Dict] = None):
        """
        Update profile based on user message.
        Infers skill level, time availability, emotional state.
        """
        self.last_interaction = datetime.utcnow()
        self.total_interactions += 1
        
        # Track message length to infer patience/detail
        self.average_response_length = (
            (self.average_response_length * (self.total_interactions - 1) + len(message)) 
            / self.total_interactions
        )
        
        # Detect frustration indicators
        frustration_keywords = [
            "tidak", "gak", "bosan", "kesel", "jengkel", "error", 
            "gagal", "tetap", "masih", "belum", "pusing", "hopeless",
            "!!", "!!!", "?"
        ]
        frustration_count = sum(1 for keyword in frustration_keywords if keyword in message.lower())
        
        if frustration_count > 2:
            self.is_frustrated = True
            self.frustration_indicators += frustration_count
        else:
            self.is_frustrated = False
        
        # Infer device if mentioned
        if context and 'device_type' in context:
            self.device_type = context['device_type']
            self.device_specs = context.get('device_specs', {})
        
        # Infer time availability from message
        urgent_keywords = ["urgent", "cepat", "asap", "bantuan", "help", "sekarang"]
        if any(keyword in message.lower() for keyword in urgent_keywords):
            self.time_availability = TimeAvailability.URGENT
        
        logger.debug(f"👤 Profile updated for {self.phone_number}: "
                    f"skill={self.skill_level}, time={self.time_availability}, "
                    f"frustrated={self.is_frustrated}")
    
    def update_skill_level(self, interaction_outcome: str):
        """
        Update skill level based on how user responds to troubleshooting.
        """
        outcomes = {
            'successful': 0.15,      # User followed steps and resolved
            'partial': 0.08,         # User resolved with hints
            'escalated': -0.05,      # User couldn't troubleshoot
            'feedback_positive': 0.20,  # User praised response
        }
        
        change = outcomes.get(interaction_outcome, 0)
        self.technical_vocabulary = min(1.0, max(0.0, self.technical_vocabulary + change))
        
        # Determine skill level based on vocabulary score
        if self.technical_vocabulary < 0.3:
            self.skill_level = SkillLevel.NEWBIE
        elif self.technical_vocabulary < 0.6:
            self.skill_level = SkillLevel.INTERMEDIATE
        elif self.technical_vocabulary < 0.85:
            self.skill_level = SkillLevel.ADVANCED
        else:
            self.skill_level = SkillLevel.EXPERT
    
    def record_issue(
        self,
        category: str,
        description: str,
        outcome: str,  # 'resolved' | 'escalated' | 'failed'
        resolution_time_minutes: int = 0
    ):
        """Record an issue for history tracking"""
        issue = {
            'timestamp': datetime.utcnow().isoformat(),
            'category': category,
            'description': description,
            'outcome': outcome,
            'resolution_time_minutes': resolution_time_minutes,
        }
        
        self.issue_history.append(issue)
        
        if outcome == 'resolved':
            self.successful_resolutions += 1
            if category not in self.previously_resolved_categories:
                self.previously_resolved_categories.append(category)
        elif outcome == 'escalated':
            self.escalations += 1
    
    def record_solution_attempt(
        self,
        category: str,
        solution_description: str,
        success: bool,
        feedback: Optional[str] = None
    ):
        """Record whether a solution worked or not"""
        if not success:
            self.previous_failed_solutions.append(f"{category}: {solution_description}")
        
        # Update skill level based on outcome
        if success:
            self.update_skill_level('successful')
        else:
            self.update_skill_level('escalated')
    
    def add_satisfaction_rating(self, rating: float):
        """Add user satisfaction rating (1-5 scale)"""
        if 1 <= rating <= 5:
            self.satisfaction_ratings.append(rating)
    
    def get_response_style(self) -> Dict[str, Any]:
        """
        Get personalized response style based on profile.
        Used to adapt AI responses and explanation depth.
        """
        style = {
            'skill_level': self.skill_level.value,
            
            # Explanation depth
            'explanation_depth': self._get_explanation_depth(),
            
            # Technical language level
            'use_technical_terms': self.skill_level in [
                SkillLevel.ADVANCED, SkillLevel.EXPERT
            ],
            
            # Speed of recommendations
            'offer_quick_fix_first': self.time_availability == TimeAvailability.URGENT,
            'detail_level': self._get_detail_level(),
            
            # Escalation tendency
            'escalate_early': self.is_frustrated or self.time_availability == TimeAvailability.URGENT,
            
            # Format preferences
            'use_bullet_points': self.skill_level != SkillLevel.NEWBIE,
            'include_why_section': self.skill_level in [
                SkillLevel.ADVANCED, SkillLevel.EXPERT
            ],
            'include_screenshots': self.skill_level == SkillLevel.NEWBIE,
        }
        
        return style
    
    def _get_explanation_depth(self) -> str:
        """Determine how detailed explanations should be"""
        if self.skill_level == SkillLevel.NEWBIE:
            return "very_simple"
        elif self.skill_level == SkillLevel.INTERMEDIATE:
            return "step_by_step"
        elif self.skill_level == SkillLevel.ADVANCED:
            return "technical"
        else:
            return "expert"
    
    def _get_detail_level(self) -> int:
        """Return detail level 1-5"""
        levels = {
            SkillLevel.NEWBIE: 1,
            SkillLevel.INTERMEDIATE: 2,
            SkillLevel.ADVANCED: 3,
            SkillLevel.EXPERT: 4,
        }
        return levels.get(self.skill_level, 2)
    
    def should_offer_alternatives(self) -> bool:
        """Should we offer alternative solutions?"""
        return (
            self.skill_level != SkillLevel.NEWBIE and
            len(self.issue_history) > 0  # Has interacted before
        )
    
    def get_context_summary(self) -> str:
        """Get human-readable summary of user profile for AI context"""
        return f"""
User Profile Summary:
- Skill: {self.skill_level.value}
- Time Available: {self.time_availability.value}
- Experience: {len(self.issue_history)} issues handled, {self.successful_resolutions} resolved
- Device: {self.device_type or 'Unknown'}
- Current State: {'Frustrated' if self.is_frustrated else 'Normal'}
- Satisfaction (avg): {sum(self.satisfaction_ratings) / len(self.satisfaction_ratings):.1f}/5 if ratings exist
- Language: {self.language_preference}
"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for storage"""
        return {
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat(),
            'last_interaction': self.last_interaction.isoformat(),
            'skill_level': self.skill_level.value,
            'technical_vocabulary': self.technical_vocabulary,
            'device_type': self.device_type,
            'device_specs': self.device_specs,
            'time_availability': self.time_availability.value,
            'preferred_explanation': self.preferred_explanation,
            'language_preference': self.language_preference,
            'total_interactions': self.total_interactions,
            'successful_resolutions': self.successful_resolutions,
            'escalations': self.escalations,
            'issue_history': self.issue_history,
            'average_satisfaction': (
                sum(self.satisfaction_ratings) / len(self.satisfaction_ratings)
                if self.satisfaction_ratings else 0
            ),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create profile from stored dictionary"""
        profile = cls(data['phone_number'])
        
        # Restore fields
        profile.created_at = datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat()))
        profile.last_interaction = datetime.fromisoformat(data.get('last_interaction', datetime.utcnow().isoformat()))
        profile.skill_level = SkillLevel(data.get('skill_level', 'newbie'))
        profile.technical_vocabulary = data.get('technical_vocabulary', 0.0)
        profile.device_type = data.get('device_type')
        profile.device_specs = data.get('device_specs', {})
        profile.time_availability = TimeAvailability(data.get('time_availability', 'short'))
        profile.preferred_explanation = data.get('preferred_explanation', 'step_by_step')
        profile.language_preference = data.get('language_preference', 'id')
        profile.total_interactions = data.get('total_interactions', 0)
        profile.successful_resolutions = data.get('successful_resolutions', 0)
        profile.escalations = data.get('escalations', 0)
        profile.issue_history = data.get('issue_history', [])
        
        return profile


class UserProfileManager:
    """
    Manages all user profiles with caching and persistence.
    Coordinates profile loading, updating, and storage.
    """
    
    def __init__(self):
        self.profiles: Dict[str, UserProfile] = {}
        logger.info("✅ User Profile Manager initialized")
    
    def get_or_create_profile(self, phone_number: str) -> UserProfile:
        """Get existing profile or create new one"""
        if phone_number not in self.profiles:
            self.profiles[phone_number] = UserProfile(phone_number)
            logger.debug(f"👤 Created new profile for {phone_number}")
        
        return self.profiles[phone_number]
    
    def update_profile(self, phone_number: str, **kwargs):
        """Update user profile with new information"""
        profile = self.get_or_create_profile(phone_number)
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)


# Singleton instance
user_profile_manager = UserProfileManager()
