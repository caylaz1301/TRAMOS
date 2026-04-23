import React, { useState, useEffect } from 'react';
import { analyticsService } from '../api.js';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import './OverviewPage.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler);

export default function OverviewPage() {
  const [data, setData] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const [dashData, timelineData] = await Promise.all([
        analyticsService.getDashboard(),
        analyticsService.getOverviewStats().catch(() => null),
      ]);
      setData(dashData);
      setTimeline(timelineData);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Loading overview...</p>
      </div>
    );
  }

  const overview = data?.overview || {};
  const categories = data?.categories?.categories || [];
  const quality = data?.quality || {};
  const sessions = data?.recent_sessions?.sessions || [];

  // Calculate AI resolution rate
  const totalSessions = overview.total_sessions || 0;
  const totalTickets = overview.total_tickets || 0;
  const aiResolved = totalSessions > 0 ? Math.max(0, totalSessions - totalTickets) : 0;
  const aiRate = totalSessions > 0 ? Math.round((aiResolved / totalSessions) * 100) : 0;

  // ── KPI Cards Data ──
  const kpis = [
    {
      label: 'Total Sessions',
      value: totalSessions.toLocaleString(),
      icon: '📱',
      color: 'accent',
      sub: `${overview.active_sessions || 0} active now`,
    },
    {
      label: 'AI Resolution Rate',
      value: `${aiRate}%`,
      icon: '🤖',
      color: 'success',
      sub: `${aiResolved} solved by AI`,
    },
    {
      label: 'Tickets Created',
      value: totalTickets.toLocaleString(),
      icon: '🎫',
      color: 'warning',
      sub: 'Escalated to support',
    },
    {
      label: 'Avg Messages',
      value: overview.avg_messages_per_session || 0,
      icon: '💬',
      color: 'info',
      sub: `${(overview.total_messages || 0).toLocaleString()} total`,
    },
  ];

  // ── Category Bar Chart ──
  const catColors = ['#38bdf8', '#34d399', '#fbbf24', '#f87171', '#818cf8', '#fb923c', '#a78bfa'];
  const categoryChartData = {
    labels: categories.map(c => c.name || 'Unknown'),
    datasets: [{
      label: 'Issues',
      data: categories.map(c => c.count),
      backgroundColor: categories.map((_, i) => catColors[i % catColors.length]),
      borderRadius: 6,
      borderSkipped: false,
      barThickness: 28,
    }],
  };

  const categoryChartOpts = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        borderColor: '#334155',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 10,
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: { color: 'rgba(51,65,85,0.4)', drawBorder: false },
        ticks: { color: '#64748b', font: { size: 12 } },
      },
      y: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 13, weight: 500 } },
      },
    },
  };

  // ── Session Quality ──
  const qualityItems = [
    { label: 'Completion Rate', value: `${quality.completion_rate || 0}%`, color: 'success' },
    { label: 'Avg Duration', value: `${Math.round((quality.avg_duration_seconds || 0) / 60)}m`, color: 'accent' },
    { label: 'Avg Messages', value: quality.avg_messages || 0, color: 'info' },
    { label: 'Abandoned', value: quality.abandoned_sessions || 0, color: 'danger' },
  ];

  return (
    <div className="overview-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>Overview</h1>
          <p className="page-subtitle">Real-time system monitoring & key metrics</p>
        </div>
        <div className="header-meta">
          <span className="live-dot" />
          <span className="meta-text">Auto-refresh 15s</span>
        </div>
      </div>

      {error && (
        <div className="page-error">
          ⚠️ {error}
          <button onClick={fetchData}>Retry</button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="kpi-grid">
        {kpis.map((kpi, i) => (
          <div key={i} className={`kpi-card kpi-${kpi.color}`} style={{ animationDelay: `${i * 80}ms` }}>
            <div className="kpi-top">
              <span className="kpi-icon">{kpi.icon}</span>
              <span className="kpi-label">{kpi.label}</span>
            </div>
            <div className="kpi-value">{kpi.value}</div>
            <div className="kpi-sub">{kpi.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Category Distribution */}
        <div className="card chart-card">
          <div className="card-header">
            <h2>Problem Categories</h2>
            <span className="card-badge">{categories.length} types</span>
          </div>
          <div className="chart-container chart-bar-h">
            {categories.length > 0 ? (
              <Bar data={categoryChartData} options={categoryChartOpts} />
            ) : (
              <div className="no-data">No category data available yet</div>
            )}
          </div>
        </div>

        {/* Session Quality */}
        <div className="card quality-card">
          <div className="card-header">
            <h2>Session Quality</h2>
          </div>
          <div className="quality-grid">
            {qualityItems.map((item, i) => (
              <div key={i} className={`quality-item quality-${item.color}`}>
                <div className="quality-value">{item.value}</div>
                <div className="quality-label">{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="card recent-card">
        <div className="card-header">
          <h2>Recent Sessions</h2>
          <span className="card-badge">{sessions.length} latest</span>
        </div>
        <div className="table-wrapper">
          {sessions.length > 0 ? (
            <table className="sessions-table">
              <thead>
                <tr>
                  <th>Driver</th>
                  <th>Category</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Messages</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {sessions.slice(0, 8).map((s, i) => (
                  <tr key={i} style={{ animationDelay: `${i * 50}ms` }}>
                    <td className="td-driver">
                      <div className="driver-avatar">{(s.name || '?').charAt(0).toUpperCase()}</div>
                      <div className="driver-info">
                        <span className="driver-name">{s.name || 'Unknown'}</span>
                        <span className="driver-phone">{s.phone ? `...${s.phone.slice(-4)}` : ''}</span>
                      </div>
                    </td>
                    <td>
                      <span className="tag tag-category">{s.category || '—'}</span>
                    </td>
                    <td>
                      <span className={`tag tag-sev tag-sev-${s.severity || 'medium'}`}>
                        {s.severity || '—'}
                      </span>
                    </td>
                    <td>
                      <span className={`tag tag-status tag-status-${s.state || 'unknown'}`}>
                        {formatState(s.state)}
                      </span>
                    </td>
                    <td className="td-center">{s.messages || 0}</td>
                    <td className="td-time">{formatTime(s.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="no-data">No sessions recorded yet</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Helpers ──
function formatState(state) {
  const map = {
    greeting: 'Started',
    collecting_name: 'Collecting',
    collecting_problem: 'Collecting',
    asking_solution_worked: 'KB Solution',
    collecting_unit: 'Escalating',
    collecting_location: 'Escalating',
    collecting_time: 'Escalating',
    confirming_details: 'Confirming',
    creating_ticket: 'Creating Ticket',
    closed: 'Closed',
    resolved: 'Resolved',
  };
  return map[state] || state || '—';
}

function formatTime(isoStr) {
  if (!isoStr) return '—';
  try {
    const d = new Date(isoStr);
    const now = new Date();
    const diffMs = now - d;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
  } catch {
    return '—';
  }
}
