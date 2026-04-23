"""
Machine Learning Pattern Analyzer
Analyzes conversation and ticket patterns to identify trends and insights
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter
from sqlalchemy.orm import Session

from app.database_models import WhatsAppSession

logger = logging.getLogger(__name__)


class MLPatternAnalyzer:
    """ML Pattern Analyzer for conversation and ticket data"""
    
    @staticmethod
    def analyze_problem_patterns(db: Session, days: int = 7) -> Dict:
        """Analyze problem patterns from recent sessions"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date,
                WhatsAppSession.problem_category.isnot(None)
            ).all()
            
            if not sessions:
                return {"error": "No data available"}
            
            # Count categories
            categories = [s.problem_category for s in sessions if s.problem_category]
            category_counts = Counter(categories)
            
            # Calculate trends
            top_issues = category_counts.most_common(5)
            
            # Severity distribution for top categories
            severity_by_category = {}
            for category, _ in top_issues:
                severities = [
                    s.problem_severity for s in sessions 
                    if s.problem_category == category and s.problem_severity
                ]
                if severities:
                    severity_counts = Counter(severities)
                    severity_by_category[category] = dict(severity_counts)
            
            return {
                "total_patterns": len(sessions),
                "top_issues": [
                    {"category": cat, "count": count, "percentage": round(count/len(sessions)*100, 1)}
                    for cat, count in top_issues
                ],
                "severity_by_category": severity_by_category,
                "unique_categories": len(category_counts),
                "data_period_days": days
            }
        except Exception as e:
            logger.error(f"Error analyzing problem patterns: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def analyze_resolution_patterns(db: Session, days: int = 7) -> Dict:
        """Analyze how problems are being resolved"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"error": "No data available"}
            
            # Resolution categories
            # Count resolved as those that reached RESOLVED state
            resolved_by_kb = len([s for s in sessions if s.current_state == "resolved"])
            escalated_to_ticket = len([s for s in sessions if s.ticket_id])
            abandoned = len([s for s in sessions if s.current_state == "closed" and not s.is_active and s.message_count < 3])
            still_active = len([s for s in sessions if s.is_active])
            
            total = len(sessions)
            
            return {
                "total_sessions": total,
                "resolved_by_kb": {
                    "count": resolved_by_kb,
                    "percentage": round(resolved_by_kb/total*100, 1) if total > 0 else 0
                },
                "escalated_to_ticket": {
                    "count": escalated_to_ticket,
                    "percentage": round(escalated_to_ticket/total*100, 1) if total > 0 else 0
                },
                "abandoned": {
                    "count": abandoned,
                    "percentage": round(abandoned/total*100, 1) if total > 0 else 0
                },
                "still_active": {
                    "count": still_active,
                    "percentage": round(still_active/total*100, 1) if total > 0 else 0
                },
                "kb_effectiveness": round(resolved_by_kb/total*100, 1) if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error analyzing resolution patterns: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def identify_hotspots(db: Session, days: int = 7) -> Dict:
        """Identify problem hotspots and recurring issues"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date,
                WhatsAppSession.problem_category.isnot(None),
                WhatsAppSession.problem_severity.isnot(None)
            ).all()
            
            if not sessions:
                return {"error": "No data available"}
            
            # Find critical issues (high severity + frequent)
            category_severity = {}
            for s in sessions:
                key = f"{s.problem_category}|{s.problem_severity}"
                if key not in category_severity:
                    category_severity[key] = 0
                category_severity[key] += 1
            
            # Sort by frequency
            hotspots = sorted(category_severity.items(), key=lambda x: x[1], reverse=True)
            
            critical_hotspots = [
                {
                    "category": h[0].split("|")[0],
                    "severity": h[0].split("|")[1],
                    "count": h[1],
                    "trend": "🔴 CRITICAL" if "critical" in h[0].lower() else "🟠 HIGH" if "high" in h[0].lower() else "🟡 MEDIUM"
                }
                for h in hotspots[:5]
            ]
            
            return {
                "total_hotspots": len(hotspots),
                "critical_hotspots": critical_hotspots,
                "recommendation": _generate_hotspot_recommendation(critical_hotspots)
            }
        except Exception as e:
            logger.error(f"Error identifying hotspots: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def analyze_temporal_patterns(db: Session, days: int = 7) -> Dict:
        """Analyze when problems occur most frequently"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"error": "No data available"}
            
            # Group by hour of day
            hourly_distribution = [0] * 24
            for s in sessions:
                if s.created_at:
                    hour = s.created_at.hour
                    hourly_distribution[hour] += 1
            
            # Find peak hours
            peak_hours = sorted(
                enumerate(hourly_distribution),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            # Group by day of week
            daily_distribution = [0] * 7  # Mon-Sun
            for s in sessions:
                if s.created_at:
                    day = s.created_at.weekday()
                    daily_distribution[day] += 1
            
            days_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            peak_days = sorted(
                [(days_name[i], daily_distribution[i]) for i in range(7)],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            return {
                "peak_hours": [
                    {"hour": f"{h:02d}:00", "sessions": count}
                    for h, count in peak_hours
                ],
                "peak_days": [
                    {"day": day, "sessions": count}
                    for day, count in peak_days
                ],
                "least_active_hour": f"{hourly_distribution.index(min(hourly_distribution)):02d}:00",
                "recommendation": f"Focus support staff during peak hours: {', '.join([f'{h:02d}:00' for h, _ in peak_hours])}"
            }
        except Exception as e:
            logger.error(f"Error analyzing temporal patterns: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_kpi_trends(db: Session, days: int = 7) -> Dict:
        """Calculate KPI trends"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"error": "No data available"}
            
            total = len(sessions)
            avg_messages = sum(s.message_count for s in sessions) / total if total > 0 else 0
            avg_duration = sum(
                (s.last_activity - s.created_at).total_seconds()
                for s in sessions if s.created_at and s.last_activity
            ) / total if total > 0 else 0
            
            kb_resolved = len([s for s in sessions if s.current_state == "resolved"])
            resolution_rate = (kb_resolved / total * 100) if total > 0 else 0
            
            tickets_created = len([s for s in sessions if s.ticket_id])
            escalation_rate = (tickets_created / total * 100) if total > 0 else 0
            
            return {
                "total_sessions": total,
                "avg_messages_per_session": round(avg_messages, 2),
                "avg_duration_minutes": round(avg_duration / 60, 2),
                "kb_resolution_rate": round(resolution_rate, 1),
                "escalation_rate": round(escalation_rate, 1),
                "customer_satisfaction_potential": round(100 - escalation_rate, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating KPI trends: {e}")
            return {"error": str(e)}


def _generate_hotspot_recommendation(hotspots: List) -> str:
    """Generate recommendation based on hotspots"""
    if not hotspots:
        return "No critical issues identified"
    
    top_issue = hotspots[0]
    category = top_issue["category"]
    severity = top_issue["severity"]
    
    if "critical" in severity.lower():
        return f"URGENT: {category} issues are critical and frequent. Immediate action needed - consider KB update or process improvement."
    elif "high" in severity.lower():
        return f"HIGH PRIORITY: {category} issues are high severity. Review KB solutions and consider escalation process improvement."
    else:
        return f"MONITOR: {category} issues appear frequently. Update KB solutions when possible."
