import React, { useState, useEffect } from 'react';
import { analyticsService } from '../api.js';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import './OverviewPage.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler);

const CHART_TOOLTIP = {
  backgroundColor: '#1a2332',
  titleColor: '#f0f4f8',
  bodyColor: '#8b9bb4',
  borderColor: 'rgba(255,255,255,0.08)',
  borderWidth: 1,
  cornerRadius: 8,
  padding: 10,
  titleFont: { weight: 600 },
};

export default function OverviewPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const dashData = await analyticsService.getDashboard();
      setData(dashData);
    } catch (err) {
      setError('Gagal memuat data. Pastikan server backend aktif.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 20000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Memuat ringkasan...</p>
      </div>
    );
  }

  const overview = data?.overview || {};
  const categories = data?.categories?.categories || [];
  const quality = data?.quality || {};
  const sessions = data?.recent_sessions?.sessions || [];
  const tickets = data?.tickets || {};
  const severity = data?.severity?.severities || [];

  const totalSessions = overview.total_sessions || 0;
  const totalTickets = overview.total_tickets || 0;
  const totalMessages = overview.total_messages || 0;
  const successRate = overview.success_rate || 0;
  const avgMessages = overview.avg_messages_per_session || 0;

  // KPI Cards
  const kpis = [
    {
      label: 'Total Percakapan',
      value: totalSessions,
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
        </svg>
      ),
      color: 'blue',
      desc: `${overview.active_sessions || 0} sedang aktif`,
    },
    {
      label: 'Tingkat Keberhasilan',
      value: `${Math.round(successRate)}%`,
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
        </svg>
      ),
      color: 'emerald',
      desc: `${totalSessions - totalTickets} diselesaikan AI`,
    },
    {
      label: 'Tiket Dibuat',
      value: totalTickets,
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      ),
      color: 'amber',
      desc: 'Diteruskan ke tim support',
    },
    {
      label: 'Total Pesan',
      value: totalMessages,
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      ),
      color: 'violet',
      desc: `Rata-rata ${avgMessages} per sesi`,
    },
  ];

  // Category Donut
  const catColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#f97316', '#06b6d4'];
  const donutData = {
    labels: categories.map(c => c.name || 'Lainnya'),
    datasets: [{
      data: categories.map(c => c.count),
      backgroundColor: categories.map((_, i) => catColors[i % catColors.length]),
      borderColor: '#1a2332',
      borderWidth: 3,
      hoverBorderWidth: 0,
    }],
  };
  const donutOpts = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '68%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#8b9bb4', font: { size: 12, weight: 500 }, padding: 16, usePointStyle: true, pointStyleWidth: 8 },
      },
      tooltip: CHART_TOOLTIP,
    },
  };

  // Severity Bar
  const sevColorMap = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', normal: '#3b82f6', low: '#10b981' };
  const sevBarData = {
    labels: severity.map(s => ({ critical: 'Kritis', high: 'Tinggi', medium: 'Sedang', normal: 'Normal', low: 'Rendah' }[s.name] || s.name)),
    datasets: [{
      data: severity.map(s => s.count),
      backgroundColor: severity.map(s => sevColorMap[s.name] || '#5a6d84'),
      borderRadius: 6,
      borderSkipped: false,
      barThickness: 28,
    }],
  };
  const sevBarOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: CHART_TOOLTIP },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#8b9bb4', font: { size: 12, weight: 500 } } },
      y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false }, ticks: { color: '#5a6d84', stepSize: 1, font: { size: 11 } } },
    },
  };

  // Quality metrics
  const avgDurationMin = Math.round((quality.avg_duration_seconds || 0) / 60);
  const qualityItems = [
    { label: 'Selesai', value: `${quality.completion_rate || 0}%`, color: 'emerald', desc: 'Sesi yang selesai dengan baik' },
    { label: 'Durasi', value: avgDurationMin > 60 ? `${Math.round(avgDurationMin/60)}j ${avgDurationMin%60}m` : `${avgDurationMin}m`, color: 'blue', desc: 'Rata-rata waktu per sesi' },
    { label: 'Pesan', value: quality.avg_messages || 0, color: 'violet', desc: 'Rata-rata pesan per percakapan' },
    { label: 'Dibatalkan', value: quality.abandoned_sessions || 0, color: 'rose', desc: 'Sesi yang tidak dilanjutkan' },
  ];

  return (
    <div className="overview-page">
      <div className="page-header">
        <div>
          <h1>Ringkasan</h1>
          <p className="page-subtitle">Pantau aktivitas chatbot dan performa layanan</p>
        </div>
        <div className="header-live">
          <span className="live-dot" />
          <span>Diperbarui otomatis</span>
        </div>
      </div>

      {error && (
        <div className="page-error">⚠️ {error}<button onClick={fetchData}>Coba Lagi</button></div>
      )}

      {/* KPI Cards */}
      <div className="kpi-grid">
        {kpis.map((kpi, i) => (
          <div key={i} className={`kpi-card kpi-${kpi.color}`} style={{ animationDelay: `${i * 60}ms` }}>
            <div className="kpi-icon-wrap">{kpi.icon}</div>
            <div className="kpi-body">
              <div className="kpi-label">{kpi.label}</div>
              <div className="kpi-value">{typeof kpi.value === 'number' ? kpi.value.toLocaleString('id-ID') : kpi.value}</div>
              <div className="kpi-desc">{kpi.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="overview-charts">
        {/* Category Donut */}
        <div className="card">
          <div className="card-header">
            <h2>Kategori Masalah</h2>
            <span className="card-badge">{categories.length} jenis</span>
          </div>
          <div className="chart-donut-wrap">
            {categories.length > 0 ? (
              <Doughnut data={donutData} options={donutOpts} />
            ) : (
              <div className="no-data">
                <span className="no-data-icon">📁</span>
                Belum ada data kategori masalah
              </div>
            )}
          </div>
        </div>

        {/* Severity Bar */}
        <div className="card">
          <div className="card-header">
            <h2>Tingkat Urgensi</h2>
            <span className="card-badge">{severity.reduce((a, s) => a + s.count, 0)} laporan</span>
          </div>
          <div className="chart-bar-wrap">
            {severity.length > 0 ? (
              <Bar data={sevBarData} options={sevBarOpts} />
            ) : (
              <div className="no-data">
                <span className="no-data-icon">📊</span>
                Belum ada data urgensi
              </div>
            )}
          </div>
        </div>

        {/* Quality Metrics */}
        <div className="card quality-card">
          <div className="card-header">
            <h2>Kualitas Sesi</h2>
          </div>
          <div className="quality-list">
            {qualityItems.map((item, i) => (
              <div key={i} className={`quality-row quality-${item.color}`}>
                <div className="quality-left">
                  <div className="quality-val">{item.value}</div>
                  <div className="quality-label">{item.label}</div>
                </div>
                <div className="quality-desc">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Ticket Summary */}
      {tickets.by_category && tickets.by_category.length > 0 && (
        <div className="card ticket-summary">
          <div className="card-header">
            <h2>Tiket per Kategori</h2>
            <span className="card-badge">{tickets.total_tickets} total</span>
          </div>
          <div className="ticket-bars">
            {tickets.by_category.map((cat, i) => {
              const pct = tickets.total_tickets > 0 ? Math.round((cat.count / tickets.total_tickets) * 100) : 0;
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
                {sessions.slice(0, 10).map((s, i) => (
                  <tr key={i} style={{ animationDelay: `${i * 40}ms` }}>
                    <td>
                      <div className="td-user">
                        <div className="user-avatar-sm">{(s.name || '?').charAt(0).toUpperCase()}</div>
                        <div>
                          <div className="user-name-cell">{s.name || 'Tanpa Nama'}</div>
                          <div className="user-phone-cell">{s.phone ? `...${s.phone.slice(-4)}` : ''}</div>
                        </div>
                      </div>
                    </td>
                    <td className="td-problem">{s.problem && s.problem !== 'N/A' ? s.problem : '—'}</td>
                    <td><span className="tag tag-cat">{s.category || '—'}</span></td>
                    <td><span className={`tag tag-status tag-status-${getStatusType(s.state)}`}>{getStatusLabel(s.state)}</span></td>
                    <td className="td-center">{s.messages || 0}</td>
                    <td className="td-time">{formatTime(s.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="no-data">
              <span className="no-data-icon">💬</span>
              Belum ada percakapan tercatat
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Helpers ──
function getStatusType(state) {
  if (!state) return 'default';
  if (['closed', 'resolved'].includes(state)) return 'success';
  if (['creating_ticket', 'confirming_details'].includes(state)) return 'warning';
  if (['greeting', 'collecting_name', 'collecting_problem'].includes(state)) return 'info';
  return 'default';
}

function getStatusLabel(state) {
  const map = {
    greeting: 'Baru Mulai',
    collecting_name: 'Mengisi Data',
    collecting_problem: 'Mengisi Data',
    asking_solution_worked: 'Menunggu Solusi',
    collecting_unit: 'Membuat Tiket',
    collecting_location: 'Membuat Tiket',
    collecting_time: 'Membuat Tiket',
    confirming_details: 'Konfirmasi',
    creating_ticket: 'Membuat Tiket',
    closed: 'Selesai',
    resolved: 'Selesai',
  };
  return map[state] || state || '—';
}

function formatTime(isoStr) {
  if (!isoStr) return '—';
  try {
    const d = new Date(isoStr);
    const now = new Date();
    const diffMin = Math.floor((now - d) / 60000);
    if (diffMin < 1) return 'Baru saja';
    if (diffMin < 60) return `${diffMin} menit lalu`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr} jam lalu`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay} hari lalu`;
    return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch {
    return '—';
  }
}
