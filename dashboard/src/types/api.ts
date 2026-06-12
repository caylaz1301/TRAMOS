// API Response Types for TRAMOS Dashboard

// Auth Types
export interface AuthUser {
  id?: number;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'operator' | 'analyst';
}

export interface AuthResponse {
  access_token: string;
  user?: AuthUser;
  needs_verification?: boolean;
  email?: string;
  message?: string;
}

// Analytics Types
export interface OverviewStats {
  total_sessions: number;
  total_tickets: number;
  total_messages: number;
  success_rate: number;
  avg_messages_per_session: number;
  active_sessions: number;
  ai_resolved_sessions?: number;
}

export interface CategoryStats {
  name: string;
  count: number;
}

export interface SeverityStats {
  name: 'critical' | 'high' | 'medium' | 'normal' | 'low';
  count: number;
}

export interface QualityMetrics {
  completion_rate: number;
  avg_duration_seconds: number;
  avg_messages: number;
  abandoned_sessions: number;
  total_sessions: number;
  completed_sessions?: number;
}

export interface TicketStats {
  total_tickets: number;
  by_category?: Array<{ category: string; count: number }>;
}

export interface TimelinePoint {
  date?: string;
  timestamp?: string;
  hour?: string;
  sessions: number;
  tickets: number;
}

export interface RecentSession {
  name: string;
  phone: string;
  problem?: string;
  category?: string;
  state: string;
  messages: number;
  created_at: string;
}

// Dashboard Response
export interface DashboardResponse {
  overview: OverviewStats;
  categories: { categories: CategoryStats[] };
  quality: QualityMetrics;
  tickets: TicketStats;
  severity: { severities: SeverityStats[] };
  recent_sessions: { sessions: RecentSession[] };
  timeline?: { timeline: TimelinePoint[] };
}

// Performance Types
export interface PerformanceResponse {
  performance_score: number;
  score_grade: string;
  action_items: string[];
}

export interface BenchmarkResponse {
  score?: number;
  industry_avg?: number;
  resolution_rate?: number;
  escalation_rate?: number;
}

// ML Insights Types
export interface MLInsights {
  weekly_trend: {
    direction: 'up' | 'down' | 'stable';
    change_percent: number;
    this_week: number;
    last_week: number;
  };
  kb_effectiveness: {
    ai_resolution_rate: number;
    resolved_by_ai: number;
    escalated: number;
  };
  top_escalated: Array<{ category: string; count: number }>;
  peak_hours: Array<{ hour: number; count: number }>;
  recommendations: Recommendation[];
}

export interface Recommendation {
  type: 'kb_gap' | 'staffing' | 'volume_alert' | 'improvement';
  priority: 'high' | 'medium' | 'low';
  message: string;
}

// Alerts Types
export interface Alert {
  id?: number;
  title: string;
  message?: string;
  description?: string;
  detail?: string;
  severity: 'critical' | 'warning' | 'info';
}

export interface AlertsResponse {
  alerts: Alert[];
  critical_count: number;
  warning_count: number;
}

// Health Check
export interface HealthCheckResponse {
  status: string;
  components: {
    database: string;
    ai_engine: string;
    whatsapp_api: string;
    osticket: string;
    knowledge_base: string;
  };
  timestamp?: string;
}

// Activity Log
export interface ActivityEvent {
  type: string;
  icon: string;
  description: string;
  timestamp: string;
  severity?: string;
}

export interface ActivityLogResponse {
  events: ActivityEvent[];
}

// Date Filter
export interface DateRange {
  startDate: string | null;
  endDate: string | null;
}