"""
Data Science & Analytics Module - Pattern Detection & Intelligence

This module contains all data analysis, pattern detection, and insights generation:
- ML-based pattern analysis (problem patterns, hotspots, temporal trends)
- Statistical reporting (executive summary, performance metrics)
- Real-time alerting (8 alert types, severity levels)
- Predictive analytics (volume, escalation, staffing forecasts)
- Report generation (daily/weekly/monthly, multiple export formats)
- Anomaly detection (8 types: spikes, quality drops, escalation surge, etc)
- Data visualization (10 chart types: trends, heatmaps, funnels, etc)
- Industry benchmark comparison (vs standards, recommendations)

Key Classes:
- MLPatternAnalyzer: Pattern detection from conversations
- StatisticsGenerator: Generate statistics and reports
- AlertManager: Real-time anomaly alerts
- PredictiveAnalytics: Forecast future trends
- ReportGenerator: Export reports in multiple formats
- AnomalyDetector: Detect unusual patterns
- VisualizationGenerator: Generate ECharts-compatible visualizations
- BenchmarkComparison: Compare metrics against industry standards
"""

from .ml_pattern_analyzer import MLPatternAnalyzer
from .statistics_generator import StatisticsGenerator
from .alert_manager import AlertManager
from .predictive_analytics import PredictiveAnalytics
from .report_generator import ReportGenerator
from .anomaly_detector import AnomalyDetector
from .visualization_generator import VisualizationGenerator
from .benchmark_comparison import BenchmarkComparison, IndustryBenchmark

__all__ = [
    "MLPatternAnalyzer",
    "StatisticsGenerator",
    "AlertManager",
    "PredictiveAnalytics",
    "ReportGenerator",
    "AnomalyDetector",
    "VisualizationGenerator",
    "BenchmarkComparison",
    "IndustryBenchmark",
]
