import React, { useState, useEffect } from 'react';
import { analyticsService } from '../api.js';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, RadarController, RadialLinearScale, Tooltip, Legend } from 'chart.js';
import { Bar, Radar } from 'react-chartjs-2';
import DateFilter from '../components/DateFilter';
import './PerformancePage.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, RadarController, RadialLinearScale, Tooltip, Legend);

const CHART_TOOLTIP = {
  backgroundColor: '#ffffff',
  titleColor: '#111827',
  bodyColor: '#4b5563',
  borderColor: '#e5e7eb',
  borderWidth: 1,
  cornerRadius: 8,
  padding: 10,
};

// SVG Icons
const Icons = {
  robot: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" y1="16" x2="8" y2="16" />
      <line x1="16" y1="16" x2="16" y2="16" />
    </svg>
  ),
  chat: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  ticket: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M15 5v2" />
      <path d="M15 11v2" />
      <path d="M15 17v2" />
      <rect x="3" y="3" width="18" height="18" rx="2" />
    </svg>
  ),
  chart: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
  star: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  ),
  thumbsUp: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
    </svg>
  ),
  warning: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  check: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  empty: (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <line x1="9" y1="9" x2="15" y2="15" />
      <line x1="15" y1="9" x2="9" y2="15" />
    </svg>
  ),
};

export default function PerformancePage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [funnelData, setFunnelData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({ startDate: null as string | null, endDate: null as string | null });

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        setError(null);
        const [dashData, funnel] = await Promise.all([
          analyticsService.getDashboard(dateRange.startDate, dateRange.endDate).catch(() => null),
          analyticsService.getFunnel().catch(() => null),
        ]);
        if (!cancelled) {
          setDashboard(dashData);
          setFunnelData(funnel);
        }
      } catch {
        if (!cancelled) {
          setError('Gagal memuat data performa');
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

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Menganalisis performa AI...</p>
      </div>
    );
  }

  // Parse data dari API
  const overview = dashboard?.overview || {};
  const quality = dashboard?.quality || {};
  const severity = dashboard?.severity?.severities || [];
  const tickets = dashboard?.tickets || {};

  // Core metrics dari backend
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

  // PERFORMANCE SCORE CALCULATION
  const aiResolutionRate = totalSessions > 0 ? (aiResolved / totalSessions) * 100 : 0;
  const abandonmentRate = totalSessions > 0 ? (abandoned / totalSessions) * 100 : 0;
  const messageEfficiency = Math.max(0, 100 - (avgMessages - 4) * 10);

  const performanceScore = Math.round(
    (aiResolutionRate * 0.40) +
    (completionRate * 0.30) +
    (Math.max(0, 100 - abandonmentRate) * 0.15) +
    (messageEfficiency * 0.15)
  );

  const scoreColor = performanceScore >= 70 ? 'emerald' : performanceScore >= 50 ? 'amber' : 'rose';
  const scoreLabel = performanceScore >= 70 ? 'Baik' : performanceScore >= 50 ? 'Cukup' : 'Perlu Perbaikan';
  const scoreIcon = performanceScore >= 70 ? Icons.star : performanceScore >= 50 ? Icons.thumbsUp : Icons.warning;
  const scoreGrade = performanceScore >= 85 ? 'A' : performanceScore >= 70 ? 'B' : performanceScore >= 55 ? 'C' : performanceScore >= 40 ? 'D' : 'F';

  // KPI CARDS
  const kpis = [
    {
      label: 'AI Resolution',
      value: `${Math.round(aiResolutionRate)}%`,
      subValue: `${aiResolved} / ${totalSessions} sesi`,
      icon: Icons.robot,
      color: aiResolutionRate >= 70 ? 'emerald' : aiResolutionRate >= 40 ? 'amber' : 'rose',
      trend: aiResolutionRate >= 50 ? 'up' : 'down',
    },
    {
      label: 'Sesi Aktif',
      value: activeSessions,
      subValue: `dari ${totalSessions} total`,
      icon: Icons.chat,
      color: 'blue',
      trend: 'neutral',
    },
    {
      label: 'Dieskalasi',
      value: totalTickets,
      subValue: totalSessions > 0 ? `${Math.round((totalTickets / totalSessions) * 100)}%` : '0%',
      icon: Icons.ticket,
      color: totalTickets === 0 ? 'emerald' : 'amber',
      trend: totalTickets === 0 ? 'up' : 'down',
    },
    {
      label: 'Tiket per Sesi',
      value: totalSessions > 0 ? (totalTickets / totalSessions).toFixed(1) : '0.0',
      subValue: `${totalTickets} tiket`,
      icon: Icons.chart,
      color: 'violet',
      trend: 'neutral',
    },
  ];

  // FUNNEL DATA from API
  const funnelChartData = funnelData?.series?.[0]?.data || [];
  const funnelLabels = funnelChartData.map((d: any) => d.name);
  const funnelValues = funnelChartData.map((d: any) => d.value);

  // Convert funnel to horizontal bar (visual representation)
  const maxFunnelValue = Math.max(...funnelValues, 1);
  const funnelBarData = {
    labels: funnelLabels,
    datasets: [
      {
        data: funnelValues,
        backgroundColor: funnelValues.map((_: any, i: number) => {
          const colors = ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'];
          return colors[i % colors.length];
        }),
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  };

  const funnelBarOpts = {
    indexAxis: 'y' as const,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        ...CHART_TOOLTIP,
        callbacks: {
          afterBody: function (tooltipItems: any[]) {
            const idx = tooltipItems[0].dataIndex;
            const val = funnelValues[idx];
            const pct = maxFunnelValue > 0 ? Math.round((val / maxFunnelValue) * 100) : 0;
            return [`${val} sesi (${pct}%)`];
          },
        },
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: { color: '#f3f4f6' },
        ticks: { color: '#9ca3af' }
      },
      y: {
        grid: { display: false },
        ticks: { color: '#6b7280', font: { size: 12, weight: 500 } }
      },
    },
  };

  // RADAR CHART for benchmark comparison
  const radarLabels = ['AI Resolution', 'Completion', 'Response Time', 'Abandonment Rate', 'Message Efficiency'];
  const radarCurrent = [
    aiResolutionRate,
    completionRate,
    Math.max(0, 100 - (avgDurationSec / 60) * 10), // Response time score
    Math.max(0, 100 - abandonmentRate),
    messageEfficiency
  ];
  const radarTarget = [70, 80, 80, 90, 70]; // Target values

  const radarData = {
    labels: radarLabels,
    datasets: [
      {
        label: 'Current',
        data: radarCurrent,
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: '#3b82f6',
        borderWidth: 2,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
      },
      {
        label: 'Target',
        data: radarTarget,
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderColor: '#10b981',
        borderWidth: 2,
        borderDash: [5, 5],
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 3,
      },
    ],
  };

  const radarOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: { color: '#6b7280', font: { size: 11 }, padding: 16, usePointStyle: true }
      },
      tooltip: {
        ...CHART_TOOLTIP,
        callbacks: {
          label: function (context: any) {
            return `${context.dataset.label}: ${Math.round(context.raw)}%`;
          },
        },
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        grid: { color: 'rgba(0,0,0,0.05)' },
        angleLines: { color: 'rgba(0,0,0,0.05)' },
        pointLabels: {
          color: '#6b7280',
          font: { size: 11, weight: 500 }
        },
        ticks: {
          color: '#9ca3af',
          backdropColor: 'transparent',
          stepSize: 25
        }
      },
    },
  };

  // RESOLUTION BREAKDOWN
  const resolutionData = {
    aiSolved: aiResolved,
    tickets: totalTickets,
    abandoned: abandoned,
    active: activeSessions,
    total: totalSessions,
  };

  // RECOMMENDATIONS
  const recommendations: Array<{ priority: string; title: string; desc: string }> = [];

  if (totalSessions > 0) {
    if (aiResolutionRate < 50) {
      recommendations.push({
        priority: 'high',
        title: 'Tingkatkan Resolusi AI',
        desc: `Hanya ${Math.round(aiResolutionRate)}% sesi diselesaikan AI. Tambahkan solusi Knowledge Base untuk kategori masalah yang sering muncul.`,
      });
    }
    if (abandoned > totalSessions * 0.1) {
      recommendations.push({
        priority: 'high',
        title: 'Kurangi Sesi Dibatalkan',
        desc: `${abandoned} sesi (${Math.round(abandonmentRate)}%) ditinggalkan sebelum selesai. Perbaiki alur awal percakapan.`,
      });
    }
    if (avgMessages > 8) {
      recommendations.push({
        priority: 'medium',
        title: 'Optimasi Panjang Percakapan',
        desc: `Rata-rata ${Math.round(avgMessages)} pesan per sesi. Ideal kurang dari 6 pesan. Simplifikasi alur dan jawaban.`,
      });
    }
    if (totalTickets > 0 && tickets.by_category?.[0]) {
      recommendations.push({
        priority: 'medium',
        title: `Fokus Kategori: ${tickets.by_category[0].category}`,
        desc: `${tickets.by_category[0].count} tiket berasal dari kategori ini. Pertimbangkan tambah solusi Knowledge Base spesifik.`,
      });
    }
    if (aiResolutionRate >= 70 && abandoned <= totalSessions * 0.05) {
      recommendations.push({
        priority: 'success',
        title: 'Performa Excellent',
        desc: 'AI chatbot bekerja dengan sangat baik. Lanjutkan monitoring dan update Knowledge Base secara berkala.',
      });
    }
  }

  // BENCHMARKS
  const benchmarks = [
    { label: 'AI Resolution', current: Math.round(aiResolutionRate), target: 70, unit: '%' },
    { label: 'Completion', current: Math.round(completionRate), target: 80, unit: '%' },
    { label: 'Abandonment', current: Math.round(abandonmentRate), target: 10, unit: '%', inverse: true },
    { label: 'Avg Messages', current: Math.round(avgMessages), target: 5, unit: '', inverse: true },
  ];

  return (
    <div className="perf-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Performa AI</h1>
          <p className="page-subtitle">Evaluasi efektivitas chatbot dalam menangani laporan</p>
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
          <p>Tidak ada percakapan dalam periode yang dipilih.</p>
        </div>
      )}

      {totalSessions > 0 && (
        <>
          {/* KPI Cards Row */}
          <div className="kpi-grid-4">
            {kpis.map((kpi, i) => (
              <div key={i} className={`kpi-card kpi-${kpi.color}`}>
                <div className="kpi-header">
                  <span className="kpi-icon">{kpi.icon}</span>
                  <span className={`kpi-trend trend-${kpi.trend}`}>
                    {kpi.trend === 'up' ? '+' : kpi.trend === 'down' ? '-' : '='}
                  </span>
                </div>
                <div className="kpi-value">{kpi.value}</div>
                <div className="kpi-label">{kpi.label}</div>
                <div className="kpi-sub">{kpi.subValue}</div>
              </div>
            ))}
          </div>

          {/* Main Content Grid */}
          <div className="perf-main-grid">
            {/* Left: Score + Funnel */}
            <div className="perf-left">
              {/* Score Card */}
              <div className="card score-card">
                <div className="score-visual">
                  <div className={`score-ring score-${scoreColor}`}>
                    <svg viewBox="0 0 120 120">
                      <circle className="ring-bg" cx="60" cy="60" r="50" />
                      <circle className="ring-fill" cx="60" cy="60" r="50" strokeDasharray={`${(performanceScore / 100) * 314} 314`} />
                    </svg>
                    <div className="score-center">
                      <span className="score-icon">{scoreIcon}</span>
                      <span className="score-num">{performanceScore}</span>
                    </div>
                  </div>
                </div>
                <div className="score-details">
                  <h3>Skor Performa AI</h3>
                  <span className={`score-badge badge-${scoreColor}`}>{scoreLabel}</span>
                  <div className="score-grade">Grade: {scoreGrade}</div>
                  <div className="score-formula">
                    <span className="formula-label">Komponen:</span>
                    <span className="formula-item">AI: {Math.round(aiResolutionRate * 0.4)}</span>
                    <span className="formula-item">Selesai: {Math.round(completionRate * 0.3)}</span>
                    <span className="formula-item">Batal: {Math.round(Math.max(0, 100 - abandonmentRate) * 0.15)}</span>
                    <span className="formula-item">Pesan: {Math.round(messageEfficiency * 0.15)}</span>
                  </div>
                </div>
              </div>

              {/* Resolution Funnel */}
              <div className="card">
                <div className="card-header">
                  <h2>Funnel Resolusi</h2>
                  <span className="card-badge">{totalSessions} sesi</span>
                </div>
                <div className="funnel-chart-wrap">
                  {funnelLabels.length > 0 ? (
                    <Bar data={funnelBarData} options={funnelBarOpts} />
                  ) : (
                    <div className="no-data">Belum ada data funnel</div>
                  )}
                </div>
                <div className="funnel-summary">
                  <div className="funnel-stat">
                    <span className="funnel-stat-value">{aiResolved}</span>
                    <span className="funnel-stat-label">Diselesaikan AI</span>
                  </div>
                  <div className="funnel-stat">
                    <span className="funnel-stat-value">{totalTickets}</span>
                    <span className="funnel-stat-label">Dieskalasi</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Session Breakdown */}
            <div className="perf-right">
              {/* Session Breakdown */}
              <div className="card">
                <div className="card-header">
                  <h2>Session Breakdown</h2>
                </div>
                <div className="breakdown-list">
                  <div className="breakdown-item">
                    <div className="breakdown-left">
                      <span className="breakdown-dot green" />
                      <span className="breakdown-label">AI Selesai</span>
                    </div>
                    <span className="breakdown-value">{resolutionData.aiSolved}</span>
                    <span className="breakdown-pct">{totalSessions > 0 ? Math.round((resolutionData.aiSolved / totalSessions) * 100) : 0}%</span>
                  </div>
                  <div className="breakdown-item">
                    <div className="breakdown-left">
                      <span className="breakdown-dot amber" />
                      <span className="breakdown-label">Dieskalasi</span>
                    </div>
                    <span className="breakdown-value">{resolutionData.tickets}</span>
                    <span className="breakdown-pct">{totalSessions > 0 ? Math.round((resolutionData.tickets / totalSessions) * 100) : 0}%</span>
                  </div>
                  <div className="breakdown-item">
                    <div className="breakdown-left">
                      <span className="breakdown-dot rose" />
                      <span className="breakdown-label">Dibatalkan</span>
                    </div>
                    <span className="breakdown-value">{resolutionData.abandoned}</span>
                    <span className="breakdown-pct">{totalSessions > 0 ? Math.round((resolutionData.abandoned / totalSessions) * 100) : 0}%</span>
                  </div>
                  <div className="breakdown-item">
                    <div className="breakdown-left">
                      <span className="breakdown-dot blue" />
                      <span className="breakdown-label">Aktif</span>
                    </div>
                    <span className="breakdown-value">{resolutionData.active}</span>
                    <span className="breakdown-pct">{totalSessions > 0 ? Math.round((resolutionData.active / totalSessions) * 100) : 0}%</span>
                  </div>
                </div>
              </div>

              {/* Radar Chart - Benchmark */}
              <div className="card radar-card">
                <div className="card-header">
                  <h2>Benchmark vs Target</h2>
                  <span className="card-badge">Radar</span>
                </div>
                <div className="radar-chart-wrap">
                  <Radar data={radarData} options={radarOpts} />
                </div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div className="card recommendations-card">
            <div className="card-header">
              <h2>Saran Perbaikan</h2>
              <span className="card-badge">{recommendations.length}</span>
            </div>
            <div className="recommendations-list">
              {recommendations.length > 0 ? (
                recommendations.map((rec, i) => (
                  <div key={i} className={`recommendation-item rec-${rec.priority}`}>
                    <div className="rec-content">
                      <div className="rec-title">{rec.title}</div>
                      <div className="rec-desc">{rec.desc}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-recs">
                  <p>Tidak ada saran kritis saat ini. AI berjalan dengan baik.</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
