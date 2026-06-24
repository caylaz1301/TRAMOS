import axios from 'axios';

// Production memakai prefix khusus agar API dashboard tidak bentrok dengan API osTicket.
const API_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000
});

// Token dashboard dikirim lewat Authorization header agar tidak bocor di URL/log proxy.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Hanya sesi yang sudah memiliki token yang boleh dipaksa logout saat 401.
// Respons 401 dari form login harus diteruskan agar UI dapat menampilkan
// pesan seperti "akun belum terdaftar", bukan me-refresh halaman.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || '';
    const isAuthenticationAttempt = ['/auth/login', '/auth/google'].some((path) =>
      requestUrl.includes(path)
    );
    const hasAccessToken = Boolean(localStorage.getItem('access_token'));

    if (error.response?.status === 401 && hasAccessToken && !isAuthenticationAttempt) {
      // Clear all auth data
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_name');
      localStorage.removeItem('user_email');
      localStorage.removeItem('user_role');
      // Redirect to login instead of page reload
      window.location.href = import.meta.env.BASE_URL;
    }
    return Promise.reject(error);
  }
);

// Auth service
export const authService = {
  register: async (fullName, email, password, phone) => {
    const response = await api.post('/auth/register', {
      full_name: fullName,
      email,
      password,
      phone: phone || null,
    });
    return response.data;
  },

  verifyOtp: async (email, otpCode) => {
    const response = await api.post('/auth/verify-otp', {
      email,
      otp_code: otpCode,
    });
    return response.data;
  },

  resendOtp: async (email) => {
    const response = await api.post('/auth/resend-otp', { email });
    return response.data;
  },

  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },
  
  logout: async () => {
    return api.post('/auth/logout');
  },
  
  verifyToken: async (token) => {
    const response = await api.post('/auth/verify', null, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    return response.data;
  },
  
  getCurrentUser: async (token) => {
    const response = await api.get('/auth/me', {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    return response.data;
  },

  deleteAccount: async () => {
    const response = await api.delete('/auth/me');
    return response.data;
  },

  googleLogin: async (idToken, isSignup = false) => {
    const response = await api.post('/auth/google', {
      id_token: idToken,
      is_signup: isSignup,
    });
    return response.data;
  }
};

// Analytics service
export const analyticsService = {
  getDashboard: async (startDate, endDate) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get('/analytics/dashboard', { params });
    return response.data;
  },
  
  getOverviewStats: async () => {
    const response = await api.get('/analytics/stats/overview');
    return response.data;
  },
  
  getCategoryStats: async () => {
    const response = await api.get('/analytics/stats/categories');
    return response.data;
  },
  
  getSeverityStats: async () => {
    const response = await api.get('/analytics/stats/severity');
    return response.data;
  },
  
  getQualityMetrics: async () => {
    const response = await api.get('/analytics/stats/quality');
    return response.data;
  },
  
  getTicketStats: async () => {
    const response = await api.get('/analytics/stats/tickets');
    return response.data;
  },
  
  getRecentSessions: async (limit = 10) => {
    const response = await api.get('/analytics/data/recent-sessions', {
      params: { limit }
    });
    return response.data;
  },

  // ML Pattern Analysis
  getPatterns: async (days = 7) => {
    const response = await api.get('/analytics/analysis/patterns', {
      params: { days }
    });
    return response.data;
  },

  getHotspots: async (days = 7) => {
    const response = await api.get('/analytics/analysis/hotspots', {
      params: { days }
    });
    return response.data;
  },

  getTemporalPatterns: async (days = 7) => {
    const response = await api.get('/analytics/analysis/temporal', {
      params: { days }
    });
    return response.data;
  },

  getResolutionAnalysis: async (days = 7) => {
    const response = await api.get('/analytics/analysis/resolution', {
      params: { days }
    });
    return response.data;
  },

  getKpiTrends: async (days = 7) => {
    const response = await api.get('/analytics/analysis/kpi-trends', {
      params: { days }
    });
    return response.data;
  },

  // Insights & Intelligence
  getSummary: async (days = 7) => {
    const response = await api.get('/analytics/insights/executive-summary', {
      params: { days }
    });
    return response.data;
  },

  getTrends: async (days = 30) => {
    const response = await api.get('/analytics/insights/trends', {
      params: { days }
    });
    return response.data;
  },

  getPerformance: async (startDate, endDate) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get('/analytics/insights/performance', { params });
    return response.data;
  },

  getInsights: async (days = 7) => {
    const response = await api.get('/analytics/insights/recommendations', {
      params: { days }
    });
    return response.data;
  },

  // Alerts & Monitoring
  getActiveAlerts: async () => {
    const response = await api.get('/analytics/alerts/active');
    return response.data;
  },

  getHealthCheck: async () => {
    const response = await api.get('/analytics/alerts/health-check');
    return response.data;
  },

  // Predictive Analytics
  predictVolume: async (days = 7) => {
    const response = await api.get('/analytics/predict/volume', {
      params: { days }
    });
    return response.data;
  },

  predictEscalation: async () => {
    const response = await api.get('/analytics/predict/escalation-risk');
    return response.data;
  },

  predictStaffing: async () => {
    const response = await api.get('/analytics/predict/staffing');
    return response.data;
  },

  predictKbGaps: async () => {
    const response = await api.get('/analytics/predict/kb-gaps');
    return response.data;
  },

  getAllPredictions: async () => {
    const response = await api.get('/analytics/predict/all');
    return response.data;
  },

  // Reports
  getDailyReport: async () => {
    const response = await api.get('/analytics/reports/daily');
    return response.data;
  },

  getWeeklyReport: async () => {
    const response = await api.get('/analytics/reports/weekly');
    return response.data;
  },

  getMonthlyReport: async () => {
    const response = await api.get('/analytics/reports/monthly');
    return response.data;
  },

  getCustomReport: async (startDate, endDate) => {
    const response = await api.get('/analytics/reports/custom', {
      params: { start_date: startDate, end_date: endDate }
    });
    return response.data;
  },

  exportJson: async (reportType = 'daily') => {
    const response = await api.get('/analytics/export/json', {
      params: { report_type: reportType }
    });
    return response.data;
  },

  exportCsv: async (days = 7) => {
    const response = await api.get('/analytics/export/csv', {
      params: { days }
    });
    return response.data;
  },

  exportHtml: async (reportType = 'daily') => {
    const response = await api.get('/analytics/export/html', {
      params: { report_type: reportType }
    });
    return response.data;
  },

  // ML Insights (new)
  getMLInsights: async (startDate, endDate) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get('/analytics/ml-insights', { params });
    return response.data;
  },

  // Activity Log - supports date filtering and limit
  getActivityLog: async (limit = 20, startDate?: string | null, endDate?: string | null) => {
    const params: Record<string, unknown> = { limit };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get('/analytics/activity-log', { params });
    return response.data;
  },

  // Timeline (new)
  getTimeline: async (startDate, endDate) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get('/analytics/stats/timeline', { params });
    return response.data;
  }
};

// Anomaly Detection Service
export const anomalyService = {
  detectAll: async () => {
    const response = await api.get('/analytics/anomalies/detect');
    return response.data;
  },

  getCritical: async () => {
    const response = await api.get('/analytics/anomalies/critical');
    return response.data;
  }
};

// Visualization Service
export const visualizationService = {
  getAll: async () => {
    const response = await api.get('/analytics/visualizations/all');
    return response.data;
  },

  getTrends: async (days = 30) => {
    const response = await api.get('/analytics/visualizations/trends', {
      params: { days }
    });
    return response.data;
  },

  getCategories: async () => {
    const response = await api.get('/analytics/visualizations/categories');
    return response.data;
  },

  getSeverity: async () => {
    const response = await api.get('/analytics/visualizations/severity');
    return response.data;
  },

  getHeatmap: async () => {
    const response = await api.get('/analytics/visualizations/heatmap');
    return response.data;
  },

  getFunnel: async () => {
    const response = await api.get('/analytics/visualizations/funnel');
    return response.data;
  },

  getHourlyActivity: async () => {
    const response = await api.get('/analytics/visualizations/hourly');
    return response.data;
  },

  getQualityTrend: async () => {
    const response = await api.get('/analytics/visualizations/quality');
    return response.data;
  }
};

// Benchmark Comparison Service
export const benchmarkService = {
  getReport: async () => {
    const response = await api.get('/analytics/benchmarks/report');
    return response.data;
  },

  getIndustryComparison: async () => {
    const response = await api.get('/analytics/benchmarks/industry');
    return response.data;
  },

  getRecommendations: async () => {
    const response = await api.get('/analytics/benchmarks/recommendations');
    return response.data;
  },

  getScore: async () => {
    const response = await api.get('/analytics/benchmarks/score');
    return response.data;
  }
};

export default api;
