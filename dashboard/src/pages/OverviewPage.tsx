import React, { useState, useEffect, useMemo } from 'react';
import { analyticsService } from '../api.js';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';
import DateFilter from '../components/DateFilter';
import './OverviewPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler
);

const CHART_TOOLTIP = {
  backgroundColor: '#ffffff',
  titleColor: '#111827',
  bodyColor: '#4b5563',
  borderColor: '#e5e7eb',
  borderWidth: 1,
  cornerRadius: 8,
  padding: 10,
  titleFont: { weight: 600 },
};

// Aggregate hourly timeline data to daily
function aggregateToDaily(timeline: any[]) {
  const dailyMap = new Map<string, { date: string; sessions: number; tickets: number }>();

  timeline.forEach((point) => {
    const dateStr = point.timestamp || point.date;
    if (!dateStr) return;

    const d = new Date(dateStr);
    const dayKey = d.toISOString().split('T')[0];

    const existing = dailyMap.get(dayKey) || { date: dayKey, sessions: 0, tickets: 0 };
    existing.sessions += point.sessions || 0;
    existing.tickets += point.tickets || 0;
    dailyMap.set(dayKey, existing);
  });

  return Array.from(dailyMap.values()).sort((a, b) => a.date.localeCompare(b.date));
}

export default function OverviewPage() {
  const [data, setData] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [liveSessions, setLiveSessions] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({ startDate: null as string | null, endDate: null as string | null });

  const fetchData = async () => {
    try {
      setError(null);
      const [dashData, timelineData, liveData] = await Promise.all([
        analyticsService.getDashboard(dateRange.startDate, dateRange.endDate),
        analyticsService.getTimeline(dateRange.startDate, dateRange.endDate).catch(() => null),
        analyticsService.getLiveSessions().catch(() => null),
      ]);
      setData(dashData);
      setLiveSessions(liveData);
      if (timelineData?.timeline) {
        setTimeline(timelineData.timeline);
      } else {
        setTimeline([]);
      }
    } catch (err) {
      setError('Gagal memuat data. Pastikan server backend aktif.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [dateRange]);

  const dailyTimeline = useMemo(() => aggregateToDaily(timeline), [timeline]);

  if (loading && !data) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Memuat ringkasan...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page-error">
        <p>{error || 'Gagal memuat data'}</p>
        <button onClick={fetchData}>Coba Lagi</button>
      </div>
    );
  }

  // Parse data dari API
  const overview = data?.overview || {};
  const categories = data?.categories?.categories || [];
  const quality = data?.quality || {};
  const tickets = data?.tickets || {};
  const severity = data?.severity?.severities || [];
  const sessions = data?.recent_sessions?.sessions || [];

  // KPI Metrics
  const totalSessions = overview.total_sessions || 0;
  const totalTickets = overview.total_tickets || 0;
  const totalMessages = overview.total_messages || 0;
  const activeSessions = overview.active_sessions || 0;
  const aiResolved = overview.ai_resolved_sessions || 0;
  const successRate = overview.success_rate || 0;
  const avgMessages = overview.avg_messages_per_session || 0;

  // Live Sessions
  const liveCount = liveSessions?.active_count || 0;

  // Donut: Top 3 categories + "Lainnya"
  const sortedCategories = [...categories].sort((a: any, b: any) => b.count - a.count);
  const top3Categories = sortedCategories.slice(0, 3);
  const otherCount = sortedCategories.slice(3).reduce((sum: number, c: any) => sum + c.count, 0);
  const donutCategories = otherCount > 0 ? [...top3Categories, { name: 'Lainnya', count: otherCount }] : top3Categories;

  // Totals untuk validasi
  const totalFromDonut = donutCategories.reduce((sum: number, c: any) => sum + c.count, 0);
  const totalFromSeverity = severity.reduce((sum: number, s: any) => sum + s.count, 0);
  const ticketByCategory = tickets.by_category || [];
  const totalTicketCount = tickets.total_tickets || 0;

  // KPI Cards
  const kpis = [
    {
      label: 'Total Percakapan',
      value: totalSessions,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      ),
      color: 'blue',
      desc: activeSessions > 0 ? `${activeSessions} sesi aktif` : 'Tidak ada sesi aktif',
    },
    {
      label: 'Diselesaikan AI',
      value: `${Math.round(successRate)}%`,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M8 14s1.5 2 4 2 4-2 4-2" />
          <line x1="9" y1="9" x2="9.01" y2="9" />
          <line x1="15" y1="9" x2="15.01" y2="9" />
        </svg>
      ),
      color: 'emerald',
      desc: `${aiResolved} sesi tanpa tiket dibuat`,
    },
    {
      label: 'Tiket Dibuat',
      value: totalTickets,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M15 5v2" />
          <path d="M15 11v2" />
          <path d="M15 17v2" />
          <rect x="3" y="3" width="18" height="18" rx="2" />
        </svg>
      ),
      color: 'amber',
      desc: totalSessions > 0 ? `${Math.round((totalTickets / totalSessions) * 100)}% dari total` : '0%',
    },
    {
      label: 'Total Pesan',
      value: totalMessages.toLocaleString('id-ID'),
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      ),
      color: 'violet',
      desc: avgMessages > 0 ? `~${Math.round(avgMessages)} pesan/sesi` : '0 pesan/sesi',
    },
  ];

  // Category colors
  const catColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#f97316', '#06b6d4', '#ec4899', '#14b8a6', '#84cc16'];

  // Category Donut - Top 3 + Lainnya
  const donutData = {
    labels: donutCategories.map((c: any) => c.name || 'Lainnya'),
    datasets: [
      {
        data: donutCategories.map((c: any) => c.count),
        backgroundColor: donutCategories.map((_: any, i: number) => catColors[i % catColors.length]),
        borderColor: '#ffffff',
        borderWidth: 3,
        hoverBorderWidth: 0,
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
        labels: { color: '#6b7280', font: { size: 11 }, padding: 12, usePointStyle: true, pointStyleWidth: 8 },
      },
      tooltip: {
        ...CHART_TOOLTIP,
        callbacks: {
          label: function (context: any) {
            const value = context.raw as number;
            const total = (context.dataset.data as number[]).reduce((a, b) => a + b, 0);
            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
            return `${context.label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  };

  // Severity Bar
  const sevColorMap: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', normal: '#3b82f6', low: '#10b981' };
  const sevLabels: Record<string, string> = { critical: 'Kritis', high: 'Tinggi', medium: 'Sedang', normal: 'Normal', low: 'Rendah' };

  const sevBarData = {
    labels: severity.map((s: any) => sevLabels[s.name] || s.name || 'Lain'),
    datasets: [
      {
        data: severity.map((s: any) => s.count),
        backgroundColor: severity.map((s: any) => sevColorMap[s.name] || '#6b7280'),
        borderRadius: 6,
        borderSkipped: false,
        barThickness: 32,
      },
    ],
  };

  const sevBarOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: CHART_TOOLTIP },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 12 } } },
      y: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { color: '#9ca3af', stepSize: 1 } },
    },
  };

  // Timeline Chart
  const timelineLabels = dailyTimeline.map((t) => {
    try {
      const d = new Date(t.date);
      return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
    } catch {
      return t.date || 'N/A';
    }
  });

  const trendChartData = {
    labels: timelineLabels,
    datasets: [
      {
        label: 'Percakapan',
        data: dailyTimeline.map((t) => t.sessions),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#3b82f6',
      },
      {
        label: 'Tiket',
        data: dailyTimeline.map((t) => t.tickets),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#f59e0b',
      },
    ],
  };

  const trendOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' as const, align: 'end' as const, labels: { color: '#6b7280', font: { size: 11 }, usePointStyle: true } },
      tooltip: {
        ...CHART_TOOLTIP,
        callbacks: {
          afterBody: function (tooltipItems: any[]) {
            const idx = tooltipItems[0].dataIndex;
            const day = dailyTimeline[idx];
            if (day) {
              const total = day.sessions + day.tickets;
              const resolved = total - day.tickets;
              return [`AI Terselesaikan: ${resolved}`, `Total Aktif: ${total}`];
            }
            return [];
          },
        },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 10 } } },
      y: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { color: '#9ca3af', stepSize: 1 } },
    },
    interaction: { mode: 'index' as const, intersect: false },
  };

  // Status helper
  const getStatusType = (state: string) => {
    if (['closed', 'resolved'].includes(state)) return 'success';
    if (['creating_ticket', 'confirming_details'].includes(state)) return 'warning';
    if (['greeting', 'collecting_name', 'collecting_problem'].includes(state)) return 'info';
    return 'default';
  };

  const getStatusLabel = (state: string) => {
    const map: Record<string, string> = {
      greeting: 'Baru Mulai',
      collecting_name: 'Input Nama',
      collecting_problem: 'Input Masalah',
      asking_solution_worked: 'Cek Solusi',
      collecting_unit: 'Input Unit',
      collecting_location: 'Input Lokasi',
      collecting_time: 'Input Waktu',
      confirming_details: 'Konfirmasi',
      creating_ticket: 'Buat Tiket',
      closed: 'Selesai',
      resolved: 'Selesai',
    };
    return map[state] || state || '-';
  };

  // Time formatter
  const formatTime = (isoStr: string) => {
    if (!isoStr) return '-';
    try {
      const ts = isoStr.endsWith('Z') ? isoStr : isoStr + 'Z';
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

  return (
    <div className="overview-page">
      <div className="page-header">
        <div>
          <h1>Ringkasan</h1>
          <p className="page-subtitle">Statistik percakapan dan tiket support</p>
        </div>
        <div className="header-live">
          <span className="live-dot" />
          <span>Auto refresh 30 detik</span>
        </div>
      </div>

      <DateFilter onFilterChange={setDateRange} />

      {error && (
        <div className="page-error">
          <p>{error}</p>
          <button onClick={fetchData}>Coba Lagi</button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="kpi-grid">
        {kpis.map((kpi, i) => (
          <div key={i} className={`kpi-card kpi-${kpi.color}`}>
            <div className="kpi-icon-wrap">{kpi.icon}</div>
            <div className="kpi-body">
              <div className="kpi-label">{kpi.label}</div>
              <div className="kpi-value">{kpi.value}</div>
              <div className="kpi-desc">{kpi.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Trend Chart */}
      {dailyTimeline.length > 1 && (
        <div className="card trend-chart-card">
          <div className="card-header">
            <h2>Tren Aktivitas Harian</h2>
            <span className="card-badge card-badge-info">{dailyTimeline.length} hari</span>
          </div>
          <div className="trend-chart-wrap">
            <Line data={trendChartData} options={trendOpts} />
          </div>
          <div className="chart-summary">
            <span>
              Total: <strong>{dailyTimeline.reduce((s, t) => s + t.sessions, 0)}</strong> percakapan,{' '}
              <strong>{dailyTimeline.reduce((s, t) => s + t.tickets, 0)}</strong> tiket
            </span>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="overview-charts">
        {/* Category Donut - Top 3 + Lainnya */}
        <div className="card">
          <div className="card-header">
            <h2>Kategori Masalah</h2>
            <span className="card-badge">Top {donutCategories.length}</span>
          </div>
          <div className="chart-donut-wrap">
            {donutCategories.length > 0 ? (
              <Doughnut data={donutData} options={donutOpts} />
            ) : (
              <div className="no-data">Belum ada data</div>
            )}
          </div>
          <div className="chart-summary">
            <span>
              Total: <strong>{totalFromDonut}</strong> masalah terdeteksi
            </span>
          </div>
        </div>

        {/* Severity Bar */}
        <div className="card">
          <div className="card-header">
            <h2>Tingkat Urgensi</h2>
            <span className="card-badge">{totalFromSeverity} laporan</span>
          </div>
          <div className="chart-bar-wrap">
            {severity.length > 0 ? (
              <Bar data={sevBarData} options={sevBarOpts} />
            ) : (
              <div className="no-data">Belum ada data</div>
            )}
          </div>
        </div>

        {/* Sesi Aktif Live Card */}
        <div className="card sesi-aktif-card">
          <div className="card-header">
            <h2>Sesi Aktif</h2>
            <span className="live-badge">
              <span className="live-dot-animated" />
              LIVE
            </span>
          </div>
          <div className="sesi-aktif-content">
            <div className="sesi-aktif-count">{liveCount}</div>
            <div className="sesi-aktif-label">percakapan aktif</div>
            {liveSessions?.sessions && liveSessions.sessions.length > 0 ? (
              <div className="sesi-aktif-list">
                {liveSessions.sessions.slice(0, 3).map((s: any, i: number) => (
                  <div key={i} className="sesi-aktif-item">
                    <span className="sesi-aktif-name">{s.name || 'User'}</span>
                    <span className="sesi-aktif-time">{s.minutes_ago}m lalu</span>
                  </div>
                ))}
                {liveSessions.sessions.length > 3 && (
                  <div className="sesi-aktif-more">+{liveSessions.sessions.length - 3} lagi</div>
                )}
              </div>
            ) : (
              <div className="sesi-aktif-empty">Tidak ada sesi aktif</div>
            )}
          </div>
        </div>
      </div>

      {/* Ticket by Category */}
      {ticketByCategory.length > 0 && (
        <div className="card ticket-summary">
          <div className="card-header">
            <h2>Tiket per Kategori</h2>
            <span className="card-badge">{totalTicketCount} total</span>
          </div>
          <div className="ticket-bars">
            {ticketByCategory.map((cat: any, i: number) => {
              const pct = totalTicketCount > 0 ? Math.round((cat.count / totalTicketCount) * 100) : 0;
              return (
                <div key={i} className="ticket-bar-row">
                  <div className="ticket-bar-label">{cat.category || 'Lainnya'}</div>
                  <div className="ticket-bar-track">
                    <div className="ticket-bar-fill" style={{ width: `${pct}%`, background: catColors[i % catColors.length] }} />
                  </div>
                  <div className="ticket-bar-count">{cat.count}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Sessions */}
      <div className="card">
        <div className="card-header">
          <h2>Percakapan Terakhir</h2>
          <span className="card-badge">{sessions.length} terbaru</span>
        </div>
        <div className="table-wrapper">
          {sessions.length > 0 ? (
            <table className="sessions-table">
              <thead>
                <tr>
                  <th>Pengguna</th>
                  <th>Masalah</th>
                  <th>Kategori</th>
                  <th>Status</th>
                  <th>Pesan</th>
                  <th>Waktu</th>
                </tr>
              </thead>
              <tbody>
                {sessions.slice(0, 10).map((s: any, i: number) => (
                  <tr key={i}>
                    <td>
                      <div className="td-user">
                        <div className="user-avatar-sm">{(s.name || '?').charAt(0).toUpperCase()}</div>
                        <div>
                          <div className="user-name-cell">{s.name || 'Tanpa Nama'}</div>
                          <div className="user-phone-cell">{s.phone || ''}</div>
                        </div>
                      </div>
                    </td>
                    <td className="td-problem">
                      {s.problem && s.problem !== 'N/A' ? s.problem.substring(0, 40) + (s.problem.length > 40 ? '...' : '') : '-'}
                    </td>
                    <td>
                      <span className="tag tag-cat">{s.category || '-'}</span>
                    </td>
                    <td>
                      <span className={`tag tag-status tag-status-${getStatusType(s.state)}`}>{getStatusLabel(s.state)}</span>
                    </td>
                    <td className="td-center">{s.messages || 0}</td>
                    <td className="td-time">{formatTime(s.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="no-data">Belum ada percakapan</div>
          )}
        </div>
      </div>
    </div>
  );
}
