import React, { useState, useEffect } from 'react';
import { analyticsService } from '../api.js';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import './PerformancePage.css';

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function PerformancePage() {
  const [performance, setPerformance] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const [perfData, dashData] = await Promise.all([
        analyticsService.getPerformance().catch(() => null),
        analyticsService.getDashboard().catch(() => null),
      ]);
      setPerformance(perfData);
      setDashboard(dashData);
    } catch (err) {
      setError('Failed to load performance data');
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

  if (loading && !performance) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Analyzing AI performance...</p>
      </div>
    );
  }

  const perf = performance || {};
  const overview = dashboard?.overview || {};
  const quality = dashboard?.quality || {};
  const severity = dashboard?.severity?.severities || [];

  // Performance score
  const score = perf.performance_score || 0;
  const grade = perf.score_grade || 'N/A';
  const scoreColor = score >= 80 ? 'success' : score >= 60 ? 'warning' : 'danger';

  // Resolution metrics
  const resMetrics = perf.resolution_metrics || {};
  const kbEff = resMetrics.kb_effectiveness || 0;
  const escRate = resMetrics.escalation_rate?.percentage || 0;
  const abandonRate = resMetrics.abandoned?.percentage || 0;
  const activeRate = resMetrics.still_active?.percentage || 0;

  // Donut: Resolution Breakdown
  const totalSessions = overview.total_sessions || 0;
  const totalTickets = overview.total_tickets || 0;
  const aiSolved = Math.max(0, totalSessions - totalTickets - (quality.abandoned_sessions || 0));
  const abandoned = quality.abandoned_sessions || 0;

  const donutData = {
    labels: ['AI Resolved', 'Escalated', 'Abandoned'],
    datasets: [{
      data: [aiSolved, totalTickets, abandoned],
      backgroundColor: ['#34d399', '#fbbf24', '#f87171'],
      borderColor: '#1e293b',
      borderWidth: 3,
      hoverBorderWidth: 0,
    }],
  };

  const donutOpts = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '72%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#94a3b8',
          font: { size: 12, weight: 500 },
          padding: 16,
          usePointStyle: true,
          pointStyleWidth: 10,
        },
      },
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
  };

  // Severity Bar
  const sevColors = {
    critical: '#f87171',
    high: '#fb923c',
    medium: '#fbbf24',
    low: '#34d399',
  };
  const sevData = {
    labels: severity.map(s => (s.name || '').charAt(0).toUpperCase() + (s.name || '').slice(1)),
    datasets: [{
      label: 'Count',
      data: severity.map(s => s.count),
      backgroundColor: severity.map(s => sevColors[s.name] || '#64748b'),
      borderRadius: 6,
      borderSkipped: false,
      barThickness: 32,
    }],
  };

  const sevOpts = {
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
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 13, weight: 500 } },
      },
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(51,65,85,0.4)', drawBorder: false },
        ticks: { color: '#64748b', font: { size: 12 }, stepSize: 1 },
      },
    },
  };

  // Metric items for the grid
  const perfMetrics = [
    { label: 'KB Effectiveness', value: `${kbEff}%`, desc: 'Problems solved by KB solutions', color: 'success', icon: '📚' },
    { label: 'Escalation Rate', value: `${escRate}%`, desc: 'Issues sent to human support', color: 'warning', icon: '📤' },
    { label: 'Abandonment', value: `${abandonRate}%`, desc: 'Users who left without resolution', color: 'danger', icon: '🚪' },
    { label: 'Completion Rate', value: `${quality.completion_rate || 0}%`, desc: 'Sessions completed successfully', color: 'accent', icon: '✅' },
  ];

  return (
    <div className="perf-page">
      <div className="page-header">
        <div>
          <h1>AI Performance</h1>
          <p className="page-subtitle">Evaluate chatbot effectiveness & resolution quality</p>
        </div>
      </div>

      {error && (
        <div className="page-error">
          ⚠️ {error}
          <button onClick={fetchData}>Retry</button>
        </div>
      )}

      {/* Score + Donut Row */}
      <div className="perf-top-row">
        {/* Performance Score */}
        <div className="card score-card">
          <div className="score-ring-wrapper">
            <div className={`score-ring score-ring-${scoreColor}`}>
              <svg viewBox="0 0 120 120">
                <circle className="ring-bg" cx="60" cy="60" r="52" />
                <circle
                  className="ring-fill"
                  cx="60" cy="60" r="52"
                  strokeDasharray={`${(score / 100) * 327} 327`}
                />
              </svg>
              <div className="score-number">
                <span className="score-val">{score}</span>
                <span className="score-max">/100</span>
              </div>
            </div>
          </div>
          <div className="score-info">
            <h3>Performance Score</h3>
            <span className={`score-grade grade-${scoreColor}`}>{grade}</span>
            <p className="score-desc">
              {score >= 80 ? 'AI is performing well' :
               score >= 60 ? 'Room for improvement' :
               'Needs attention'}
            </p>
          </div>
        </div>

        {/* Resolution Donut */}
        <div className="card donut-card">
          <div className="card-header">
            <h2>Resolution Breakdown</h2>
            <span className="card-badge">{totalSessions} total</span>
          </div>
          <div className="donut-container">
            {totalSessions > 0 ? (
              <Doughnut data={donutData} options={donutOpts} />
            ) : (
              <div className="no-data">No data available</div>
            )}
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="perf-metrics-grid">
        {perfMetrics.map((m, i) => (
          <div key={i} className={`perf-metric-card perf-metric-${m.color}`} style={{ animationDelay: `${i * 80}ms` }}>
            <div className="metric-icon-wrap">
              <span>{m.icon}</span>
            </div>
            <div className="metric-body">
              <div className="metric-val">{m.value}</div>
              <div className="metric-label">{m.label}</div>
              <div className="metric-desc">{m.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Severity Chart */}
      <div className="card severity-card">
        <div className="card-header">
          <h2>Issue Severity Distribution</h2>
          <span className="card-badge">{severity.reduce((a, s) => a + s.count, 0)} issues</span>
        </div>
        <div className="severity-chart-container">
          {severity.length > 0 ? (
            <Bar data={sevData} options={sevOpts} />
          ) : (
            <div className="no-data">No severity data available</div>
          )}
        </div>
      </div>

      {/* Action Items */}
      {perf.action_items && perf.action_items.length > 0 && (
        <div className="card action-card">
          <div className="card-header">
            <h2>📋 Recommended Actions</h2>
          </div>
          <div className="action-list">
            {perf.action_items.map((item, i) => (
              <div key={i} className="action-item">
                <div className="action-num">{i + 1}</div>
                <p>{item}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
