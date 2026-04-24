"""
Adaptive Dialog Flow Engine - Intelligent conversation flow that adapts to context
Instead of linear scripts, uses state machine with intelligent transitions

Note: This uses its own DialogState enum (conceptual states) separate from
session_manager.DialogState (actual chatbot states). They serve different purposes.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from enum import Enum
from datetime import datetime

from app.utils.user_profile_manager import UserProfile, TimeAvailability
from app.utils.semantic_kb_matcher import SemanticKBMatcher

logger = logging.getLogger(__name__)


class AdaptiveDialogState(str, Enum):
    """Conceptual conversation states for adaptive dialog flow
    
    NOTE: This is separate from session_manager.DialogState which drives
    the actual chatbot state machine. This enum is used only by
    AdaptiveDialogFlowEngine for conceptual flow analysis.
    """
    GREETING = "greeting"
    LISTENING = "listening"
    ANALYZING = "analyzing"
    PROPOSING = "proposing"
    TROUBLESHOOTING = "troubleshooting"
    VALIDATING = "validating"
    ESCALATING = "escalating"
    RESOLVED = "resolved"
    FEEDBACK = "feedback"


class DialogTransition:
    """Represents a state transition with conditions"""
    
    def __init__(
        self,
        from_state: AdaptiveDialogState,
        to_state: AdaptiveDialogState,
        condition: callable,
        priority: int = 1
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.priority = priority


class AdaptiveDialogFlowEngine:
    """
    Manages intelligent conversation flow that adapts to:
    - User expertise level
    - Problem complexity
    - User frustration
    - Time constraints
    - Success indicators
    """
    
    def __init__(self, semantic_matcher: Optional[SemanticKBMatcher] = None):
        self.semantic_matcher = semantic_matcher
        self.transitions: List[DialogTransition] = []
        self._register_transitions()
        logger.info("✅ Adaptive Dialog Flow Engine initialized")
    
    def _register_transitions(self):
        """Register all possible state transitions with conditions"""
        
        # GREETING → LISTENING (after greeting, ready to hear problem)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.GREETING,
            AdaptiveDialogState.LISTENING,
            lambda ctx: ctx.get('received_problem_indication', False),
            priority=10
        ))
        
        # GREETING → FEEDBACK (user doesn't have new problem)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.GREETING,
            AdaptiveDialogState.FEEDBACK,
            lambda ctx: ctx.get('intent') == 'feedback' and ctx.get('total_issues', 0) > 0,
            priority=5
        ))
        
        # LISTENING → ANALYZING (collected enough details)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.LISTENING,
            AdaptiveDialogState.ANALYZING,
            lambda ctx: self._is_problem_detailed_enough(ctx),
            priority=10
        ))
        
        # LISTENING → ESCALATING (user too frustrated, give up early)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.LISTENING,
            AdaptiveDialogState.ESCALATING,
            lambda ctx: (
                ctx.get('frustration_level', 0) > 0.8 and
                ctx.get('time_available') == TimeAvailability.URGENT.value
            ),
            priority=15  # High priority - escalate frustrated users ASAP
        ))
        
        # ANALYZING → PROPOSING (understood the problem)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.ANALYZING,
            AdaptiveDialogState.PROPOSING,
            lambda ctx: ctx.get('solution_confidence', 0) >= 0.6,
            priority=10
        ))
        
        # ANALYZING → ESCALATING (don't understand, confidence too low)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.ANALYZING,
            AdaptiveDialogState.ESCALATING,
            lambda ctx: (
                ctx.get('solution_confidence', 0) < 0.4 and
                ctx.get('analysis_attempts', 0) >= 2
            ),
            priority=12
        ))
        
        # PROPOSING → TROUBLESHOOTING (user accepts solution)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.PROPOSING,
            AdaptiveDialogState.TROUBLESHOOTING,
            lambda ctx: ctx.get('user_accepted_solution', False),
            priority=10
        ))
        
        # PROPOSING → ESCALATING (user rejects, prefers human)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.PROPOSING,
            AdaptiveDialogState.ESCALATING,
            lambda ctx: (
                ctx.get('user_rejected', False) and
                ctx.get('alternatives_offered', 0) >= 1
            ),
            priority=11
        ))
        
        # TROUBLESHOOTING → VALIDATING (user reports attempting step)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.TROUBLESHOOTING,
            AdaptiveDialogState.VALIDATING,
            lambda ctx: ctx.get('step_attempted', False),
            priority=10
        ))
        
        # TROUBLESHOOTING → ESCALATING (too many failed attempts)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.TROUBLESHOOTING,
            AdaptiveDialogState.ESCALATING,
            lambda ctx: ctx.get('failed_step_count', 0) >= 3,
            priority=13
        ))
        
        # VALIDATING → RESOLVED (solution worked!)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.VALIDATING,
            AdaptiveDialogState.RESOLVED,
            lambda ctx: ctx.get('solution_worked', False),
            priority=10
        ))
        
        # VALIDATING → TROUBLESHOOTING (solution didn't work, try next step)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.VALIDATING,
            AdaptiveDialogState.TROUBLESHOOTING,
            lambda ctx: (
                not ctx.get('solution_worked', False) and
                ctx.get('steps_remaining', 0) > 0
            ),
            priority=10
        ))
        
        # VALIDATING → ESCALATING (ran out of steps, nothing worked)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.VALIDATING,
            AdaptiveDialogState.ESCALATING,
            lambda ctx: (
                not ctx.get('solution_worked', False) and
                ctx.get('steps_remaining', 0) == 0
            ),
            priority=12
        ))
        
        # RESOLVED → FEEDBACK (ask for satisfaction rating)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.RESOLVED,
            AdaptiveDialogState.FEEDBACK,
            lambda ctx: True,  # Always ask for feedback after resolution
            priority=5
        ))
        
        # ESCALATING → FEEDBACK (after escalation, ask for feedback)
        self.transitions.append(DialogTransition(
            AdaptiveDialogState.ESCALATING,
            AdaptiveDialogState.FEEDBACK,
            lambda ctx: ctx.get('escalation_completed', False),
            priority=5
        ))
        
        logger.info(f"✅ Registered {len(self.transitions)} state transitions")
    
    def _is_problem_detailed_enough(self, context: Dict) -> bool:
        """Check if we have enough details about the problem"""
        problem_desc = context.get('problem_description', '')
        attempts_count = context.get('detail_collection_attempts', 0)
        min_length = 20  # Minimum characters
        
        # Accept if we have enough detail or already asked multiple times
        return len(problem_desc) >= min_length or attempts_count >= 2
    
    def get_next_state(self, current_state: AdaptiveDialogState, context: Dict) -> Tuple[AdaptiveDialogState, str]:
        """
        Determine next state based on current state and context.
        Returns (next_state, reason_for_transition).
        """
        
        # Get applicable transitions
        applicable = [
            t for t in self.transitions
            if t.from_state == current_state
        ]
        
        # Sort by priority (higher = more urgent)
        applicable.sort(key=lambda t: t.priority, reverse=True)
        
        # Find first transition where condition is true
        for transition in applicable:
            try:
                if transition.condition(context):
                    logger.info(
                        f"📍 Dialog flow: {current_state.value} → {transition.to_state.value}"
                    )
                    return (transition.to_state, f"Transitioned based on priority {transition.priority}")
            except Exception as e:
                logger.warning(f"⚠️ Transition condition error: {e}")
        
        # No transition, stay in current state
        logger.debug(f"⚠️ No transition from {current_state.value}")
        return (current_state, "Staying in current state")
    
    def should_escalate_early(self, context: Dict) -> bool:
        """
        Determine if we should escalate early (don't torture the user).
        """
        
        frustration = context.get('frustration_level', 0)
        attempts = context.get('failed_attempt_count', 0)
        time = context.get('total_time_spent_minutes', 0)
        confidence = context.get('solution_confidence', 0)
        
        escalation_triggers = [
            (frustration > 0.7, "User very frustrated"),
            (attempts > 3, "Multiple failed attempts"),
            (time > 30 and frustration > 0.5, "Too much time, user getting frustrated"),
            (confidence < 0.3 and attempts > 1, "Low confidence after attempting"),
        ]
        
        for trigger, reason in escalation_triggers:
            if trigger:
                logger.warning(f"⚠️ Early escalation recommended: {reason}")
                return True
        
        return False
    
    def get_next_action(
        self,
        current_state: AdaptiveDialogState,
        user_profile: Optional[UserProfile] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate next action/prompt for the AI based on current state.
        Highly adaptive and context-aware.
        """
        
        context = context or {}
        
        actions_map = {
            AdaptiveDialogState.GREETING: self._action_greeting,
            AdaptiveDialogState.LISTENING: self._action_listening,
            AdaptiveDialogState.ANALYZING: self._action_analyzing,
            AdaptiveDialogState.PROPOSING: self._action_proposing,
            AdaptiveDialogState.TROUBLESHOOTING: self._action_troubleshooting,
            AdaptiveDialogState.VALIDATING: self._action_validating,
            AdaptiveDialogState.ESCALATING: self._action_escalating,
            AdaptiveDialogState.RESOLVED: self._action_resolved,
            AdaptiveDialogState.FEEDBACK: self._action_feedback,
        }
        
        action_fn = actions_map.get(current_state)
        if not action_fn:
            return {'action': 'error', 'message': f'Unknown state: {current_state}'}
        
        return action_fn(user_profile, context)
    
    def _action_greeting(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Greeting action"""
        greeting = "Halo! Selamat datang di TRAMOS Support 👋"
        if user and user.total_interactions > 0:
            greeting = f"Halo {user.phone_number}! Ada yang bisa kami bantu? 🤔"
        
        return {
            'state': AdaptiveDialogState.GREETING.value,
            'action': 'greet',
            'message': greeting,
            'next_step': 'Wait for user problem description',
        }
    
    def _action_listening(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Listening action - collect problem details"""
        
        question = "Bisa jelaskan masalahnya lebih detail? 🔍"
        
        if user and user.is_frustrated:
            question += "\n(Saya tahu ini frustasi, tapi detail membantu saya menemukan solusinya dengan cepat)"
        
        if user and user.time_availability == TimeAvailability.URGENT.value:
            question = "Terburu-buru? Jelaskan masalahnya sesingkat mungkin, saya akan bantu dengan cepat ⚡"
        
        return {
            'state': AdaptiveDialogState.LISTENING.value,
            'action': 'ask_detail',
            'message': question,
            'collect_fields': ['problem_description', 'device_info', 'steps_tried'],
            'next_step': 'Analyze collected details',
        }
    
    def _action_analyzing(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Analyzing action - think through the problem"""
        
        return {
            'state': AdaptiveDialogState.ANALYZING.value,
            'action': 'analyze',
            'message': "Saya sedang menganalisis masalahnya... ⏳",
            'analyze_tools': ['semantic_matching', 'kb_search', 'user_history'],
            'next_step': 'Generate solution or escalate',
        }
    
    def _action_proposing(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Proposing action - suggest solution"""
        
        message = "Mari kita coba mengatasi masalahnya:"
        
        # If advanced user, be more direct
        if user and user.skill_level.value == 'advanced':
            message = "Saya punya solusinya:"
        
        return {
            'state': AdaptiveDialogState.PROPOSING.value,
            'action': 'propose_solution',
            'message': message,
            'include': ['first_step', 'expected_outcome', 'if_fails_message'],
            'next_step': 'Wait for user response - accepted or rejected?',
        }
    
    def _action_troubleshooting(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Troubleshooting action - guide through steps"""
        
        current_step = ctx.get('current_step', 1)
        
        return {
            'state': AdaptiveDialogState.TROUBLESHOOTING.value,
            'action': 'execute_troubleshooting',
            'message': f"Langkah {current_step}: [Specific instruction for this step]",
            'include': ['detailed_instructions', 'verification_criteria', 'help_if_stuck'],
            'is_progressive': True,  # One step at a time, not overwhelming
            'next_step': 'Ask user to report back after attempting',
        }
    
    def _action_validating(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Validating action - check if solution worked"""
        
        return {
            'state': AdaptiveDialogState.VALIDATING.value,
            'action': 'validate_outcome',
            'message': "Apakah langkah tadi berhasil? 🤞",
            'options': ['worked', 'partially_worked', 'failed', 'not_attempted'],
            'next_step': 'Based on response - next troubleshooting step or escalate',
        }
    
    def _action_escalating(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Escalating action - hand off to human"""
        
        reason = ctx.get('escalation_reason', 'unknown')
        
        message = (
            "Sepertinya ini memerlukan bantuan dari tim expert kami. "
            "Saya akan hubungi mereka sekarang.  👤 -> 👥"
        )
        
        if reason == 'frustrated':
            message = (
                "Saya mengerti ini sudah frustasi. "
                "Mari saya hubungi tim expert kami untuk bantuan personal. 🤝"
            )
        
        return {
            'state': AdaptiveDialogState.ESCALATING.value,
            'action': 'escalate_to_human',
            'message': message,
            'escalation_priority': ctx.get('escalation_priority', 'normal'),
            'next_step': 'Human support takes over',
        }
    
    def _action_resolved(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Resolved action - celebrate solution"""
        
        message = "Wah! Masalahnya sudah solved! 🎉"
        
        if user and user.skill_level.value == 'advanced':
            message = "Masalah terselesaikan! Bagus! 👍"
        
        return {
            'state': AdaptiveDialogState.RESOLVED.value,
            'action': 'celebrate_resolution',
            'message': message,
            'record_metrics': {
                'resolution_time': ctx.get('total_time_spent_minutes'),
                'attempts': ctx.get('step_count'),
                'success': True,
            },
            'next_step': 'Ask for feedback',
        }
    
    def _action_feedback(self, user: Optional[UserProfile], ctx: Dict) -> Dict:
        """Feedback action - gather user satisfaction"""
        
        return {
            'state': AdaptiveDialogState.FEEDBACK.value,
            'action': 'collect_feedback',
            'message': "Berapa rating untuk bantuan kami? (1-5 bintang) ⭐",
            'options': ['1', '2', '3', '4', '5'],
            'next_step': 'Thank user and end conversation',
        }
    
    def get_conversation_summary(self, context: Dict) -> str:
        """Generate human-readable summary of conversation journey"""
        
        states_visited = context.get('states_visited', [])
        time_spent = context.get('total_time_spent_minutes', 0)
        steps_taken = context.get('step_count', 0)
        success = context.get('resolved', False)
        
        summary = f"""
Conversation Journey:
- Path: {' → '.join(states_visited)}
- Time spent: {time_spent} minutes
- Steps attempted: {steps_taken}
- Outcome: {'✅ RESOLVED' if success else '⚠️ ESCALATED'}
"""
        
        return summary


# Singleton instance
dialog_flow_engine = AdaptiveDialogFlowEngine()
