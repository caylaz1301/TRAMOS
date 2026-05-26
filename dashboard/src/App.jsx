import React, { useState, useEffect } from 'react';
import Login from './Login.jsx';
import Layout from './components/Layout.jsx';
import OverviewPage from './pages/OverviewPage.jsx';
import PerformancePage from './pages/PerformancePage.jsx';
import InsightsPage from './pages/InsightsPage.jsx';

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState(null);
  const [currentPage, setCurrentPage] = useState('overview');
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    if (savedToken) {
      setToken(savedToken);
      setIsLoggedIn(true);
    }
  }, []);

  const handleLoginSuccess = (accessToken) => {
    setToken(accessToken);
    setIsLoggedIn(true);
  };

  const handleLogoutRequest = () => {
    setShowLogoutModal(true);
  };

  const handleLogoutConfirm = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_role');
    setIsLoggedIn(false);
    setToken(null);
    setCurrentPage('overview');
    setShowLogoutModal(false);
  };

  const handleLogoutCancel = () => {
    setShowLogoutModal(false);
  };

  if (!isLoggedIn) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const userName = localStorage.getItem('user_name') || 'User';
  const userRole = localStorage.getItem('user_role') || 'user';

  const renderPage = () => {
    switch (currentPage) {
      case 'performance':
        return <PerformancePage />;
      case 'insights':
        return <InsightsPage />;
      case 'overview':
      default:
        return <OverviewPage />;
    }
  };

  return (
    <>
      <Layout
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        username={userName}
        userRole={userRole}
        onLogout={handleLogoutRequest}
      >
        {renderPage()}
      </Layout>

      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="logout-overlay" onClick={handleLogoutCancel}>
          <div className="logout-modal" onClick={(e) => e.stopPropagation()}>
            <div className="logout-modal-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </div>
            <h3 className="logout-modal-title">Keluar dari Dashboard?</h3>
            <p className="logout-modal-text">Kamu akan perlu login kembali untuk mengakses dashboard.</p>
            <div className="logout-modal-actions">
              <button className="btn-logout-cancel" onClick={handleLogoutCancel}>Batal</button>
              <button className="btn-logout-confirm" onClick={handleLogoutConfirm}>Ya, Keluar</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
