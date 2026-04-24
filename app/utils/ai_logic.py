"""AI-based logic for troubleshooting and intent detection - Ollama/Mistral Version (ENHANCED)
Now with:
- Semantic KB matching (instead of keyword-only)
- User profile personalization
- Solution effectiveness tracking
- Smart prompt engineering
- Adaptive dialog flow
"""
import logging
from typing import Tuple, Optional, Dict, Any
import json
import requests
from datetime import datetime

from app.config import settings
from app.utils.kb_troubleshooting import KB_TROUBLESHOOTING
from app.utils.semantic_kb_matcher import SemanticKBMatcher
from app.utils.user_profile_manager import UserProfileManager
from app.utils.solution_effectiveness_tracker import SolutionEffectivenessTracker, SolutionOutcome
from app.utils.smart_prompt_engineer import SmartPromptEngineer
from app.utils.dialog_flow_engine import AdaptiveDialogFlowEngine, AdaptiveDialogState

logger = logging.getLogger(__name__)

# Ollama Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"
OLLAMA_TIMEOUT = 30  # seconds


class AITroubleshootingEngine:
    """AI-powered troubleshooting with LLM support (Ollama/Mistral - Local) - ENHANCED VERSION
    
    Now includes:
    - Semantic KB matching (not keyword-only) ✨ NEW
    - User profile personalization ✨ NEW
    - Solution effectiveness tracking ✨ NEW
    - Smart prompt engineering ✨ NEW
    - Adaptive dialog flow ✨ NEW
    """
    
    def __init__(self):
        """Initialize AI engine with all enhancements"""
        self.use_llm = settings.USE_LLM
        self.ollama_available = self._check_ollama_connection()
        self.fallback_count = 0
        
        # ✨ NEW: Initialize semantic matcher
        self.semantic_matcher = SemanticKBMatcher()
        
        # ✨ NEW: Initialize user profile manager
        self.user_profile_manager = UserProfileManager()
        
        # ✨ NEW: Initialize solution effectiveness tracker
        self.solution_tracker = SolutionEffectivenessTracker()
        
        # ✨ NEW: Initialize smart prompt engineer
        self.prompt_engineer = SmartPromptEngineer()
        
        # ✨ NEW: Initialize dialog flow engine
        self.dialog_flow = AdaptiveDialogFlowEngine(self.semantic_matcher)
        
        if self.use_llm and self.ollama_available:
            logger.info(f"✅ Ollama/Mistral LLM initialized (local): {OLLAMA_MODEL}")
            logger.info("✅ With semantic matching, user profiling, and adaptive dialog flow")
        elif self.use_llm:
            logger.warning("⚠️ Ollama not running. Falling back to keyword matching.")
            logger.warning("   Start Ollama with: ollama serve")
            self.use_llm = False
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=3
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama connection check failed: {e}")
            return False
    
    # Knowledge base categories derived from KB_TROUBLESHOOTING (single source of truth)
    @property
    def KB_CATEGORIES(self):
        return list(KB_TROUBLESHOOTING.keys())
    
    @property
    def KB_KEYWORDS(self):
        return {cat: data.get("keywords", []) for cat, data in KB_TROUBLESHOOTING.items()}
    
    def _detect_intent_with_ollama(self, message: str, context: Optional[str] = None) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Use Ollama/Mistral to detect intent - ENHANCED & ROBUST VERSION"""
        try:
            context_section = f"\n\nPrevious context: {context}" if context else ""
            
            prompt = f"""You are a professional TRAMOS fleet support AI assistant. Your job is to understand user intent accurately.

Analyze this user message:
"{message}"{context_section}

IMPORTANT: Return ONLY VALID JSON (no markdown, no extra text, no explanation):
{{"intent": "value", "category": null_or_string, "confidence": 0.0-1.0, "tone": "value"}}

Intent must be ONE of: greeting, problem, resolved, unresolved, escalate, feedback, unknown
Category must be ONE of: gps, connectivity, device, vehicle, app, ticket, or null (if unknown)
Tone must be ONE of: urgent, frustrated, neutral, satisfied, seeking_help

If the message mentions:
- GPS, location, tracking, signal, lokasi, sinyal → category: "gps"
- Internet, connection, network, offline, koneksi → category: "connectivity"  
- Device, crash, freeze, camera → category: "device"
- Vehicle, mogok, breakdown, stall → category: "vehicle"
- App, aplikasi, software → category: "app"
- Ticket, tiket, support → category: "ticket"
- Or if category unclear → category: null

RESPOND WITH ONLY JSON, NOTHING ELSE."""

            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,  # Even lower for consistency
                    "top_p": 0.9,
                    "top_k": 30,
                    "num_predict": 100,
                    "repeat_penalty": 1.1,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Ollama API error: {response.status_code}")
                return ("unknown", None, {"source": "ollama_error", "error": f"HTTP {response.status_code}"})
            
            response_data = response.json()
            response_text = response_data.get("response", "").strip()
            
            # Clean up response
            response_text = response_text.replace("```json", "").replace("```", "")
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                result = json.loads(response_text)
                
                intent = result.get("intent", "unknown")
                category = result.get("category")
                confidence = float(result.get("confidence", 0.5))
                tone = result.get("tone", "neutral")
                
                # Validate values
                if category == "null" or category is None:
                    category = None
                
                if intent not in ["greeting", "problem", "resolved", "unresolved", "escalate", "feedback", "unknown"]:
                    intent = "unknown"
                
                logger.debug(f"🧠 Ollama: intent={intent}, category={category}, conf={confidence:.1%}")
                
                return (intent, category, {
                    "source": "ollama",
                    "confidence": confidence,
                    "tone": tone,
                })
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse failed: {str(e)[:50]}")
                return ("unknown", None, {"source": "parse_error"})
            
        except requests.exceptions.Timeout:
            logger.error("⏱️ Ollama request timeout")
            return ("unknown", None, {"source": "timeout"})
        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama connection failed")
            return ("unknown", None, {"source": "connection_error"})
        except Exception as e:
            logger.error(f"❌ Ollama error: {str(e)[:100]}")
            return ("unknown", None, {"source": "unknown_error"})
    
    def detect_intent(self, message: str, context: Optional[str] = None, phone_number: Optional[str] = None) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """
        Detect intent from user message with LLM + smart prompt engineering
        
        ✨ NEW: Uses smart_prompt_engineer instead of hardcoded prompts
        ✨ NEW: Uses user profile for context awareness
        ✨ NEW: Returns enhanced metadata
        
        Returns: (intent, category, metadata)
        """
        # ✨ NEW: Update user profile from message
        if phone_number:
            self.user_profile_manager.update_from_message(phone_number, message)
            user_profile = self.user_profile_manager.get_or_create_profile(phone_number)
        else:
            user_profile = None
        
        # Try LLM first if available
        if self.use_llm and self.ollama_available:
            # ✨ NEW: Use smart prompt engineer to generate better intent detection prompt
            prompt = self.prompt_engineer.generate_intent_detection_prompt(
                message=message,
                context_history=[context] if context else [],
                user_profile=user_profile
            )
            
            intent, category, metadata = self._detect_intent_with_custom_prompt(
                prompt,
                user_profile
            )
            
            # Use LLM result if confidence is acceptable
            confidence = metadata.get("confidence", 0)
            if isinstance(confidence, (int, float)) and confidence >= settings.AI_CONFIDENCE_THRESHOLD:
                if phone_number:
                    logger.info(f"🧠 Intent detected (smart): {intent} ({confidence:.0%})")
                return (intent, category, metadata)
            elif isinstance(confidence, (int, float)):
                logger.debug(f"⚠️ Low confidence ({confidence:.1%}), using keywords")
        
        # Fallback to keyword matching
        self.fallback_count += 1
        intent, category = self._detect_intent_with_keywords(message)
        return (intent, category, {"source": "keywords", "confidence": 0.6})
    
    def _detect_intent_with_custom_prompt(self, prompt: str, user_profile: Optional[Any]) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Execute intent detection with custom prompt (from smart_prompt_engineer)"""
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 30,
                    "num_predict": 100,
                    "repeat_penalty": 1.1,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Ollama API error: {response.status_code}")
                return ("unknown", None, {"source": "ollama_error", "error": f"HTTP {response.status_code}"})
            
            response_data = response.json()
            response_text = response_data.get("response", "").strip()
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                result = json.loads(response_text)
                
                intent = result.get("intent", "unknown")
                category = result.get("category")
                confidence = float(result.get("confidence", 0.5))
                tone = result.get("tone", "neutral")
                
                if category == "null" or category is None:
                    category = None
                
                if intent not in ["greeting", "problem", "resolved", "unresolved", "escalate", "feedback", "unknown"]:
                    intent = "unknown"
                
                return (intent, category, {
                    "source": "ollama_smart",
                    "confidence": confidence,
                    "tone": tone,
                })
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse failed: {str(e)[:50]}")
                return ("unknown", None, {"source": "parse_error"})
            
        except Exception as e:
            logger.error(f"❌ Intent detection error: {str(e)[:100]}")
            return ("unknown", None, {"source": "error", "error": str(e)[:50]})
    
    def _detect_intent_with_keywords(self, message: str) -> Tuple[str, Optional[str]]:
        """Fallback: Keyword-based intent detection"""
        message_lower = message.lower()
        
        # Check for greeting
        if any(w in message_lower for w in ["halo", "pagi", "siang", "hi", "hello", "hei"]):
            return ("greeting", None)
        
        # Check for problem category FIRST (before checking resolution)
        for issue_key, issue_data in KB_TROUBLESHOOTING.items():
            if any(kw in message_lower for kw in issue_data.get("keywords", [])):
                return ("problem", issue_key)
        
        # Check resolution
        if any(w in message_lower for w in ["ya", "yes", "ok", "sudah", "jadi", "berhasil", "fixed", "worked"]):
            return ("resolved", None)
        
        if any(w in message_lower for w in ["tidak", "no", "gak", "nggak", "belum", "tetap", "masih error"]):
            return ("unresolved", None)
        
        # Check escalation need
        if any(w in message_lower for w in ["urgent", "critical", "asap", "bantu", "help", "emergency"]):
            return ("escalate", None)
        
        return ("unknown", None)
    
    def analyze_problem_context(self, problem_description: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Deep analyze the user's SPECIFIC problem context using AI
        Returns detailed understanding of the actual issue
        """
        if not self.use_llm or not self.ollama_available:
            return {"status": "no_ai", "error": "AI not available"}
        
        try:
            prompt = f"""Analyze this specific technical problem and provide detailed context understanding.
Problem Description: "{problem_description}"
Suspected Category: {category or "Unknown"}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "root_cause_hypothesis": "What you think is the ACTUAL root cause",
  "symptoms_detected": ["list", "of", "specific symptoms"],
  "possible_causes": ["most likely cause 1", "possible cause 2", "less likely cause 3"],
  "severity_assessment": "critical|high|medium|low",
  "needs_immediate_action": true|false,
  "recommended_first_step": "Exact action to try first based on this specific problem",
  "confidence_level": 0.0-1.0,
  "hallucination_risk": "low|medium|high"
}}

Be precise. Don't hallucinate. If unsure, say so in the output."""

            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2,  # Low temperature for factual analysis
                    "top_p": 0.85,
                    "top_k": 25,
                    "num_predict": 400,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.warning(f"Problem context analysis failed: {response.status_code}")
                return {"status": "api_error"}
            
            response_text = response.json().get("response", "").strip()
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                result = json.loads(response_text)
                # Ensure status field is always present
                result["status"] = "success"
                logger.info(f"🧠 Context analyzed: {result.get('root_cause_hypothesis', 'Unknown')}")
                return result
            except json.JSONDecodeError:
                logger.warning("Failed to parse context analysis JSON")
                return {"status": "parse_error"}
                
        except Exception as e:
            logger.error(f"Problem context analysis error: {str(e)[:100]}")
            return {"status": "error", "error": str(e)[:50]}
    
    def generate_context_aware_troubleshooting(self, problem_description: str, category: Optional[str] = None, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate specific troubleshooting steps based on ACTUAL problem context
        
        ✨ ENHANCED: Now uses semantic KB matching instead of keyword matching
        ✨ NEW: Uses smart_prompt_engineer
        ✨ NEW: Uses user profile for personalization
        ✨ NEW: Logs solution attempt for tracking
        
        Returns: {status, steps, semantic_match_score, kb_solutions, etc}
        """
        if not self.use_llm or not self.ollama_available:
            return {"status": "no_ai", "steps": []}
        
        try:
            # ✨ NEW: Get user profile for adaptive responses
            user_profile = None
            if phone_number:
                user_profile = self.user_profile_manager.get_or_create_profile(phone_number)
            
            # ✨ NEW: Try semantic matching FIRST (much more accurate than keywords)
            semantic_match = self.semantic_matcher.find_matching_solution(problem_description)
            match_score = semantic_match.get("confidence", 0)
            kb_solutions = semantic_match.get("alternatives", [])
            
            logger.info(f"🔍 Semantic KB search: {match_score:.0%} confidence, {len(kb_solutions)} alternatives")
            
            # Build context for troubleshooting generation
            analysis_context = {
                "semantic_match_score": match_score,
                "kb_solutions": kb_solutions[:3],  # Top 3 alternatives
                "skill_level": user_profile.skill_level.value if user_profile else "intermediate",
                "frustration_level": (min(1.0, (user_profile.frustration_indicators or 0) / 5.0) if user_profile else 0.0),
            }
            
            # ✨ NEW: Use smart prompt engineer to generate better troubleshooting prompt
            analysis = self.analyze_problem_context_with_smart_prompt(
                problem_description,
                category,
                user_profile,
                kb_solutions
            )
            
            if analysis.get("status") != "success":
                logger.warning(f"Problem analysis failed: {analysis.get('error')}")
                return {"status": "analysis_error", "steps": []}
            
            # Generate troubleshooting steps
            prompt = self.prompt_engineer.generate_troubleshooting_steps_prompt(
                problem_description=problem_description,
                category=category or analysis.get("category", "general"),
                user_profile=user_profile,
                problem_analysis=analysis,
                previous_attempts=[]
            )
            
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.25,
                    "top_p": 0.85,
                    "top_k": 30,
                    "num_predict": 600,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.warning(f"Troubleshooting generation failed: {response.status_code}")
                return {"status": "api_error", "steps": []}
            
            response_text = response.json().get("response", "").strip()
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                result = json.loads(response_text)
                
                # ✨ NEW: Log solution attempt for effectiveness tracking
                if phone_number and category:
                    solution_id = f"{category}_{hash(problem_description) % 10000}"
                    self.solution_tracker.log_solution_attempt(
                        solution_id=solution_id,
                        category=category,
                        problem_description=problem_description,
                        solution_steps=result.get("steps", []),
                        kb_match_score=match_score,
                        user_skill_level=user_profile.skill_level.value if user_profile else "intermediate",
                        user_frustration=(min(1.0, (user_profile.frustration_indicators or 0) / 5.0) if user_profile else 0.0),
                        ai_confidence=result.get("ai_confidence", 0.5)
                    )
                
                if result.get("ai_confidence", 0) < 0.5:
                    logger.warning(f"⚠️ Low confidence troubleshooting ({result.get('ai_confidence'):.0%})")
                
                logger.info(f"✅ Generated {len(result.get('steps', []))} personalized troubleshooting steps (semantic match: {match_score:.0%})")
                
                # Add metadata
                result["semantic_match_score"] = match_score
                result["kb_solutions_used"] = len(kb_solutions)
                result["personalized_for_skill_level"] = user_profile.skill_level.value if user_profile else "unknown"
                
                return result
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse troubleshooting JSON")
                return {"status": "parse_error", "steps": []}
                
        except Exception as e:
            logger.error(f"Troubleshooting generation error: {str(e)[:100]}")
            return {"status": "error", "steps": [], "error": str(e)[:50]}
    
    def analyze_problem_context_with_smart_prompt(self, problem_description: str, category: Optional[str], user_profile: Optional[Any], kb_solutions: list) -> Dict[str, Any]:
        """Analyze problem using smart_prompt_engineer for better understanding"""
        
        # ✨ NEW: Use smart prompt engineer
        prompt = self.prompt_engineer.generate_problem_context_analysis_prompt(
            problem_description=problem_description,
            category=category,
            user_profile=user_profile,
            previous_attempts=[],
            kb_solutions=kb_solutions[:2]
        )
        
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2,
                    "top_p": 0.85,
                    "top_k": 25,
                    "num_predict": 400,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.warning(f"Problem analysis failed: {response.status_code}")
                return {"status": "api_error"}
            
            response_text = response.json().get("response", "").strip()
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                result = json.loads(response_text)
                result["status"] = "success"
                return result
            except json.JSONDecodeError:
                logger.warning("Failed to parse analysis JSON")
                return {"status": "parse_error"}
                
        except Exception as e:
            logger.error(f"Context analysis error: {str(e)[:100]}")
            return {"status": "error", "error": str(e)[:50]}
    
    @staticmethod
    def validate_response_sanity(response_text: str, problem_context: str) -> bool:
        """
        Validate that AI response makes sense for the problem
        Prevents hallucinations by checking relevance
        """
        try:
            # Handle None or empty inputs
            if not response_text or not problem_context:
                return False
            
            # Check if response content is relevant to problem
            problem_words = set(problem_context.lower().split())
            response_words = set(response_text.lower().split())
            
            # At least some word overlap suggests relevance
            if not problem_words:
                return len(response_text) > 20  # If no problem words, just check length
            
            overlap = len(problem_words & response_words) / len(problem_words)
            
            return overlap > 0.1 and len(response_text) > 20
        except Exception as e:
            logger.warning(f"Response validation error: {e}")
            return False  # Conservative: reject if can't validate
    
    def generate_response(self, message: str, intent: str, category: Optional[str] = None, phone_number: Optional[str] = None, tone: str = "neutral", semantic_matches: Optional[list] = None) -> str:
        """Generate intelligent response based on intent & category
        
        ✨ NEW: Uses smart_prompt_engineer instead of hardcoded templates
        ✨ NEW: Uses user profile for personalization
        ✨ NEW: Uses semantic KB matches for informed responses
        ✨ NEW: Adaptive response based on dialog flow state
        
        Returns: Natural, context-aware response in Indonesian
        """
        try:
            # ✨ NEW: Get user profile
            user_profile = None
            if phone_number:
                user_profile = self.user_profile_manager.get_or_create_profile(phone_number)
            
            if not self.use_llm or not self.ollama_available:
                return self._get_fallback_response(intent, category, user_profile)
            
            # ✨ NEW: Use smart prompt engineer to generate response prompt
            prompt = self.prompt_engineer.generate_response_prompt(
                message=message,
                intent=intent,
                category=category,
                user_profile=user_profile,
                semantic_kb_matches=semantic_matches or [],
                conversation_context={"tone": tone}
            )
            
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.6,
                    "top_p": 0.95,
                    "num_predict": 200,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code == 200:
                response_text = response.json().get("response", "").strip()
                if response_text and len(response_text) > 10:
                    response_text = response_text[:500].strip()
                    response_text = response_text.replace("```", "").strip()
                    
                    # ✨ NEW: Track the response with solution effectiveness tracker
                    if phone_number and category and intent == "problem":
                        self.solution_tracker.log_solution_attempt(
                            solution_id=f"response_{hash(message) % 10000}",
                            category=category,
                            problem_description=message,
                            solution_steps=[],
                            kb_match_score=0.5,
                            ai_confidence=0.7
                        )
                    
                    # Format for WhatsApp
                    from app.utils.smart_response_system import smart_response_system
                    return smart_response_system.format_for_whatsapp(response_text)
            
            return self._get_fallback_response(intent, category, user_profile)
            
        except Exception as e:
            logger.debug(f"Response generation error: {e}")
            user_profile = None
            if phone_number:
                user_profile = self.user_profile_manager.get_or_create_profile(phone_number)
            return self._get_fallback_response(intent, category, user_profile)
    
    def _get_fallback_response(self, intent: str, category: Optional[str], user_profile: Optional[Any] = None) -> str:
        """Fallback response when LLM unavailable - now personalized based on user profile
        
        ✨ ENHANCED: Uses user profile for personalization instead of generic responses
        """
        from app.utils.smart_response_system import smart_response_system
        
        # Get response style from user profile
        response_style = {"explanation_depth": 2, "use_technical_terms": False} if not user_profile else user_profile.get_response_style()
        
        # Build context-aware response based on intent & user profile
        if intent == "greeting":
            if user_profile and user_profile.total_interactions > 5:
                msg = f"Halo! Apa yang bisa kami bantu hari ini? 👋"
            else:
                msg = "Selamat datang di TRAMOS Support! 👋 Ada yang bisa kami bantu?"
                
        elif intent == "problem":
            if user_profile and user_profile.is_frustrated:
                msg = "Saya mengerti, ini sangat frustasi. Mari kita selesaikan bersama-sama. Bisa jelaskan masalahnya? 🤝"
            elif category:
                msg = f"Saya paham ada masalah dengan {category}. Mari kita troubleshoot step by step. Bisa jelaskan detail masalahnya? 🔍"
            else:
                msg = "Saya siap membantu. Bisa jelaskan secara detail masalahnya? Semakin detail, semakin cepat solusinya. 🔍"
                
        elif intent == "resolved":
            msg = smart_response_system.format_success_message("solusi yang kami berikan", [])
            
        elif intent == "unresolved":
            msg = smart_response_system.format_escalation_message(
                "Troubleshooting standard tidak efektif",
                estimated_time="2 jam"
            )
            
        elif intent == "escalate":
            msg = smart_response_system.format_escalation_message(
                "Masalah memerlukan bantuan urgent dari tim expert",
                estimated_time="30 menit"
            )
            
        elif intent == "feedback":
            msg = "Terima kasih atas feedback Anda! Kami terus improve layanan untuk memberikan yang terbaik. 🙏"
            
        elif intent == "confirmation":
            msg = "Apakah semua informasi sudah benar? 🤔\n\n1️⃣ Ya, semua benar\n2️⃣ Tidak, ingin ubah"
            
        else:  # unknown
            if user_profile and user_profile.skill_level.value == "expert":
                msg = "Bisa jelaskan technical detailnya lebih lanjut? 🤖"
            else:
                msg = "Bisa jelaskan lebih detail tentang masalahnya? Semakin detail, semakin cepat kami bantu. 🤔"
        
        return smart_response_system.format_for_whatsapp(msg)
    
    @staticmethod
    def should_collect_details(message: str) -> bool:
        """Check if message has enough detail for troubleshooting"""
        # Better heuristics: check for problem indicators
        message = message.lower().strip()
        
        # If very short, likely needs details
        if len(message) < 5:
            return True
        
        # Check if message seems complete (has action words or tech keywords)
        tech_keywords = ["tidak bisa", "error", "rusak", "mogok", "offline", "mati", 
                        "broken", "not", "fail", "problem", "issue", "stuck"]
        has_tech_keyword = any(keyword in message for keyword in tech_keywords)
        
        # If has tech keyword or reasonable length with context, likely has enough detail
        if has_tech_keyword or len(message) > 15:
            return False
        
        return True


# Singleton instance
ai_engine = AITroubleshootingEngine()

