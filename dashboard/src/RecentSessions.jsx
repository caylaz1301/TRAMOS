import React from 'react';
import './RecentSessions.css';

export default function RecentSessions({ sessions }) {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getStateColor = (state) => {
    const stateColors = {
      'closed': '#10b981',
      'greeting': '#3b82f6',
      'collecting_name': '#f59e0b',
      'collecting_problem': '#f59e0b',
      'collecting_unit': '#f59e0b',
      'collecting_location': '#f59e0b',
      'collecting_time': '#f59e0b',
      'confirming_details': '#8b5cf6',
      'creating_ticket': '#06b6d4'
    };
    return stateColors[state] || '#9ca3af';
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      'critical': '🔴',
      'high': '🟠',
      'medium': '🟡',
      'low': '🟢'
    };
    return icons[severity] || '⚪';
  };

  return (
    <div className="recent-sessions-container">
      <h2>📋 Recent Sessions</h2>
      <div className="sessions-table-wrapper">
        <table className="sessions-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Phone</th>
              <th>Driver Name</th>
              <th>Problem</th>
              <th>Category</th>
              <th>Severity</th>
              <th>State</th>
              <th>Messages</th>
              <th>Ticket ID</th>
            </tr>
          </thead>
          <tbody>
            {sessions && sessions.length > 0 ? (
              sessions.map((session, idx) => (
                <tr key={idx}>
                  <td className="time">{formatDate(session.created_at)}</td>
                  <td className="phone">{session.phone}</td>
                  <td className="name">{session.name || 'Unknown'}</td>
                  <td className="problem" title={session.problem}>{session.problem || 'N/A'}</td>
                  <td className="category">{session.category || 'N/A'}</td>
                  <td className="severity">
                    <span className="severity-badge">
                      {getSeverityIcon(session.severity)} {session.severity || 'N/A'}
                    </span>
                  </td>
                  <td className="state">
                    <span className="state-badge" style={{ backgroundColor: getStateColor(session.state) }}>
                      {session.state.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="messages">{session.messages}</td>
                  <td className="ticket-id">
                    {session.ticket_id ? (
                      <span className="ticket-badge">#{session.ticket_id}</span>
                    ) : (
                      <span className="no-ticket">-</span>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="9" className="no-sessions">No sessions yet</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
