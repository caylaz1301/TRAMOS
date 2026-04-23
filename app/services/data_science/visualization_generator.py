"""
Advanced Visualizations Data Generator
Provides structured data for various chart types: trends, distributions, heatmaps, etc.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session

from app.database_models import WhatsAppSession

logger = logging.getLogger(__name__)


class VisualizationGenerator:
    """Generate data for advanced dashboard visualizations"""
    
    @staticmethod
    def generate_all_visualizations(db: Session) -> Dict[str, Any]:
        """Generate all visualization data"""
        try:
            return {
                "trend_chart": VisualizationGenerator.generate_trend_chart(db),
                "category_distribution": VisualizationGenerator.generate_category_distribution(db),
                "severity_distribution": VisualizationGenerator.generate_severity_distribution(db),
                "temporal_heatmap": VisualizationGenerator.generate_temporal_heatmap(db),
                "escalation_timeline": VisualizationGenerator.generate_escalation_timeline(db),
                "resolution_funnel": VisualizationGenerator.generate_resolution_funnel(db),
                "state_distribution": VisualizationGenerator.generate_state_distribution(db),
                "hourly_activity": VisualizationGenerator.generate_hourly_activity(db),
                "message_distribution": VisualizationGenerator.generate_message_distribution(db),
                "quality_trend": VisualizationGenerator.generate_quality_trend(db),
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_trend_chart(db: Session, days: int = 30) -> Dict[str, Any]:
        """Generate 30-day trend line data"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Group by day
            daily_data = defaultdict(lambda: {"sessions": 0, "escalated": 0, "resolved": 0})
            
            for s in sessions:
                date_key = s.created_at.strftime("%Y-%m-%d") if s.created_at else None
                if date_key:
                    daily_data[date_key]["sessions"] += 1
                    if s.ticket_id:
                        daily_data[date_key]["escalated"] += 1
                    if s.current_state == "resolved":
                        daily_data[date_key]["resolved"] += 1
            
            # Prepare chart data
            dates = sorted(daily_data.keys())
            
            return {
                "chart_type": "line",
                "title": "30-Day Activity Trend",
                "xAxis": {
                    "type": "category",
                    "data": dates
                },
                "series": [
                    {
                        "name": "Sessions",
                        "data": [daily_data[d]["sessions"] for d in dates],
                        "type": "line",
                        "smooth": True,
                        "itemStyle": {"color": "#667eea"}
                    },
                    {
                        "name": "Escalated",
                        "data": [daily_data[d]["escalated"] for d in dates],
                        "type": "line",
                        "smooth": True,
                        "itemStyle": {"color": "#ff6b6b"}
                    },
                    {
                        "name": "Resolved",
                        "data": [daily_data[d]["resolved"] for d in dates],
                        "type": "line",
                        "smooth": True,
                        "itemStyle": {"color": "#4caf50"}
                    }
                ],
                "tooltip": {"trigger": "cross"},
                "legend": {"top": "bottom"}
            }
        except Exception as e:
            logger.error(f"Error generating trend chart: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_category_distribution(db: Session) -> Dict[str, Any]:
        """Generate category distribution pie chart"""
        try:
            cutoff = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Count by category
            categories = defaultdict(int)
            for s in sessions:
                cat = s.problem_category or "Unknown"
                categories[cat] += 1
            
            total = len(sessions)
            data = [
                {
                    "value": count,
                    "name": cat,
                    "label": f"{cat} ({count}/{total})"
                }
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)
            ]
            
            return {
                "chart_type": "pie",
                "title": "Issue Distribution (7 days)",
                "series": [
                    {
                        "type": "pie",
                        "radius": ["40%", "70%"],
                        "data": data,
                        "emphasis": {
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)"
                            }
                        }
                    }
                ],
                "legend": {
                    "orient": "vertical",
                    "left": "left"
                },
                "tooltip": {
                    "trigger": "item",
                    "formatter": "{b}: {c} ({d}%)"
                }
            }
        except Exception as e:
            logger.error(f"Error generating category distribution: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_severity_distribution(db: Session) -> Dict[str, Any]:
        """Generate severity level distribution bar chart"""
        try:
            cutoff = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Count by severity
            severities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for s in sessions:
                sev = s.problem_severity or "low"
                if sev in severities:
                    severities[sev] += 1
                else:
                    severities["low"] += 1
            
            return {
                "chart_type": "bar",
                "title": "Issues by Severity",
                "xAxis": {
                    "type": "category",
                    "data": ["Critical", "High", "Medium", "Low"]
                },
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "name": "Count",
                        "data": [
                            severities["critical"],
                            severities["high"],
                            severities["medium"],
                            severities["low"]
                        ],
                        "type": "bar",
                        "itemStyle": {
                            "color": {
                                "type": "pattern",
                                "pattern": [
                                    {"color": "#ff5252"},
                                    {"color": "#ffb74d"},
                                    {"color": "#fdd835"},
                                    {"color": "#4caf50"}
                                ]
                            }
                        }
                    }
                ],
                "tooltip": {"trigger": "axis"}
            }
        except Exception as e:
            logger.error(f"Error generating severity distribution: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_temporal_heatmap(db: Session) -> Dict[str, Any]:
        """Generate hourly activity heatmap"""
        try:
            cutoff = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Create hour x day matrix
            heatmap_data = []
            
            for s in sessions:
                if s.created_at:
                    day_of_week = s.created_at.weekday()  # 0=Monday
                    hour = s.created_at.hour
                    heatmap_data.append([hour, day_of_week, 1])
            
            # Aggregate
            hour_day_counts = defaultdict(lambda: defaultdict(int))
            for h, d, count in heatmap_data:
                hour_day_counts[h][d] += count
            
            # Convert to heatmap format
            data = []
            days_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for hour in range(24):
                for day in range(7):
                    count = hour_day_counts[hour][day]
                    if count > 0:
                        data.append([day, hour, count])
            
            return {
                "chart_type": "heatmap",
                "title": "Activity Heatmap (Hour × Day of Week)",
                "xAxis": {
                    "type": "category",
                    "data": days_names
                },
                "yAxis": {
                    "type": "category",
                    "data": [f"{h:02d}:00" for h in range(24)]
                },
                "series": [
                    {
                        "name": "Sessions",
                        "data": data,
                        "type": "heatmap",
                        "label": {"show": False}
                    }
                ],
                "visualMap": {
                    "min": 0,
                    "max": max([d[2] for d in data]) if data else 1,
                    "inRange": {
                        "color": ["#ebedf0", "#c6e48b", "#7bc96f", "#239a3b", "#196127"]
                    }
                },
                "tooltip": {"trigger": "item"}
            }
        except Exception as e:
            logger.error(f"Error generating temporal heatmap: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_escalation_timeline(db: Session, days: int = 30) -> Dict[str, Any]:
        """Generate escalation rate over time"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Daily escalation rates
            daily_stats = defaultdict(lambda: {"total": 0, "escalated": 0})
            
            for s in sessions:
                date_key = s.created_at.strftime("%Y-%m-%d") if s.created_at else None
                if date_key:
                    daily_stats[date_key]["total"] += 1
                    if s.ticket_id:
                        daily_stats[date_key]["escalated"] += 1
            
            dates = sorted(daily_stats.keys())
            escalation_rates = [
                (daily_stats[d]["escalated"] / daily_stats[d]["total"] * 100)
                if daily_stats[d]["total"] > 0 else 0
                for d in dates
            ]
            
            return {
                "chart_type": "area",
                "title": "Escalation Rate Trend",
                "xAxis": {
                    "type": "category",
                    "data": dates
                },
                "yAxis": {
                    "type": "value",
                    "axisLabel": {"formatter": "{value}%"}
                },
                "series": [
                    {
                        "name": "Escalation %",
                        "data": escalation_rates,
                        "type": "line",
                        "fill": "start",
                        "areaStyle": {"color": "rgba(255, 107, 107, 0.3)"},
                        "itemStyle": {"color": "#ff6b6b"},
                        "smooth": True
                    }
                ],
                "tooltip": {"trigger": "axis"}
            }
        except Exception as e:
            logger.error(f"Error generating escalation timeline: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_resolution_funnel(db: Session) -> Dict[str, Any]:
        """Generate resolution funnel chart"""
        try:
            cutoff = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            total = len(sessions)
            created_greeting = total
            problem_collected = len([s for s in sessions if s.problem_description])
            kb_searched = len([s for s in sessions if s.problem_category])
            resolved_by_kb = len([s for s in sessions if s.current_state == "resolved"])
            escalated = len([s for s in sessions if s.ticket_id])
            closed = len([s for s in sessions if s.current_state == "closed"])
            
            return {
                "chart_type": "funnel",
                "title": "Conversation Resolution Funnel",
                "series": [
                    {
                        "name": "Sessions",
                        "type": "funnel",
                        "left": "10%",
                        "top": 60,
                        "bottom": 60,
                        "width": "80%",
                        "minSize": "50%",
                        "maxSize": "100%",
                        "sort": "descending",
                        "data": [
                            {"value": created_greeting, "name": "Greeting"},
                            {"value": problem_collected, "name": "Problem Collected"},
                            {"value": kb_searched, "name": "KB Searched"},
                            {"value": resolved_by_kb, "name": "Resolved by KB"},
                            {"value": escalated, "name": "Escalated"},
                            {"value": closed, "name": "Closed"}
                        ],
                        "itemStyle": {
                            "borderColor": "#333",
                            "borderWidth": 1
                        },
                        "emphasis": {
                            "label": {"fontSize": 20}
                        }
                    }
                ],
                "tooltip": {"trigger": "item"},
                "legend": {"bottom": "10%"}
            }
        except Exception as e:
            logger.error(f"Error generating resolution funnel: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_state_distribution(db: Session) -> Dict[str, Any]:
        """Generate conversation state distribution"""
        try:
            cutoff = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Count by state
            states = defaultdict(int)
            for s in sessions:
                state = s.current_state or "unknown"
                states[state] += 1
            
            return {
                "chart_type": "doughnut",
                "title": "Conversation States",
                "series": [
                    {
                        "type": "doughnut",
                        "radius": ["40%", "70%"],
                        "data": [
                            {"value": count, "name": state.replace("_", " ").title()}
                            for state, count in sorted(states.items(), key=lambda x: x[1], reverse=True)
                        ]
                    }
                ],
                "tooltip": {"trigger": "item"},
                "legend": {"orient": "vertical", "right": 0}
            }
        except Exception as e:
            logger.error(f"Error generating state distribution: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_hourly_activity(db: Session) -> Dict[str, Any]:
        """Generate hourly activity pattern"""
        try:
            cutoff = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Group by hour
            hourly_counts = defaultdict(int)
            for s in sessions:
                if s.created_at:
                    hour = s.created_at.hour
                    hourly_counts[hour] += 1
            
            return {
                "chart_type": "bar",
                "title": "Hourly Activity Pattern",
                "xAxis": {
                    "type": "category",
                    "data": [f"{h:02d}:00" for h in range(24)]
                },
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "name": "Sessions",
                        "data": [hourly_counts[h] for h in range(24)],
                        "type": "bar",
                        "itemStyle": {"color": "#667eea"}
                    }
                ],
                "tooltip": {"trigger": "axis"}
            }
        except Exception as e:
            logger.error(f"Error generating hourly activity: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_message_distribution(db: Session) -> Dict[str, Any]:
        """Generate message count distribution"""
        try:
            cutoff = datetime.now() - timedelta(days=7)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Group message counts into buckets
            buckets = {"1-3": 0, "4-6": 0, "7-10": 0, "11-15": 0, "15+": 0}
            
            for s in sessions:
                msg_count = s.message_count or 0
                if msg_count <= 3:
                    buckets["1-3"] += 1
                elif msg_count <= 6:
                    buckets["4-6"] += 1
                elif msg_count <= 10:
                    buckets["7-10"] += 1
                elif msg_count <= 15:
                    buckets["11-15"] += 1
                else:
                    buckets["15+"] += 1
            
            return {
                "chart_type": "bar",
                "title": "Messages per Session Distribution",
                "xAxis": {
                    "type": "category",
                    "data": list(buckets.keys())
                },
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "name": "Sessions",
                        "data": list(buckets.values()),
                        "type": "bar",
                        "itemStyle": {
                            "color": ["#4caf50", "#8bc34a", "#fdd835", "#ffb74d", "#ff6b6b"]
                        }
                    }
                ],
                "tooltip": {"trigger": "axis"}
            }
        except Exception as e:
            logger.error(f"Error generating message distribution: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_quality_trend(db: Session) -> Dict[str, Any]:
        """Generate quality score trend over time"""
        try:
            cutoff = datetime.now() - timedelta(days=30)
            sessions = db.query(WhatsAppSession).filter(
                WhatsAppSession.created_at >= cutoff
            ).all()
            
            # Daily quality scores
            daily_quality = defaultdict(lambda: {"resolved": 0, "escalated": 0, "total": 0})
            
            for s in sessions:
                date_key = s.created_at.strftime("%Y-%m-%d") if s.created_at else None
                if date_key:
                    daily_quality[date_key]["total"] += 1
                    if s.current_state == "resolved":
                        daily_quality[date_key]["resolved"] += 1
                    if s.ticket_id:
                        daily_quality[date_key]["escalated"] += 1
            
            dates = sorted(daily_quality.keys())
            quality_scores = [
                max(0, (daily_quality[d]["resolved"] * 100 - daily_quality[d]["escalated"] * 50) / daily_quality[d]["total"])
                if daily_quality[d]["total"] > 0 else 0
                for d in dates
            ]
            
            return {
                "chart_type": "line",
                "title": "Quality Score Trend (30 days)",
                "xAxis": {
                    "type": "category",
                    "data": dates
                },
                "yAxis": {
                    "type": "value",
                    "axisLabel": {"formatter": "{value}"}
                },
                "series": [
                    {
                        "name": "Quality Score",
                        "data": quality_scores,
                        "type": "line",
                        "smooth": True,
                        "itemStyle": {"color": "#764ba2"},
                        "areaStyle": {"color": "rgba(118, 75, 162, 0.2)"}
                    }
                ],
                "tooltip": {"trigger": "axis"}
            }
        except Exception as e:
            logger.error(f"Error generating quality trend: {e}")
            return {"error": str(e)}
