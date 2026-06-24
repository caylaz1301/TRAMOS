import React, { useState, useEffect } from 'react';
import { analyticsService } from '../api.js';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import DateFilter from '../components/DateFilter';
import './PerformancePage.css';

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Tooltip, Legend);

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({ startDate: null as string | null, endDate: null as string | null });

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        setError(null);
        const dashData = await analyticsService.getDashboard(dateRange.startDate, dateRange.endDate).catch(() => null);
        if (!cancelled) {
          setDashboard(dashData);
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

  // RESOLUTION BREAKDOWN
  const resolutionData = {
    aiSolved: aiResolved,
    tickets: totalTickets,
    abandoned: abandoned,
    active: activeSessions,
    total: totalSessions,
  };

  const donutData = {
    labels: ['AI Selesai', 'Tiket', 'Batal', 'Aktif'],
    datasets: [
      {
        data: [resolutionData.aiSolved, resolutionData.tickets, resolutionData.abandoned, resolutionData.active],
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#3b82f6'],
        borderColor: '#ffffff',
        borderWidth: 3,
      },
    ],
  };

  const donutOpts = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: { color: '#9ca3af', font: { size: 11, weight: 500 }, padding: 10, usePointStyle: true, pointStyleWidth: 8 },
      },
      tooltip: {
        ...CHART_TOOLTIP,
        callbacks: {
          label: function (context: any) {
            const value = context.raw as number;
            const total = resolutionData.total || 1;
            const pct = Math.round((value / total) * 100);
            return `${context.label}: ${value} (${pct}%)`;
          },
        },
      },
    },
  };

  // SEVERITY DISTRIBUTION
  const sevMap: Record<string, string> = { critical: 'Kritis', high: 'Tinggi', medium: 'Sedang', normal: 'Normal', low: 'Rendah' };
  const sevColors: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', normal: '#3b82f6', low: '#10b981' };

  const sevBarData = {
    labels: severity.map((s: any) => sevMap[s.name] || s.name || 'Lain'),
    datasets: [
      {
        data: severity.map((s: any) => s.count),
        backgroundColor: severity.map((s: any) => sevColors[s.name] || '#5a6d84'),
        borderRadius: 6,
        borderSkipped: false,
        barThickness: 28,
      },
    ],
  };

  const sevBarOpts = {
    indexAxis: 'y' as const,
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: CHART_TOOLTIP },
    scales: {
      x: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { color: '#9ca3af', stepSize: 1 } },
      y: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 12, weight: 500 } } },
    },
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
            {/* Left: Score + Donut */}
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

              {/* Resolution Donut */}
              <div className="card">
                <div className="card-header">
                  <h2>Breakdown Sesi</h2>
                  <span className="card-badge">{totalSessions} total</span>
                </div>
                <div className="donut-wrap">
                  <Doughnut data={donutData} options={donutOpts} />
                </div>
                <div className="breakdown-legend">
                  <div className="legend-item">
                    <span className="dot green" />
                    AI Selesai: {resolutionData.aiSolved}
                  </div>
                  <div className="legend-item">
                    <span className="dot amber" />
                    Tiket: {resolutionData.tickets}
                  </div>
                  <div className="legend-item">
                    <span className="dot rose" />
                    Batal: {resolutionData.abandoned}
                  </div>
                  <div className="legend-item">
                    <span className="dot blue" />
                    Aktif: {resolutionData.active}
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Severity + Quality Stats */}
            <div className="perf-right">
              {/* Severity */}
              <div className="card">
                <div className="card-header">
                  <h2>Distribusi Urgensi</h2>
                  <span className="card-badge">{severity.reduce((a: number, s: any) => a + s.count, 0)}</span>
                </div>
                <div className="sev-chart-wrap">
                  {severity.length > 0 ? (
                    <Bar data={sevBarData} options={sevBarOpts} />
                  ) : (
                    <div className="no-data">Belum ada data urgensi</div>
                  )}
                </div>
              </div>

              {/* Quality Stats */}
              <div className="card quality-card">
                <div className="card-header">
                  <h2>Statistik Kualitas</h2>
                </div>
                <div className="quality-grid">
                  <div className="quality-item">
                    <div className="quality-label">Durasi Rata-rata</div>
                    <div className="quality-value">
                      {avgDurationMin === 0 ? '<1m' : avgDurationMin < 60 ? `${avgDurationMin}m` : `${Math.floor(avgDurationMin / 60)}j ${avgDurationMin % 60}m`}
                    </div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-label">Pesan per Sesi</div>
                    <div className="quality-value">{Math.round(avgMessages)}</div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-label">Total Pesan</div>
                    <div className="quality-value">{totalMessages.toLocaleString('id-ID')}</div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-label">Completion Rate</div>
                    <div className="quality-value">{Math.round(completionRate)}%</div>
                  </div>
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

          {/* Benchmark Comparison */}
          <div className="card benchmark-card">
            <div className="card-header">
              <h2>Benchmark Industri</h2>
              <span className="card-badge">Perbandingan</span>
            </div>
            <div className="benchmark-list">
              {benchmarks.map((b, i) => {
                const isGood = b.inverse ? b.current <= b.target : b.current >= b.target;
                const progress = b.inverse
                  ? Math.max(0, 100 - ((b.current - b.target) / b.target) * 100)
                  : Math.min(100, (b.current / b.target) * 100);
                return (
                  <div key={i} className="benchmark-row">
                    <div className="benchmark-label">{b.label}</div>
                    <div className="benchmark-values">
                      <span className={`benchmark-current ${isGood ? 'good' : 'warn'}`}>
                        {b.current}
                        {b.unit}
                      </span>
                      <span className="benchmark-sep">/</span>
                      <span className="benchmark-target">
                        {b.target}
                        {b.unit}
                      </span>
                    </div>
                    <div className="benchmark-bar">
                      <div className={`benchmark-fill ${isGood ? 'fill-good' : 'fill-warn'}`} style={{ width: `${Math.min(100, progress)}%` }} />
                    </div>
                    <span className={`benchmark-status ${isGood ? 'status-good' : 'status-warn'}`}>{isGood ? Icons.check : Icons.warning}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
