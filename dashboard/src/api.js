import axios from 'axios';

// Use relative URL so Vite proxy handles routing to backend
const API_URL = '/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.params = config.params || {};
      config.params.token = token;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auto-logout on 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

// Auth service
export const authService = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },
  
  logout: async () => {
    return api.post('/auth/logout');
  },
  
  verifyToken: async (token) => {
    const response = await api.post('/auth/verify', null, {
      params: { token }
    });
    return response.data;
  },
  
  getCurrentUser: async (token) => {
    const response = await api.get('/auth/me', {
      params: { token }
    });
    return response.data;
  }
};

// Analytics service
export const analyticsService = {
  getDashboard: async () => {
    const response = await api.get('/analytics/dashboard');
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

  getPerformance: async () => {
    const response = await api.get('/analytics/insights/performance');
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
  getMLInsights: async () => {
    const response = await api.get('/analytics/ml-insights');
    return response.data;
  },

  // Activity Log (new)
  getActivityLog: async (limit = 20) => {
    const response = await api.get('/analytics/activity-log', {
      params: { limit }
    });
    return response.data;
  },

  // Timeline (new)
  getTimeline: async () => {
    const response = await api.get('/analytics/stats/timeline');
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
