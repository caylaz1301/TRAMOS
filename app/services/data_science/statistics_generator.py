"""
Statistics Generator
Generates insights and recommendations from analyzed data
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session

from app.database_models import WhatsAppSession
from app.services.data_science.ml_pattern_analyzer import MLPatternAnalyzer

logger = logging.getLogger(__name__)


class StatisticsGenerator:
    """Generates comprehensive statistics and insights"""
    
    @staticmethod
    def generate_executive_summary(db: Session, days: int = 7) -> Dict:
        """Generate executive summary for management"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"error": "No data available"}
            
            # Basic metrics
            total = len(sessions)
            active_pct = (len([s for s in sessions if s.is_active]) / total * 100) if total > 0 else 0
            
            # Get patterns
            resolution = MLPatternAnalyzer.analyze_resolution_patterns(db, days)
            hotspots = MLPatternAnalyzer.identify_hotspots(db, days)
            kpis = MLPatternAnalyzer.calculate_kpi_trends(db, days)
            
            return {
                "period": f"Last {days} days",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_sessions": total,
                    "active_sessions_pct": round(active_pct, 1),
                    "kb_resolution_rate": resolution.get("kb_effectiveness", 0),
                    "escalation_rate": resolution.get("escalated_to_ticket", {}).get("percentage", 0),
                    "avg_response_messages": round(kpis.get("avg_messages_per_session", 0), 1),
                    "avg_resolution_time": kpis.get("avg_duration_minutes", 0)
                },
                "key_metrics": kpis,
                "top_issues": hotspots.get("critical_hotspots", []),
                "main_recommendation": hotspots.get("recommendation", "Monitor system performance"),
                "status": _determine_system_health(resolution, hotspots)
            }
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_trend_analysis(db: Session, days: int = 30) -> Dict:
        """Generate trend analysis over longer period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"error": "No data available"}
            
            # Split into weeks for trend analysis
            weeks = {}
            for s in sessions:
                if s.created_at:
                    week = s.created_at.isocalendar()[1]
                    if week not in weeks:
                        weeks[week] = []
                    weeks[week].append(s)
            
            trends = []
            for week_num in sorted(weeks.keys()):
                week_sessions = weeks[week_num]
                resolved = len([s for s in week_sessions if s.current_state == "closed"])
                escalated = len([s for s in week_sessions if s.ticket_id])
                
                trends.append({
                    "week": f"Week {week_num}",
                    "sessions": len(week_sessions),
                    "resolved": resolved,
                    "escalated": escalated,
                    "resolution_rate": round(resolved / len(week_sessions) * 100, 1) if week_sessions else 0
                })
            
            # Calculate trend direction
            if len(trends) >= 2:
                recent_rate = trends[-1]["resolution_rate"]
                previous_rate = trends[-2]["resolution_rate"]
                trend_direction = "📈 Improving" if recent_rate > previous_rate else "📉 Declining" if recent_rate < previous_rate else "➡️ Stable"
            else:
                trend_direction = "➡️ Insufficient data"
            
            return {
                "period": f"Last {days} days",
                "weekly_trends": trends,
                "trend_direction": trend_direction,
                "overall_trend": _calculate_overall_trend(trends),
                "recommendation": _generate_trend_recommendation(trends)
            }
        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_performance_report(db: Session) -> Dict:
        """Generate comprehensive performance report"""
        try:
            # Daily stats
            daily_patterns = MLPatternAnalyzer.analyze_temporal_patterns(db, 7)
            
            # Resolution stats
            resolution = MLPatternAnalyzer.analyze_resolution_patterns(db, 7)
            
            # Problem patterns
            problems = MLPatternAnalyzer.analyze_problem_patterns(db, 7)
            
            # Calculate performance score (0-100)
            kb_effectiveness = resolution.get("kb_effectiveness", 0)
            low_abandonment = 100 - resolution.get("abandoned", {}).get("percentage", 100)
            
            # Performance score: 40% KB effectiveness + 30% low abandonment + 30% KPIs
            perf_score = (
                kb_effectiveness * 0.4 +
                low_abandonment * 0.3 +
                (100 - resolution.get("escalation_rate", {}).get("percentage", 50)) * 0.3
            )
            
            return {
                "performance_score": round(perf_score, 1),
                "score_grade": _calculate_grade(perf_score),
                "resolution_metrics": resolution,
                "problem_patterns": problems,
                "temporal_patterns": daily_patterns,
                "next_review_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "action_items": _generate_action_items(resolution, problems, daily_patterns)
            }
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_insights_report(db: Session, days: int = 7) -> Dict:
        """Generate AI-powered insights and recommendations"""
        try:
            hotspots = MLPatternAnalyzer.identify_hotspots(db, days)
            patterns = MLPatternAnalyzer.analyze_problem_patterns(db, days)
            resolution = MLPatternAnalyzer.analyze_resolution_patterns(db, days)
            temporal = MLPatternAnalyzer.analyze_temporal_patterns(db, days)
            
            insights = {
                "generated_at": datetime.now().isoformat(),
                "insights": [],
                "recommendations": [],
                "warnings": []
            }
            
            # Generate insights
            if patterns.get("top_issues"):
                top_issue = patterns["top_issues"][0]
                insights["insights"].append({
                    "category": "Top Issue",
                    "detail": f"{top_issue['category']} is the most frequent problem ({top_issue['percentage']}% of all issues)",
                    "severity": "🟡 Medium"
                })
            
            if resolution.get("kb_effectiveness", 0) < 50:
                insights["warnings"].append({
                    "category": "Low KB Effectiveness",
                    "detail": f"Only {resolution['kb_effectiveness']}% of issues are resolved by KB. Consider KB improvement.",
                    "severity": "🔴 Critical"
                })
            
            if resolution.get("abandoned", {}).get("percentage", 0) > 15:
                insights["warnings"].append({
                    "category": "High Abandonment Rate",
                    "detail": f"{resolution['abandoned']['percentage']}% of sessions are abandoned. Review user experience.",
                    "severity": "🟠 High"
                })
            
            # Generate recommendations
            if temporal.get("peak_hours"):
                peak_hour = temporal["peak_hours"][0]["hour"]
                insights["recommendations"].append(
                    f"Schedule peak support staff availability during {peak_hour}-{int(peak_hour.split(':')[0])+1}:00"
                )
            
            if hotspots.get("critical_hotspots"):
                top_hotspot = hotspots["critical_hotspots"][0]
                insights["recommendations"].append(
                    f"Update KB solutions for '{top_hotspot['category']}' severity '{top_hotspot['severity']}' to reduce escalations"
                )
            
            if resolution.get("escalation_rate", {}).get("percentage", 0) > 40:
                insights["recommendations"].append(
                    "Consider expanding KB coverage or improving solution presentation format"
                )
            
            return insights
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {"error": str(e)}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _determine_system_health(resolution: Dict, hotspots: Dict) -> Dict:
    """Determine overall system health status"""
    kb_eff = resolution.get("kb_effectiveness", 0)
    escalation = resolution.get("escalated_to_ticket", {}).get("percentage", 0)
    
    if kb_eff >= 70 and escalation <= 30:
        return {
            "status": "🟢 Healthy",
            "level": "Good",
            "description": "System is performing well"
        }
    elif kb_eff >= 50 and escalation <= 50:
        return {
            "status": "🟡 Moderate",
            "level": "Fair",
            "description": "System is functional but has optimization opportunities"
        }
    else:
        return {
            "status": "🔴 Needs Attention",
            "level": "Poor",
            "description": "System requires immediate improvement"
        }


def _calculate_overall_trend(trends: List) -> str:
    """Calculate overall trend direction"""
    if len(trends) < 2:
        return "Insufficient data"
    
    recent_rates = [t["resolution_rate"] for t in trends[-3:]] if len(trends) >= 3 else [t["resolution_rate"] for t in trends]
    
    if all(recent_rates[i] <= recent_rates[i+1] for i in range(len(recent_rates)-1)):
        return "📈 Consistently Improving"
    elif all(recent_rates[i] >= recent_rates[i+1] for i in range(len(recent_rates)-1)):
        return "📉 Consistently Declining"
    else:
        return "⬆️⬇️ Fluctuating"


def _generate_trend_recommendation(trends: List) -> str:
    """Generate recommendation based on trends"""
    if not trends:
        return "No data for recommendation"
    
    recent_rate = trends[-1]["resolution_rate"] if trends else 0
    
    if recent_rate >= 80:
        return "Excellent performance - maintain current processes"
    elif recent_rate >= 60:
        return "Good performance - continue incremental improvements"
    elif recent_rate >= 40:
        return "Fair performance - implement optimization initiatives"
    else:
        return "Poor performance - urgent review and changes needed"


def _calculate_grade(score: float) -> str:
    """Convert score to letter grade"""
    if score >= 90:
        return "A (Excellent)"
    elif score >= 80:
        return "B (Good)"
    elif score >= 70:
        return "C (Satisfactory)"
    elif score >= 60:
        return "D (Fair)"
    else:
        return "F (Poor)"


def _generate_action_items(resolution: Dict, problems: Dict, temporal: Dict) -> List[str]:
    """Generate action items for management"""
    actions = []
    
    # High escalation
    if resolution.get("escalation_rate", {}).get("percentage", 0) > 40:
        actions.append("ACTION: Address high escalation rate - review KB solutions")
    
    # Low KB effectiveness
    if resolution.get("kb_effectiveness", 0) < 60:
        actions.append("ACTION: Improve KB solution quality - focus on top categories")
    
    # High abandonment
    if resolution.get("abandoned", {}).get("percentage", 0) > 20:
        actions.append("ACTION: Investigate user experience issues - high abandonment detected")
    
    # Peak hour preparation
    if temporal.get("peak_hours"):
        actions.append(f"ACTION: Schedule staff for peak hours identified in temporal analysis")
    
    if not actions:
        actions.append("MAINTAIN: Current processes are performing well - continue monitoring")
    
    return actions
