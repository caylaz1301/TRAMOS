"""
NLP Extractor - Extracts structured information from problem descriptions
Uses Mistral LLM for semantic understanding of problem details
"""

import json
import logging
import re
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class ProblemExtractor:
    """Extract structured problem details from free-text descriptions using NLP"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "mistral"
    
    def extract_problem_details(self, problem_description: str) -> Dict[str, Any]:
        """
        Extract problem details from description
        Returns: {
            'category': str,
            'severity': 'low'|'medium'|'high'|'critical',
            'affected_systems': list,
            'error_description': str,
            'additional_context': str,
            'requires_escalation': bool,
            'confidence': float (0.0-1.0)
        }
        """
        
        try:
            # Create extraction prompt
            prompt = self._build_extraction_prompt(problem_description)
            
            # Call Mistral with extraction prompt
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,  # Lower temp for consistent extraction
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama extraction failed: {response.text}")
                return self._get_default_extraction()
            
            # Parse response
            response_text = response.json().get("response", "").strip()
            extracted = self._parse_extraction_response(response_text, problem_description)
            
            return extracted
        
        except Exception as e:
            logger.error(f"Error extracting problem details: {e}")
            return self._get_default_extraction()
    
    def _build_extraction_prompt(self, problem_description: str) -> str:
        """Build prompt for NLP extraction"""
        prompt = f"""
Analyze the following problem report and extract structured information. 
Return ONLY valid JSON without markdown formatting.

Problem Report:
"{problem_description}"

CATEGORY GUIDE:
- GPS: Issues with tracking, location, signal, navigation (keywords: gps, tracking, lokasi, signal, hilang, posisi)
- Camera: Recording issues, video problems (keywords: kamera, video, rekam, feed, display)
- Battery: Power, charging issues (keywords: baterai, battery, power, charge, mati, cepat habis)
- Connectivity: Internet, network, wifi (keywords: internet, koneksi, network, wifi, offline, signal)
- Billing: Payment issues (keywords: tagihan, invoice, billing, biaya)
- Maintenance: Service, repair needed  
- Service: General issues that don't fit above
- Other: Unknown

Extract and return JSON with these fields:
{{
    "category": One of [GPS, Camera, Battery, Connectivity, Billing, Maintenance, Service, Other],
    "severity": "low" | "medium" | "high" | "critical",
    "affected_systems": ["list", "of", "systems"],
    "error_description": "brief error summary",
    "requires_escalation": boolean,
    "confidence": 0.7
}}

Be precise. Only return valid JSON.
"""
        return prompt
    
    def _parse_extraction_response(self, response_text: str, original_problem: str) -> Dict[str, Any]:
        """Parse extraction response from Mistral"""
        
        # Try to extract JSON from response
        try:
            # Look for JSON in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                extracted_json = json.loads(json_match.group())
                
                # Validate required fields
                result = {
                    'category': extracted_json.get('category', 'Other'),
                    'severity': extracted_json.get('severity', 'medium'),
                    'affected_systems': extracted_json.get('affected_systems', []),
                    'error_description': extracted_json.get('error_description', original_problem[:100]),
                    'requires_escalation': extracted_json.get('requires_escalation', False),
                    'confidence': float(extracted_json.get('confidence', 0.7)),
                    'source': 'llm'
                }
                
                # If AI classified as generic "Service", check keywords to see if we can be more specific
                if result['category'] == 'Service':
                    keyword_result = self._extract_by_keywords(original_problem)
                    if keyword_result['category'] != 'Service':
                        # Keywords found a more specific category
                        result['category'] = keyword_result['category']
                        result['source'] = 'llm_with_keyword_override'
                
                return result
        
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from NLP response")
        
        # Fallback: use keyword detection
        return self._extract_by_keywords(original_problem)
    
    def _extract_by_keywords(self, problem_description: str) -> Dict[str, Any]:
        """Fallback keyword-based extraction"""
        description_lower = problem_description.lower()
        
        # Determine category
        if any(keyword in description_lower for keyword in ['gps', 'tracking', 'lokasi', 'signal', 'hilang']):
            category = 'GPS'
        elif any(keyword in description_lower for keyword in ['kamera', 'video', 'rekam', 'feed', 'display']):
            category = 'Camera'
        elif any(keyword in description_lower for keyword in ['baterai', 'battery', 'power', 'charge', 'mati']):
            category = 'Battery'
        elif any(keyword in description_lower for keyword in ['internet', 'koneksi', 'network', 'wifi', 'offline', 'lelet', 'lambat', 'slow', 'lemot', 'lag', 'disconnect', 'putus']):
            category = 'Connectivity'
        elif any(keyword in description_lower for keyword in ['tagihan', 'invoice', 'billing', 'biaya']):
            category = 'Billing'
        else:
            category = 'Service'
        
        # Determine severity
        if any(word in description_lower for word in ['urgent', 'emergency', 'sangat', 'gawat', 'kritis']):
            severity = 'critical'
        elif any(word in description_lower for word in ['penting', 'serius', 'serious', 'important']):
            severity = 'high'
        elif any(word in description_lower for word in ['sedikit', 'minor', 'kecil']):
            severity = 'low'
        else:
            severity = 'medium'
        
        return {
            'category': category,
            'severity': severity,
            'affected_systems': [category.lower()],
            'error_description': problem_description[:100],
            'requires_escalation': severity in ['high', 'critical'],
            'confidence': 0.6,
            'source': 'keyword'
        }
    
    def _get_default_extraction(self) -> Dict[str, Any]:
        """Return default extraction when all else fails"""
        return {
            'category': 'Service',
            'severity': 'medium',
            'affected_systems': [],
            'error_description': '',
            'requires_escalation': False,
            'confidence': 0.0,
            'source': 'default'
        }
    
    def classify_urgency(self, problem_description: str, category: str) -> str:
        """Classify problem urgency for ticket priority"""
        
        # Get extraction details
        details = self.extract_problem_details(problem_description)
        severity = details.get('severity', 'medium')
        
        # Map to ticket priority
        priority_map = {
            'critical': 'emergency',
            'high': 'high',
            'medium': 'normal',
            'low': 'low'
        }
        
        return priority_map.get(severity, 'normal')


# Global instance
problem_extractor = ProblemExtractor()
