"""
Smart Prompt Engineer - Generate sophisticated, context-aware prompts for LLM
Creates prompts that are specific to user's problem, history, and profile
"""

import logging
from typing import Optional, Dict, Any, List
from app.utils.user_profile_manager import UserProfile
from app.utils.semantic_kb_matcher import SemanticKBMatcher

logger = logging.getLogger(__name__)


class SmartPromptEngineer:
    """
    Generates LLM prompts that are:
    - Specific to user's actual problem (not generic)
    - Aware of user's skill level and history
    - Constrained to avoid hallucinations
    - Optimized for Mistral model characteristics
    """
    
    def __init__(self, semantic_matcher: Optional[SemanticKBMatcher] = None):
        self.semantic_matcher = semantic_matcher
        logger.info("✅ Smart Prompt Engineer initialized")
    
    def generate_intent_detection_prompt(
        self,
        user_message: str,
        context_history: Optional[List[str]] = None,
        user_profile: Optional[UserProfile] = None
    ) -> str:
        """
        Generate prompt to accurately detect user intent.
        Context-aware, not just pattern matching.
        """
        
        context_section = ""
        if context_history and len(context_history) > 0:
            recent_context = " ".join(context_history[-3:])  # Last 3 messages
            context_section = f"\nRecent conversation: {recent_context}"
        
        profile_section = ""
        if user_profile:
            profile_section = f"""
User Profile Context:
- Technical level: {user_profile.skill_level.value}
- Current mood: {'frustrated' if user_profile.is_frustrated else 'neutral'}
- Time available: {user_profile.time_availability.value}
- Previous issues: {len(user_profile.issue_history)}
"""
        
        prompt = f"""You are TRAMOS AI assistant. Analyze user message for INTENT.

MESSAGE: "{user_message}"{context_section}{profile_section}

Determine SINGLE best intent. Return ONLY valid JSON, no other text:
{{"intent": "VALUE", "category": null_or_string, "confidence": 0.0-1.0, "tone": "VALUE"}}

INTENT options ONLY: greeting | problem | resolved | unresolved | escalate | feedback | unknown
CATEGORY options: gps | connectivity | device | vehicle | app | ticket | or null
TONE options: urgent | frustrated | neutral | satisfied | seeking_help
CONFIDENCE: 0.0-1.0 (how sure are you)

Think step by step:
1. What does user ACTUALLY want?
2. Is this the first message or continuation?
3. What emotion/urgency is expressed?
4. If unclear, respond with "unknown" intent

Respond with ONLY JSON."""
        
        return prompt
    
    def generate_problem_context_analysis_prompt(
        self,
        problem_description: str,
        category: Optional[str],
        user_profile: Optional[UserProfile] = None,
        previous_attempts: Optional[List[str]] = None,
        kb_matches: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate prompt to deeply understand the specific problem.
        NOT generic analysis - specific to THIS problem.
        """
        
        profile_context = ""
        if user_profile:
            profile_context = f"""
User Context:
- Skill level: {user_profile.skill_level.value}
- Device: {user_profile.device_type or 'Unknown'}
- Previous success rate: {user_profile.successful_resolutions}/{len(user_profile.issue_history)}
- Frustration level: {'HIGH' if user_profile.is_frustrated else 'normal'}
"""
        
        attempts_context = ""
        if previous_attempts:
            attempts_context = f"""
Already tried:
{chr(10).join(f"- {attempt}" for attempt in previous_attempts[-3:])}

These didn't work, so diagnose DIFFERENT root cause.
"""
        
        kb_context = ""
        if kb_matches:
            kb_context = f"""
Similar known issues:
{chr(10).join(f"- {m['title']}: {m.get('similarity', 0):.0%} match" for m in kb_matches[:2])}

Use these as reference but adapt to THIS specific problem.
"""
        
        prompt = f"""Analyze this SPECIFIC technical problem in depth.

PROBLEM: "{problem_description}"
CATEGORY: {category or 'Unknown'}
{profile_context}{attempts_context}{kb_context}

Your job: Understand ROOT CAUSE of THIS problem, not generic diagnosis.

Return ONLY valid JSON, no other text:
{{
  "root_cause_hypothesis": "What you think is ACTUAL root cause for THEIR situation",
  "why_this_cause": "2-3 sentences explaining why",
  "symptoms_detected": ["list", "of", "SPECIFIC symptoms mentioned"],
  "possible_causes": ["MOST likely (99%)", "less likely (50%)", "least likely (10%)"],
  "severity": "critical | high | medium | low",
  "needs_immediate_action": true | false,
  "next_priority_question": "If you need more info, what should we ask?",
  "confidence_level": 0.0-1.0,
  "hallucination_risk": "low | medium | high (be honest!)"
}}

Requirements:
- Be SPECIFIC to their problem, not generic
- Don't hallucinate - if unsure, admit it
- If previous attempts failed, suggest DIFFERENT approach
- Give confidence score honestly
- Acknowledge if this might be hardware issue

Respond with ONLY JSON."""
        
        return prompt
    
    def generate_troubleshooting_steps_prompt(
        self,
        problem_description: str,
        category: Optional[str],
        user_profile: Optional[UserProfile] = None,
        problem_analysis: Optional[Dict] = None,
        previous_failures: Optional[List[str]] = None
    ) -> str:
        """
        Generate prompt for creating specific troubleshooting steps.
        Progressive, not overwhelming. Adapted to user's skill level.
        """
        
        skill_guidance = ""
        if user_profile:
            if user_profile.skill_level.value == 'newbie':
                skill_guidance = """
For NEWBIE user:
- Start with EASIEST steps first
- No technical jargon
- Very detailed instructions
- Include "how to verify this worked"
"""
            elif user_profile.skill_level.value == 'advanced':
                skill_guidance = """
For ADVANCED user:
- Can skip basic checks
- Use technical language
- Suggest alternative approaches
- Explain WHY each step matters
"""
        
        analysis_context = ""
        if problem_analysis:
            analysis_context = f"""
Problem Analysis:
- Root cause: {problem_analysis.get('root_cause_hypothesis')}
- Severity: {problem_analysis.get('severity')}
- Confidence: {problem_analysis.get('confidence_level')}
"""
        
        failures_context = ""
        if previous_failures and len(previous_failures) > 0:
            failures_context = f"""
These already FAILED:
{chr(10).join(f"- {fail}" for fail in previous_failures[-2:])}

Generate DIFFERENT approach. Don't repeat failed steps!
"""
        
        prompt = f"""Generate troubleshooting steps for THIS SPECIFIC problem.

PROBLEM: "{problem_description}"
CATEGORY: {category or 'Unknown'}{analysis_context}{failures_context}{skill_guidance}

Generate 3-5 SPECIFIC, ACTIONABLE steps that:
1. Are relevant to THIS problem (not generic)
2. Progressively diagnose and resolve
3. Each step can be completed in <10 minutes
4. Include CLEAR success criteria for each
5. Don't repeat failed attempts
6. Are realistic (user is {user_profile.skill_level.value if user_profile else 'unknown'} level)

Return ONLY valid JSON:
{{
  "steps": [
    {{
      "number": 1,
      "title": "Short action title",
      "why_try_this": "Why this specific step helps for THEIR problem",
      "instructions": [
        "Specific step 1 for this problem",
        "Specific step 2 for this problem"
      ],
      "verification": "How to know if this step worked",
      "expected_outcome": "What should happen if successful",
      "time_estimate_minutes": 5-10,
      "difficulty": "easy | medium | hard",
      "if_fails": "What they should try next"
    }}
  ],
  "total_estimated_time_minutes": 20,
  "success_probability": 0.0-1.0,
  "escalation_trigger": "If X happens, escalate instead",
  "important_caveats": "Any warnings or things to avoid",
  "ai_confidence": 0.0-1.0
}}

CONSTRAINTS:
- Only include steps you're confident about
- Be honest about confidence level
- If uncertain, mark escalation_trigger
- Make each step specific to their problem

Respond with ONLY JSON."""
        
        return prompt
    
    def generate_response_prompt(
        self,
        user_message: str,
        intent: str,
        category: Optional[str] = None,
        user_profile: Optional[UserProfile] = None,
        semantic_matches: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate prompt for crafting natural, non-template response.
        """
        
        profile_guidance = ""
        if user_profile:
            style = user_profile.get_response_style()
            profile_guidance = f"""
User Preferences:
- Skill level: {style['skill_level']}
- Explanation depth: {style['explanation_depth']}
- Time available: {user_profile.time_availability.value}
- Language: {user_profile.language_preference}
- Current mood: {'frustrated' if user_profile.is_frustrated else 'normal'}
"""
        
        matches_context = ""
        if semantic_matches and len(semantic_matches) > 0:
            top_match = semantic_matches[0]
            matches_context = f"""
Similar issues resolved before:
- {top_match.get('title')}: {top_match.get('similarity', 0):.0%} match
You can reference this experience.
"""
        
        prompt = f"""You are TRAMOS support AI. Reply naturally, like helping a colleague.

USER SAID: "{user_message}"
INTENT: {intent}
CATEGORY: {category or 'none'}{profile_guidance}{matches_context}

Generate response that:
1. Acknowledges THEIR specific situation (not generic)
2. Shows you understood the problem
3. Proposes ONE clear next action based on THEIR actual problem
4. Is warm but professional
5. Language: Indonesian (natural, not robotic)
6. Length: 2-4 sentences max
7. Emoji: 1 max, only if natural

Response rules:
- NO templates
- NO generic phrases
- NO "mari kita troubleshoot" without knowing WHAT
- BE SPECIFIC to their situation
- If frustrated, validate emotion first
- NO technical jargon for newbies

Generate ONLY the response text, nothing else."""
        
        return prompt
    
    def generate_escalation_prompt(
        self,
        problem_summary: str,
        user_profile: Optional[UserProfile] = None,
        escalation_reason: str = "unknown"
    ) -> str:
        """
        Generate prompt to craft empathetic escalation message.
        """
        
        profile_context = ""
        if user_profile:
            profile_context = f"""
User: {user_profile.phone_number}
- Previous interactions: {len(user_profile.issue_history)}
- Frustration level: {'HIGH' if user_profile.is_frustrated else 'normal'}
- Time available: {user_profile.time_availability.value}
"""
        
        prompt = f"""Craft an empathetic escalation message to human support.

PROBLEM: {problem_summary}
REASON: {escalation_reason}
{profile_context}

Message should:
1. Acknowledge we couldn't resolve it fully (be honest)
2. Validate their frustration if present
3. Set realistic expectation for next step
4. Show we care about resolution
5. Indonesian language
6. Professional but warm

Generate ONLY the message text."""
        
        return prompt
    
    def validate_constraint_adherence(
        self,
        prompt: str,
        model: str = "mistral"
    ) -> Dict[str, Any]:
        """
        Check if prompt is optimized for the LLM model.
        """
        checks = {
            'requests_json_only': '"{' in prompt or '{"' in prompt,
            'no_excessive_formatting': prompt.count('*') < 5,
            'clear_constraints': any(
                word in prompt.lower()
                for word in ['only', 'respond', 'json', 'no other', "don't"]
            ),
            'reasonable_length': 200 < len(prompt) < 2000,
            'has_role_context': any(
                word in prompt.lower()
                for word in ['you are', 'your job', 'roleplaying']
            ),
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        return {
            'checks': checks,
            'score': passed / total,
            'recommendation': 'good' if passed >= 4 else 'needs_improvement',
        }


# Singleton instance
smart_prompt_engineer = SmartPromptEngineer()
