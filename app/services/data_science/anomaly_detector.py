"""
Anomaly Detection for WhatsApp Bot Analytics
Detects unusual patterns, anomalies, and outliers in conversation data
Uses statistical methods: z-score, standard deviation, moving averages
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from statistics import mean, stdev
from sqlalchemy.orm import Session

from app.database_models import WhatsAppSession, Conversation

logger = logging.getLogger(__name__)


class AnomalyType:
    """Types of detectable anomalies"""
    VOLUME_SPIKE = "volume_spike"
    ESCALATION_SURGE = "escalation_surge"
    RESPONSE_TIME_ANOMALY = "response_time_anomaly"
    QUALITY_DROP = "quality_drop"
    RESOLUTION_FAILURE = "resolution_failure"
    ABANDONMENT_SPIKE = "abandonment_spike"
    UNRESPONSIVE_PERIOD = "unresponsive_period"
    CATEGORY_SHIFT = "category_shift"


class Anomaly:
    """Represents a detected anomaly"""
    
    def __init__(
        self, 
        type: str,
        severity: str,  # low, medium, high, critical
        title: str,
        description: str,
        metric: str,
        current_value: float,
        expected_value: float,
        deviation_percent: float,
        timestamp: datetime,
        recommendation: str,
        affected_period: str = "1 hour"
    ):
        self.type = type
        self.severity = severity
        self.title = title
        self.description = description
        self.metric = metric
        self.current_value = current_value
        self.expected_value = expected_value
        self.deviation_percent = deviation_percent
        self.timestamp = timestamp
        self.recommendation = recommendation
        self.affected_period = affected_period
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert anomaly to dictionary"""
        severity_icons = {
            "low": "🟡",
            "medium": "🟠",
            "high": "🔴",
            "critical": "🔴🔴"
        }
        return {
            "type": self.type,
            "severity": self.severity,
            "icon": severity_icons.get(self.severity, "❓"),
            "title": self.title,
            "description": self.description,
            "metric": self.metric,
            "current_value": round(self.current_value, 2),
            "expected_value": round(self.expected_value, 2),
            "deviation_percent": round(self.deviation_percent, 1),
            "timestamp": self.timestamp.isoformat(),
            "affected_period": self.affected_period,
            "recommendation": self.recommendation
        }


class AnomalyDetector:
    """Detect anomalies in conversation patterns and metrics"""
    
    # Thresholds for anomaly detection
    VOLUME_Z_SCORE_THRESHOLD = 2.5
    TIME_WINDOW = 24  # Last 24 hours for baseline
    SPIKE_THRESHOLD_PERCENT = 50  # 50% deviation triggers spike
    QUALITY_DROP_THRESHOLD = 20  # 20% drop triggers anomaly
    
    @staticmethod
    def detect_all_anomalies(db: Session) -> Dict[str, Any]:
        """Run all anomaly detection methods"""
        anomalies = []
        
        try:
            anomalies.extend(AnomalyDetector._detect_volume_spikes(db))
            anomalies.extend(AnomalyDetector._detect_escalation_surge(db))
            anomalies.extend(AnomalyDetector._detect_response_time_anomaly(db))
            anomalies.extend(AnomalyDetector._detect_quality_degradation(db))
            anomalies.extend(AnomalyDetector._detect_resolution_failure_pattern(db))
            anomalies.extend(AnomalyDetector._detect_abandonment_spike(db))
            anomalies.extend(AnomalyDetector._detect_category_shift(db))
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return {"error": str(e), "anomalies": []}
        
        return {
            "total_anomalies": len(anomalies),
            "critical_count": len([a for a in anomalies if a.severity == "critical"]),
            "high_count": len([a for a in anomalies if a.severity == "high"]),
            "medium_count": len([a for a in anomalies if a.severity == "medium"]),
            "anomalies": [a.to_dict() for a in sorted(
                anomalies, 
                key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.severity, 0),
                reverse=True
            )],
            "generated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def _detect_volume_spikes(db: Session) -> List[Anomaly]:
        """Detect unusual volume spikes"""
        anomalies = []
        
        try:
            # Get last 24 hours of sessions
            cutoff_24h = datetime.now() - timedelta(hours=24)
            cutoff_avg = datetime.now() - timedelta(hours=48, minutes=-24)  # 24-48h window for baseline
            
            current_sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_24h
            ).count()
            
            baseline_sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_avg,
                WhatsAppSession.created_at < cutoff_24h
            ).count()
            
            if baseline_sessions > 0:
                percent_change = ((current_sessions - baseline_sessions) / baseline_sessions) * 100
                
                if percent_change > AnomalyDetector.SPIKE_THRESHOLD_PERCENT:
                    anomalies.append(Anomaly(
                        type=AnomalyType.VOLUME_SPIKE,
                        severity="high" if percent_change > 100 else "medium",
                        title=f"Unusual Volume Spike ({percent_change:.0f}%)",
                        description=f"Session volume increased significantly from previous period",
                        metric="Sessions per 24h",
                        current_value=current_sessions,
                        expected_value=baseline_sessions,
                        deviation_percent=percent_change,
                        timestamp=datetime.now(),
                        recommendation="Monitor system capacity, may need additional resources",
                        affected_period="Last 24 hours"
                    ))
        
        except Exception as e:
            logger.error(f"Error detecting volume spikes: {e}")
        
        return anomalies
    
    @staticmethod
    def _detect_escalation_surge(db: Session) -> List[Anomaly]:
        """Detect unusual escalation patterns"""
        anomalies = []
        
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            if not sessions or len(sessions) < 3:
                return anomalies
            
            escalation_count = len([s for s in sessions if s.ticket_id])
            escalation_rate = (escalation_count / len(sessions) * 100) if sessions else 0
            
            # If escalation rate > 70%, it's a surge
            if escalation_rate > 70:
                anomalies.append(Anomaly(
                    type=AnomalyType.ESCALATION_SURGE,
                    severity="critical" if escalation_rate > 85 else "high",
                    title=f"Escalation Surge ({escalation_rate:.0f}%)",
                    description="Unusually high number of issues being escalated",
                    metric="Escalation Rate",
                    current_value=escalation_rate,
                    expected_value=40,  # Expected baseline
                    deviation_percent=escalation_rate - 40,
                    timestamp=datetime.now(),
                    recommendation="Review KB solutions, increase support staff, investigate root cause",
                    affected_period="Last 24 hours"
                ))
        
        except Exception as e:
            logger.error(f"Error detecting escalation surge: {e}")
        
        return anomalies
    
    @staticmethod
    def _detect_response_time_anomaly(db: Session) -> List[Anomaly]:
        """Detect response time anomalies"""
        anomalies = []
        
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff,
                WhatsAppSession.created_at != None,
                WhatsAppSession.last_activity != None
            ).all()
            
            if not sessions or len(sessions) < 3:
                return anomalies
            
            response_times = []
            for s in sessions:
                if s.created_at and s.last_activity:
                    duration = (s.last_activity - s.created_at).total_seconds()
                    response_times.append(duration)
            
            if len(response_times) >= 3:
                avg_response = mean(response_times)
                std_dev = stdev(response_times) if len(response_times) > 1 else 0
                
                # Flag if any session takes 3x the average
                slow_sessions = [t for t in response_times if t > avg_response + (std_dev * 2)]
                
                if len(slow_sessions) > 0:
                    worst_time = max(slow_sessions)
                    anomalies.append(Anomaly(
                        type=AnomalyType.RESPONSE_TIME_ANOMALY,
                        severity="high" if worst_time > avg_response * 5 else "medium",
                        title=f"Response Time Anomaly ({worst_time/60:.0f} min vs {avg_response/60:.0f} min)",
                        description="Some sessions taking unusually long to complete",
                        metric="Session Duration (seconds)",
                        current_value=worst_time,
                        expected_value=avg_response,
                        deviation_percent=((worst_time - avg_response) / avg_response * 100),
                        timestamp=datetime.now(),
                        recommendation="Check system performance, review stuck conversations, increase timeout thresholds",
                        affected_period="Last 24 hours"
                    ))
        
        except Exception as e:
            logger.error(f"Error detecting response time anomaly: {e}")
        
        return anomalies
    
    @staticmethod
    def _detect_quality_degradation(db: Session) -> List[Anomaly]:
        """Detect quality degradation patterns"""
        anomalies = []
        
        try:
            cutoff_recent = datetime.now() - timedelta(hours=12)
            cutoff_prev = datetime.now() - timedelta(hours=24)
            
            recent = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_recent
            ).all()
            
            previous = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_prev,
                WhatsAppSession.created_at < cutoff_recent
            ).all()
            
            if not recent or not previous or len(recent) < 2 or len(previous) < 2:
                return anomalies
            
            # Calculate resolution by state
            recent_resolved = len([s for s in recent if s.current_state == "resolved"])
            recent_escalated = len([s for s in recent if s.ticket_id])
            recent_quality = (recent_resolved / len(recent) * 100) - (recent_escalated / len(recent) * 100)
            
            prev_resolved = len([s for s in previous if s.current_state == "resolved"])
            prev_escalated = len([s for s in previous if s.ticket_id])
            prev_quality = (prev_resolved / len(previous) * 100) - (prev_escalated / len(previous) * 100)
            
            quality_drop = prev_quality - recent_quality
            
            if quality_drop > AnomalyDetector.QUALITY_DROP_THRESHOLD:
                anomalies.append(Anomaly(
                    type=AnomalyType.QUALITY_DROP,
                    severity="high" if quality_drop > 40 else "medium",
                    title=f"Quality Degradation ({quality_drop:.0f}%)",
                    description="Service quality has declined significantly",
                    metric="Quality Score",
                    current_value=recent_quality,
                    expected_value=prev_quality,
                    deviation_percent=-quality_drop,
                    timestamp=datetime.now(),
                    recommendation="Audit recent conversations, add staff, improve KB solutions, check system stability",
                    affected_period="Last 12 hours"
                ))
        
        except Exception as e:
            logger.error(f"Error detecting quality degradation: {e}")
        
        return anomalies
    
    @staticmethod
    def _detect_resolution_failure_pattern(db: Session) -> List[Anomaly]:
        """Detect repeated resolution failures"""
        anomalies = []
        
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            if not sessions:
                return anomalies
            
            # Count sessions by category
            category_counts = {}
            category_escalations = {}
            
            for s in sessions:
                cat = s.problem_category or "Unknown"
                category_counts[cat] = category_counts.get(cat, 0) + 1
                
                if s.ticket_id:  # Escalated = not resolved by KB
                    category_escalations[cat] = category_escalations.get(cat, 0) + 1
            
            # Find categories with >80% escalation
            for cat, count in category_counts.items():
                escalations = category_escalations.get(cat, 0)
                escalation_rate = (escalations / count * 100) if count > 0 else 0
                
                if escalation_rate > 80 and count >= 3:
                    anomalies.append(Anomaly(
                        type=AnomalyType.RESOLUTION_FAILURE,
                        severity="critical" if escalation_rate > 90 else "high",
                        title=f"Resolution Failure: {cat} ({escalation_rate:.0f}%)",
                        description=f"Category '{cat}' has high failure rate",
                        metric="Escalation Rate by Category",
                        current_value=escalation_rate,
                        expected_value=40,
                        deviation_percent=escalation_rate - 40,
                        timestamp=datetime.now(),
                        recommendation=f"Urgent: Address KB solutions for {cat}, add detection rules, improve troubleshooting steps",
                        affected_period="Last 24 hours"
                    ))
        
        except Exception as e:
            logger.error(f"Error detecting resolution failures: {e}")
        
        return anomalies
    
    @staticmethod
    def _detect_abandonment_spike(db: Session) -> List[Anomaly]:
        """Detect abandonment pattern spikes"""
        anomalies = []
        
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            if not sessions or len(sessions) < 5:
                return anomalies
            
            abandoned = len([s for s in sessions if s.current_state == "closed" and not s.is_active and s.message_count < 3])
            abandonment_rate = (abandoned / len(sessions) * 100) if sessions else 0
            
            if abandonment_rate > 30:
                anomalies.append(Anomaly(
                    type=AnomalyType.ABANDONMENT_SPIKE,
                    severity="high" if abandonment_rate > 50 else "medium",
                    title=f"Abandonment Spike ({abandonment_rate:.0f}%)",
                    description="Users abandoning conversations without resolution",
                    metric="Abandonment Rate",
                    current_value=abandonment_rate,
                    expected_value=10,
                    deviation_percent=abandonment_rate - 10,
                    timestamp=datetime.now(),
                    recommendation="Improve initial response quality, faster greetings, clearer instructions, reduce friction",
                    affected_period="Last 24 hours"
                ))
        
        except Exception as e:
            logger.error(f"Error detecting abandonment spike: {e}")
        
        return anomalies
    
    @staticmethod
    def _detect_category_shift(db: Session) -> List[Anomaly]:
        """Detect unusual shifts in issue categories"""
        anomalies = []
        
        try:
            cutoff_recent = datetime.now() - timedelta(hours=12)
            cutoff_prev = datetime.now() - timedelta(hours=24)
            
            recent = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_recent
            ).all()
            
            previous = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_prev,
                WhatsAppSession.created_at < cutoff_recent
            ).all()
            
            if not recent or not previous:
                return anomalies
            
            # Get category distributions
            recent_cats = {}
            for s in recent:
                cat = s.problem_category or "Unknown"
                recent_cats[cat] = recent_cats.get(cat, 0) + 1
            
            prev_cats = {}
            for s in previous:
                cat = s.problem_category or "Unknown"
                prev_cats[cat] = prev_cats.get(cat, 0) + 1
            
            # Find category that changed most
            max_change = 0
            changed_category = None
            
            all_cats = set(recent_cats.keys()) | set(prev_cats.keys())
            for cat in all_cats:
                recent_pct = (recent_cats.get(cat, 0) / len(recent) * 100) if recent else 0
                prev_pct = (prev_cats.get(cat, 0) / len(previous) * 100) if previous else 0
                change = abs(recent_pct - prev_pct)
                
                if change > max_change:
                    max_change = change
                    changed_category = cat
            
            if max_change > 30 and changed_category:
                anomalies.append(Anomaly(
                    type=AnomalyType.CATEGORY_SHIFT,
                    severity="medium",
                    title=f"Category Shift: {changed_category} ({max_change:.0f}%)",
                    description=f"Unusual change in problem distribution",
                    metric="Category Share Change",
                    current_value=max_change,
                    expected_value=10,
                    deviation_percent=max_change - 10,
                    timestamp=datetime.now(),
                    recommendation=f"Investigate what's causing increase in {changed_category} issues, may indicate system problem",
                    affected_period="Last 12 hours"
                ))
        
        except Exception as e:
            logger.error(f"Error detecting category shift: {e}")
        
        return anomalies
