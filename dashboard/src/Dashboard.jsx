import React, { useState, useEffect } from 'react';
import { analyticsService, authService } from './api.js';
import MetricCard from './MetricCard.jsx';
import ChartSection from './ChartSection.jsx';
import RecentSessions from './RecentSessions.jsx';
import './Dashboard.css';

export default function Dashboard({ token, onLogout, onSwitchToInsights }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [username, setUsername] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const dashData = await analyticsService.getDashboard();
      setData(dashData);
    } catch (err) {
      setError('Failed to fetch dashboard data: ' + err.message);
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const storedUsername = localStorage.getItem('username');
    setUsername(storedUsername || 'User');
    fetchData();
    
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    onLogout();
  };

  if (loading && !data) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading analytics data...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="dashboard-error">
        <h2>Error Loading Dashboard</h2>
        <p>{error}</p>
        <button onClick={fetchData} className="btn-retry">
          Retry
        </button>
      </div>
    );
  }

  const overview = data?.overview || {};
  const categories = data?.categories?.categories || [];
  const severity = data?.severity?.severities || [];
  const quality = data?.quality || {};
  const tickets = data?.tickets || {};

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>📊 TRAMOS Analytics Dashboard</h1>
        </div>
        <div className="header-right">
          <button 
            onClick={onSwitchToInsights}
            className="btn-switch"
            title="View AI Insights"
          >
            🧠 AI Insights
          </button>
          <span className="user-info">👤 {username}</span>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </header>

      {/* Status Message */}
      {error && (
        <div className="dashboard-warning">
          <strong>⚠️ Warning:</strong> {error}
        </div>
      )}

      {/* Metrics Section */}
      <section className="metrics-section">
        <h2>Key Metrics</h2>
        <div className="metrics-grid">
          <MetricCard
            label="Total Sessions"
            value={overview.total_sessions || 0}
            icon="📱"
            color="blue"
          />
          <MetricCard
            label="Tickets Created"
            value={overview.total_tickets || 0}
            icon="🎫"
            color="green"
          />
          <MetricCard
            label="Success Rate"
            value={`${overview.success_rate || 0}%`}
            icon="✅"
            color="purple"
          />
          <MetricCard
            label="Active Sessions"
            value={overview.active_sessions || 0}
            icon="🔴"
            color="red"
          />
          <MetricCard
            label="Total Messages"
            value={overview.total_messages || 0}
            icon="💬"
            color="orange"
          />
          <MetricCard
            label="Avg Messages/Session"
            value={overview.avg_messages_per_session || 0}
            icon="📊"
            color="cyan"
          />
        </div>
      </section>

      {/* Quality Metrics */}
      <section className="quality-section">
        <h2>Session Quality</h2>
        <div className="quality-grid">
          <div className="quality-card">
            <h3>Completion Rate</h3>
            <div className="quality-value">{quality.completion_rate || 0}%</div>
            <p>{quality.completed_sessions || 0} of {quality.total_sessions || 0} completed</p>
          </div>
          <div className="quality-card">
            <h3>Avg Duration</h3>
            <div className="quality-value">{quality.avg_duration_seconds || 0}s</div>
            <p>Average session time</p>
          </div>
          <div className="quality-card">
            <h3>Avg Messages</h3>
            <div className="quality-value">{quality.avg_messages || 0}</div>
            <p>Messages per session</p>
          </div>
          <div className="quality-card">
            <h3>Abandoned</h3>
            <div className="quality-value">{quality.abandoned_sessions || 0}</div>
            <p>Sessions not completed</p>
          </div>
        </div>
      </section>

      {/* Charts Section */}
      <section className="charts-section">
        <ChartSection
          categories={categories}
          severity={severity}
          tickets={tickets}
        />
      </section>

      {/* Recent Sessions */}
      <section className="recent-section">
        <RecentSessions sessions={data?.recent_sessions?.sessions || []} />
      </section>

      {/* Footer */}
      <footer className="dashboard-footer">
        <p>🔄 Auto-refreshing every 5 seconds | Last updated: {new Date().toLocaleTimeString()}</p>
        <p>TRAMOS WhatsApp AI Support System © 2026</p>
      </footer>
    </div>
  );
}
