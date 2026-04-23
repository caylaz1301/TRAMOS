"""
Analytics API Routes
Provides endpoints for dashboard data, ML analysis, and insights
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, and_
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


# ============================================================================
# BASIC STATISTICS
# ============================================================================

@router.get("/stats/overview")
async def get_overview_stats(db: Session = Depends(get_db)):
    """Get overview statistics"""
    try:
        total_sessions = db.query(WhatsAppSession).count()
        
        # Total tickets created
        total_tickets = db.query(WhatsAppSession).filter(
            WhatsAppSession.ticket_id.isnot(None)
        ).count()
        
        # Active sessions (last 5 minutes)
        five_min_ago = datetime.now() - timedelta(minutes=5)
        active_sessions = db.query(WhatsAppSession).filter(
            WhatsAppSession.last_activity >= five_min_ago,
            WhatsAppSession.is_active == True
        ).count()
        
        # Total messages
        total_messages = db.query(func.sum(WhatsAppSession.message_count)).scalar() or 0
        
        # Success rate
        success_rate = (total_tickets / total_sessions * 100) if total_sessions > 0 else 0
        
        return {
            "total_sessions": total_sessions,
            "total_tickets": total_tickets,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
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
async def get_category_stats(db: Session = Depends(get_db)):
    """Get problem category distribution"""
    try:
        categories = db.query(
            WhatsAppSession.problem_category,
            func.count(WhatsAppSession.id).label("count")
        ).filter(
            WhatsAppSession.problem_category.isnot(None)
        ).group_by(
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
async def get_severity_stats(db: Session = Depends(get_db)):
    """Get problem severity distribution"""
    try:
        severities = db.query(
            WhatsAppSession.problem_severity,
            func.count(WhatsAppSession.id).label("count")
        ).filter(
            WhatsAppSession.problem_severity.isnot(None)
        ).group_by(
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
async def get_timeline_stats(db: Session = Depends(get_db)):
    """Get sessions created over time (last 24 hours by hour)"""
    try:
        # Get sessions from last 24 hours grouped by hour
        sessions_by_hour = db.query(
            func.date_trunc('hour', WhatsAppSession.created_at).label("hour"),
            func.count(WhatsAppSession.id).label("count")
        ).filter(
            WhatsAppSession.created_at >= datetime.now() - timedelta(hours=24)
        ).group_by(
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
async def get_quality_metrics(db: Session = Depends(get_db)):
    """Get session quality metrics"""
    try:
        sessions = db.query(WhatsAppSession).all()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "completed_sessions": 0,
                "completion_rate": 0,
                "avg_messages": 0,
                "avg_duration_seconds": 0,
                "abandoned_sessions": 0
            }
        
        completed = len([s for s in sessions if s.current_state == "closed"])
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
async def get_recent_sessions(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent sessions"""
    try:
        sessions = db.query(WhatsAppSession).order_by(
            WhatsAppSession.created_at.desc()
        ).limit(limit).all()
        
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
                    "created_at": s.created_at.isoformat() if s.created_at else None
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
async def get_ticket_stats(db: Session = Depends(get_db)):
    """Get ticket statistics"""
    try:
        total_tickets = db.query(WhatsAppSession).filter(
            WhatsAppSession.ticket_id.isnot(None)
        ).count()
        
        tickets_by_category = db.query(
            WhatsAppSession.problem_category,
            func.count(WhatsAppSession.id).label("count")
        ).filter(
            WhatsAppSession.ticket_id.isnot(None),
            WhatsAppSession.problem_category.isnot(None)
        ).group_by(
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
async def get_dashboard_data(db: Session = Depends(get_db)):
    """Get all dashboard data in one call"""
    try:
        overview = await get_overview_stats(db)
        categories = await get_category_stats(db)
        severity = await get_severity_stats(db)
        quality = await get_quality_metrics(db)
        tickets = await get_ticket_stats(db)
        recent = await get_recent_sessions(10, db)
        
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
    """Quick health check endpoint"""
    try:
        alerts = AlertManager.check_system_health(db)
        has_critical = any(a.severity.value == "critical" for a in alerts)
        
        return {
            "status": "unhealthy" if has_critical else "healthy",
            "alerts_count": len(alerts),
            "critical_alerts": len([a for a in alerts if a.severity.value == "critical"]),
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
