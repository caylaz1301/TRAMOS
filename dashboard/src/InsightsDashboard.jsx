import React, { useState, useEffect } from 'react';
import { analyticsService } from './api.js';
import './InsightsDashboard.css';

export default function InsightsDashboard({ token, onLogout }) {
  const [insights, setInsights] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [trends, setTrends] = useState(null);
  const [hotspots, setHotspots] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('insights');

  const fetchInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [insightsData, perfData, trendsData, hotspotsData] = await Promise.all([
        analyticsService.getInsights(),
        analyticsService.getPerformance(),
        analyticsService.getTrends(),
        analyticsService.getHotspots()
      ]);
      
      setInsights(insightsData);
      setPerformance(perfData);
      setTrends(trendsData);
      setHotspots(hotspotsData);
    } catch (err) {
      setError('Failed to fetch insights: ' + err.message);
      console.error('Error fetching insights:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
    const interval = setInterval(fetchInsights, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    onLogout();
  };

  if (loading && !insights) {
    return (
      <div className="insights-loading">
        <div className="spinner"></div>
        <p>Analyzing data and generating insights...</p>
      </div>
    );
  }

  if (error && !insights) {
    return (
      <div className="insights-error">
        <h2>Error Loading Insights</h2>
        <p>{error}</p>
        <button onClick={fetchInsights} className="btn-retry">
          Retry
        </button>
      </div>
    );
  }

  const username = localStorage.getItem('username') || 'User';
  const perfData = performance || {};
  const insightsData = insights || {};
  const trendsData = trends || {};
  const hotspotsData = hotspots || {};

  return (
    <div className="insights-dashboard">
      {/* Header */}
      <header className="insights-header">
        <div className="header-left">
          <h1>🧠 TRAMOS AI Insights & Analytics</h1>
          <p className="subtitle">Machine Learning Analysis & Management Insights</p>
        </div>
        <div className="header-right">
          <span className="user-info">👤 {username}</span>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="insights-nav">
        <button 
          className={`tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          💡 AI Insights
        </button>
        <button 
          className={`tab-btn ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          📈 Performance
        </button>
        <button 
          className={`tab-btn ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          📊 Trends
        </button>
        <button 
          className={`tab-btn ${activeTab === 'hotspots' ? 'active' : ''}`}
          onClick={() => setActiveTab('hotspots')}
        >
          🔥 Hotspots
        </button>
      </nav>

      {/* Content */}
      <div className="insights-content">
        {/* AI Insights Tab */}
        {activeTab === 'insights' && (
          <section className="insights-section">
            <h2>🤖 AI-Powered Insights & Recommendations</h2>
            
            {/* Key Insights */}
            {insightsData.insights && insightsData.insights.length > 0 && (
              <div className="insight-group">
                <h3>Key Findings</h3>
                {insightsData.insights.map((insight, idx) => (
                  <div key={idx} className="insight-card insight-info">
                    <div className="insight-header">
                      <span className="severity-badge">{insight.severity}</span>
                      <h4>{insight.category}</h4>
                    </div>
                    <p>{insight.detail}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Warnings */}
            {insightsData.warnings && insightsData.warnings.length > 0 && (
              <div className="insight-group">
                <h3>⚠️ Alerts</h3>
                {insightsData.warnings.map((warning, idx) => (
                  <div key={idx} className="insight-card insight-warning">
                    <div className="insight-header">
                      <span className="severity-badge">{warning.severity}</span>
                      <h4>{warning.category}</h4>
                    </div>
                    <p>{warning.detail}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Recommendations */}
            {insightsData.recommendations && insightsData.recommendations.length > 0 && (
              <div className="insight-group">
                <h3>✨ Recommended Actions</h3>
                <div className="recommendations-list">
                  {insightsData.recommendations.map((rec, idx) => (
                    <div key={idx} className="recommendation-item">
                      <span className="rec-icon">→</span>
                      <p>{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <section className="performance-section">
            <h2>📊 System Performance Report</h2>
            
            {/* Performance Score */}
            <div className="perf-header">
              <div className="perf-score-card">
                <h3>Performance Score</h3>
                <div className={`perf-score-large ${_getScoreClass(perfData.performance_score)}`}>
                  {perfData.performance_score || 0}
                </div>
                <p className="perf-grade">{perfData.score_grade || 'N/A'}</p>
              </div>

              <div className="perf-status-card">
                <h3>System Status</h3>
                <div className="status-indicator">
                  {perfData.resolution_metrics?.kb_effectiveness >= 70 ? (
                    <>
                      <span className="status-dot green"></span>
                      <p>🟢 Healthy</p>
                    </>
                  ) : perfData.resolution_metrics?.kb_effectiveness >= 50 ? (
                    <>
                      <span className="status-dot yellow"></span>
                      <p>🟡 Fair</p>
                    </>
                  ) : (
                    <>
                      <span className="status-dot red"></span>
                      <p>🔴 Needs Attention</p>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="perf-metrics-grid">
              {perfData.resolution_metrics && (
                <>
                  <div className="metric-box">
                    <h4>KB Effectiveness</h4>
                    <div className="metric-value">{perfData.resolution_metrics.kb_effectiveness || 0}%</div>
                    <p>Problems solved by KB solutions</p>
                  </div>
                  <div className="metric-box">
                    <h4>Escalation Rate</h4>
                    <div className="metric-value">{perfData.resolution_metrics.escalation_rate?.percentage || 0}%</div>
                    <p>Issues sent to support team</p>
                  </div>
                  <div className="metric-box">
                    <h4>Abandonment Rate</h4>
                    <div className="metric-value">{perfData.resolution_metrics.abandoned?.percentage || 0}%</div>
                    <p>Users who gave up</p>
                  </div>
                  <div className="metric-box">
                    <h4>Active Sessions</h4>
                    <div className="metric-value">{perfData.resolution_metrics.still_active?.percentage || 0}%</div>
                    <p>Ongoing conversations</p>
                  </div>
                </>
              )}
            </div>

            {/* Action Items */}
            {perfData.action_items && perfData.action_items.length > 0 && (
              <div className="action-items-section">
                <h3>📋 Action Items</h3>
                {perfData.action_items.map((item, idx) => (
                  <div key={idx} className="action-item">
                    <span className="action-icon">✓</span>
                    <p>{item}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Trends Tab */}
        {activeTab === 'trends' && (
          <section className="trends-section">
            <h2>📈 Trend Analysis</h2>
            
            <div className="trend-header">
              <div className="trend-direction">
                <h3>Overall Trend</h3>
                <p className="trend-indicator">{trendsData.trend_direction || '➡️ No data'}</p>
              </div>
              <div className="trend-summary">
                <p>{trendsData.recommendation || 'Collect more data for recommendations'}</p>
              </div>
            </div>

            {/* Weekly Trends */}
            {trendsData.weekly_trends && trendsData.weekly_trends.length > 0 && (
              <div className="weekly-trends">
                <h3>Weekly Performance</h3>
                <table className="trends-table">
                  <thead>
                    <tr>
                      <th>Period</th>
                      <th>Sessions</th>
                      <th>Resolved</th>
                      <th>Escalated</th>
                      <th>Resolution Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trendsData.weekly_trends.map((trend, idx) => (
                      <tr key={idx}>
                        <td>{trend.week}</td>
                        <td>{trend.sessions}</td>
                        <td>{trend.resolved}</td>
                        <td>{trend.escalated}</td>
                        <td>
                          <div className="trend-bar">
                            <div 
                              className="trend-fill" 
                              style={{width: `${trend.resolution_rate}%`}}
                            ></div>
                            <span>{trend.resolution_rate}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {/* Hotspots Tab */}
        {activeTab === 'hotspots' && (
          <section className="hotspots-section">
            <h2>🔥 Critical Issue Hotspots</h2>
            
            {hotspotsData.critical_hotspots && hotspotsData.critical_hotspots.length > 0 ? (
              <>
                <div className="hotspots-grid">
                  {hotspotsData.critical_hotspots.map((hotspot, idx) => (
                    <div key={idx} className="hotspot-card">
                      <div className="hotspot-severity">
                        {hotspot.trend}
                      </div>
                      <h3>{hotspot.category}</h3>
                      <div className="hotspot-details">
                        <p><strong>Severity:</strong> {hotspot.severity}</p>
                        <p><strong>Occurrences:</strong> {hotspot.count}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {hotspotsData.recommendation && (
                  <div className="hotspot-recommendation">
                    <h3>Recommended Action</h3>
                    <p>{hotspotsData.recommendation}</p>
                  </div>
                )}
              </>
            ) : (
              <div className="no-data">
                <p>✅ No critical hotspots detected. System is performing well!</p>
              </div>
            )}
          </section>
        )}
      </div>

      {/* Footer */}
      <footer className="insights-footer">
        <p>📊 Last updated: {new Date().toLocaleTimeString()}</p>
        <p>TRAMOS AI Insights System © 2026</p>
      </footer>
    </div>
  );
}

// Helper function to get score class
function _getScoreClass(score) {
  if (score >= 90) return 'score-excellent';
  if (score >= 80) return 'score-good';
  if (score >= 70) return 'score-fair';
  if (score >= 60) return 'score-poor';
  return 'score-critical';
}
