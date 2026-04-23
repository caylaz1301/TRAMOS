"""
Smart Solution Searcher - AI-powered KB solution finding
Uses LLM to intelligently match problems with KB solutions
Now uses dynamic response generation instead of hardcoded templates
Leverages AI context analysis for truly intelligent troubleshooting
"""

import logging
import json
import requests
from typing import Optional, Dict, Any, List, Tuple
from app.config import settings
from app.utils.kb_troubleshooting import KB_TROUBLESHOOTING
from app.utils.smart_response_system import smart_response_system
from app.utils.ai_logic import ai_engine

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"


class SolutionSearcher:
    """Intelligent solution finder using AI + KB matching"""
    
    def __init__(self):
        """Initialize solution searcher"""
        self.use_llm = settings.USE_LLM
        self.ollama_available = self._check_ollama_connection()
        
        # Use unified smart response system
        self.response_system = smart_response_system
        
        # Cache KB summary for AI searches
        self._kb_summary_cache = None
        # Cache last Ollama connection check time to avoid repeated checks
        self._last_ollama_check = 0
        
        if self.use_llm and self.ollama_available:
            logger.info("✓ Solution Searcher initialized with AI")
        else:
            logger.warning("⚠️ Solution Searcher: Using keyword matching fallback")
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=2
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            return False
    
    def _query_ollama(self, prompt: str, temperature: float = 0.3) -> str:
        """Query Ollama LLM"""
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_ctx": 2048,
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                logger.warning(f"Ollama error: {response.status_code}")
                return ""
        except Exception as e:
            logger.warning(f"Ollama query failed: {e}")
            return ""
    
    def search_solutions(self, problem_description: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search KB for matching solutions
        
        Returns:
            List of solutions with confidence scores, sorted by relevance
        """
        
        if not problem_description:
            return []
        
        # Try AI-powered semantic matching first
        if self.use_llm and self.ollama_available:
            solutions = self._ai_search_solutions(problem_description)
            if solutions:
                return solutions
        
        # Fallback to keyword-based matching
        return self._keyword_search_solutions(problem_description, category)
    
    def _ai_search_solutions(self, problem_description: str) -> List[Dict[str, Any]]:
        """AI-powered solution search using semantic understanding"""
        
        # Get cached or generate KB summary
        if self._kb_summary_cache is None:
            kb_categories = list(KB_TROUBLESHOOTING.keys())
            self._kb_summary_cache = "\n".join([
                f"- {cat}: {KB_TROUBLESHOOTING[cat]['title']}"
                for cat in kb_categories
            ])
        
        prompt = f"""Analyze this problem and find the best matching category from KB:

Problem: "{problem_description}"

Available KB categories:
{self._kb_summary_cache}

Return ONLY a JSON object with:
{{
  "best_match": "category_name",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

Be strict: only return one of the listed categories. If no match, set best_match to null."""
        
        try:
            response_text = self._query_ollama(prompt, temperature=0.1)
            
            # Extract JSON from response (sometimes model adds extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                best_match = result.get("best_match")
                confidence = float(result.get("confidence", 0))
                
                if best_match and best_match in KB_TROUBLESHOOTING:
                    logger.info(f"✓ AI matched: {best_match} (confidence: {confidence})")
                    return self._format_solution(best_match, confidence)
                
                logger.debug(f"AI match: {best_match} not in KB or no match")
        except Exception as e:
            logger.warning(f"AI search failed: {e}, using keyword matching")
        
        return []
    
    def _keyword_search_solutions(self, problem_description: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fallback keyword-based solution search - OPTIMIZED"""
        
        problem_lower = problem_description.lower()
        # Split problem into words for efficient matching
        problem_words = set(problem_lower.split())
        matches = []
        
        # If category provided, search that first
        if category and category in KB_TROUBLESHOOTING:
            kb_item = KB_TROUBLESHOOTING[category]
            kb_keywords = set(kb_item.get("keywords", []))
            # Use set intersection for faster matching
            if problem_words & kb_keywords:
                matches.append((category, 0.95))
        
        # Search all other categories - optimized with set operations
        for cat, kb_data in KB_TROUBLESHOOTING.items():
            if category and cat == category:
                continue  # Already added
            
            # Use set intersection instead of repeated substring searches
            kb_keywords = set(kb_data.get("keywords", []))
            keyword_matches = len(problem_words & kb_keywords)
            
            if keyword_matches > 0:
                # Confidence based on number of matching keywords
                confidence = min(0.9, keyword_matches * 0.3)
                matches.append((cat, confidence))
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 3 matches formatted
        solutions = []
        for cat, confidence in matches[:3]:
            solutions.extend(self._format_solution(cat, confidence))
        
        if solutions:
            logger.info(f"✓ Keyword matched: {matches[0][0]} (confidence: {matches[0][1]:.2f})")
        
        return solutions
    
    def _format_solution(self, category: str, confidence: float) -> List[Dict[str, Any]]:
        """Format KB solution into response structure"""
        
        if category not in KB_TROUBLESHOOTING:
            return []
        
        kb = KB_TROUBLESHOOTING[category]
        
        return [{
            "category": category,
            "confidence": confidence,
            "title": kb.get("title", ""),
            "first_response": kb.get("first_response", ""),
            "troubleshooting_steps": kb.get("troubleshooting_steps", []),
            "workaround": kb.get("workaround", ""),
            "escalation_triggers": kb.get("escalation_triggers", []),
        }]
    
    def format_solution_for_user(self, solution: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> str:
        """Format solution for WhatsApp - compact and clear (without feedback question)"""
        
        category = solution.get("category", "app")
        confidence = solution.get("confidence", 0.5)
        
        # Determine severity
        severity = "medium"
        if user_context:
            if user_context.get("is_urgent", False) or user_context.get("is_critical", False):
                severity = "critical"
            elif user_context.get("multiple_attempts", 0) > 1:
                severity = "high"
        
        # Build response components
        user_frustrated = user_context and user_context.get("frustrated", False)
        opening = self.response_system.generate_empathetic_opening(category, user_frustrated)
        
        # Get troubleshooting steps
        troubleshooting = self.response_system.generate_troubleshooting_steps(category, severity)
        
        # Combine - simple and compact format (no feedback question - added by caller)
        confidence_text = self.get_solution_confidence_text(confidence)
        
        message = f"""{opening}

{solution.get('title', '')} - {confidence_text}

{troubleshooting}"""
        
        return message
    
    def format_next_step(self, solution: Dict[str, Any], step_number: int = 0, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Format next troubleshooting step using dynamic generation"""
        
        category = solution.get("category", "app")
        
        # Determine severity
        severity = "medium"
        if user_context:
            if user_context.get("is_urgent", False):
                severity = "critical"
            elif user_context.get("multiple_attempts", 0) > 2:
                severity = "high"
        
        # Generate dynamic troubleshooting steps (not hardcoded)
        troubleshooting = self.response_system.generate_troubleshooting_steps(category, severity)
        
        # Response CTA based on step progression
        if step_number < 2:
            cta = "\n\nCoba langkah ini ya. Reply: *Berhasil* atau *Gagal* 👍"
        else:
            cta = "\n\nKalau berhasil, masalahmu sudah teratasi! 🎉\nKalau gagal, kita ke tahap selanjutnya 🔧"
        
        return troubleshooting + cta
    
    def generate_ai_powered_troubleshooting(self, problem_description: str, category: Optional[str] = None, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate CONTEXT-AWARE troubleshooting using AI
        This is NOT hardcoded or template-based - AI analyzes the ACTUAL problem
        and generates specific troubleshooting steps for that exact issue
        """
        
        if not problem_description or len(problem_description.strip()) < 5:
            logger.warning("Problem description too short for AI analysis")
            return {"status": "error", "reason": "insufficient_data"}
        
        logger.info(f"🧠 Analyzing problem context: {problem_description[:60]}...")
        
        # Step 1: Analyze problem context deeply
        context = ai_engine.analyze_problem_context(problem_description, category)
        
        if context.get("status") in ["error", "api_error", "no_ai"]:
            logger.warning(f"Could not analyze context: {context.get('error')}")
            return {
                "status": "fallback",
                "reason": "ai_unavailable",
                "steps": []
            }
        
        logger.info(f"✅ Root cause identified: {context.get('root_cause_hypothesis', '?')}")
        
        # Step 2: Generate context-specific troubleshooting
        troubleshooting = ai_engine.generate_context_aware_troubleshooting(problem_description, category)
        
        if troubleshooting.get("status") in ["error", "api_error", "parse_error"]:
            logger.warning(f"Could not generate troubleshooting: {troubleshooting.get('error')}")
            return {
                "status": "fallback",
                "reason": "generation_failed",
                "steps": []
            }
        
        # Step 3: Validate confidence
        ai_confidence = troubleshooting.get("ai_confidence", 0)
        if ai_confidence < 0.4:
            logger.warning(f"⚠️ Low AI confidence ({ai_confidence:.0%}) - result may not be reliable")
            return {
                "status": "low_confidence",
                "confidence": ai_confidence,
                "steps": troubleshooting.get("steps", []),
                "warning": "AI not confident in this solution"
            }
        
        logger.info(f"✅ Generated context-aware troubleshooting (confidence: {ai_confidence:.0%})")
        
        # Step 4: Format troubleshooting nicely for WhatsApp
        formatted_response = self._format_ai_troubleshooting(troubleshooting, context)
        
        return {
            "status": "success",
            "context": context,
            "troubleshooting": troubleshooting,
            "formatted_message": formatted_response,
            "confidence": ai_confidence,
            "steps_count": len(troubleshooting.get("steps", []))
        }
    
    def _format_ai_troubleshooting(self, troubleshooting: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Format AI-generated troubleshooting for WhatsApp using unified response system"""
        
        try:
            steps = troubleshooting.get("steps", [])
            expected_outcome = troubleshooting.get("expected_outcome", "")
            caveats = troubleshooting.get("caveats", "")
            
            # Build complete message
            parts = []
            
            # Expected outcome
            if expected_outcome:
                parts.append(f"✅ {expected_outcome}")
            
            # Troubleshooting steps (max 3 for WhatsApp)
            if steps:
                parts.append(f"\n🔧 *Langkah Troubleshooting:*\n")
                
                for i, step in enumerate(steps[:3], 1):
                    title = step.get("title", "")
                    instructions = step.get("instructions", [])
                    verification = step.get("verification", "")
                    
                    parts.append(f"*{i}. {title}*")
                    
                    for instr in instructions:
                        parts.append(f"  → {instr}")
                    
                    if verification:
                        parts.append(f"  ✓ Cek: {verification}")
                    parts.append("")
            
            # Caveats/warnings
            if caveats:
                parts.append(f"⚠️ *Catatan penting:*\n{caveats}")
            
            # Call CTA
            parts.append("\nCoba langkah-langkah di atas dan kasih tahu hasilnya 👍")
            
            message = "\n".join(parts).strip()
            
            # Use unified formatter for WhatsApp optimization
            return self.response_system.format_for_whatsapp(message)
            
        except Exception as e:
            logger.error(f"Error formatting AI troubleshooting: {e}")
            return "Terjadi error saat memformat solusi. Coba lagi nanti."
    
    def _format_escalation_message(self, solution: Dict[str, Any], category: str = "") -> str:
        """Format escalation message using unified response system"""
        
        category = category or solution.get("category", "")
        
        # Professional escalation message
        escalation = self.response_system.format_escalation_message(
            reason=f"Troubleshooting standard tidak efektif untuk {category} issue",
            ticket_id="(akan dibuat)",
            estimated_time="1-2 jam"
        )
        
        # Info needed - clean list format
        info_list = [
            "Nama lengkap kamu",
            "Nomor unit/vehicle (kalau ada)",
            "Lokasi sekarang",
            "Kapan masalah terjadi",
            "Sudah coba langkah apa aja"
        ]
        
        info_section = self.response_system.format_list(
            "📝 Info yang kami butuhkan",
            info_list
        )
        
        closing = "\nTolong isi supaya tim expert bisa bantu lebih cepat ya 🙏"
        
        return escalation + "\n\n" + info_section + closing
    
    def get_solution_confidence_text(self, confidence: float) -> str:
        """Convert confidence score to user-friendly text"""
        if confidence >= 0.85:
            return "Sangat yakin ini solusinya"
        elif confidence >= 0.7:
            return "Kemungkinan besar ini solusinya"
        elif confidence >= 0.5:
            return "Mungkin ini solusinya"
        else:
            return "Solusi yang mungkin cocok"


# Global instance
solution_searcher = SolutionSearcher()
