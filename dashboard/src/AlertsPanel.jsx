import React, { useState, useEffect } from 'react';
import { analyticsService } from './api.js';
import './AlertsPanel.css';

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const [alertsData, healthData] = await Promise.all([
        analyticsService.getActiveAlerts(),
        analyticsService.getHealthCheck()
      ]);
      
      setAlerts(alertsData.alerts || []);
      setHealth(healthData);
    } catch (err) {
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="alerts-loading">Loading alerts...</div>;
  }

  return (
    <div className="alerts-panel">
      <div className="alerts-header">
        <h2>🚨 Real-Time Alerts & Health</h2>
        <div className="health-badge">
          {health?.status === 'healthy' ? (
            <span className="health-good">🟢 Healthy</span>
          ) : (
            <span className="health-warning">🔴 Issues Detected ({health?.critical_alerts})</span>
          )}
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="no-alerts">
          <p>✅ No active alerts. System is performing well!</p>
        </div>
      ) : (
        <div className="alerts-list">
          {alerts.map((alert, idx) => (
            <div key={idx} className={`alert-item alert-${alert.severity}`}>
              <div className="alert-icon">{alert.icon}</div>
              <div className="alert-content">
                <h3>{alert.title}</h3>
                <p>{alert.message}</p>
                <div className="alert-metrics">
                  <span>Value: {alert.metric_value}</span>
                  <span>Threshold: {alert.threshold}</span>
                </div>
                <p className="alert-recommendation">💡 {alert.recommendation}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
