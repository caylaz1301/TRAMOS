// API Response Types for TRAMOS Dashboard
// These types match the backend analytics.py definitions

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
// Overview Stats - calculated from WhatsAppSession table
export interface OverviewStats {
  total_sessions: number;           // All sessions in date range
  total_tickets: number;            // Sessions with ticket_id IS NOT NULL
  total_messages: number;            // Sum of message_count
  success_rate: number;             // (ai_resolved_sessions / total_sessions) * 100
  avg_messages_per_session: number;  // total_messages / total_sessions
  active_sessions: number;          // Sessions where last_activity >= 5 min ago AND is_active == True
  ai_resolved_sessions: number;     // Sessions where ticket_id IS NULL AND current_state IN ("resolved", "closed")
}

// Category distribution of detected problems
export interface CategoryStats {
  name: string;
  count: number;
}

// Severity/urgency distribution
export interface SeverityStats {
  name: 'critical' | 'high' | 'medium' | 'normal' | 'low';
  count: number;
}

// Quality metrics from session analysis
export interface QualityMetrics {
  completion_rate: number;              // Percentage of completed sessions
  avg_duration_seconds: number;         // Average session duration
  avg_messages: number;                 // Average messages per session
  abandoned_sessions: number;           // current_state != "closed" AND is_active == False
  total_sessions: number;
  completed_sessions?: number;           // Sessions that reached completion
}

// Ticket statistics
export interface TicketStats {
  total_tickets: number;
  by_category?: Array<{ category: string; count: number }>;
}

// Timeline point - hourly data from backend
// Note: Backend returns HOURLY data, frontend should aggregate to daily
export interface TimelinePoint {
  timestamp?: string;    // ISO datetime string like "2026-06-17 10:00:00"
  date?: string;
  hour?: string;
  sessions: number;
  tickets?: number;
  count?: number;       // Alternative field name
}

// Recent session record
export interface RecentSession {
  id?: number;
  name: string;
  phone: string;
  problem?: string;
  category?: string;
  state: string;        // Bot state machine state
  messages?: number;     // Message count
  message_count?: number;
  created_at: string;
  last_activity?: string;
  ticket_id?: number | null;
  is_active?: boolean;
}

// Dashboard Response - combined data from all analytics endpoints
export interface DashboardResponse {
  overview: OverviewStats;
  categories: { categories: CategoryStats[] };
  quality: QualityMetrics;
  tickets: TicketStats;
  severity: { severities: SeverityStats[] };
  recent_sessions: { sessions: RecentSession[] };
  timeline?: { timeline: TimelinePoint[] };
}

// Performance Report from ML analysis
export interface PerformanceResponse {
  performance_score: number;
  score_grade: string;
  action_items: string[];
  summary?: {
    total_sessions: number;
    resolved_by_ai: number;
    escalated: number;
    avg_resolution_time: number;
  };
}

// Benchmark score response
export interface BenchmarkResponse {
  score?: number;
  industry_avg?: number;
  resolution_rate?: number;
  escalation_rate?: number;
  generated_at?: string;
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
  timestamp?: string;
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
  icon?: string;
  description: string;
  timestamp: string;
  severity?: string;
  category?: string;
}

export interface ActivityLogResponse {
  events: ActivityEvent[];
}

// Date Filter
export interface DateRange {
  startDate: string | null;
  endDate: string | null;
}
