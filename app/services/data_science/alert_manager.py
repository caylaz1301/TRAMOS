"""
Alert Manager
Manages real-time alerts and notifications based on system metrics
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.database_models import WhatsAppSession

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    HIGH_ESCALATION = "high_escalation"
    LOW_RESOLUTION = "low_resolution"
    HIGH_ABANDONMENT = "high_abandonment"
    QUALITY_DROP = "quality_drop"
    PEAK_ISSUE = "peak_issue"
    RESPONSE_TIME = "response_time"
    KB_INEFFECTIVE = "kb_ineffective"
    SYSTEM_ANOMALY = "system_anomaly"


@dataclass
class Alert:
    """Alert data structure"""
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    metric_value: float
    threshold: float
    recommendation: str
    timestamp: datetime


class AlertManager:
    """Manages system alerts and notifications"""
    
    # Alert thresholds
    THRESHOLDS = {
        AlertType.HIGH_ESCALATION: 40,  # % of sessions escalated
        AlertType.LOW_RESOLUTION: 50,   # % of issues resolved by KB
        AlertType.HIGH_ABANDONMENT: 15, # % of abandoned sessions
        AlertType.RESPONSE_TIME: 300,   # seconds avg response time
    }
    
    @staticmethod
    def check_system_health(db: Session) -> List[Alert]:
        """Check overall system health and generate alerts"""
        alerts = []
        
        try:
            # Get recent sessions (last 24 hours)
            cutoff_date = datetime.now() - timedelta(hours=24)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return alerts
            
            total = len(sessions)
            
            # Check escalation rate
            escalated = len([s for s in sessions if s.ticket_id])
            escalation_rate = (escalated / total * 100) if total > 0 else 0
            
            if escalation_rate > AlertManager.THRESHOLDS[AlertType.HIGH_ESCALATION]:
                alerts.append(Alert(
                    type=AlertType.HIGH_ESCALATION,
                    severity=AlertSeverity.CRITICAL,
                    title="High Escalation Rate Detected",
                    message=f"{escalation_rate:.1f}% of sessions are being escalated to support",
                    metric_value=escalation_rate,
                    threshold=AlertManager.THRESHOLDS[AlertType.HIGH_ESCALATION],
                    recommendation="Review KB solutions and improve response quality",
                    timestamp=datetime.now()
                ))
            
            # Check resolution rate
            resolved = len([s for s in sessions if s.current_state == "resolved"])
            resolution_rate = (resolved / total * 100) if total > 0 else 0
            
            if resolution_rate < AlertManager.THRESHOLDS[AlertType.LOW_RESOLUTION]:
                alerts.append(Alert(
                    type=AlertType.LOW_RESOLUTION,
                    severity=AlertSeverity.WARNING,
                    title="Low KB Resolution Rate",
                    message=f"Only {resolution_rate:.1f}% of issues resolved without escalation",
                    metric_value=resolution_rate,
                    threshold=AlertManager.THRESHOLDS[AlertType.LOW_RESOLUTION],
                    recommendation="Improve KB solution accuracy and coverage",
                    timestamp=datetime.now()
                ))
            
            # Check abandonment rate
            abandoned = len([s for s in sessions if s.current_state == "closed" and not s.is_active and s.message_count < 3])
            abandonment_rate = (abandoned / total * 100) if total > 0 else 0
            
            if abandonment_rate > AlertManager.THRESHOLDS[AlertType.HIGH_ABANDONMENT]:
                alerts.append(Alert(
                    type=AlertType.HIGH_ABANDONMENT,
                    severity=AlertSeverity.WARNING,
                    title="High Session Abandonment Rate",
                    message=f"{abandonment_rate:.1f}% of users are abandoning conversations",
                    metric_value=abandonment_rate,
                    threshold=AlertManager.THRESHOLDS[AlertType.HIGH_ABANDONMENT],
                    recommendation="Simplify initial greeting and improve UX",
                    timestamp=datetime.now()
                ))
            
            # Check response time
            durations = []
            for s in sessions:
                if s.created_at and s.last_activity:
                    duration = (s.last_activity - s.created_at).total_seconds()
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            if avg_duration > AlertManager.THRESHOLDS[AlertType.RESPONSE_TIME]:
                alerts.append(Alert(
                    type=AlertType.RESPONSE_TIME,
                    severity=AlertSeverity.WARNING,
                    title="Slow Response Time Detected",
                    message=f"Average session duration: {avg_duration:.0f} seconds",
                    metric_value=avg_duration,
                    threshold=AlertManager.THRESHOLDS[AlertType.RESPONSE_TIME],
                    recommendation="Optimize bot responses and KB search algorithm",
                    timestamp=datetime.now()
                ))
            
            return alerts
        
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return []
    
    @staticmethod
    def detect_quality_drop(db: Session, days: int = 7) -> Optional[Alert]:
        """Detect sudden drop in system quality"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if len(sessions) < 10:
                return None
            
            # Split into periods
            mid_point = len(sessions) // 2
            first_half = sessions[:mid_point]
            second_half = sessions[mid_point:]
            
            # Calculate metrics for each period
            def calc_quality(session_list):
                if not session_list:
                    return 100
                resolved = len([s for s in session_list if s.current_state == "resolved"])
                escalated = len([s for s in session_list if s.ticket_id])
                abandoned = len([s for s in session_list if s.current_state == "closed" and not s.is_active])
                
                success_rate = (resolved / len(session_list) * 100) if session_list else 0
                escalation_rate = (escalated / len(session_list) * 100) if session_list else 0
                
                return max(0, success_rate - (escalation_rate * 0.5))
            
            first_quality = calc_quality(first_half)
            second_quality = calc_quality(second_half)
            
            # Alert if quality dropped more than 10%
            quality_drop = first_quality - second_quality
            
            if quality_drop > 10:
                return Alert(
                    type=AlertType.QUALITY_DROP,
                    severity=AlertSeverity.CRITICAL,
                    title="Quality Drop Detected",
                    message=f"System quality decreased by {quality_drop:.1f}% in recent period",
                    metric_value=second_quality,
                    threshold=first_quality,
                    recommendation="Investigate recent changes and revert if necessary",
                    timestamp=datetime.now()
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting quality drop: {e}")
            return None
    
    @staticmethod
    def detect_peak_issues(db: Session) -> List[Alert]:
        """Detect if specific issues are becoming more frequent"""
        alerts = []
        
        try:
            cutoff_date = datetime.now() - timedelta(hours=24)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date,
                WhatsAppSession.problem_category.isnot(None)
            ).all()
            
            if not sessions:
                return alerts
            
            # Count issues
            issue_counts = {}
            for s in sessions:
                key = f"{s.problem_category}|{s.problem_severity}"
                issue_counts[key] = issue_counts.get(key, 0) + 1
            
            # Alert if any issue appears > 30% of the time
            total = len(sessions)
            for issue, count in issue_counts.items():
                percentage = (count / total * 100)
                if percentage > 30:
                    category, severity = issue.split("|")
                    alerts.append(Alert(
                        type=AlertType.PEAK_ISSUE,
                        severity=AlertSeverity.WARNING if percentage < 50 else AlertSeverity.CRITICAL,
                        title=f"Peak Issue: {category} ({severity})",
                        message=f"This issue represents {percentage:.1f}% of all recent problems",
                        metric_value=percentage,
                        threshold=30,
                        recommendation=f"Prioritize KB solutions for {category} issues",
                        timestamp=datetime.now()
                    ))
            
            return alerts
        
        except Exception as e:
            logger.error(f"Error detecting peak issues: {e}")
            return []
    
    @staticmethod
    def get_all_active_alerts(db: Session) -> List[Alert]:
        """Get all active alerts"""
        all_alerts = []
        
        # Health checks
        all_alerts.extend(AlertManager.check_system_health(db))
        
        # Quality drop detection
        quality_alert = AlertManager.detect_quality_drop(db)
        if quality_alert:
            all_alerts.append(quality_alert)
        
        # Peak issues
        all_alerts.extend(AlertManager.detect_peak_issues(db))
        
        # Sort by severity
        severity_order = {AlertSeverity.CRITICAL: 0, AlertSeverity.WARNING: 1, AlertSeverity.INFO: 2}
        all_alerts.sort(key=lambda x: severity_order.get(x.severity, 3))
        
        return all_alerts
    
    @staticmethod
    def format_alert_for_display(alert: Alert) -> Dict:
        """Format alert for API response"""
        return {
            "type": alert.type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "metric_value": round(alert.metric_value, 2),
            "threshold": round(alert.threshold, 2),
            "recommendation": alert.recommendation,
            "timestamp": alert.timestamp.isoformat(),
            "icon": _get_alert_icon(alert.severity),
            "color": _get_alert_color(alert.severity)
        }


def _get_alert_icon(severity: AlertSeverity) -> str:
    """Get icon for alert severity"""
    if severity == AlertSeverity.CRITICAL:
        return "🔴"
    elif severity == AlertSeverity.WARNING:
        return "🟠"
    else:
        return "🟡"


def _get_alert_color(severity: AlertSeverity) -> str:
    """Get color for alert severity"""
    if severity == AlertSeverity.CRITICAL:
        return "#ff5252"
    elif severity == AlertSeverity.WARNING:
        return "#ffb74d"
    else:
        return "#fdd835"
