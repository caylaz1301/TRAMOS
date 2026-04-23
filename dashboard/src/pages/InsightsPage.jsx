import React, { useState, useEffect } from 'react';
import { analyticsService } from '../api.js';
import './InsightsPage.css';

export default function InsightsPage() {
  const [insights, setInsights] = useState(null);
  const [trends, setTrends] = useState(null);
  const [hotspots, setHotspots] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const [insightsData, trendsData, hotspotsData, alertsData] = await Promise.all([
        analyticsService.getInsights().catch(() => null),
        analyticsService.getTrends().catch(() => null),
        analyticsService.getHotspots().catch(() => null),
        analyticsService.getActiveAlerts().catch(() => null),
      ]);
      setInsights(insightsData);
      setTrends(trendsData);
      setHotspots(hotspotsData);
      setAlerts(alertsData);
    } catch (err) {
      setError('Failed to load insights');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !insights) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Generating insights...</p>
      </div>
    );
  }

  const insightsData = insights || {};
  const trendsData = trends || {};
  const hotspotsData = hotspots || {};
  const alertsData = alerts || {};
  const activeAlerts = alertsData.alerts || [];
  const criticalCount = alertsData.critical_count || 0;
  const warningCount = alertsData.warning_count || 0;

  return (
    <div className="insights-page">
      <div className="page-header">
        <div>
          <h1>Insights & Alerts</h1>
          <p className="page-subtitle">AI-powered analysis, recommendations & system monitoring</p>
        </div>
      </div>

      {error && (
        <div className="page-error">
          ⚠️ {error}
          <button onClick={fetchData}>Retry</button>
        </div>
      )}

      {/* Alert Summary Strip */}
      <div className="alert-strip">
        <div className={`alert-status ${criticalCount > 0 ? 'status-critical' : warningCount > 0 ? 'status-warning' : 'status-healthy'}`}>
          <span className="status-icon">
            {criticalCount > 0 ? '🔴' : warningCount > 0 ? '🟡' : '🟢'}
          </span>
          <span className="status-text">
            {criticalCount > 0 ? `${criticalCount} Critical Alert${criticalCount > 1 ? 's' : ''}` :
             warningCount > 0 ? `${warningCount} Warning${warningCount > 1 ? 's' : ''}` :
             'System Healthy'}
          </span>
        </div>
        <div className="alert-count">
          {activeAlerts.length} total alert{activeAlerts.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Content Grid */}
      <div className="insights-grid">
        {/* Left: Alerts + Hotspots */}
        <div className="insights-left">
          {/* Active Alerts */}
          <div className="card">
            <div className="card-header">
              <h2>⚡ Active Alerts</h2>
              <span className="card-badge">{activeAlerts.length}</span>
            </div>
            <div className="alerts-list">
              {activeAlerts.length > 0 ? (
                activeAlerts.slice(0, 6).map((alert, i) => (
                  <div key={i} className={`alert-row alert-${alert.severity || 'info'}`}>
                    <div className="alert-indicator" />
                    <div className="alert-body">
                      <div className="alert-title">{alert.title || alert.message || 'Alert'}</div>
                      <div className="alert-detail">{alert.description || alert.detail || ''}</div>
                    </div>
                    <span className={`alert-badge badge-${alert.severity || 'info'}`}>
                      {alert.severity || 'info'}
                    </span>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <span className="empty-icon">✅</span>
                  <p>No active alerts — system running smoothly</p>
                </div>
              )}
            </div>
          </div>

          {/* Hotspots */}
          <div className="card">
            <div className="card-header">
              <h2>🔥 Issue Hotspots</h2>
            </div>
            <div className="hotspots-list">
              {hotspotsData.critical_hotspots && hotspotsData.critical_hotspots.length > 0 ? (
                hotspotsData.critical_hotspots.map((hs, i) => (
                  <div key={i} className="hotspot-row">
                    <div className="hotspot-rank">{i + 1}</div>
                    <div className="hotspot-body">
                      <div className="hotspot-cat">{hs.category}</div>
                      <div className="hotspot-meta">
                        <span>Severity: <strong>{hs.severity}</strong></span>
                        <span>Count: <strong>{hs.count}</strong></span>
                      </div>
                    </div>
                    <span className="hotspot-trend">{hs.trend || '→'}</span>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <span className="empty-icon">🎉</span>
                  <p>No critical hotspots detected</p>
                </div>
              )}
              {hotspotsData.recommendation && (
                <div className="hotspot-rec">
                  <span>💡</span> {hotspotsData.recommendation}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Insights + Trends */}
        <div className="insights-right">
          {/* AI Recommendations */}
          <div className="card">
            <div className="card-header">
              <h2>💡 AI Recommendations</h2>
            </div>
            <div className="recs-container">
              {/* Key Findings */}
              {insightsData.insights && insightsData.insights.length > 0 && (
                <div className="rec-group">
                  <h3 className="rec-group-title">Key Findings</h3>
                  {insightsData.insights.slice(0, 4).map((ins, i) => (
                    <div key={i} className="rec-item rec-finding">
                      <span className={`rec-severity sev-${ins.severity || 'info'}`}>
                        {ins.severity === 'critical' ? '🔴' : ins.severity === 'warning' ? '🟡' : 'ℹ️'}
                      </span>
                      <div className="rec-content">
                        <div className="rec-cat">{ins.category}</div>
                        <div className="rec-detail">{ins.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Warnings */}
              {insightsData.warnings && insightsData.warnings.length > 0 && (
                <div className="rec-group">
                  <h3 className="rec-group-title">⚠️ Warnings</h3>
                  {insightsData.warnings.slice(0, 3).map((w, i) => (
                    <div key={i} className="rec-item rec-warn">
                      <span className="rec-severity sev-warning">🟡</span>
                      <div className="rec-content">
                        <div className="rec-cat">{w.category}</div>
                        <div className="rec-detail">{w.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Action Recommendations */}
              {insightsData.recommendations && insightsData.recommendations.length > 0 && (
                <div className="rec-group">
                  <h3 className="rec-group-title">✨ Suggested Actions</h3>
                  {insightsData.recommendations.slice(0, 5).map((rec, i) => (
                    <div key={i} className="rec-action">
                      <span className="rec-arrow">→</span>
                      <p>{rec}</p>
                    </div>
                  ))}
                </div>
              )}

              {(!insightsData.insights?.length && !insightsData.warnings?.length && !insightsData.recommendations?.length) && (
                <div className="empty-state">
                  <span className="empty-icon">📊</span>
                  <p>Collect more data to generate AI insights</p>
                </div>
              )}
            </div>
          </div>

          {/* Trend Analysis */}
          <div className="card">
            <div className="card-header">
              <h2>📈 Trend Analysis</h2>
            </div>
            <div className="trend-container">
              <div className="trend-direction-box">
                <div className="trend-arrow">
                  {trendsData.trend_direction || '➡️'}
                </div>
                <div className="trend-label">Overall Direction</div>
              </div>
              {trendsData.recommendation && (
                <div className="trend-rec">
                  {trendsData.recommendation}
                </div>
              )}
              {trendsData.weekly_trends && trendsData.weekly_trends.length > 0 && (
                <div className="trend-weeks">
                  <h4>Weekly Summary</h4>
                  <div className="week-bars">
                    {trendsData.weekly_trends.slice(-4).map((w, i) => (
                      <div key={i} className="week-item">
                        <div className="week-bar-track">
                          <div
                            className="week-bar-fill"
                            style={{ height: `${Math.min(w.resolution_rate || 0, 100)}%` }}
                          />
                        </div>
                        <div className="week-label">{w.week || `W${i + 1}`}</div>
                        <div className="week-val">{w.resolution_rate || 0}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {!trendsData.trend_direction && !trendsData.weekly_trends?.length && (
                <div className="empty-state">
                  <span className="empty-icon">📈</span>
                  <p>Not enough data for trend analysis</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
