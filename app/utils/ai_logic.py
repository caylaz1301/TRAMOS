"""AI-based logic for troubleshooting and intent detection"""
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class AITroubleshootingEngine:
    """Simple AI logic for troubleshooting assistance"""
    
    # Simple knowledge base for common issues
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
    
    @staticmethod
    def detect_intent(message: str) -> Tuple[str, Optional[str]]:
        """
        Detect intent from user message
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


# Singleton instance
ai_engine = AITroubleshootingEngine()
