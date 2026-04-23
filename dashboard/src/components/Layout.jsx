import React from 'react';
import './Layout.css';

const NAV_ITEMS = [
  { id: 'overview',    label: 'Overview',       icon: '📊' },
  { id: 'performance', label: 'AI Performance', icon: '🤖' },
  { id: 'insights',    label: 'Insights',       icon: '💡' },
];

export default function Layout({ currentPage, onNavigate, username, onLogout, children }) {
  return (
    <div className="layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">🚛</div>
          <div className="brand-text">
            <span className="brand-name">TRAMOS</span>
            <span className="brand-sub">AI Dashboard</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {currentPage === item.id && <span className="nav-indicator" />}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-section">
            <div className="user-avatar">
              {(username || 'A').charAt(0).toUpperCase()}
            </div>
            <div className="user-details">
              <span className="user-name">{username || 'Admin'}</span>
              <span className="user-role">Administrator</span>
            </div>
          </div>
          <button className="btn-logout" onClick={onLogout} title="Logout">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
