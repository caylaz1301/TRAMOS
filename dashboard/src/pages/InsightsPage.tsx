import React, { useState, useEffect } from 'react';
import { analyticsService, benchmarkService } from '../api.js';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import DateFilter from '../components/DateFilter';
import './InsightsPage.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler);

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

export default function InsightsPage() {
  const [alerts, setAlerts] = useState(null);
  const [health, setHealth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [mlInsights, setMlInsights] = useState(null);
  const [activityLog, setActivityLog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({ startDate: null, endDate: null });

  const fetchData = async () => {
    try {
      setError(null);
      setLoading(true);
      const [alertsData, healthData, dashData, mlData, logData] = await Promise.all([
        analyticsService.getActiveAlerts().catch(() => null),
        analyticsService.getHealthCheck().catch(() => null),
        analyticsService.getDashboard(dateRange.startDate, dateRange.endDate).catch(() => null),
        analyticsService.getMLInsights(dateRange.startDate, dateRange.endDate).catch(() => null),
        analyticsService.getActivityLog(15).catch(() => null),
      ]);
      setAlerts(alertsData);
      setHealth(healthData);
      setDashboard(dashData);
      setMlInsights(mlData);
      setActivityLog(logData);
    } catch (err) {
      setError('Gagal memuat data laporan');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Menyiapkan laporan...</p>
      </div>
    );
  }

  const alertsData = alerts || {};
  const activeAlerts = alertsData.alerts || [];
  const criticalCount = alertsData.critical_count || 0;
  const warningCount = alertsData.warning_count || 0;

  const healthData = health || {};
  const components = healthData.components || {};

  const overview = dashboard?.overview || {};
  const quality = dashboard?.quality || {};
  const categories = dashboard?.categories?.categories || [];

  const totalSessions = overview.total_sessions || 0;
  const totalMessages = overview.total_messages || 0;
  const completionRate = quality.completion_rate || 0;
  const avgDuration = Math.round((quality.avg_duration_seconds || 0) / 60);
  const avgMessages = overview.avg_messages_per_session || 0;

  // ML data
  const ml = mlInsights || {};
  const weeklyTrend = ml.weekly_trend || {};
  const kbEffectiveness = ml.kb_effectiveness || {};
  const topEscalated = ml.top_escalated || [];
  const peakHours = ml.peak_hours || [];
  const recommendations = ml.recommendations || [];

  // Activity log
  const events = activityLog?.events || [];

  // System health status
  const systemStatus = criticalCount > 0 ? 'critical' : warningCount > 0 ? 'warning' : 'healthy';
  const statusLabels = { critical: 'Ada Masalah Kritis', warning: 'Ada Peringatan', healthy: 'Semua Berjalan Normal' };
  const statusIcons = { critical: '🔴', warning: '🟡', healthy: '🟢' };

  // System components
  const systemComponents = [
    { name: 'Database', status: components.database || 'unknown', icon: '🗄️' },
    { name: 'Gemini AI', status: components.ai_engine || 'unknown', icon: '🤖' },
    { name: 'WhatsApp API', status: components.whatsapp_api || 'unknown', icon: '💬' },
    { name: 'osTicket', status: components.osticket || 'unknown', icon: '🎫' },
    { name: 'Knowledge Base RAG', status: components.knowledge_base || 'unknown', icon: '📚' },
  ];

  // Build insights from data
  const insights = buildInsights(overview, quality, categories, kbEffectiveness);

  return (
    <div className="insights-page">
      <div className="page-header">
        <div>
          <h1>Laporan & Notifikasi</h1>
          <p className="page-subtitle">Kesehatan sistem, analisis AI, dan rekomendasi operasional</p>
        </div>
        <button className="btn-refresh" onClick={fetchData}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
          </svg>
          Perbarui
        </button>
      </div>

      <DateFilter onFilterChange={setDateRange} />

      {error && (
        <div className="page-error">⚠️ {error}<button onClick={fetchData}>Coba Lagi</button></div>
      )}

      {/* System Status Strip */}
      <div className={`status-strip status-${systemStatus}`}>
        <div className="status-left">
          <span className="status-icon">{statusIcons[systemStatus]}</span>
          <div>
            <div className="status-title">{statusLabels[systemStatus]}</div>
            <div className="status-sub">{activeAlerts.length > 0 ? `${activeAlerts.length} notifikasi aktif` : 'Tidak ada notifikasi'}</div>
          </div>
        </div>
        <div className="status-right">
          <span className="status-time">Terakhir dicek: {new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="insights-grid">
        {/* Left Column */}
        <div className="insights-col">
          {/* System Health */}
          <div className="card">
            <div className="card-header">
              <h2>Status Sistem</h2>
            </div>
            <div className="components-list">
              {systemComponents.map((comp, i) => (
                <div key={i} className="comp-row">
                  <span className="comp-icon">{comp.icon}</span>
                  <span className="comp-name">{comp.name}</span>
                  <span className={`comp-status comp-${getCompStatusType(comp.status)}`}>
                    {getCompStatusLabel(comp.status)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Notifications */}
          <div className="card">
            <div className="card-header">
              <h2>Notifikasi</h2>
              <span className="card-badge">{activeAlerts.length}</span>
            </div>
            <div className="alerts-content">
              {activeAlerts.length > 0 ? (
                activeAlerts.slice(0, 5).map((alert, i) => (
                  <div key={i} className={`alert-row alert-${alert.severity || 'info'}`}>
                    <div className={`alert-dot dot-${alert.severity || 'info'}`} />
                    <div className="alert-body">
                      <div className="alert-title">{alert.title || alert.message || 'Notifikasi'}</div>
                      <div className="alert-desc">{alert.description || alert.detail || ''}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="alerts-empty">
                  <div className="empty-icon-wrap">✓</div>
                  <p className="empty-title">Tidak Ada Notifikasi</p>
                  <p className="empty-desc">Semua komponen berjalan normal.</p>
                </div>
              )}
            </div>
          </div>

          {/* AI Recommendations */}
          <div className="card">
            <div className="card-header">
              <h2>Rekomendasi AI</h2>
              <span className="card-badge">{recommendations.length}</span>
            </div>
            <div className="recommendations-content">
              {recommendations.length > 0 ? (
                recommendations.map((rec, i) => (
                  <div key={i} className={`rec-row rec-${rec.priority}`}>
                    <div className={`rec-priority priority-${rec.priority}`}>
                      {rec.priority === 'high' ? '🔴' : rec.priority === 'medium' ? '🟡' : '🟢'}
                    </div>
                    <div className="rec-body">
                      <div className="rec-type">{getRecTypeLabel(rec.type)}</div>
                      <div className="rec-message">{rec.message}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="alerts-empty">
                  <div className="empty-icon-wrap">👍</div>
                  <p className="empty-title">Tidak Ada Rekomendasi</p>
                  <p className="empty-desc">Sistem berjalan optimal. Akan ada rekomendasi jika terdeteksi area yang bisa ditingkatkan.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="insights-col">
          {/* ML Analytics Summary */}
          <div className="card">
            <div className="card-header">
              <h2>Analisis Machine Learning</h2>
            </div>
            <div className="ml-summary">
              <div className="ml-stat">
                <div className="ml-stat-header">
                  <span className="ml-stat-label">Tren Volume Mingguan</span>
                  <span className={`ml-trend trend-${weeklyTrend.direction || 'stable'}`}>
                    {weeklyTrend.direction === 'up' ? '↑' : weeklyTrend.direction === 'down' ? '↓' : '→'} {Math.abs(weeklyTrend.change_percent || 0)}%
                  </span>
                </div>
                <div className="ml-stat-detail">
                  Minggu ini: <strong>{weeklyTrend.this_week || 0}</strong> sesi &bull; Minggu lalu: <strong>{weeklyTrend.last_week || 0}</strong> sesi
                </div>
                <div className="ml-trend-bar-wrap">
                  <div className="ml-trend-bar">
                    <div className="ml-trend-bar-last" style={{ width: `${Math.min(100, ((weeklyTrend.last_week || 0) / Math.max(1, weeklyTrend.this_week || 0, weeklyTrend.last_week || 0)) * 100)}%` }} />
                  </div>
                  <div className="ml-trend-bar">
                    <div className="ml-trend-bar-this" style={{ width: `${Math.min(100, ((weeklyTrend.this_week || 0) / Math.max(1, weeklyTrend.this_week || 0, weeklyTrend.last_week || 0)) * 100)}%` }} />
                  </div>
                </div>
              </div>
              <div className="ml-stat">
                <div className="ml-stat-header">
                  <span className="ml-stat-label">Efektivitas AI Chatbot</span>
                  <span className="ml-stat-value">{kbEffectiveness.ai_resolution_rate || 0}%</span>
                </div>
                <div className="ml-stat-detail">
                  <span className="stat-chip chip-emerald">AI: {kbEffectiveness.resolved_by_ai || 0}</span>
                  <span className="stat-chip chip-amber">Eskalasi: {kbEffectiveness.escalated || 0}</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${kbEffectiveness.ai_resolution_rate || 0}%` }} />
                </div>
                <div className="ml-stat-insight">
                  {(kbEffectiveness.ai_resolution_rate || 0) >= 70
                    ? '✅ AI menangani masalah dengan sangat baik'
                    : (kbEffectiveness.ai_resolution_rate || 0) >= 40
                      ? '⚠️ Perlu peningkatan solusi di Knowledge Base'
                      : '🔴 Banyak masalah memerlukan bantuan manusia'}
                </div>
              </div>
              {topEscalated.length > 0 && (
                <div className="ml-stat">
                  <div className="ml-stat-header">
                    <span className="ml-stat-label">Kategori Sering Dieskalasi</span>
                  </div>
                  <div className="escalation-list">
                    {topEscalated.slice(0, 5).map((cat, i) => (
                      <div key={i} className="escalation-item">
                        <span className="escalation-rank">#{i + 1}</span>
                        <span className="escalation-name">{cat.category}</span>
                        <div className="escalation-bar-track">
                          <div className="escalation-bar-fill" style={{ width: `${Math.min(100, (cat.count / Math.max(1, topEscalated[0].count)) * 100)}%` }} />
                        </div>
                        <span className="escalation-count">{cat.count}x</span>
                      </div>
                    ))}
                  </div>
                  <div className="ml-stat-insight">
                    💡 Fokuskan penambahan solusi KB untuk kategori "{topEscalated[0]?.category}" agar eskalasi berkurang.
                  </div>
                </div>
              )}
              {peakHours.length > 0 && (
                <div className="ml-stat">
                  <div className="ml-stat-header">
                    <span className="ml-stat-label">Jam Sibuk (Peak Hours)</span>
                  </div>
                  <div className="peak-hours">
                    {peakHours.slice(0, 6).map((ph, i) => (
                      <div key={i} className={`peak-hour-badge ${i === 0 ? 'peak-primary' : ''}`}>
                        <span className="peak-time">{String(ph.hour).padStart(2, '0')}:00</span>
                        <span className="peak-count">{ph.count} sesi</span>
                      </div>
                    ))}
                  </div>
                  <div className="ml-stat-insight">
                    🕐 Jam tersibuk: {String(peakHours[0]?.hour || 0).padStart(2, '0')}:00 dengan {peakHours[0]?.count || 0} percakapan
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Data Insights */}
          <div className="card">
            <div className="card-header">
              <h2>Rangkuman Data</h2>
            </div>
            <div className="insights-content">
              {insights.length > 0 ? (
                insights.map((ins, i) => (
                  <div key={i} className={`insight-row insight-${ins.type}`}>
                    <div className={`insight-icon-wrap icon-${ins.type}`}>{ins.icon}</div>
                    <div className="insight-body">
                      <div className="insight-title">{ins.title}</div>
                      <div className="insight-desc">{ins.desc}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-data">
                  <span className="no-data-icon">📊</span>
                  Belum ada cukup data untuk membuat rangkuman
                </div>
              )}
            </div>
          </div>

          {/* Activity Log */}
          <div className="card">
            <div className="card-header">
              <h2>Log Aktivitas</h2>
              <span className="card-badge">{events.length}</span>
            </div>
            <div className="activity-log">
              {events.length > 0 ? (
                events.slice(0, 10).map((evt, i) => (
                  <div key={i} className={`activity-row activity-${evt.type}`}>
                    <span className="activity-icon">{evt.icon}</span>
                    <div className="activity-body">
                      <div className="activity-desc">{evt.description}</div>
                      <div className="activity-time">
                        {evt.timestamp ? formatTimeAgo(evt.timestamp) : '-'}
                        {evt.severity && <span className={`activity-severity sev-${evt.severity}`}>{evt.severity}</span>}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="alerts-empty">
                  <div className="empty-icon-wrap">📝</div>
                  <p className="empty-title">Belum Ada Aktivitas</p>
                  <p className="empty-desc">Log akan terisi otomatis saat ada percakapan dan tiket baru.</p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="card">
            <div className="card-header">
              <h2>Statistik Cepat</h2>
            </div>
            <div className="quick-stats">
              <div className="qstat">
                <div className="qstat-val">{totalSessions}</div>
                <div className="qstat-label">Total Percakapan</div>
              </div>
              <div className="qstat">
                <div className="qstat-val">{totalMessages.toLocaleString('id-ID')}</div>
                <div className="qstat-label">Total Pesan</div>
              </div>
              <div className="qstat">
                <div className="qstat-val">{categories.length}</div>
                <div className="qstat-label">Kategori Masalah</div>
              </div>
              <div className="qstat">
                <div className="qstat-val">{Math.round(avgMessages)}</div>
                <div className="qstat-label">Pesan/Sesi</div>
              </div>
              <div className="qstat">
                <div className="qstat-val">{avgDuration > 60 ? `${Math.round(avgDuration/60)}j` : `${avgDuration}m`}</div>
                <div className="qstat-label">Durasi Rata-rata</div>
              </div>
              <div className="qstat">
                <div className="qstat-val">{`${completionRate}%`}</div>
                <div className="qstat-label">Tingkat Selesai</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Build insights from real data ──
function buildInsights(overview, quality, categories, kbEffectiveness) {
  const insights = [];
  const totalSessions = overview.total_sessions || 0;
  const totalTickets = overview.total_tickets || 0;
  const completionRate = quality.completion_rate || 0;
  const aiRate = kbEffectiveness.ai_resolution_rate || 0;

  if (totalSessions > 0) {
    const escalationRate = Math.round((totalTickets / totalSessions) * 100);
    if (escalationRate > 60) {
      insights.push({
        type: 'warning', icon: '⚠️',
        title: 'Tingkat Eskalasi Tinggi',
        desc: `${escalationRate}% percakapan berakhir dengan tiket. Tambahkan solusi di Knowledge Base untuk mengurangi eskalasi.`,
      });
    } else if (escalationRate <= 30 && totalSessions >= 5) {
      insights.push({
        type: 'success', icon: '✅',
        title: 'Chatbot Bekerja Efektif',
        desc: `Hanya ${escalationRate}% percakapan diteruskan ke support. AI berhasil menangani mayoritas masalah.`,
      });
    }
  }

  if (completionRate > 0 && completionRate < 70) {
    insights.push({
      type: 'warning', icon: '📉',
      title: 'Tingkat Penyelesaian Perlu Ditingkatkan',
      desc: `Hanya ${completionRate}% sesi yang berhasil diselesaikan. Periksa alur percakapan chatbot.`,
    });
  }

  if (categories.length > 0) {
    const topCat = categories.reduce((a, b) => a.count > b.count ? a : b);
    insights.push({
      type: 'info', icon: '📋',
      title: `Masalah Terbanyak: ${topCat.name}`,
      desc: `Kategori "${topCat.name}" mendominasi dengan ${topCat.count} laporan. Fokuskan KB pada area ini.`,
    });
  }

  if (totalSessions === 0) {
    insights.push({
      type: 'info', icon: '📊',
      title: 'Mulai Mengumpulkan Data',
      desc: 'Belum ada percakapan tercatat. Begitu ada pengguna menghubungi chatbot, data akan muncul otomatis.',
    });
  }

  return insights;
}

// ── Helpers ──
function getCompStatusType(status) {
  if (!status || status === 'unknown') return 'unknown';
  if (status === 'connected' || status === 'operational' || status === 'configured' || status.startsWith('loaded') || status.startsWith('rag_')) return 'ok';
  if (status === 'not_configured') return 'off';
  if (status.startsWith('error') || status === 'unreachable') return 'error';
  return 'unknown';
}

function getCompStatusLabel(status) {
  if (!status || status === 'unknown') return 'Tidak Diketahui';
  if (status === 'connected') return 'Terhubung';
  if (status === 'operational') return 'Aktif';
  if (status === 'configured') return 'Dikonfigurasi';
  if (status === 'not_configured') return 'Belum Dikonfigurasi';
  if (status === 'unreachable') return 'Tidak Terjangkau';
  if (status.startsWith('loaded')) return 'Aktif';
  if (status.startsWith('rag_')) return status.includes('pgvector_true') ? 'RAG + pgvector Aktif' : 'RAG Aktif';
  if (status.startsWith('error')) return 'Error';
  return status;
}

function getRecTypeLabel(type) {
  const labels = {
    'kb_gap': 'Knowledge Base',
    'staffing': 'Jadwal Tim',
    'volume_alert': 'Volume',
    'improvement': 'Peningkatan',
    'kb_improvement': 'Knowledge Base',
  };
  return labels[type] || type;
}

function formatTimeAgo(timestamp) {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffMin < 1) return 'Baru saja';
  if (diffMin < 60) return `${diffMin} menit lalu`;
  if (diffHour < 24) return `${diffHour} jam lalu`;
  if (diffDay < 7) return `${diffDay} hari lalu`;
  return then.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
}
