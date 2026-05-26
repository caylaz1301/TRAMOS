import React from 'react';
import './Layout.css';

const NAV_ITEMS = [
  { id: 'overview',    label: 'Ringkasan',          icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { id: 'performance', label: 'Performa AI',        icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { id: 'insights',    label: 'Laporan & Notifikasi', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
];

function NavIcon({ path }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={path} />
    </svg>
  );
}

export default function Layout({ currentPage, onNavigate, username, userRole, onLogout, children }) {
  const displayRole = {
    admin: 'Administrator',
    user: 'User',
    operator: 'Operator',
    analyst: 'Analyst',
  }[userRole] || 'User';

  return (
    <div className="layout">
      <aside className="sidebar">
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="brand-logo">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect width="28" height="28" rx="8" fill="url(#brand-grad)" />
              <path d="M8 18V12l6-4 6 4v6l-6 4-6-4z" fill="white" fillOpacity="0.9" />
              <path d="M14 8v10M8 12l6 6 6-6" stroke="white" strokeWidth="1.5" strokeOpacity="0.5" />
              <defs>
                <linearGradient id="brand-grad" x1="0" y1="0" x2="28" y2="28">
                  <stop stopColor="#3b82f6" />
                  <stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="brand-text">
            <span className="brand-name">TRAMOS</span>
            <span className="brand-sub">Dashboard</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <div className="nav-section-label">Menu</div>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              <span className="nav-icon"><NavIcon path={item.icon} /></span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div className="user-section">
            <div className="user-avatar">
              {(username || 'U').charAt(0).toUpperCase()}
            </div>
            <div className="user-details">
              <span className="user-name">{username || 'User'}</span>
              <span className="user-role">{displayRole}</span>
            </div>
          </div>
          <button className="btn-logout" onClick={onLogout} title="Keluar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </aside>

      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
