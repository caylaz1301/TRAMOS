"""
Predictive Analytics Engine
Forecasts future trends and anomalies using time-series analysis
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from statistics import mean, stdev

from app.database_models import WhatsAppSession

logger = logging.getLogger(__name__)


class PredictiveAnalytics:
    """Predictive analytics engine for trend forecasting"""
    
    @staticmethod
    def forecast_issue_volume(db: Session, days_to_predict: int = 7) -> Dict:
        """Forecast issue volume for next N days"""
        try:
            # Get historical data (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"error": "Insufficient data"}
            
            # Group by day
            daily_counts = _group_by_day(sessions)
            if len(daily_counts) < 7:
                return {"error": "Insufficient historical data"}
            
            # Calculate trend
            values = list(daily_counts.values())
            trend = _calculate_trend(values)
            
            # Generate forecast
            forecast = []
            last_value = values[-1]
            
            for i in range(1, days_to_predict + 1):
                predicted_value = last_value + (trend * i)
                predicted_value = max(0, predicted_value)  # Can't be negative
                
                forecast_date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                forecast.append({
                    "date": forecast_date,
                    "predicted_volume": round(predicted_value, 0),
                    "confidence": _calculate_confidence(len(values), i)
                })
            
            return {
                "forecast": forecast,
                "trend_direction": "📈 Increasing" if trend > 0 else "📉 Decreasing" if trend < 0 else "➡️ Stable",
                "trend_strength": abs(round(trend, 2)),
                "historical_avg": round(mean(values), 1),
                "historical_std": round(stdev(values) if len(values) > 1 else 0, 1)
            }
        
        except Exception as e:
            logger.error(f"Error forecasting issue volume: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def predict_escalation_risk(db: Session) -> Dict:
        """Predict escalation risk based on current patterns"""
        try:
            cutoff_date = datetime.now() - timedelta(hours=24)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"error": "Insufficient data"}
            
            # Analyze current patterns
            escalations = len([s for s in sessions if s.ticket_id])
            total = len(sessions)
            current_rate = (escalations / total * 100) if total > 0 else 0
            
            # Historical rate (last 7 days)
            history_cutoff = datetime.now() - timedelta(days=7)
            historical_sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= history_cutoff
            ).all()
            
            historical_escalations = len([s for s in historical_sessions if s.ticket_id])
            historical_total = len(historical_sessions)
            historical_rate = (historical_escalations / historical_total * 100) if historical_total > 0 else 0
            
            # Risk assessment
            risk_increase = current_rate - historical_rate
            
            if risk_increase > 5:
                risk_level = "🔴 HIGH"
                recommendation = "Urgent: Escalation rate increasing. Review KB quality immediately."
            elif risk_increase > 2:
                risk_level = "🟠 MEDIUM"
                recommendation = "Monitor: Escalation increasing. Plan KB improvements."
            else:
                risk_level = "🟢 LOW"
                recommendation = "Good: Escalation rate stable or improving."
            
            return {
                "current_escalation_rate": round(current_rate, 1),
                "historical_escalation_rate": round(historical_rate, 1),
                "risk_change": round(risk_increase, 1),
                "risk_level": risk_level,
                "recommendation": recommendation,
                "prediction": f"If current trend continues, escalation may reach {round(current_rate + (risk_increase * 3), 1)}% in 3 days"
            }
        
        except Exception as e:
            logger.error(f"Error predicting escalation risk: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def predict_optimal_staffing(db: Session) -> Dict:
        """Predict optimal support staff levels"""
        try:
            # Analyze last 7 days by hour
            cutoff_date = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"error": "Insufficient data"}
            
            # Group by hour
            hourly_distribution = [0] * 24
            for s in sessions:
                if s.created_at:
                    hour = s.created_at.hour
                    hourly_distribution[hour] += 1
            
            total_sessions = sum(hourly_distribution)
            avg_per_hour = total_sessions / 24 if total_sessions > 0 else 0
            
            # Identify peak hours
            peak_threshold = avg_per_hour * 1.5
            peak_hours = [i for i, count in enumerate(hourly_distribution) if count > peak_threshold]
            
            # Calculate staffing needs
            staffing_recommendations = []
            for hour in range(24):
                sessions_in_hour = hourly_distribution[hour]
                # Assume 1 staff can handle ~5 concurrent issues
                staff_needed = max(1, int(sessions_in_hour / 5))
                
                staffing_recommendations.append({
                    "hour": f"{hour:02d}:00-{hour+1:02d}:00",
                    "expected_sessions": sessions_in_hour,
                    "recommended_staff": staff_needed,
                    "priority": "🔴 HIGH" if hour in peak_hours else "🟢 NORMAL"
                })
            
            return {
                "average_sessions_per_hour": round(avg_per_hour, 1),
                "peak_hours": [f"{h:02d}:00" for h in peak_hours],
                "staffing_plan": staffing_recommendations,
                "recommendation": f"Schedule additional staff during {', '.join([f'{h:02d}:00' for h in peak_hours[:3]])} hours"
            }
        
        except Exception as e:
            logger.error(f"Error predicting staffing: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def predict_kb_coverage_gaps(db: Session) -> Dict:
        """Identify areas where KB coverage is insufficient"""
        try:
            cutoff_date = datetime.now() - timedelta(days=14)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date,
                WhatsAppSession.problem_category.isnot(None),
                WhatsAppSession.ticket_id.isnot(None)  # Only escalated issues
            ).all()
            
            if not sessions:
                return {"error": "Insufficient escalation data"}
            
            # Count escalations by category
            category_escalations = {}
            for s in sessions:
                category = s.problem_category or "Unknown"
                if category not in category_escalations:
                    category_escalations[category] = 0
                category_escalations[category] += 1
            
            # Identify gaps
            gaps = sorted(category_escalations.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "kb_coverage_gaps": [
                    {
                        "category": cat,
                        "escalation_count": count,
                        "priority": "🔴 CRITICAL" if count > 10 else "🟠 HIGH"
                    }
                    for cat, count in gaps
                ],
                "recommendation": f"Focus KB improvements on: {', '.join([g[0] for g in gaps[:3]])}",
                "estimated_impact": f"Improving KB for top 3 gaps could reduce escalations by ~{sum([g[1] for g in gaps[:3]])} issues"
            }
        
        except Exception as e:
            logger.error(f"Error predicting KB gaps: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_all_predictions(db: Session) -> Dict:
        """Get comprehensive predictions"""
        return {
            "volume_forecast": PredictiveAnalytics.forecast_issue_volume(db),
            "escalation_risk": PredictiveAnalytics.predict_escalation_risk(db),
            "staffing": PredictiveAnalytics.predict_optimal_staffing(db),
            "kb_gaps": PredictiveAnalytics.predict_kb_coverage_gaps(db),
            "generated_at": datetime.now().isoformat()
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _group_by_day(sessions: List) -> Dict[str, int]:
    """Group sessions by day"""
    daily = {}
    for s in sessions:
        if s.created_at:
            day = s.created_at.strftime("%Y-%m-%d")
            daily[day] = daily.get(day, 0) + 1
    return daily


def _calculate_trend(values: List[float]) -> float:
    """Calculate linear trend using simple regression"""
    if len(values) < 2:
        return 0
    
    n = len(values)
    x = list(range(n))
    
    mean_x = sum(x) / n
    mean_y = sum(values) / n
    
    numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    return numerator / denominator if denominator != 0 else 0


def _calculate_confidence(data_points: int, days_ahead: int) -> float:
    """Calculate forecast confidence based on data and prediction distance"""
    base_confidence = min(95, 50 + (data_points * 2))  # More data = higher confidence
    decay = max(0, 100 - (days_ahead * 5))  # Confidence decreases with distance
    return round(min(base_confidence, decay), 0)
