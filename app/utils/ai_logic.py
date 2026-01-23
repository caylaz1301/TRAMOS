"""AI-based logic for troubleshooting and intent detection"""
import logging
from typing import Tuple, Optional, Dict, Any
import json

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)


class AITroubleshootingEngine:
    """AI-powered troubleshooting with LLM support (Gemini)"""
    
    def __init__(self):
        """Initialize AI engine with optional Gemini support"""
        self.use_llm = settings.USE_LLM and GEMINI_AVAILABLE
        self.gemini_model = None
        
        if self.use_llm:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
                logger.info(f"✓ Gemini LLM initialized: {settings.GEMINI_MODEL}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}. Falling back to keyword matching.")
                self.use_llm = False
    
    # Simple knowledge base for common issues (fallback when LLM unavailable)
    TROUBLESHOOTING_KB = {
        "gps": {
            "keywords": ["gps", "location", "tracking", "signal"],
            "response": "I see you're having GPS/tracking issues. Let me help you troubleshoot:\n"
                       "1. Check if your vehicle has clear sky view\n"
                       "2. Restart the tracking device\n"
                       "3. Verify your vehicle's internet connection\n\n"
                       "Is the issue resolved?",
            "category": "GPS"
        },
        "camera": {
            "keywords": ["camera", "video", "recording", "feed"],
            "response": "I see you're having camera issues. Let's troubleshoot:\n"
                       "1. Check if the camera lens is clean\n"
                       "2. Verify power supply to the camera\n"
                       "3. Check cable connections\n\n"
                       "Is the issue resolved?",
            "category": "Camera"
        },
        "connectivity": {
            "keywords": ["connection", "internet", "network", "offline", "connected"],
            "response": "I see you're having connectivity issues. Let's try:\n"
                       "1. Check your vehicle's internet connection (4G/WiFi)\n"
                       "2. Restart the modem/router\n"
                       "3. Check if you have active data plan\n\n"
                       "Is the issue resolved?",
            "category": "Connectivity"
        },
        "battery": {
            "keywords": ["battery", "power", "charge", "low", "drain"],
            "response": "I see you're having battery issues. Let's troubleshoot:\n"
                       "1. Check battery voltage with a multimeter\n"
                       "2. Verify charging cable is working\n"
                       "3. Check if battery contacts are clean\n\n"
                       "Is the issue resolved?",
            "category": "Battery"
        }
    }
    
    def _detect_intent_with_gemini(self, message: str) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Use Gemini to detect intent with high accuracy"""
        try:
            prompt = f"""Analyze this TRAMOS fleet management truck issue report and respond with JSON only (no markdown):

Message: "{message}"

Determine:
1. intent: one of [resolved, unresolved, escalate, troubleshooting, unknown]
2. category: one of [GPS, Camera, Battery, Connectivity, Other, null]
3. confidence: 0.0-1.0

Intent definitions:
- "resolved" = problem is FIXED or WORKING NORMALLY now (e.g., "sudah fixed", "working sekarang")
- "troubleshooting" = problem EXISTS and user WANTS HELP to fix it (e.g., "tidak berfungsi", "error", "tidak merekam")
- "unresolved" = user says problem STILL EXISTS, solution DIDN'T WORK (e.g., "masih tidak bekerja", "tetap error")
- "escalate" = URGENT or needs HUMAN SUPPORT (keywords: urgent, critical, help now, asap, serious)
- "unknown" = cannot determine intent

Categories:
- GPS: gps, location, tracking, signal, coordinates, maps
- Camera: camera, video, recording, feed, dashboard
- Battery: battery, power, charge, voltage, drain, low
- Connectivity: connection, network, offline, internet, data, wifi
- Other: anything else
- null: no issue mentioned

Respond ONLY with JSON, no other text, no markdown:
{{"intent": "...", "category": "...", "confidence": 0.95}}"""

            response = self.gemini_model.generate_content(prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            intent = result.get("intent", "unknown")
            category = result.get("category")
            
            # Convert null string to None
            if category == "null" or category == "Other":
                category = None
            
            confidence = result.get("confidence", 0.5)
            
            logger.debug(f"Gemini intent detection: {intent}, category: {category}, confidence: {confidence}")
            
            return (intent, category, {"source": "gemini", "confidence": confidence})
            
        except Exception as e:
            logger.error(f"Gemini intent detection failed: {e}")
            return ("unknown", None, {"source": "gemini_error", "error": str(e)})
    
    def detect_intent(self, message: str) -> Tuple[str, Optional[str]]:
        """
        Detect intent from user message with optional LLM enhancement
        Returns: (intent, category)
        """
        # Try LLM first if available
        if self.use_llm and self.gemini_model:
            intent, category, metadata = self._detect_intent_with_gemini(message)
            
            # Use LLM result if confidence is high
            if metadata.get("confidence", 0) >= settings.AI_CONFIDENCE_THRESHOLD:
                return (intent, category)
            else:
                logger.debug(f"Gemini confidence too low ({metadata.get('confidence')}), falling back to keywords")
        
        # Fallback to keyword matching
        return self._detect_intent_with_keywords(message)
    
    def _detect_intent_with_keywords(self, message: str) -> Tuple[str, Optional[str]]:
        """
        Detect intent from user message using keyword matching (fallback method)
        Returns: (intent, category)
        """
        message_lower = message.lower()
        
        # Check for resolution indicators
        if any(word in message_lower for word in ["yes", "resolved", "working", "fixed", "ok"]):
            return ("resolved", None)
        
        if any(word in message_lower for word in ["no", "still", "not working", "doesn't"]):
            return ("unresolved", None)
        
        # Check for escalation
        if any(word in message_lower for word in ["help", "urgent", "critical", "serious", "asap", "now"]):
            return ("escalate", None)
        
        # Check troubleshooting KB
        for issue_key, issue_data in AITroubleshootingEngine.TROUBLESHOOTING_KB.items():
            if any(keyword in message_lower for keyword in issue_data["keywords"]):
                return ("troubleshooting", issue_data["category"])
        
        return ("unknown", None)
    
    @staticmethod
    def get_troubleshooting_response(category: Optional[str]) -> str:
        """Get troubleshooting response for a category"""
        if category:
            for issue_key, issue_data in AITroubleshootingEngine.TROUBLESHOOTING_KB.items():
                if issue_data["category"] == category:
                    return issue_data["response"]
        
        # Default response
        return ("I understand you have an issue. To better assist you, could you tell me more about:\n"
                "- What specific problem are you experiencing?\n"
                "- When did it start?\n"
                "- Is it affecting all functions or just specific ones?\n\n"
                "Or would you like me to escalate this to our support team?")
    
    @staticmethod
    def should_collect_details(message: str) -> bool:
        """Determine if we should ask for more details"""
        return len(message) < 10 or message.count(" ") < 2


# Singleton instance - initialize with LLM support
ai_engine = AITroubleshootingEngine()
