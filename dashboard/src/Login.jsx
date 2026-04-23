import React, { useState } from 'react';
import { authService } from './api.js';
import './Login.css';

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Masukkan username dan password');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const response = await authService.login(username, password);
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('username', username);
      onLoginSuccess(response.access_token);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail) {
        setError('Username atau password salah');
      } else if (err.code === 'ERR_NETWORK') {
        setError('Tidak dapat terhubung ke server. Pastikan backend sudah berjalan.');
      } else {
        setError('Terjadi kesalahan. Silakan coba lagi.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-bg">
        <div className="bg-gradient bg-gradient-1" />
        <div className="bg-gradient bg-gradient-2" />
      </div>

      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo">
              <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
                <rect width="44" height="44" rx="12" fill="url(#login-grad)" />
                <path d="M13 28V19l9-6 9 6v9l-9 6-9-6z" fill="white" fillOpacity="0.9" />
                <path d="M22 13v15M13 19l9 9 9-9" stroke="white" strokeWidth="1.5" strokeOpacity="0.4" />
                <defs>
                  <linearGradient id="login-grad" x1="0" y1="0" x2="44" y2="44">
                    <stop stopColor="#3b82f6" />
                    <stop offset="1" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h1>TRAMOS</h1>
            <p>Masuk ke Dashboard</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="login-username">Username</label>
              <input
                id="login-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Masukkan username"
                required
                disabled={loading}
                autoComplete="username"
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Masukkan password"
                required
                disabled={loading}
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div className="login-error">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="login-btn">
              {loading ? (
                <><span className="spinner spinner-sm" /> Memproses...</>
              ) : (
                'Masuk'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
