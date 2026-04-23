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

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    setIsLoggedIn(false);
    setToken(null);
    setCurrentPage('overview');
  };

  if (!isLoggedIn) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const username = localStorage.getItem('username') || 'Admin';

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
    <Layout
      currentPage={currentPage}
      onNavigate={setCurrentPage}
      username={username}
      onLogout={handleLogout}
    >
      {renderPage()}
    </Layout>
  );
}
