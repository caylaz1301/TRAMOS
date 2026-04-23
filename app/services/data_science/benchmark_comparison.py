"""
Benchmark Comparison Service
Compares current metrics against industry standards and historical benchmarks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.database_models import WhatsAppSession

logger = logging.getLogger(__name__)


class IndustryBenchmark:
    """Industry standard benchmarks for WhatsApp AI support systems"""
    
    # Industry averages for AI-powered WhatsApp support
    INDUSTRY_STANDARDS = {
        "kb_resolution_rate": {
            "excellent": 75,
            "good": 60,
            "average": 45,
            "poor": 30
        },
        "escalation_rate": {
            "excellent": 20,
            "good": 35,
            "average": 50,
            "poor": 70
        },
        "avg_messages_per_session": {
            "excellent": 5,
            "good": 7,
            "average": 10,
            "poor": 15
        },
        "avg_resolution_time_minutes": {
            "excellent": 5,
            "good": 10,
            "average": 15,
            "poor": 30
        },
        "abandonment_rate": {
            "excellent": 5,
            "good": 10,
            "average": 20,
            "poor": 40
        },
        "customer_satisfaction": {
            "excellent": 90,
            "good": 80,
            "average": 70,
            "poor": 50
        }
    }


class BenchmarkComparison:
    """Compare system metrics against benchmarks"""
    
    @staticmethod
    def generate_benchmark_report(db: Session) -> Dict[str, Any]:
        """Generate comprehensive benchmark comparison report"""
        try:
            # Get current metrics
            current_metrics = BenchmarkComparison._calculate_current_metrics(db)
            
            # Get historical metrics
            historical_metrics = BenchmarkComparison._calculate_historical_metrics(db)
            
            # Compare against industry
            industry_comparison = BenchmarkComparison._compare_with_industry(current_metrics)
            
            # Generate recommendations
            recommendations = BenchmarkComparison._generate_recommendations(
                current_metrics, 
                historical_metrics,
                industry_comparison
            )
            
            return {
                "period": f"Last 7 days",
                "generated_at": datetime.now().isoformat(),
                "current_metrics": current_metrics,
                "historical_metrics": historical_metrics,
                "industry_comparison": industry_comparison,
                "recommendations": recommendations,
                "overall_score": BenchmarkComparison._calculate_overall_score(industry_comparison)
            }
        except Exception as e:
            logger.error(f"Error generating benchmark report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _calculate_current_metrics(db: Session) -> Dict[str, Any]:
        """Calculate current system metrics"""
        cutoff = datetime.now() - timedelta(days=7)
        sessions = db.query(WhatsAppSession).filter(
            WhatsAppSession.created_at >= cutoff
        ).all()
        
        if not sessions:
            return {}
        
        total = len(sessions)
        resolved = len([s for s in sessions if s.current_state == "resolved"])
        escalated = len([s for s in sessions if s.ticket_id])
        abandoned = len([s for s in sessions if s.current_state == "closed" and not s.is_active and s.message_count < 3])
        
        total_messages = sum(s.message_count for s in sessions)
        total_duration = sum(
            (s.last_activity - s.created_at).total_seconds() / 60
            for s in sessions 
            if s.created_at and s.last_activity
        )
        
        kb_resolution_rate = (resolved / total * 100) if total > 0 else 0
        escalation_rate = (escalated / total * 100) if total > 0 else 0
        abandonment_rate = (abandoned / total * 100) if total > 0 else 0
        avg_messages = total_messages / total if total > 0 else 0
        avg_resolution_time = total_duration / total if total > 0 else 0
        
        # Estimate satisfaction from resolution
        estimated_satisfaction = max(30, min(95, kb_resolution_rate * 1.2 - escalation_rate * 0.8))
        
        return {
            "total_sessions": total,
            "kb_resolution_rate": round(kb_resolution_rate, 1),
            "escalation_rate": round(escalation_rate, 1),
            "abandonment_rate": round(abandonment_rate, 1),
            "avg_messages_per_session": round(avg_messages, 1),
            "avg_resolution_time_minutes": round(avg_resolution_time, 1),
            "customer_satisfaction": round(estimated_satisfaction, 1)
        }
    
    @staticmethod
    def _calculate_historical_metrics(db: Session) -> Dict[str, Any]:
        """Calculate metrics from previous period (7-14 days ago)"""
        cutoff_current = datetime.now() - timedelta(days=7)
        cutoff_previous = datetime.now() - timedelta(days=14)
        
        sessions = db.query(WhatsAppSession).filter(
            WhatsAppSession.created_at >= cutoff_previous,
            WhatsAppSession.created_at < cutoff_current
        ).all()
        
        if not sessions:
            return {}
        
        total = len(sessions)
        resolved = len([s for s in sessions if s.current_state == "resolved"])
        escalated = len([s for s in sessions if s.ticket_id])
        abandoned = len([s for s in sessions if s.current_state == "closed" and not s.is_active and s.message_count < 3])
        
        total_messages = sum(s.message_count for s in sessions)
        total_duration = sum(
            (s.last_activity - s.created_at).total_seconds() / 60
            for s in sessions 
            if s.created_at and s.last_activity
        )
        
        kb_resolution_rate = (resolved / total * 100) if total > 0 else 0
        escalation_rate = (escalated / total * 100) if total > 0 else 0
        abandonment_rate = (abandoned / total * 100) if total > 0 else 0
        avg_messages = total_messages / total if total > 0 else 0
        avg_resolution_time = total_duration / total if total > 0 else 0
        
        estimated_satisfaction = max(30, min(95, kb_resolution_rate * 1.2 - escalation_rate * 0.8))
        
        return {
            "total_sessions": total,
            "kb_resolution_rate": round(kb_resolution_rate, 1),
            "escalation_rate": round(escalation_rate, 1),
            "abandonment_rate": round(abandonment_rate, 1),
            "avg_messages_per_session": round(avg_messages, 1),
            "avg_resolution_time_minutes": round(avg_resolution_time, 1),
            "customer_satisfaction": round(estimated_satisfaction, 1)
        }
    
    @staticmethod
    def _compare_with_industry(current: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current metrics with industry benchmarks"""
        if not current:
            return {}
        
        comparison = {}
        standards = IndustryBenchmark.INDUSTRY_STANDARDS
        
        # KB Resolution Rate
        kb_rate = current.get("kb_resolution_rate", 0)
        kb_level = "poor"
        for level, threshold in [("excellent", 75), ("good", 60), ("average", 45)]:
            if kb_rate >= threshold:
                kb_level = level
                break
        
        comparison["kb_resolution_rate"] = {
            "current": kb_rate,
            "benchmark": {
                "excellent": standards["kb_resolution_rate"]["excellent"],
                "good": standards["kb_resolution_rate"]["good"],
                "average": standards["kb_resolution_rate"]["average"]
            },
            "level": kb_level,
            "gap": kb_rate - standards["kb_resolution_rate"]["good"],
            "status": "✅ Above Target" if kb_level in ["excellent", "good"] else "⚠️ Below Target"
        }
        
        # Escalation Rate
        esc_rate = current.get("escalation_rate", 0)
        esc_level = "poor"
        for level, threshold in [("excellent", 20), ("good", 35), ("average", 50)]:
            if esc_rate <= threshold:
                esc_level = level
                break
        
        comparison["escalation_rate"] = {
            "current": esc_rate,
            "benchmark": {
                "excellent": standards["escalation_rate"]["excellent"],
                "good": standards["escalation_rate"]["good"],
                "average": standards["escalation_rate"]["average"]
            },
            "level": esc_level,
            "gap": esc_rate - standards["escalation_rate"]["good"],
            "status": "✅ Above Target" if esc_level in ["excellent", "good"] else "⚠️ Below Target"
        }
        
        # Average Messages
        avg_msg = current.get("avg_messages_per_session", 0)
        msg_level = "poor"
        for level, threshold in [("excellent", 5), ("good", 7), ("average", 10)]:
            if avg_msg <= threshold:
                msg_level = level
                break
        
        comparison["avg_messages_per_session"] = {
            "current": avg_msg,
            "benchmark": {
                "excellent": standards["avg_messages_per_session"]["excellent"],
                "good": standards["avg_messages_per_session"]["good"],
                "average": standards["avg_messages_per_session"]["average"]
            },
            "level": msg_level,
            "gap": avg_msg - standards["avg_messages_per_session"]["good"],
            "status": "✅ Above Target" if msg_level in ["excellent", "good"] else "⚠️ Below Target"
        }
        
        # Resolution Time
        res_time = current.get("avg_resolution_time_minutes", 0)
        time_level = "poor"
        for level, threshold in [("excellent", 5), ("good", 10), ("average", 15)]:
            if res_time <= threshold:
                time_level = level
                break
        
        comparison["avg_resolution_time_minutes"] = {
            "current": res_time,
            "benchmark": {
                "excellent": standards["avg_resolution_time_minutes"]["excellent"],
                "good": standards["avg_resolution_time_minutes"]["good"],
                "average": standards["avg_resolution_time_minutes"]["average"]
            },
            "level": time_level,
            "gap": res_time - standards["avg_resolution_time_minutes"]["good"],
            "status": "✅ Above Target" if time_level in ["excellent", "good"] else "⚠️ Below Target"
        }
        
        # Abandonment Rate
        aband_rate = current.get("abandonment_rate", 0)
        aband_level = "poor"
        for level, threshold in [("excellent", 5), ("good", 10), ("average", 20)]:
            if aband_rate <= threshold:
                aband_level = level
                break
        
        comparison["abandonment_rate"] = {
            "current": aband_rate,
            "benchmark": {
                "excellent": standards["abandonment_rate"]["excellent"],
                "good": standards["abandonment_rate"]["good"],
                "average": standards["abandonment_rate"]["average"]
            },
            "level": aband_level,
            "gap": aband_rate - standards["abandonment_rate"]["good"],
            "status": "✅ Above Target" if aband_level in ["excellent", "good"] else "⚠️ Below Target"
        }
        
        # Satisfaction
        sat = current.get("customer_satisfaction", 0)
        sat_level = "poor"
        for level, threshold in [("excellent", 90), ("good", 80), ("average", 70)]:
            if sat >= threshold:
                sat_level = level
                break
        
        comparison["customer_satisfaction"] = {
            "current": sat,
            "benchmark": {
                "excellent": standards["customer_satisfaction"]["excellent"],
                "good": standards["customer_satisfaction"]["good"],
                "average": standards["customer_satisfaction"]["average"]
            },
            "level": sat_level,
            "gap": sat - standards["customer_satisfaction"]["good"],
            "status": "✅ Above Target" if sat_level in ["excellent", "good"] else "⚠️ Below Target"
        }
        
        return comparison
    
    @staticmethod
    def _generate_recommendations(
        current: Dict[str, Any],
        historical: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on benchmarks"""
        recommendations = []
        
        if not current or not comparison:
            return recommendations
        
        # KB Resolution - if below good benchmark
        if comparison.get("kb_resolution_rate", {}).get("gap", 0) < 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "KB Performance",
                "action": "Expand knowledge base solutions",
                "detail": f"KB resolution at {current.get('kb_resolution_rate', 0)}% vs good benchmark of 60%",
                "impact": "Could reduce escalations by ~10-15%"
            })
        
        # Escalation Rate - if above good benchmark
        if comparison.get("escalation_rate", {}).get("gap", 0) > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Escalation Management",
                "action": "Reduce escalation rate",
                "detail": f"Escalations at {current.get('escalation_rate', 0)}% vs good benchmark of 35%",
                "impact": "Improve KB solutions and automation rules"
            })
        
        # Message Count - if above benchmark
        if comparison.get("avg_messages_per_session", {}).get("gap", 0) > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Conversation Efficiency",
                "action": "Streamline conversation flow",
                "detail": f"Average {current.get('avg_messages_per_session', 0)} messages vs good benchmark of 7",
                "impact": "Improve initial greeting and faster problem identification"
            })
        
        # Resolution Time - if above benchmark
        if comparison.get("avg_resolution_time_minutes", {}).get("gap", 0) > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Speed Optimization",
                "action": "Reduce conversation duration",
                "detail": f"Average {current.get('avg_resolution_time_minutes', 0)} min vs good benchmark of 10 min",
                "impact": "Optimize initial response and KB search algorithms"
            })
        
        # Abandonment - if above benchmark
        if comparison.get("abandonment_rate", {}).get("gap", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "User Retention",
                "action": "Reduce abandonment rate",
                "detail": f"Abandonment at {current.get('abandonment_rate', 0)}% vs good benchmark of 10%",
                "impact": "Improve initial greeting and user experience"
            })
        
        # Trend comparison
        if historical:
            kb_trend = current.get("kb_resolution_rate", 0) - historical.get("kb_resolution_rate", 0)
            if kb_trend < -10:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Trend Analysis",
                    "action": "Investigate KB performance decline",
                    "detail": f"KB resolution dropped {abs(kb_trend):.1f}% from previous period",
                    "impact": "Check for system changes or KB solution degradation"
                })
            elif kb_trend > 10:
                recommendations.append({
                    "priority": "INFO",
                    "category": "Trend Analysis",
                    "action": "Maintain momentum",
                    "detail": f"KB resolution improved {kb_trend:.1f}% - keep this up!",
                    "impact": "Whatever changes made are working well"
                })
        
        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "INFO": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))
        
        return recommendations
    
    @staticmethod
    def _calculate_overall_score(comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system score"""
        if not comparison:
            return {}
        
        levels = []
        for metric, data in comparison.items():
            level = data.get("level", "poor")
            level_scores = {"excellent": 100, "good": 80, "average": 60, "poor": 40}
            levels.append(level_scores.get(level, 40))
        
        average_score = sum(levels) / len(levels) if levels else 0
        
        # Overall grade
        if average_score >= 90:
            grade = "A"
            status = "🟢 Excellent"
        elif average_score >= 80:
            grade = "B"
            status = "🟢 Good"
        elif average_score >= 70:
            grade = "C"
            status = "🟡 Average"
        elif average_score >= 60:
            grade = "D"
            status = "🟠 Below Average"
        else:
            grade = "F"
            status = "🔴 Poor"
        
        return {
            "score": round(average_score, 1),
            "grade": grade,
            "status": status,
            "metrics_evaluated": len(comparison)
        }
