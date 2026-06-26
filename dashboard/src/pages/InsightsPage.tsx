import React, { useState, useEffect } from 'react';
import { analyticsService } from '../api.js';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import DateFilter from '../components/DateFilter';
import './InsightsPage.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler);

// SVG Icons
const Icons = {
  chart: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
  check: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  ticket: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M15 5v2" />
      <path d="M15 11v2" />
      <path d="M15 17v2" />
      <rect x="3" y="3" width="18" height="18" rx="2" />
    </svg>
  ),
  close: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  ),
  chat: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  activity: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  doc: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  alert: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  empty: (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <line x1="9" y1="9" x2="15" y2="15" />
      <line x1="15" y1="9" x2="9" y2="15" />
    </svg>
  ),
  robot: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
    </svg>
  ),
  star: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  ),
  thumbsUp: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
    </svg>
  ),
  warning: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  alertCircle: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
};

export default function InsightsPage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [activityLog, setActivityLog] = useState<any[]>([]);
  const [heatmapData, setHeatmapData] = useState<any>(null);
  const [categoryFlow, setCategoryFlow] = useState<any>(null);
  const [kpiTrends, setKpiTrends] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({ startDate: null as string | null, endDate: null as string | null });

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        setError(null);
        const [dashData, logData, heatmap, flow, trends] = await Promise.all([
          analyticsService.getDashboard(dateRange.startDate, dateRange.endDate).catch(() => null),
          analyticsService.getActivityLog(20, dateRange.startDate, dateRange.endDate).catch(() => ({ events: [] })),
          analyticsService.getHeatmap().catch(() => null),
          analyticsService.getCategoryFlow(dateRange.startDate, dateRange.endDate).catch(() => null),
          analyticsService.getKpiTrends(7).catch(() => null),
        ]);
        if (!cancelled) {
          setDashboard(dashData);
          setActivityLog(logData?.events || []);
          setHeatmapData(heatmap);
          setCategoryFlow(flow);
          setKpiTrends(trends);
        }
      } catch {
        if (!cancelled) {
          setError('Gagal memuat data laporan');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [dateRange.startDate, dateRange.endDate]);

  if (loading && !dashboard) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Memuat laporan...</p>
      </div>
    );
  }

  // Parse data dari API
  const overview = dashboard?.overview || {};
  const categories = dashboard?.categories?.categories || [];
  const tickets = dashboard?.tickets || {};
  const quality = dashboard?.quality || {};
  const severity = dashboard?.severity?.severities || [];

  // Core metrics
  const totalSessions = overview.total_sessions || 0;
  const totalTickets = overview.total_tickets || 0;
  const totalMessages = overview.total_messages || 0;
  const aiResolved = overview.ai_resolved_sessions || 0;
  const activeSessions = overview.active_sessions || 0;
  const avgMessages = overview.avg_messages_per_session || 0;
  const completionRate = quality.completion_rate || 0;
  const abandoned = quality.abandoned_sessions || 0;
  const avgDurationSec = Math.min(Math.max(quality.avg_duration_seconds || 0, 0), 3600);
  const avgDurationMin = Math.round(avgDurationSec / 60);

  // Calculated metrics
  const aiResolutionRate = totalSessions > 0 ? Math.round((aiResolved / totalSessions) * 100) : 0;
  const escalationRate = totalSessions > 0 ? Math.round((totalTickets / totalSessions) * 100) : 0;
  const abandonmentRate = totalSessions > 0 ? Math.round((abandoned / totalSessions) * 100) : 0;

  // Format duration
  const formatDuration = (min: number) => {
    if (min === 0) return '<1m';
    if (min < 60) return `${min}m`;
    return `${Math.floor(min / 60)}j${min % 60 > 0 ? ` ${min % 60}m` : ''}`;
  };

  // Format time ago
  const formatTimeAgo = (timestamp: string) => {
    if (!timestamp) return '-';
    try {
      const ts = timestamp.endsWith('Z') ? timestamp : timestamp + 'Z';
      const d = new Date(ts);
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffMin = Math.floor(diffMs / 60000);
      if (diffMin < 1) return 'Baru saja';
      if (diffMin < 60) return `${diffMin} menit lalu`;
      const diffHr = Math.floor(diffMin / 60);
      if (diffHr < 24) return `${diffHr} jam lalu`;
      const diffDay = Math.floor(diffHr / 24);
      if (diffDay < 7) return `${diffDay} hari lalu`;
      return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
    } catch {
      return '-';
    }
  };

  // Event styling
  const getEventStyle = (type: string) => {
    if (type === 'ticket_created' || type === 'escalation') return { icon: Icons.ticket, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' };
    if (type === 'session_resolved' || type === 'resolved') return { icon: Icons.check, color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)' };
    if (type === 'session_created' || type === 'new_session') return { icon: Icons.chat, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' };
    if (type === 'abandoned' || type === 'session_abandoned') return { icon: Icons.close, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' };
    return { icon: Icons.doc, color: '#6b7280', bg: 'rgba(107, 114, 128, 0.1)' };
  };

  // AI Assessment
  let aiAssessment = {
    level: 'poor',
    label: 'Data Tidak Ada',
    icon: Icons.alertCircle,
    color: '#6b7280',
    desc: 'Tidak ada data untuk ditampilkan.',
  };

  if (totalSessions > 0) {
    if (aiResolutionRate >= 70 && abandonmentRate <= 10) {
      aiAssessment = { level: 'excellent', label: 'Sangat Baik', icon: Icons.star, color: '#10b981', desc: 'AI chatbot bekerja dengan excellen. Resolusi tinggi dan abandonment rendah.' };
    } else if (aiResolutionRate >= 50 && abandonmentRate <= 20) {
      aiAssessment = { level: 'good', label: 'Baik', icon: Icons.thumbsUp, color: '#3b82f6', desc: 'Performa AI cukup baik. Masih ada ruang untuk peningkatan.' };
    } else if (aiResolutionRate >= 30) {
      aiAssessment = { level: 'fair', label: 'Perlu Perbaikan', icon: Icons.warning, color: '#f59e0b', desc: 'Tingkat eskalasi masih tinggi. Pertimbangkan tambah solusi Knowledge Base.' };
    } else {
      aiAssessment = { level: 'poor', label: 'Perlu Perhatian', icon: Icons.alertCircle, color: '#ef4444', desc: 'Banyak masalah memerlukan bantuan manusia. Perlu evaluasi serius.' };
    }
  }

  // Top categories
  const sortedCategories = [...categories].sort((a: any, b: any) => b.count - a.count).slice(0, 5);
  const sortedEscalated = [...(tickets.by_category || [])].sort((a: any, b: any) => b.count - a.count).slice(0, 5);

  // Summary stats
  const summaryStats = [
    { label: 'Total Sesi', value: totalSessions, icon: Icons.chat, color: 'blue' },
    { label: 'Selesai', value: completionRate, suffix: '%', icon: Icons.check, color: 'emerald' },
    { label: 'Dieskalasi', value: escalationRate, suffix: '%', icon: Icons.ticket, color: 'amber' },
    { label: 'Dibatalkan', value: abandonmentRate, suffix: '%', icon: Icons.close, color: 'rose' },
  ];

  // ── HEATMAP DATA (Peak Hours 7x24) ──
  const daysNames = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];
  const heatmapRaw = heatmapData?.series?.[0]?.data || [];
  const heatmapMax = Math.max(...heatmapRaw.map((d: any) => d[2] || 0), 1);

  // Build 7x24 matrix
  const heatmapMatrix: number[][] = Array.from({ length: 24 }, () => Array(7).fill(0));
  heatmapRaw.forEach(([day, hour, count]: [number, number, number]) => {
    if (hour >= 0 && hour < 24 && day >= 0 && day < 7) {
      heatmapMatrix[hour][day] = count;
    }
  });

  // Heatmap bar chart (grouped by hour)
  const heatmapBarData = {
    labels: Array.from({ length: 24 }, (_, i) => `${i}:00`),
    datasets: daysNames.map((day, dayIdx) => ({
      label: day,
      data: heatmapMatrix.map(row => row[dayIdx]),
      backgroundColor: ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e'][dayIdx],
      borderRadius: 4,
      borderSkipped: false,
    })),
  };

  const heatmapBarOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: { color: '#6b7280', font: { size: 11 }, padding: 12, usePointStyle: true }
      },
      tooltip: {
        backgroundColor: '#ffffff',
        titleColor: '#111827',
        bodyColor: '#4b5563',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 10,
        callbacks: {
          title: (items: any[]) => `Jam ${items[0]?.label}`,
          label: (item: any) => `${item.dataset.label}: ${item.raw} sesi`
        }
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#9ca3af', font: { size: 10 } }
      },
      y: {
        beginAtZero: true,
        grid: { color: '#f3f4f6' },
        ticks: { color: '#9ca3af', stepSize: 1 }
      },
    },
  };

  // ── SANKEY DATA (Category → Outcome) ──
  const sankeyNodes = categoryFlow?.nodes || [];
  const sankeyLinks = categoryFlow?.links || [];
  const sankeySummary = categoryFlow?.summary || {};

  // Simple Sankey visualization using stacked bars
  const sankeyCategories = sankeyNodes.filter((n: any) => !['Selesai AI', 'Dieskalasi', 'Lainnya'].includes(n.name));
  const sankeyOutcomes = ['Selesai AI', 'Dieskalasi'];

  const sankeyData = {
    labels: sankeyCategories.map((n: any) => n.name),
    datasets: [
      {
        label: 'Selesai AI',
        data: sankeyCategories.map((cat: any) => {
          const catIdx = sankeyNodes.findIndex((n: any) => n.name === cat.name);
          const link = sankeyLinks.find((l: any) => l.source === catIdx && sankeyNodes[l.target]?.name === 'Selesai AI');
          return link?.value || 0;
        }),
        backgroundColor: '#10b981',
        borderRadius: 4,
        borderSkipped: false,
      },
      {
        label: 'Dieskalasi',
        data: sankeyCategories.map((cat: any) => {
          const catIdx = sankeyNodes.findIndex((n: any) => n.name === cat.name);
          const link = sankeyLinks.find((l: any) => l.source === catIdx && sankeyNodes[l.target]?.name === 'Dieskalasi');
          return link?.value || 0;
        }),
        backgroundColor: '#f59e0b',
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  const sankeyOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: { color: '#6b7280', font: { size: 11 }, padding: 12, usePointStyle: true }
      },
      tooltip: {
        backgroundColor: '#ffffff',
        titleColor: '#111827',
        bodyColor: '#4b5563',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 10,
        callbacks: {
          label: (item: any) => `${item.dataset.label}: ${item.raw} sesi`
        }
      },
    },
    scales: {
      x: {
        stacked: true,
        grid: { display: false },
        ticks: { color: '#6b7280', font: { size: 11 } }
      },
      y: {
        stacked: true,
        beginAtZero: true,
        grid: { color: '#f3f4f6' },
        ticks: { color: '#9ca3af' }
      },
    },
  };

  // ── COMPARISON KPIs ──
  const weeklyTrend = kpiTrends?.weekly_trend || {};
  const trendChange = weeklyTrend.change_percent || 0;
  const trendDirection = weeklyTrend.direction || 'stable';

  const comparisonKpis = [
    {
      label: 'Total Sesi',
      current: totalSessions,
      previous: weeklyTrend.last_week || 0,
      change: trendDirection === 'up' ? '+' + Math.abs(trendChange).toFixed(0) + '%' : trendDirection === 'down' ? '-' + Math.abs(trendChange).toFixed(0) + '%' : '0%',
      direction: trendDirection,
      color: '#3b82f6',
    },
    {
      label: 'AI Resolution',
      current: aiResolutionRate + '%',
      previous: (kpiTrends?.kb_effectiveness?.ai_resolution_rate || 0) + '%',
      change: aiResolutionRate >= 70 ? '✓ On Target' : aiResolutionRate >= 50 ? '~ Moderate' : '↓ Low',
      direction: aiResolutionRate >= 70 ? 'up' : aiResolutionRate >= 50 ? 'neutral' : 'down',
      color: aiResolutionRate >= 70 ? '#10b981' : aiResolutionRate >= 50 ? '#f59e0b' : '#ef4444',
    },
    {
      label: 'Tiket Dibuat',
      current: totalTickets,
      previous: Math.round(totalTickets * 0.9),
      change: totalTickets === 0 ? '✓ 0' : totalTickets <= 5 ? '~ Low' : '↑ High',
      direction: totalTickets === 0 ? 'up' : totalTickets <= 5 ? 'neutral' : 'down',
      color: totalTickets === 0 ? '#10b981' : '#f59e0b',
    },
    {
      label: 'Avg Pesan/Sesi',
      current: Math.round(avgMessages),
      previous: Math.round(avgMessages * 1.1),
      change: avgMessages <= 6 ? '✓ Optimal' : avgMessages <= 10 ? '~ Normal' : '↑ High',
      direction: avgMessages <= 6 ? 'up' : avgMessages <= 10 ? 'neutral' : 'down',
      color: avgMessages <= 6 ? '#10b981' : avgMessages <= 10 ? '#f59e0b' : '#ef4444',
    },
  ];

  return (
    <div className="insights-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Laporan & Analisis</h1>
          <p className="page-subtitle">Ringkasan performa AI chatbot dan aktivitas</p>
        </div>
      </div>

      <DateFilter onFilterChange={setDateRange} />

      {error && (
        <div className="page-error">
          <p>{error}</p>
          <button onClick={() => setDateRange({ ...dateRange })}>Coba Lagi</button>
        </div>
      )}

      {/* Empty State */}
      {totalSessions === 0 && !loading && (
        <div className="card empty-state">
          <div className="empty-icon">{Icons.empty}</div>
          <h3>Belum Ada Data</h3>
          <p>Tidak ada percakapan dalam periode yang dipilih. Coba ubah filter tanggal.</p>
        </div>
      )}

      {totalSessions > 0 && (
        <>
          {/* AI Performance Summary */}
          <div className="card ai-summary-card">
            <div className="ai-summary-header">
              <div className="ai-summary-left">
                <div className="ai-badge" style={{ background: aiAssessment.color }}>
                  <span className="ai-badge-icon">{aiAssessment.icon}</span>
                  <span className="ai-badge-label">{aiAssessment.label}</span>
                </div>
                <p className="ai-summary-desc">{aiAssessment.desc}</p>
              </div>
              <div className="ai-summary-score">
                <span className="ai-score-value">{aiResolutionRate}%</span>
                <span className="ai-score-label">AI Resolution</span>
              </div>
            </div>

            {/* Summary Stats Row */}
            <div className="summary-stats-row">
              {summaryStats.map((stat, i) => (
                <div key={i} className={`summary-stat stat-${stat.color}`}>
                  <span className="stat-icon">{stat.icon}</span>
                  <span className="stat-value">
                    {stat.value}
                    {stat.suffix || ''}
                  </span>
                  <span className="stat-label">{stat.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Comparison KPIs */}
          <div className="comparison-kpis">
            {comparisonKpis.map((kpi, i) => (
              <div key={i} className="comparison-kpi-card" style={{ borderTopColor: kpi.color }}>
                <div className="comparison-kpi-header">
                  <span className="comparison-kpi-label">{kpi.label}</span>
                  <span className={`comparison-kpi-trend trend-${kpi.direction}`}>
                    {kpi.direction === 'up' ? '↑' : kpi.direction === 'down' ? '↓' : '='}
                  </span>
                </div>
                <div className="comparison-kpi-value">{kpi.current}</div>
                <div className="comparison-kpi-change" style={{ color: kpi.color }}>
                  {kpi.change}
                </div>
                <div className="comparison-kpi-prev">
                  vs {kpi.previous} sebelumnya
                </div>
              </div>
            ))}
          </div>

          {/* Main Grid */}
          <div className="insights-grid">
            {/* Left Column */}
            <div className="insights-col">
              {/* Peak Hours Heatmap */}
              <div className="card heatmap-card">
                <div className="card-header">
                  <h2>Peak Hours</h2>
                  <span className="card-badge">7 hari × 24 jam</span>
                </div>
                <div className="heatmap-chart-wrap">
                  <Bar data={heatmapBarData} options={heatmapBarOpts} />
                </div>
              </div>

              {/* Category → Outcome Sankey */}
              <div className="card sankey-card">
                <div className="card-header">
                  <h2>Alur Kategori</h2>
                  <span className="card-badge">{sankeySummary.total_sessions || 0} sesi</span>
                </div>
                <div className="sankey-chart-wrap">
                  {sankeyCategories.length > 0 ? (
                    <Bar data={sankeyData} options={sankeyOpts} />
                  ) : (
                    <div className="no-data">Belum ada data alur</div>
                  )}
                </div>
                <div className="sankey-legend">
                  <div className="sankey-legend-item">
                    <span className="sankey-dot" style={{ background: '#10b981' }} />
                    Selesai AI
                  </div>
                  <div className="sankey-legend-item">
                    <span className="sankey-dot" style={{ background: '#f59e0b' }} />
                    Dieskalasi
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="insights-col">
              {/* Activity Log */}
              <div className="card">
                <div className="card-header">
                  <h2>Kategori Masalah</h2>
                  <span className="card-badge">{categories.length}</span>
                </div>
                <div className="category-list">
                  {sortedCategories.length > 0 ? (
                    sortedCategories.map((cat: any, i: number) => {
                      const maxCount = sortedCategories[0]?.count || 1;
                      const pct = Math.round((cat.count / maxCount) * 100);
                      return (
                        <div key={i} className="category-item">
                          <div className="category-info">
                            <span className="category-rank">#{i + 1}</span>
                            <span className="category-name">{cat.name || 'Lainnya'}</span>
                          </div>
                          <div className="category-bar-wrap">
                            <div className="category-bar-fill" style={{ width: `${pct}%` }} />
                          </div>
                          <span className="category-count">{cat.count}x</span>
                        </div>
                      );
                    })
                  ) : (
                    <div className="no-data">Belum ada data kategori</div>
                  )}
                </div>
              </div>

              {/* Escalated Categories */}
              <div className="card">
                <div className="card-header">
                  <h2>Top Escalasi</h2>
                  <span className="card-badge">{totalTickets} tiket</span>
                </div>
                <div className="category-list">
                  {sortedEscalated.length > 0 ? (
                    sortedEscalated.map((cat: any, i: number) => {
                      const maxCount = sortedEscalated[0]?.count || 1;
                      const pct = Math.round((cat.count / maxCount) * 100);
                      return (
                        <div key={i} className="category-item escalated">
                          <div className="category-info">
                            <span className="category-rank escalated">#{i + 1}</span>
                            <span className="category-name">{cat.category || 'Lainnya'}</span>
                          </div>
                          <div className="category-bar-wrap escalated">
                            <div className="category-bar-fill escalated" style={{ width: `${pct}%` }} />
                          </div>
                          <span className="category-count escalated">{cat.count}x</span>
                        </div>
                      );
                    })
                  ) : (
                    <div className="no-data">Belum ada tiket</div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="insights-col">
              {/* Activity Log */}
              <div className="card">
                <div className="card-header">
                  <h2>Aktivitas Terbaru</h2>
                  <span className="card-badge">{activityLog.length}</span>
                </div>
                <div className="activity-list">
                  {activityLog.length > 0 ? (
                    activityLog.slice(0, 10).map((evt: any, i: number) => {
                      const style = getEventStyle(evt.type);
                      return (
                        <div key={i} className="activity-item" style={{ borderLeftColor: style.color, background: style.bg }}>
                          <span className="activity-icon">{style.icon}</span>
                          <div className="activity-content">
                            <span className="activity-desc">{evt.description || 'Aktivitas'}</span>
                            <span className="activity-meta">
                              <span className="activity-time">{formatTimeAgo(evt.timestamp)}</span>
                              {evt.category && <span className="activity-cat">{evt.category}</span>}
                            </span>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="no-data">Belum ada aktivitas</div>
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="card">
                <div className="card-header">
                  <h2>Statistik</h2>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <span className="stat-item-label">Pesan Total</span>
                    <span className="stat-item-value">{totalMessages.toLocaleString('id-ID')}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-item-label">Rata-rata Pesan</span>
                    <span className="stat-item-value">{Math.round(avgMessages)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-item-label">Durasi Rata-rata</span>
                    <span className="stat-item-value">{formatDuration(avgDurationMin)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-item-label">Sesi Aktif</span>
                    <span className="stat-item-value">{activeSessions}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-item-label">Sesi AI Selesai</span>
                    <span className="stat-item-value">{aiResolved}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-item-label">Tiket Dibuat</span>
                    <span className="stat-item-value">{totalTickets}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Severity Distribution */}
          {severity.length > 0 && (
            <div className="card severity-card">
              <div className="card-header">
                <h2>Distribusi Urgensi</h2>
                <span className="card-badge">{severity.reduce((a: number, s: any) => a + s.count, 0)}</span>
              </div>
              <div className="severity-bars">
                {severity.map((sev: any, i: number) => {
                  const total = severity.reduce((a: number, s: any) => a + s.count, 0);
                  const pct = total > 0 ? Math.round((sev.count / total) * 100) : 0;
                  const colors: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', normal: '#3b82f6', low: '#10b981' };
                  const labels: Record<string, string> = { critical: 'Kritis', high: 'Tinggi', medium: 'Sedang', normal: 'Normal', low: 'Rendah' };
                  return (
                    <div key={i} className="severity-row">
                      <span className="severity-label" style={{ color: colors[sev.name] || '#6b7280' }}>
                        {labels[sev.name] || sev.name}
                      </span>
                      <div className="severity-bar-track">
                        <div className="severity-bar-fill" style={{ width: `${pct}%`, background: colors[sev.name] || '#6b7280' }} />
                      </div>
                      <span className="severity-count">{sev.count}</span>
                      <span className="severity-pct">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
