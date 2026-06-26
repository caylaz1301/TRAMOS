"""
Analytics API Routes
Provides endpoints for dashboard data, ML analysis, and insights
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, and_, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database_models import WhatsAppSession, DatabaseManager
from app.services.data_science.ml_pattern_analyzer import MLPatternAnalyzer
from app.services.data_science.statistics_generator import StatisticsGenerator
from app.services.data_science.alert_manager import AlertManager
from app.services.data_science.predictive_analytics import PredictiveAnalytics
from app.services.data_science.report_generator import ReportGenerator
from app.services.data_science.anomaly_detector import AnomalyDetector
from app.services.data_science.visualization_generator import VisualizationGenerator
from app.services.data_science.benchmark_comparison import BenchmarkComparison

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Lazy-initialized DatabaseManager — avoids creating a connection pool at import time
_db_manager = None


def _get_db_manager() -> DatabaseManager:
    """Get or create DatabaseManager singleton (lazy initialization)"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(settings.DATABASE_URL)
    return _db_manager


def get_db() -> Session:
    """Get database session via dependency injection"""
    db = _get_db_manager().SessionLocal()
    try:
        yield db
    finally:
        db.close()

def apply_date_filter(query, model, start_date: str = None, end_date: str = None):
    """Helper to apply date filters to queries"""
    if start_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(model.created_at >= start)
        except ValueError as exc:
            logger.debug("Invalid start_date ignored: %s (%s)", start_date, exc)
    if end_date:
        try:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # If end date is at midnight, extend to end of day
            if end.hour == 0 and end.minute == 0:
                end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(model.created_at <= end)
        except ValueError as exc:
            logger.debug("Invalid end_date ignored: %s (%s)", end_date, exc)
    return query


# ============================================================================
# BASIC STATISTICS
# ============================================================================

@router.get("/stats/overview")
async def get_overview_stats(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get overview statistics"""
    try:
        # Base query for sessions
        base_query = db.query(WhatsAppSession)
        filtered_query = apply_date_filter(base_query, WhatsAppSession, start_date, end_date)
        total_sessions = filtered_query.count()
        
        # Total tickets created
        tickets_query = db.query(WhatsAppSession).filter(WhatsAppSession.ticket_id.isnot(None))
        tickets_filtered = apply_date_filter(tickets_query, WhatsAppSession, start_date, end_date)
        total_tickets = tickets_filtered.count()
        
        # Active sessions (last 5 minutes) - typically don't need date filter, but we'll apply if it's a historical range
        five_min_ago = datetime.now() - timedelta(minutes=5)
        active_query = db.query(WhatsAppSession).filter(
            WhatsAppSession.last_activity >= five_min_ago,
            WhatsAppSession.is_active == True
        )
        active_filtered = apply_date_filter(active_query, WhatsAppSession, start_date, end_date)
        active_sessions = active_filtered.count()
        
        # Total messages
        msg_query = db.query(func.sum(WhatsAppSession.message_count))
        msg_filtered = apply_date_filter(msg_query, WhatsAppSession, start_date, end_date)
        total_messages = msg_filtered.scalar() or 0
        
        # Success rate dashboard = sesi yang selesai oleh AI tanpa dibuatkan tiket.
        ai_resolved_query = db.query(WhatsAppSession).filter(
            WhatsAppSession.ticket_id.is_(None),
            WhatsAppSession.current_state.in_(["resolved", "closed"]),
        )
        ai_resolved_filtered = apply_date_filter(ai_resolved_query, WhatsAppSession, start_date, end_date)
        ai_resolved_sessions = ai_resolved_filtered.count()
        success_rate = (ai_resolved_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        return {
            "total_sessions": total_sessions,
            "total_tickets": total_tickets,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "ai_resolved_sessions": ai_resolved_sessions,
            "success_rate": round(success_rate, 2),
            "avg_messages_per_session": round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CATEGORY ANALYTICS
# ============================================================================

@router.get("/stats/categories")
async def get_category_stats(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get problem category distribution"""
    try:
        base_query = db.query(
            WhatsAppSession.problem_category,
            func.count(WhatsAppSession.id).label("count")
        ).filter(
            WhatsAppSession.problem_category.isnot(None)
        )
        filtered_query = apply_date_filter(base_query, WhatsAppSession, start_date, end_date)
        categories = filtered_query.group_by(
            WhatsAppSession.problem_category
        ).all()
        
        return {
            "categories": [
                {
                    "name": cat[0] or "Unknown",
                    "count": cat[1]
                }
                for cat in categories
            ]
        }
    except Exception as e:
        logger.error(f"Error getting category stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SEVERITY ANALYTICS
# ============================================================================

@router.get("/stats/severity")
async def get_severity_stats(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get problem severity distribution"""
    try:
        base_query = db.query(
            WhatsAppSession.problem_severity,
            func.count(WhatsAppSession.id).label("count")
        ).filter(
            WhatsAppSession.problem_severity.isnot(None)
        )
        filtered_query = apply_date_filter(base_query, WhatsAppSession, start_date, end_date)
        severities = filtered_query.group_by(
            WhatsAppSession.problem_severity
        ).all()
        
        return {
            "severities": [
                {
                    "name": sev[0] or "Unknown",
                    "count": sev[1]
                }
                for sev in severities
            ]
        }
    except Exception as e:
        logger.error(f"Error getting severity stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TIME ANALYTICS
# ============================================================================

@router.get("/stats/timeline")
async def get_timeline_stats(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get sessions created over time"""
    try:
        base_query = db.query(
            func.date_trunc('hour', WhatsAppSession.created_at).label("hour"),
            func.count(WhatsAppSession.id).label("count")
        )
        
        if start_date or end_date:
            filtered_query = apply_date_filter(base_query, WhatsAppSession, start_date, end_date)
        else:
            # Default to last 24 hours if no date provided
            filtered_query = base_query.filter(
                WhatsAppSession.created_at >= datetime.now() - timedelta(hours=24)
            )
            
        sessions_by_hour = filtered_query.group_by(
            func.date_trunc('hour', WhatsAppSession.created_at)
        ).order_by("hour").all()
        
        return {
            "timeline": [
                {
                    "timestamp": str(hour),
                    "sessions": count
                }
                for hour, count in sessions_by_hour
            ]
        }
    except Exception as e:
        logger.error(f"Error getting timeline stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SESSION QUALITY METRICS
# ============================================================================

@router.get("/stats/quality")
async def get_quality_metrics(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get session quality metrics"""
    try:
        base_query = db.query(WhatsAppSession)
        filtered_query = apply_date_filter(base_query, WhatsAppSession, start_date, end_date)
        sessions = filtered_query.all()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "completed_sessions": 0,
                "completion_rate": 0,
                "avg_messages": 0,
                "avg_duration_seconds": 0,
                "abandoned_sessions": 0
            }
        
        completed = len([s for s in sessions if s.current_state in {"closed", "resolved"}])
        abandoned = len([s for s in sessions if s.current_state != "closed" and s.is_active == False])
        
        total_messages = sum(s.message_count for s in sessions)
        avg_messages = total_messages / len(sessions) if sessions else 0
        
        # Average duration
        durations = []
        for s in sessions:
            if s.created_at and s.last_activity:
                duration = (s.last_activity - s.created_at).total_seconds()
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_sessions": len(sessions),
            "completed_sessions": completed,
            "completion_rate": round((completed / len(sessions) * 100), 2) if sessions else 0,
            "avg_messages": round(avg_messages, 2),
            "avg_duration_seconds": round(avg_duration, 2),
            "abandoned_sessions": abandoned
        }
    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RECENT SESSIONS
# ============================================================================

@router.get("/data/recent-sessions")
async def get_recent_sessions(limit: int = 10, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get recent sessions"""
    try:
        base_query = db.query(WhatsAppSession).order_by(WhatsAppSession.created_at.desc())
        filtered_query = apply_date_filter(base_query, WhatsAppSession, start_date, end_date)
        sessions = filtered_query.limit(limit).all()
        
        return {
            "sessions": [
                {
                    "id": s.session_id,
                    "phone": s.phone_number,
                    "name": s.driver_name,
                    "problem": s.problem_description[:50] if s.problem_description else "N/A",
                    "category": s.problem_category,
                    "severity": s.problem_severity,
                    "ticket_id": s.ticket_id,
                    "messages": s.message_count,
                    "state": s.current_state,
                    # Convert to UTC ISO format - always include Z to indicate UTC
                    "created_at": (s.created_at.isoformat() + "Z") if s.created_at else None
                }
                for s in sessions
            ]
        }
    except Exception as e:
        logger.error(f"Error getting recent sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TICKET STATISTICS
# ============================================================================

@router.get("/stats/tickets")
async def get_ticket_stats(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get ticket statistics"""
    try:
        base_tickets = db.query(WhatsAppSession).filter(WhatsAppSession.ticket_id.isnot(None))
        total_tickets = apply_date_filter(base_tickets, WhatsAppSession, start_date, end_date).count()
        
        base_cats = db.query(
            WhatsAppSession.problem_category,
            func.count(WhatsAppSession.id).label("count")
        ).filter(
            WhatsAppSession.ticket_id.isnot(None),
            WhatsAppSession.problem_category.isnot(None)
        )
        cat_filtered = apply_date_filter(base_cats, WhatsAppSession, start_date, end_date)
        tickets_by_category = cat_filtered.group_by(
            WhatsAppSession.problem_category
        ).all()
        
        return {
            "total_tickets": total_tickets,
            "by_category": [
                {
                    "category": cat[0] or "Unknown",
                    "count": cat[1]
                }
                for cat in tickets_by_category
            ]
        }
    except Exception as e:
        logger.error(f"Error getting ticket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMPREHENSIVE DASHBOARD DATA
# ============================================================================

@router.get("/dashboard")
async def get_dashboard_data(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get all dashboard data in one call"""
    try:
        overview = await get_overview_stats(start_date, end_date, db)
        categories = await get_category_stats(start_date, end_date, db)
        severity = await get_severity_stats(start_date, end_date, db)
        quality = await get_quality_metrics(start_date, end_date, db)
        tickets = await get_ticket_stats(start_date, end_date, db)
        recent = await get_recent_sessions(10, start_date, end_date, db)
        
        return {
            "overview": overview,
            "categories": categories,
            "severity": severity,
            "quality": quality,
            "tickets": tickets,
            "recent_sessions": recent
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ML PATTERN ANALYSIS
# ============================================================================

@router.get("/analysis/patterns")
async def get_pattern_analysis(days: int = 7, db: Session = Depends(get_db)):
    """Get ML-based problem pattern analysis"""
    try:
        problems = MLPatternAnalyzer.analyze_problem_patterns(db, days)
        return problems
    except Exception as e:
        logger.error(f"Error in pattern analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/hotspots")
async def get_hotspot_analysis(days: int = 7, db: Session = Depends(get_db)):
    """Identify critical issue hotspots"""
    try:
        hotspots = MLPatternAnalyzer.identify_hotspots(db, days)
        return hotspots
    except Exception as e:
        logger.error(f"Error in hotspot analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/temporal")
async def get_temporal_analysis(days: int = 7, db: Session = Depends(get_db)):
    """Analyze when problems occur (temporal patterns)"""
    try:
        temporal = MLPatternAnalyzer.analyze_temporal_patterns(db, days)
        return temporal
    except Exception as e:
        logger.error(f"Error in temporal analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/resolution")
async def get_resolution_analysis(days: int = 7, db: Session = Depends(get_db)):
    """Analyze how problems are being resolved"""
    try:
        resolution = MLPatternAnalyzer.analyze_resolution_patterns(db, days)
        return resolution
    except Exception as e:
        logger.error(f"Error in resolution analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/kpi-trends")
async def get_kpi_trends(days: int = 7, db: Session = Depends(get_db)):
    """Get KPI trends and metrics"""
    try:
        kpis = MLPatternAnalyzer.calculate_kpi_trends(db, days)
        return kpis
    except Exception as e:
        logger.error(f"Error in KPI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTELLIGENCE & INSIGHTS
# ============================================================================

@router.get("/insights/executive-summary")
async def get_executive_summary(days: int = 7, db: Session = Depends(get_db)):
    """Get executive summary for management"""
    try:
        summary = StatisticsGenerator.generate_executive_summary(db, days)
        return summary
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/trends")
async def get_trend_insights(days: int = 30, db: Session = Depends(get_db)):
    """Get trend analysis and insights"""
    try:
        trends = StatisticsGenerator.generate_trend_analysis(db, days)
        return trends
    except Exception as e:
        logger.error(f"Error generating trend analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/performance")
async def get_performance_report(db: Session = Depends(get_db)):
    """Get comprehensive performance report with scoring"""
    try:
        report = StatisticsGenerator.generate_performance_report(db)
        return report
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/recommendations")
async def get_ai_recommendations(days: int = 7, db: Session = Depends(get_db)):
    """Get AI-powered insights and recommendations"""
    try:
        insights = StatisticsGenerator.generate_insights_report(db, days)
        return insights
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ALERTS & MONITORING
# ============================================================================

@router.get("/alerts/active")
async def get_active_alerts(db: Session = Depends(get_db)):
    """Get all active system alerts"""
    try:
        alerts = AlertManager.get_all_active_alerts(db)
        return {
            "alerts": [AlertManager.format_alert_for_display(alert) for alert in alerts],
            "total_alerts": len(alerts),
            "critical_count": len([a for a in alerts if a.severity.value == "critical"]),
            "warning_count": len([a for a in alerts if a.severity.value == "warning"]),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/health-check")
async def health_check(db: Session = Depends(get_db)):
    """Quick health check endpoint with component status"""
    try:
        from app.utils.kb_troubleshooting import KB_TROUBLESHOOTING

        alerts = AlertManager.check_system_health(db)
        has_critical = any(a.severity.value == "critical" for a in alerts)

        # ── Component health probes ──
        # Database
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "error"

        # Gemini readiness cukup dicek dari konfigurasi agar endpoint monitoring tetap cepat.
        try:
            from app.utils.ai_logic import ai_engine
            ai_status = "operational" if getattr(ai_engine, "gemini_available", False) else "not_configured"
        except Exception as exc:
            logger.debug("AI health probe failed: %s", str(exc)[:120])
            ai_status = "not_configured"

        # WhatsApp API dan osTicket dicek dari settings, tanpa membuka secret ke response.
        wa_status = "configured" if settings.WHATSAPP_API_TOKEN else "not_configured"

        ost_status = "configured" if settings.OSTICKET_API_KEY else "not_configured"

        # Knowledge Base
        kb_status = f"loaded_{len(KB_TROUBLESHOOTING)}_categories" if KB_TROUBLESHOOTING else "error"
        if settings.KB_RAG_ENABLED:
            try:
                from app.services.knowledge_base import KnowledgeBaseRetrievalService
                rag_health = KnowledgeBaseRetrievalService(db).health()
                kb_status = (
                    f"rag_{rag_health['documents']}_docs_"
                    f"{rag_health['chunks']}_chunks_pgvector_{rag_health['pgvector_enabled']}"
                )
            except Exception as exc:
                logger.debug("RAG health probe failed: %s", str(exc)[:120])

        return {
            "status": "unhealthy" if has_critical else "healthy",
            "alerts_count": len(alerts),
            "critical_alerts": len([a for a in alerts if a.severity.value == "critical"]),
            "components": {
                "database": db_status,
                "ai_engine": ai_status,
                "whatsapp_api": wa_status,
                "osticket": ost_status,
                "knowledge_base": kb_status,
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PREDICTIVE ANALYTICS
# ============================================================================

@router.get("/predict/volume")
async def predict_volume(days: int = 7, db: Session = Depends(get_db)):
    """Forecast issue volume for next N days"""
    try:
        forecast = PredictiveAnalytics.forecast_issue_volume(db, days)
        return forecast
    except Exception as e:
        logger.error(f"Error predicting volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/escalation-risk")
async def predict_escalation(db: Session = Depends(get_db)):
    """Predict escalation risk"""
    try:
        risk = PredictiveAnalytics.predict_escalation_risk(db)
        return risk
    except Exception as e:
        logger.error(f"Error predicting escalation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/staffing")
async def predict_staffing(db: Session = Depends(get_db)):
    """Get optimal staffing recommendations"""
    try:
        staffing = PredictiveAnalytics.predict_optimal_staffing(db)
        return staffing
    except Exception as e:
        logger.error(f"Error predicting staffing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/kb-gaps")
async def predict_kb_gaps(db: Session = Depends(get_db)):
    """Identify KB coverage gaps"""
    try:
        gaps = PredictiveAnalytics.predict_kb_coverage_gaps(db)
        return gaps
    except Exception as e:
        logger.error(f"Error predicting KB gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/all")
async def get_all_predictions(db: Session = Depends(get_db)):
    """Get all predictions"""
    try:
        predictions = PredictiveAnalytics.get_all_predictions(db)
        return predictions
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REPORTS & EXPORTS
# ============================================================================

@router.get("/reports/daily")
async def get_daily_report(db: Session = Depends(get_db)):
    """Get daily summary report"""
    try:
        report = ReportGenerator.generate_daily_report(db)
        return report
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/weekly")
async def get_weekly_report(db: Session = Depends(get_db)):
    """Get weekly comprehensive report"""
    try:
        report = ReportGenerator.generate_weekly_report(db)
        return report
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/monthly")
async def get_monthly_report(db: Session = Depends(get_db)):
    """Get monthly report with trends and predictions"""
    try:
        report = ReportGenerator.generate_monthly_report(db)
        return report
    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/custom")
async def get_custom_report(start_date: str, end_date: str, db: Session = Depends(get_db)):
    """Get custom date-range report"""
    try:
        report = ReportGenerator.generate_custom_report(db, start_date, end_date)
        return report
    except Exception as e:
        logger.error(f"Error generating custom report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json")
async def export_json(report_type: str = "daily", db: Session = Depends(get_db)):
    """Export report as JSON"""
    try:
        if report_type == "daily":
            report = ReportGenerator.generate_daily_report(db)
        elif report_type == "weekly":
            report = ReportGenerator.generate_weekly_report(db)
        elif report_type == "monthly":
            report = ReportGenerator.generate_monthly_report(db)
        else:
            report = ReportGenerator.generate_daily_report(db)
        
        json_str = ReportGenerator.export_report_json(report)
        return {"data": json_str, "type": "application/json"}
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/csv")
async def export_csv(days: int = 7, db: Session = Depends(get_db)):
    """Export sessions data as CSV"""
    try:
        csv_data = ReportGenerator.export_report_csv(db, days)
        return {"data": csv_data, "type": "text/csv"}
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/html")
async def export_html(report_type: str = "daily", db: Session = Depends(get_db)):
    """Export report as HTML"""
    try:
        if report_type == "daily":
            report = ReportGenerator.generate_daily_report(db)
            title = "Daily Report"
        elif report_type == "weekly":
            report = ReportGenerator.generate_weekly_report(db)
            title = "Weekly Report"
        elif report_type == "monthly":
            report = ReportGenerator.generate_monthly_report(db)
            title = "Monthly Report"
        else:
            report = ReportGenerator.generate_daily_report(db)
            title = "Report"
        
        html_str = ReportGenerator.export_report_html(report, title)
        return {"data": html_str, "type": "text/html"}
    except Exception as e:
        logger.error(f"Error exporting HTML: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANOMALY DETECTION ENDPOINTS
# ============================================================================

@router.get("/anomalies/detect")
async def detect_anomalies(db: Session = Depends(get_db)):
    """Detect all system anomalies"""
    try:
        anomalies = AnomalyDetector.detect_all_anomalies(db)
        return anomalies
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/critical")
async def get_critical_anomalies(db: Session = Depends(get_db)):
    """Get only critical anomalies"""
    try:
        anomalies = AnomalyDetector.detect_all_anomalies(db)
        critical = [a for a in anomalies.get("anomalies", []) if a.get("severity") == "critical"]
        return {
            "critical_count": len(critical),
            "anomalies": critical,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting critical anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VISUALIZATION ENDPOINTS
# ============================================================================

@router.get("/visualizations/all")
async def get_all_visualizations(db: Session = Depends(get_db)):
    """Get all visualization data"""
    try:
        visualizations = VisualizationGenerator.generate_all_visualizations(db)
        return visualizations
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/trends")
async def get_trend_chart(days: int = 30, db: Session = Depends(get_db)):
    """Get trend chart data"""
    try:
        trend = VisualizationGenerator.generate_trend_chart(db, days)
        return trend
    except Exception as e:
        logger.error(f"Error generating trend chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/categories")
async def get_category_distribution(db: Session = Depends(get_db)):
    """Get category distribution pie chart"""
    try:
        chart = VisualizationGenerator.generate_category_distribution(db)
        return chart
    except Exception as e:
        logger.error(f"Error generating category distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/severity")
async def get_severity_distribution(db: Session = Depends(get_db)):
    """Get severity distribution bar chart"""
    try:
        chart = VisualizationGenerator.generate_severity_distribution(db)
        return chart
    except Exception as e:
        logger.error(f"Error generating severity distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/heatmap")
async def get_temporal_heatmap(db: Session = Depends(get_db)):
    """Get hourly activity heatmap"""
    try:
        heatmap = VisualizationGenerator.generate_temporal_heatmap(db)
        return heatmap
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/funnel")
async def get_resolution_funnel(db: Session = Depends(get_db)):
    """Get resolution funnel chart"""
    try:
        funnel = VisualizationGenerator.generate_resolution_funnel(db)
        return funnel
    except Exception as e:
        logger.error(f"Error generating funnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/hourly")
async def get_hourly_activity(db: Session = Depends(get_db)):
    """Get hourly activity pattern"""
    try:
        hourly = VisualizationGenerator.generate_hourly_activity(db)
        return hourly
    except Exception as e:
        logger.error(f"Error generating hourly activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/quality")
async def get_quality_trend(db: Session = Depends(get_db)):
    """Get quality score trend"""
    try:
        quality = VisualizationGenerator.generate_quality_trend(db)
        return quality
    except Exception as e:
        logger.error(f"Error generating quality trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BENCHMARK COMPARISON ENDPOINTS
# ============================================================================

@router.get("/benchmarks/report")
async def get_benchmark_report(db: Session = Depends(get_db)):
    """Get comprehensive benchmark comparison report"""
    try:
        report = BenchmarkComparison.generate_benchmark_report(db)
        return report
    except Exception as e:
        logger.error(f"Error generating benchmark report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmarks/industry")
async def get_industry_comparison(db: Session = Depends(get_db)):
    """Get current vs industry standard comparison"""
    try:
        current_metrics = BenchmarkComparison._calculate_current_metrics(db)
        industry_comparison = BenchmarkComparison._compare_with_industry(current_metrics)
        return {
            "current_metrics": current_metrics,
            "comparison": industry_comparison,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting industry comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmarks/recommendations")
async def get_benchmark_recommendations(db: Session = Depends(get_db)):
    """Get actionable recommendations from benchmark analysis"""
    try:
        current_metrics = BenchmarkComparison._calculate_current_metrics(db)
        historical_metrics = BenchmarkComparison._calculate_historical_metrics(db)
        industry_comparison = BenchmarkComparison._compare_with_industry(current_metrics)
        
        recommendations = BenchmarkComparison._generate_recommendations(
            current_metrics,
            historical_metrics,
            industry_comparison
        )
        
        return {
            "total_recommendations": len(recommendations),
            "critical": len([r for r in recommendations if r["priority"] == "CRITICAL"]),
            "high": len([r for r in recommendations if r["priority"] == "HIGH"]),
            "medium": len([r for r in recommendations if r["priority"] == "MEDIUM"]),
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmarks/score")
async def get_overall_score(db: Session = Depends(get_db)):
    """Get overall system performance score and grade"""
    try:
        current_metrics = BenchmarkComparison._calculate_current_metrics(db)
        industry_comparison = BenchmarkComparison._compare_with_industry(current_metrics)
        score = BenchmarkComparison._calculate_overall_score(industry_comparison)
        
        return {
            "score": score,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ML INSIGHTS - Actionable analytics for dashboard
# ============================================================================

@router.get("/ml-insights")
async def get_ml_insights(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get ML-driven insights: top escalations, peak hours, weekly trend, KB rate"""
    try:
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)
        
        # --- Top escalated categories ---
        base_escalated = db.query(
            WhatsAppSession.problem_category,
            func.count(WhatsAppSession.id).label("count")
        ).filter(
            WhatsAppSession.ticket_id.isnot(None),
            WhatsAppSession.problem_category.isnot(None)
        )
        escalated_filtered = apply_date_filter(base_escalated, WhatsAppSession, start_date, end_date)
        escalated_categories = escalated_filtered.group_by(
            WhatsAppSession.problem_category
        ).order_by(func.count(WhatsAppSession.id).desc()).limit(5).all()
        
        top_escalated = [
            {"category": cat or "Unknown", "count": cnt}
            for cat, cnt in escalated_categories
        ]
        
        # --- Peak hours analysis ---
        base_peak = db.query(
            func.extract('hour', WhatsAppSession.created_at).label("hour"),
            func.count(WhatsAppSession.id).label("count")
        )
        if start_date or end_date:
            peak_filtered = apply_date_filter(base_peak, WhatsAppSession, start_date, end_date)
        else:
            peak_filtered = base_peak.filter(WhatsAppSession.created_at >= seven_days_ago)
            
        peak_hours_raw = peak_filtered.group_by(
            func.extract('hour', WhatsAppSession.created_at)
        ).order_by(func.count(WhatsAppSession.id).desc()).all()
        
        peak_hours = [
            {"hour": int(hour), "count": cnt}
            for hour, cnt in peak_hours_raw
        ]
        
        # --- Weekly trend (this week vs last week) ---
        this_week_count = db.query(func.count(WhatsAppSession.id)).filter(
            WhatsAppSession.created_at >= seven_days_ago
        ).scalar() or 0
        
        last_week_count = db.query(func.count(WhatsAppSession.id)).filter(
            and_(
                WhatsAppSession.created_at >= fourteen_days_ago,
                WhatsAppSession.created_at < seven_days_ago
            )
        ).scalar() or 0
        
        if last_week_count > 0:
            trend_pct = round(((this_week_count - last_week_count) / last_week_count) * 100, 1)
        else:
            trend_pct = 100.0 if this_week_count > 0 else 0.0
        
        # --- KB effectiveness ---
        base_sessions = db.query(func.count(WhatsAppSession.id))
        total_sessions = apply_date_filter(base_sessions, WhatsAppSession, start_date, end_date).scalar() or 0
        
        base_tickets = db.query(func.count(WhatsAppSession.id)).filter(WhatsAppSession.ticket_id.isnot(None))
        tickets_created = apply_date_filter(base_tickets, WhatsAppSession, start_date, end_date).scalar() or 0
        
        resolved_by_ai = total_sessions - tickets_created
        kb_rate = round((resolved_by_ai / total_sessions * 100), 1) if total_sessions > 0 else 0
        
        # --- Generate recommendations ---
        recommendations = []
        
        if top_escalated:
            top_cat = top_escalated[0]["category"]
            recommendations.append({
                "type": "kb_gap",
                "priority": "high",
                "message": f"Kategori '{top_cat}' paling sering dieskalasi. Pertimbangkan untuk menambah solusi KB yang lebih detail.",
            })
        
        if peak_hours:
            peak_h = peak_hours[0]["hour"]
            recommendations.append({
                "type": "staffing",
                "priority": "medium",
                "message": f"Jam sibuk: {peak_h}:00. Pastikan tim support standby di jam-jam tersebut.",
            })
        
        if trend_pct > 20:
            recommendations.append({
                "type": "volume_alert",
                "priority": "high",
                "message": f"Volume laporan naik {trend_pct}% dibanding minggu lalu. Perlu evaluasi.",
            })
        elif trend_pct < -10:
            recommendations.append({
                "type": "improvement",
                "priority": "low",
                "message": f"Volume laporan turun {abs(trend_pct)}%. Sistem semakin stabil.",
            })
        
        if kb_rate < 50:
            recommendations.append({
                "type": "kb_improvement",
                "priority": "high",
                "message": f"Hanya {kb_rate}% masalah terselesaikan tanpa eskalasi. Knowledge base perlu diperkaya.",
            })
        
        return {
            "top_escalated": top_escalated,
            "peak_hours": peak_hours,
            "weekly_trend": {
                "this_week": this_week_count,
                "last_week": last_week_count,
                "change_percent": trend_pct,
                "direction": "up" if trend_pct > 0 else "down" if trend_pct < 0 else "stable"
            },
            "kb_effectiveness": {
                "total_sessions": total_sessions,
                "resolved_by_ai": resolved_by_ai,
                "escalated": tickets_created,
                "ai_resolution_rate": kb_rate
            },
            "recommendations": recommendations,
            "generated_at": now.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting ML insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LIVE SESSIONS - Real-time active sessions
# ============================================================================

@router.get("/live-sessions")
async def get_live_sessions(db: Session = Depends(get_db)):
    """Get real-time count of active sessions (last 5 minutes)"""
    try:
        five_min_ago = datetime.now() - timedelta(minutes=5)
        active_sessions = db.query(WhatsAppSession).filter(
            WhatsAppSession.last_activity >= five_min_ago,
            WhatsAppSession.is_active == True
        ).all()

        return {
            "active_count": len(active_sessions),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "phone": s.phone_number,
                    "name": s.driver_name,
                    "state": s.current_state,
                    "created_at": (s.created_at.isoformat() + "Z") if s.created_at else None,
                    "minutes_ago": int((datetime.now() - s.last_activity).total_seconds() / 60) if s.last_activity else 0
                }
                for s in active_sessions
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting live sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CATEGORY FLOW - For Sankey diagram
# ============================================================================

@router.get("/category-flow")
async def get_category_flow(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """Get category to outcome flow for Sankey diagram"""
    try:
        base_query = db.query(WhatsAppSession).filter(
            WhatsAppSession.problem_category.isnot(None)
        )
        filtered_query = apply_date_filter(base_query, WhatsAppSession, start_date, end_date)
        sessions = filtered_query.all()

        # Build flow data: category -> outcome
        flow_data = {}
        for s in sessions:
            category = s.problem_category or "Unknown"

            # Determine outcome
            if s.ticket_id:
                outcome = "Dieskalasi"
            elif s.current_state in ["resolved", "closed"]:
                outcome = "Selesai AI"
            else:
                outcome = "Lainnya"

            key = (category, outcome)
            flow_data[key] = flow_data.get(key, 0) + 1

        # Convert to sankey format
        nodes = []
        categories = set()
        outcomes = set()
        links = []

        for (cat, outcome), count in flow_data.items():
            categories.add(cat)
            outcomes.add(outcome)

        # Create nodes
        for cat in sorted(categories):
            nodes.append({"name": cat})
        for outcome in sorted(outcomes):
            nodes.append({"name": outcome})

        # Create links
        cat_index = {cat: i for i, cat in enumerate(sorted(categories))}
        outcome_index = {out: i + len(categories) for i, out in enumerate(sorted(outcomes))}

        for (cat, outcome), count in flow_data.items():
            links.append({
                "source": cat_index[cat],
                "target": outcome_index[outcome],
                "value": count
            })

        return {
            "nodes": nodes,
            "links": links,
            "summary": {
                "total_sessions": len(sessions),
                "resolved_by_ai": sum(1 for s in sessions if not s.ticket_id and s.current_state in ["resolved", "closed"]),
                "escalated": sum(1 for s in sessions if s.ticket_id)
            }
        }
    except Exception as e:
        logger.error(f"Error getting category flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ACTIVITY LOG - Recent events timeline
# ============================================================================

@router.get("/activity-log")
async def get_activity_log(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent activity events for dashboard timeline"""
    try:
        recent = db.query(WhatsAppSession).order_by(
            WhatsAppSession.last_activity.desc()
        ).limit(limit).all()
        
        events = []
        for s in recent:
            # Determine event type
            if s.ticket_id:
                event_type = "ticket_created"
                event_icon = "🎫"
                event_desc = f"Tiket #{s.ticket_id} dibuat untuk {s.driver_name or 'user'} ({s.problem_category or 'General'})"
            elif s.current_state == "closed":
                event_type = "session_resolved"
                event_icon = "✅"
                event_desc = f"Masalah {s.driver_name or 'user'} terselesaikan ({s.problem_category or 'N/A'})"
            else:
                event_type = "session_active"
                event_icon = "💬"
                event_desc = f"Sesi aktif dari {s.driver_name or s.phone_number} ({s.message_count} pesan)"
            
            events.append({
                "type": event_type,
                "icon": event_icon,
                "description": event_desc,
                # Convert to UTC ISO format - always include Z to indicate UTC
                "timestamp": (s.last_activity.isoformat() + "Z") if s.last_activity else ((s.created_at.isoformat() + "Z") if s.created_at else None),
                "phone": s.phone_number,
                "category": s.problem_category,
                "severity": s.problem_severity,
            })
        
        return {"events": events}
    except Exception as e:
        logger.error(f"Error getting activity log: {e}")
        raise HTTPException(status_code=500, detail=str(e))
