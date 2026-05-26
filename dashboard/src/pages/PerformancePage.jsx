import React, { useState, useEffect } from 'react';
import { analyticsService, benchmarkService } from '../api.js';
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

export default function PerformancePage() {
  const [perf, setPerf] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({ startDate: null, endDate: null });

  const fetchData = async () => {
    try {
      setError(null);
      const [perfData, dashData, benchData] = await Promise.all([
        analyticsService.getPerformance(dateRange.startDate, dateRange.endDate).catch(() => null),
        analyticsService.getDashboard(dateRange.startDate, dateRange.endDate).catch(() => null),
        benchmarkService.getScore().catch(() => null),
      ]);
      setPerf(perfData);
      setDashboard(dashData);
      setBenchmark(benchData);
    } catch (err) {
      setError('Gagal memuat data performa');
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
        <p>Menganalisis performa AI...</p>
      </div>
    );
  }

  const perfData = perf || {};
  const overview = dashboard?.overview || {};
  const quality = dashboard?.quality || {};
  const severity = dashboard?.severity?.severities || [];

  const score = perfData.performance_score || 0;
  const grade = perfData.score_grade || 'N/A';
  const totalSessions = overview.total_sessions || 0;
  const totalTickets = overview.total_tickets || 0;
  const abandoned = quality.abandoned_sessions || 0;
  const aiSolved = Math.max(0, totalSessions - totalTickets - abandoned);
  const completionRate = quality.completion_rate || 0;

  // Score ring color
  const scoreColor = score >= 70 ? 'emerald' : score >= 40 ? 'amber' : 'rose';
  const scoreLabel = score >= 70 ? 'Baik' : score >= 40 ? 'Perlu Ditingkatkan' : 'Perlu Perhatian';

  // Resolution Donut
  const donutData = {
    labels: ['Diselesaikan AI', 'Dibuat Tiket', 'Dibatalkan'],
    datasets: [{
      data: [aiSolved, totalTickets, abandoned],
      backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
      borderColor: '#ffffff',
      borderWidth: 3,
    }],
  };
  const donutOpts = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: {
      legend: { position: 'bottom', labels: { color: '#9ca3af', font: { size: 12, weight: 500 }, padding: 14, usePointStyle: true, pointStyleWidth: 8 } },
      tooltip: CHART_TOOLTIP,
    },
  };

  // Severity Bar
  const sevMap = { critical: 'Kritis', high: 'Tinggi', medium: 'Sedang', normal: 'Normal', low: 'Rendah' };
  const sevColors = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', normal: '#3b82f6', low: '#10b981' };
  const sevBarData = {
    labels: severity.map(s => sevMap[s.name] || s.name),
    datasets: [{
      data: severity.map(s => s.count),
      backgroundColor: severity.map(s => sevColors[s.name] || '#5a6d84'),
      borderRadius: 6,
      borderSkipped: false,
      barThickness: 28,
    }],
  };
  const sevBarOpts = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: CHART_TOOLTIP },
    scales: {
      x: { beginAtZero: true, grid: { color: '#f3f4f6', drawBorder: false }, ticks: { color: '#9ca3af', stepSize: 1 } },
      y: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 13, weight: 500 } } },
    },
  };

  // Metric cards
  const metrics = [
    { label: 'Tingkat Penyelesaian', value: `${Math.round(completionRate)}%`, desc: 'Percakapan yang berhasil diselesaikan oleh chatbot', color: 'emerald' },
    { label: 'Sesi Dieskalasi', value: totalTickets, desc: 'Masalah yang diteruskan ke tim support', color: 'amber' },
    { label: 'Rata-rata Pesan', value: Math.round(overview.avg_messages_per_session || 0), desc: 'Jumlah chat bolak-balik per sesi', color: 'blue' },
    { label: 'Sesi Dibatalkan', value: abandoned, desc: 'Pengguna yang pergi sebelum masalah selesai ditangani', color: 'rose' },
  ];

  // Action items
  const actions = perfData.action_items || [];

  return (
    <div className="perf-page">
      <div className="page-header">
        <div>
          <h1>Performa AI</h1>
          <p className="page-subtitle">Evaluasi efektivitas chatbot dalam menangani laporan</p>
        </div>
      </div>

      <DateFilter onFilterChange={setDateRange} />

      {error && (
        <div className="page-error">⚠️ {error}<button onClick={fetchData}>Coba Lagi</button></div>
      )}

      {/* Score + Donut */}
      <div className="perf-top">
        <div className="card score-card">
          <div className="score-visual">
            <div className={`score-ring score-${scoreColor}`}>
              <svg viewBox="0 0 120 120">
                <circle className="ring-bg" cx="60" cy="60" r="50" />
                <circle className="ring-fill" cx="60" cy="60" r="50" strokeDasharray={`${(score / 100) * 314} 314`} />
              </svg>
              <div className="score-center">
                <span className="score-num">{Math.round(score)}</span>
              </div>
            </div>
          </div>
          <div className="score-details">
            <h3>Skor Performa</h3>
            <span className={`score-badge badge-${scoreColor}`}>{scoreLabel}</span>
            <p className="score-grade">Grade: {grade}</p>
            <p className="score-explanation">
              {score >= 70
                ? 'Chatbot menangani sebagian besar masalah dengan baik tanpa perlu eskalasi ke tim support.'
                : score >= 40
                  ? 'Chatbot cukup membantu, namun masih banyak masalah yang perlu ditangani tim support.'
                  : 'Sebagian besar percakapan berakhir dengan eskalasi. Pertimbangkan untuk menambah solusi di Knowledge Base.'
              }
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Hasil Penanganan</h2>
            <span className="card-badge">{totalSessions} sesi</span>
          </div>
          <div className="donut-wrap">
            {totalSessions > 0 ? (
              <Doughnut data={donutData} options={donutOpts} />
            ) : (
              <div className="no-data">
                <span className="no-data-icon">📊</span>
                Belum ada data sesi
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="perf-metrics">
        {metrics.map((m, i) => (
          <div key={i} className={`metric-card metric-${m.color}`} style={{ animationDelay: `${i * 60}ms` }}>
            <div className="metric-val">{typeof m.value === 'number' ? m.value.toLocaleString('id-ID') : m.value}</div>
            <div className="metric-label">{m.label}</div>
            <div className="metric-desc">{m.desc}</div>
          </div>
        ))}
      </div>

      {/* Severity + Actions */}
      <div className="perf-bottom">
        <div className="card">
          <div className="card-header">
            <h2>Distribusi Urgensi</h2>
          </div>
          <div className="sev-chart-wrap">
            {severity.length > 0 ? (
              <Bar data={sevBarData} options={sevBarOpts} />
            ) : (
              <div className="no-data">
                <span className="no-data-icon">📋</span>
                Belum ada data urgensi tercatat
              </div>
            )}
          </div>
        </div>

        <div className="card actions-card">
          <div className="card-header">
            <h2>Saran Perbaikan</h2>
          </div>
          <div className="actions-list">
            {actions.length > 0 ? (
              actions.map((item, i) => (
                <div key={i} className="action-row">
                  <div className="action-num">{i + 1}</div>
                  <p>{translateAction(item)}</p>
                </div>
              ))
            ) : (
              <div className="actions-empty">
                <div className="empty-check">✓</div>
                <p className="empty-title">Tidak Ada Saran Saat Ini</p>
                <p className="empty-desc">Performa chatbot dalam kondisi baik. Terus pantau secara berkala untuk menjaga kualitas layanan.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function translateAction(text) {
  // Translate common AI-generated action items to Indonesian
  const translations = {
    'ACTION: Improve KB solution quality - focus on top categories': 'Tingkatkan kualitas solusi di Knowledge Base, terutama untuk kategori masalah yang paling sering muncul.',
    'Improve first-response accuracy': 'Tingkatkan akurasi jawaban pertama chatbot.',
    'Add more solutions to knowledge base': 'Tambahkan lebih banyak solusi ke dalam Knowledge Base.',
    'Monitor escalation patterns': 'Pantau pola eskalasi untuk menemukan area yang perlu perbaikan.',
  };
  return translations[text] || text;
}
