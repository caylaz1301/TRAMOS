"""
Report Generator
Generates comprehensive reports for export and management review
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session

from app.database_models import WhatsAppSession
from app.services.data_science.statistics_generator import StatisticsGenerator
from app.services.data_science.ml_pattern_analyzer import MLPatternAnalyzer
from app.services.data_science.predictive_analytics import PredictiveAnalytics

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates various types of reports"""
    
    @staticmethod
    def generate_daily_report(db: Session) -> Dict:
        """Generate daily summary report"""
        try:
            cutoff_date = datetime.now() - timedelta(days=1)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "message": "No sessions today"
                }
            
            total = len(sessions)
            resolved = len([s for s in sessions if s.current_state == "resolved"])
            escalated = len([s for s in sessions if s.ticket_id])
            abandoned = len([s for s in sessions if s.current_state == "closed" and not s.is_active and s.message_count < 3])
            
            total_messages = sum(s.message_count for s in sessions)
            
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_sessions": total,
                "resolved": {
                    "count": resolved,
                    "percentage": round(resolved / total * 100, 1) if total > 0 else 0
                },
                "escalated": {
                    "count": escalated,
                    "percentage": round(escalated / total * 100, 1) if total > 0 else 0
                },
                "abandoned": {
                    "count": abandoned,
                    "percentage": round(abandoned / total * 100, 1) if total > 0 else 0
                },
                "total_messages": total_messages,
                "avg_messages_per_session": round(total_messages / total, 2) if total > 0 else 0,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_weekly_report(db: Session) -> Dict:
        """Generate weekly comprehensive report"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"message": "No sessions this week"}
            
            # Get all analytics
            patterns = MLPatternAnalyzer.analyze_problem_patterns(db, 7)
            resolution = MLPatternAnalyzer.analyze_resolution_patterns(db, 7)
            hotspots = MLPatternAnalyzer.identify_hotspots(db, 7)
            
            # Summary stats
            total = len(sessions)
            avg_messages = sum(s.message_count for s in sessions) / total if total > 0 else 0
            
            durations = []
            for s in sessions:
                if s.created_at and s.last_activity:
                    duration = (s.last_activity - s.created_at).total_seconds()
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                "report_type": "weekly",
                "period": f"{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
                "summary": {
                    "total_sessions": total,
                    "avg_messages_per_session": round(avg_messages, 2),
                    "avg_resolution_time_minutes": round(avg_duration / 60, 2),
                },
                "performance": {
                    "kb_effectiveness": resolution.get("kb_effectiveness", 0),
                    "escalation_rate": resolution.get("escalated_to_ticket", {}).get("percentage", 0),
                    "abandonment_rate": resolution.get("abandoned", {}).get("percentage", 0)
                },
                "top_issues": patterns.get("top_issues", [])[:5],
                "critical_hotspots": hotspots.get("critical_hotspots", [])[:3],
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_monthly_report(db: Session) -> Dict:
        """Generate full monthly report with trends and predictions"""
        try:
            # Historical data
            cutoff_date = datetime.now() - timedelta(days=30)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            if not sessions:
                return {"message": "No sessions this month"}
            
            # Get all insights
            summary = StatisticsGenerator.generate_executive_summary(db, 30)
            trends = StatisticsGenerator.generate_trend_analysis(db, 30)
            performance = StatisticsGenerator.generate_performance_report(db)
            
            # Get predictions
            predictions = PredictiveAnalytics.get_all_predictions(db)
            
            return {
                "report_type": "monthly",
                "period": f"{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
                "executive_summary": summary,
                "trends": trends,
                "performance": performance,
                "predictions": predictions,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_custom_report(db: Session, start_date: str, end_date: str) -> Dict:
        """Generate custom date-range report"""
        try:
            from datetime import datetime as dt
            
            start = dt.fromisoformat(start_date)
            end = dt.fromisoformat(end_date)
            
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= start,
                WhatsAppSession.created_at <= end
            ).all()
            
            if not sessions:
                return {"message": f"No sessions between {start_date} and {end_date}"}
            
            days_diff = (end - start).days
            
            # Analytics for this period
            patterns = MLPatternAnalyzer.analyze_problem_patterns(db, days_diff)
            resolution = MLPatternAnalyzer.analyze_resolution_patterns(db, days_diff)
            
            return {
                "report_type": "custom",
                "period": f"{start_date} to {end_date}",
                "duration_days": days_diff,
                "total_sessions": len(sessions),
                "daily_average": round(len(sessions) / max(1, days_diff), 2),
                "patterns": patterns,
                "resolution": resolution,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating custom report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def export_report_json(report: Dict) -> str:
        """Export report as JSON"""
        return json.dumps(report, indent=2, default=str)
    
    @staticmethod
    def export_report_csv(db: Session, days: int = 7) -> str:
        """Export sessions data as CSV"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff_date
            ).all()
            
            # CSV header
            csv_rows = [
                "Session_ID,Phone_Number,Driver_Name,Problem_Category,Severity,State,Messages,Ticket_ID,Created_At,Duration_Seconds"
            ]
            
            # CSV rows
            for s in sessions:
                duration = 0
                if s.created_at and s.last_activity:
                    duration = (s.last_activity - s.created_at).total_seconds()
                
                row = f'"{s.session_id}","{s.phone_number}","{s.driver_name or ""}","{s.problem_category or ""}","{s.problem_severity or ""}","{s.current_state}",{s.message_count},"{s.ticket_id or ""}","{s.created_at}",{duration}'
                csv_rows.append(row)
            
            return "\n".join(csv_rows)
        
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return f"Error: {str(e)}"
    
    @staticmethod
    def export_report_html(report: Dict, title: str = "TRAMOS Report") -> str:
        """Export report as HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #764ba2; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 15px; padding: 15px; background: #f9f9f9; border-radius: 4px; border-left: 4px solid #667eea; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .metric-label {{ color: #666; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #667eea; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f9f9f9; }}
        .footer {{ text-align: center; color: #999; margin-top: 40px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div id="content">
            {_dict_to_html(report)}
        </div>
        
        <div class="footer">
            <p>TRAMOS WhatsApp AI Support System © 2026</p>
        </div>
    </div>
</body>
</html>
"""
        return html


def _dict_to_html(d: Dict, level: int = 2) -> str:
    """Convert dictionary to HTML representation"""
    html = []
    
    for key, value in d.items():
        key_display = key.replace("_", " ").title()
        
        if isinstance(value, dict):
            html.append(f"<h{level}>{key_display}</h{level}>")
            html.append(_dict_to_html(value, level + 1))
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                html.append(f"<h{level}>{key_display}</h{level}>")
                html.append("<table>")
                
                # Headers
                headers = set()
                for item in value:
                    headers.update(item.keys())
                
                html.append("<tr>" + "".join(f"<th>{h.replace('_', ' ').title()}</th>" for h in sorted(headers)) + "</tr>")
                
                # Rows
                for item in value:
                    html.append("<tr>" + "".join(f"<td>{item.get(h, '')}</td>" for h in sorted(headers)) + "</tr>")
                
                html.append("</table>")
            else:
                html.append(f"<div class='metric'><div class='metric-label'>{key_display}</div><div class='metric-value'>{', '.join(map(str, value))}</div></div>")
        else:
            html.append(f"<div class='metric'><div class='metric-label'>{key_display}</div><div class='metric-value'>{value}</div></div>")
    
    return "".join(html)
