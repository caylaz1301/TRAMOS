"""Extractor deterministik untuk kategori dan urgensi masalah driver.

Modul ini sengaja tidak memanggil service AI eksternal agar dialog flow tetap
cepat dan stabil saat WhatsApp/Gemini sedang tidak dipakai untuk test terminal.
"""

import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ProblemExtractor:
    """Extract structured problem details from free-text descriptions."""
    
    def __init__(self):
        self.model = "keyword-rules"
    
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
            return self._extract_by_keywords(problem_description)
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
- GPS: Tracking, location, signal, navigation (keywords: gps, tracking, lokasi, signal, hilang, posisi, peta)
- Camera: Recording, video problems (keywords: kamera, video, rekam, feed, dashcam)
- Connectivity: Internet, network, wifi (keywords: internet, koneksi, network, wifi, offline, lambat, putus)
- Device: Hardware device issues (keywords: device, perangkat, hardware, mati, restart, error)
- Vehicle: Vehicle-specific problems (keywords: kendaraan, mobil, truk, mesin, rem, ban)
- App: Application/software issues (keywords: aplikasi, app, crash, bug, update, error)
- Billing: Payment issues (keywords: tagihan, invoice, billing, biaya, bayar)
- Ticket: Support ticket issues (keywords: tiket, ticket, support, bantuan, lapor)
- Maintenance: Service, repair, scheduling (keywords: maintenance, perawatan, servis, jadwal, oli)
- Sensor: IoT sensor problems (keywords: sensor, fuel, suhu, temperature, geofence, alarm)
- Driver: Driver behavior, management (keywords: driver, pengemudi, sopir, speeding, pelanggaran)
- Report: Reports, data export (keywords: laporan, report, export, download, riwayat, statistik)
- Account: Login, password, access (keywords: login, password, akun, lupa, reset, hak akses)
- Other: Unknown category

Extract and return JSON with these fields:
{{
    "category": One of [GPS, Camera, Connectivity, Device, Vehicle, App, Billing, Ticket, Maintenance, Sensor, Driver, Report, Account, Other],
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
        
        # Determine category — check most specific first
        if any(kw in description_lower for kw in ['sensor', 'fuel', 'suhu', 'temperature', 'geofence', 'alarm', 'tangki', 'bbm', 'odometer']):
            category = 'Sensor'
        elif any(kw in description_lower for kw in ['driver', 'pengemudi', 'sopir', 'supir', 'speeding', 'ngebut', 'pelanggaran', 'rem mendadak', 'skor driver']):
            category = 'Driver'
        elif any(kw in description_lower for kw in ['gps', 'tracking', 'lokasi', 'signal gps', 'posisi', 'peta', 'koordinat', 'tidak terlacak']):
            category = 'GPS'
        elif any(kw in description_lower for kw in ['kamera', 'video', 'rekam', 'dashcam', 'feed', 'recording']):
            category = 'Camera'
        elif any(kw in description_lower for kw in ['internet', 'koneksi', 'network', 'wifi', 'offline', 'lelet', 'lambat', 'slow', 'lemot', 'lag', 'disconnect', 'putus']):
            category = 'Connectivity'
        elif any(kw in description_lower for kw in ['maintenance', 'perawatan', 'servis', 'service', 'oli', 'ban', 'jadwal servis', 'tune up']):
            category = 'Maintenance'
        elif any(kw in description_lower for kw in ['login', 'password', 'akun', 'lupa password', 'reset password', 'hak akses', 'blocked']):
            category = 'Account'
        elif any(kw in description_lower for kw in ['laporan', 'report', 'export', 'download', 'unduh', 'riwayat', 'statistik', 'excel', 'csv']):
            category = 'Report'
        elif any(kw in description_lower for kw in ['tagihan', 'invoice', 'billing', 'biaya', 'bayar', 'pembayaran']):
            category = 'Billing'
        elif any(kw in description_lower for kw in ['tiket', 'ticket', 'support', 'bantuan', 'lapor', 'aduan']):
            category = 'Ticket'
        elif any(kw in description_lower for kw in ['device', 'perangkat', 'hardware', 'restart', 'reboot', 'modul']):
            category = 'Device'
        elif any(kw in description_lower for kw in ['kendaraan', 'mobil', 'truk', 'mesin', 'plat', 'unit']):
            category = 'Vehicle'
        elif any(kw in description_lower for kw in ['aplikasi', 'app', 'crash', 'bug', 'update', 'install', 'versi']):
            category = 'App'
        else:
            category = 'Other'
        
        # Determine severity
        if any(word in description_lower for word in ['urgent', 'emergency', 'sangat', 'gawat', 'kritis', 'darurat', 'bahaya']):
            severity = 'critical'
        elif any(word in description_lower for word in ['penting', 'serius', 'serious', 'important', 'parah']):
            severity = 'high'
        elif any(word in description_lower for word in ['sedikit', 'minor', 'kecil', 'ringan']):
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
