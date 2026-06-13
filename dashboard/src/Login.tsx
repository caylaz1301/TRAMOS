import React, { useState, useEffect, useCallback, useRef } from 'react';
import { authService } from './api';
import './Login.css';

// Google Client ID dari environment variable
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

export default function Login({ onLoginSuccess }) {
  const [isSignUp, setIsSignUp] = useState(false);
  // Sign-up step: 'form' → 'otp'
  const [signUpStep, setSignUpStep] = useState('form');
  const [pendingEmail, setPendingEmail] = useState('');

  // Form fields
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // OTP
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const otpRefs = useRef([]);

  // UI state
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [accountPrompt, setAccountPrompt] = useState(false);
  const [heroImageLoaded, setHeroImageLoaded] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);

  useEffect(() => {
    if (!showTerms) return undefined;

    const closeWithEscape = (event) => {
      if (event.key === 'Escape') setShowTerms(false);
    };
    document.addEventListener('keydown', closeWithEscape);
    return () => document.removeEventListener('keydown', closeWithEscape);
  }, [showTerms]);

  // ── Reset state on mode toggle ──
  const toggleMode = (toSignUp) => {
    setIsSignUp(toSignUp);
    setSignUpStep('form');
    setError('');
    setSuccess('');
    setAccountPrompt(false);
    setShowPassword(false);
    setOtp(['', '', '', '', '', '']);
  };

  // ═══════════════════════════════════════════════
  // GOOGLE SSO
  // ═══════════════════════════════════════════════

  // useCallback dengan isSignUp sebagai dependency untuk avoid stale closure
  const handleGoogleCallback = useCallback(async (response) => {
    setError('');
    setLoading(true);
    try {
      const result = await authService.googleLogin(response.credential, isSignUp);

      // If backend says OTP verification needed (sign-up flow)
      if (result.needs_verification) {
        setPendingEmail(result.email);
        if (!isSignUp) setIsSignUp(true);
        setSignUpStep('otp');
        setSuccess(result.message || 'Kode verifikasi telah dikirim ke email kamu!');
        setError('');
        return;
      }

      // Normal login success
      localStorage.setItem('access_token', result.access_token);
      localStorage.setItem('user_name', result.user?.name || 'User');
      localStorage.setItem('user_email', result.user?.email || '');
      localStorage.setItem('user_role', result.user?.role || 'user');
      onLoginSuccess(result.access_token);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const httpStatus = err.response?.status;
      if (
        httpStatus === 401 &&
        typeof detail === 'string' &&
        (detail.toLowerCase().includes('belum terdaftar') ||
          detail.toLowerCase().includes('tidak ditemukan'))
      ) {
        setAccountPrompt(true);
        setError('Akun Google ini belum terdaftar. Buat akun terlebih dahulu untuk masuk.');
      } else {
        setError(typeof detail === 'string' ? detail : 'Google login gagal. Coba lagi.');
      }
    } finally {
      setLoading(false);
    }
  }, [onLoginSuccess, isSignUp]);

  // Initialize Google Identity Services
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      console.warn('VITE_GOOGLE_CLIENT_ID not configured - Google login disabled');
      return;
    }

    const initGoogle = () => {
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCallback,
          auto_select: false,
          cancel_on_tap_outside: true,
        });
      }
    };

    if (window.google?.accounts?.id) {
      initGoogle();
    } else {
      // Poll until Google SDK is loaded
      const iv = setInterval(() => {
        if (window.google?.accounts?.id) {
          initGoogle();
          clearInterval(iv);
        }
      }, 200);
      return () => clearInterval(iv);
    }
  }, [handleGoogleCallback]);

  const handleGoogleLogin = () => {
    if (isSignUp && !acceptedTerms) {
      setError('Setujui Syarat dan Ketentuan terlebih dahulu untuk membuat akun.');
      return;
    }
    if (!GOOGLE_CLIENT_ID) {
      setError('Google login belum dikonfigurasi.');
      return;
    }
    if (!window.google?.accounts?.id) {
      setError('Google belum siap. Tunggu sebentar...');
      return;
    }
    window.google.accounts.id.prompt((n) => {
      if (n.isNotDisplayed() || n.isSkippedMoment()) {
        const c = document.getElementById('google-btn-hidden');
        if (c) {
          c.innerHTML = '';
          window.google.accounts.id.renderButton(c, { type: 'standard', theme: 'outline', size: 'large', width: 300 });
          setTimeout(() => { const b = c.querySelector('div[role="button"]'); if (b) b.click(); }, 100);
        }
      }
    });
  };

  // ═══════════════════════════════════════════════
  // SIGN IN
  // ═══════════════════════════════════════════════

  const handleSignIn = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) { setError('Mohon lengkapi semua data'); return; }
    setError(''); setSuccess(''); setAccountPrompt(false); setLoading(true);
    try {
      const response = await authService.login(email.trim(), password);
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user_name', response.user?.name || email);
      localStorage.setItem('user_email', response.user?.email || email);
      localStorage.setItem('user_role', response.user?.role || 'user');
      onLoginSuccess(response.access_token);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const httpStatus = err.response?.status;
      if (httpStatus === 403) {
        // Account not verified
        setPendingEmail(email.trim().toLowerCase());
        setError(typeof detail === 'string' ? detail : 'Akun belum diverifikasi.');
      } else if (httpStatus === 401 && typeof detail === 'string' && detail.toLowerCase().includes('akun tidak ditemukan')) {
        setAccountPrompt(true);
        setError('Akun belum terdaftar. Buat akun terlebih dahulu untuk masuk ke dashboard TRAMOS.');
      } else if (typeof detail === 'string') {
        setError(detail);
      } else if (err.code === 'ERR_NETWORK') {
        setError('Tidak dapat terhubung ke server.');
      } else {
        setError('Login gagal. Silakan coba lagi.');
      }
    } finally { setLoading(false); }
  };

  const handleOpenSignUpFromPrompt = () => {
    const currentEmail = email.trim().toLowerCase();
    toggleMode(true);
    setEmail(currentEmail);
    setError('');
    setSuccess('');
  };

  // ═══════════════════════════════════════════════
  // SIGN UP (Step 1: Form → Step 2: OTP)
  // ═══════════════════════════════════════════════

  const handleSignUp = async (e) => {
    e.preventDefault();
    if (!acceptedTerms) {
      setError('Setujui Syarat dan Ketentuan terlebih dahulu untuk membuat akun.');
      return;
    }
    if (!fullName.trim() || !email.trim() || !password.trim()) {
      setError('Mohon lengkapi nama, email, dan password');
      return;
    }
    if (password.trim().length < 6) {
      setError('Password minimal 6 karakter');
      return;
    }
    setError(''); setLoading(true);
    try {
      const result = await authService.register(
        fullName.trim(),
        email.trim().toLowerCase(),
        password,
        phone.trim()
      );
      setPendingEmail(email.trim().toLowerCase());
      setSignUpStep('otp');
      setSuccess(result.message || 'Kode verifikasi telah dikirim ke email kamu!');
      setError('');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Pendaftaran gagal.');
    } finally { setLoading(false); }
  };

  // ═══════════════════════════════════════════════
  // OTP VERIFICATION
  // ═══════════════════════════════════════════════

  const handleOtpChange = (index, value) => {
    if (value.length > 1) value = value.slice(-1);
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtp = [...otp];
    for (let i = 0; i < text.length; i++) newOtp[i] = text[i];
    setOtp(newOtp);
    otpRefs.current[Math.min(text.length, 5)]?.focus();
  };

  const handleVerifyOtp = async () => {
    const code = otp.join('');
    if (code.length !== 6) { setError('Masukkan 6 digit kode OTP'); return; }
    setError(''); setLoading(true);
    try {
      await authService.verifyOtp(pendingEmail, code);
      setSuccess('Akun berhasil diverifikasi! Silakan login.');
      setSignUpStep('form');
      // Switch to Sign In after successful verification
      setTimeout(() => {
        toggleMode(false);
        setEmail(pendingEmail);
        setSuccess('Akun terverifikasi! Silakan login.');
      }, 1500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Verifikasi gagal.');
    } finally { setLoading(false); }
  };

  const handleResendOtp = async () => {
    setError(''); setLoading(true);
    try {
      const result = await authService.resendOtp(pendingEmail);
      setSuccess(result.message || 'Kode OTP baru telah dikirim!');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Gagal mengirim ulang kode verifikasi.');
    } finally { setLoading(false); }
  };

  // ═══════════════════════════════════════════════
  // SHARED COMPONENTS
  // ═══════════════════════════════════════════════

  const EyeIcon = () => (
    <span className="eye-icon" onClick={() => setShowPassword(!showPassword)}>
      {showPassword ? (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" /><line x1="1" y1="1" x2="23" y2="23" /></svg>
      ) : (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
      )}
    </span>
  );

  const GoogleButton = ({ label }) => (
    <div className="sso-buttons">
      <button type="button" onClick={handleGoogleLogin} className="btn-sso btn-sso-google" disabled={loading}>
        <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
        {label || 'Continue with Google'}
      </button>
    </div>
  );

  const DividerOr = () => (
    <div className="divider-or">
      <span className="divider-line" />
      <span className="divider-text">atau</span>
      <span className="divider-line" />
    </div>
  );

  // ═══════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════

  return (
    <div className={`luxury-login-wrapper ${isSignUp ? 'sign-up-active' : ''}`}>
      <div className="luxury-card">

        {/* ── Left Panel: Sign In ── */}
        <div className="form-section sign-in-section">
          <div className="form-container">
            <div className="brand-logo-text">TRAMOS</div>
            <div className="form-heading">
              <h1>Welcome back</h1>
              <p>Sign in to access your dashboard</p>
            </div>

            <form onSubmit={handleSignIn} className="luxury-form">
              <GoogleButton label="Sign in with Google" />
              <DividerOr />

              <div className="input-group">
                <label>Email or Phone</label>
                <input type="text" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="nama@email.com" required disabled={loading} className="pill-input" />
              </div>
              <div className="input-group">
                <label>Password</label>
                <div className="password-wrapper">
                  <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••••••" required disabled={loading} className="pill-input" />
                  <EyeIcon />
                </div>
              </div>

              {accountPrompt && !isSignUp ? (
                <div className="account-prompt" role="alert">
                  <div className="account-prompt-title">Akun belum ditemukan</div>
                  <div className="account-prompt-text">
                    Email atau nomor ini belum terdaftar. Buat akun dulu, lalu verifikasi email sebelum login.
                  </div>
                  <button type="button" className="account-prompt-button" onClick={handleOpenSignUpFromPrompt}>
                    Create Account
                  </button>
                </div>
              ) : (
                error && !isSignUp && <div className="error-toast">{error}</div>
              )}
              {success && !isSignUp && <div className="success-toast">{success}</div>}

              <button type="submit" disabled={loading} className="btn-pill-primary">
                {loading ? 'Memproses...' : 'Sign In'}
              </button>

              <div className="form-footer">
                <span className="footer-link">
                  Don't have an account? <b onClick={() => toggleMode(true)}>Sign up</b>
                </span>
                <button type="button" className="terms-link" onClick={() => setShowTerms(true)}>
                  Terms & Conditions
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* ── Right Panel: Sign Up ── */}
        <div className="form-section sign-up-section">
          <div className="form-container">
            <div className="brand-logo-text">TRAMOS</div>

            {signUpStep === 'form' ? (
              <>
                <div className="form-heading">
                  <h1>Create an account</h1>
                  <p>Daftar untuk mengakses dashboard</p>
                </div>

                <form onSubmit={handleSignUp} className="luxury-form">
                  <GoogleButton label="Sign up with Google" />
                  <DividerOr />

                  <div className="input-group">
                    <label>Full name</label>
                    <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="John Doe" disabled={loading} className="pill-input" required />
                  </div>
                  <div className="input-group">
                    <label>Email</label>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="nama@email.com" required disabled={loading} className="pill-input" />
                  </div>
                  <div className="input-group">
                    <label>Phone <span className="label-optional">(opsional)</span></label>
                    <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+62 812 3456 7890" disabled={loading} className="pill-input" />
                  </div>
                  <div className="input-group">
                    <label>Password</label>
                    <div className="password-wrapper">
                      <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min. 6 karakter" required disabled={loading} className="pill-input" />
                      <EyeIcon />
                    </div>
                  </div>

                  <label className="terms-consent">
                    <input
                      type="checkbox"
                      checked={acceptedTerms}
                      onChange={(event) => setAcceptedTerms(event.target.checked)}
                      disabled={loading}
                    />
                    <span>
                      Saya menyetujui{' '}
                      <button type="button" onClick={() => setShowTerms(true)}>
                        Syarat dan Ketentuan
                      </button>
                      .
                    </span>
                  </label>

                  {error && isSignUp && <div className="error-toast">{error}</div>}

                  <button type="submit" disabled={loading || !acceptedTerms} className="btn-pill-primary">
                    {loading ? 'Memproses...' : 'Create Account'}
                  </button>

                  <div className="form-footer">
                    <span className="footer-link">
                      Have an account? <b onClick={() => toggleMode(false)}>Sign in</b>
                    </span>
                    <button type="button" className="terms-link" onClick={() => setShowTerms(true)}>
                      Terms & Conditions
                    </button>
                  </div>
                </form>
              </>
            ) : (
              /* ── OTP Verification Step ── */
              <div className="otp-screen">
                <div className="otp-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="4" width="20" height="16" rx="2" />
                    <path d="M22 7l-10 6L2 7" />
                  </svg>
                </div>
                <h2 className="otp-title">Verifikasi Email</h2>
                <p className="otp-subtitle">
                  Masukkan 6 digit kode yang dikirim ke<br />
                  <strong>{pendingEmail}</strong>
                </p>

                <div className="otp-inputs" onPaste={handleOtpPaste}>
                  {otp.map((digit, i) => (
                    <input
                      key={i}
                      ref={(el) => (otpRefs.current[i] = el)}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(i, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      className={`otp-digit ${digit ? 'filled' : ''}`}
                      disabled={loading}
                      autoFocus={i === 0}
                    />
                  ))}
                </div>

                {error && <div className="error-toast">{error}</div>}
                {success && <div className="success-toast">{success}</div>}

                <button onClick={handleVerifyOtp} disabled={loading || otp.join('').length !== 6} className="btn-pill-primary">
                  {loading ? 'Memverifikasi...' : 'Verifikasi'}
                </button>

                <div className="otp-actions">
                  <span className="otp-resend" onClick={!loading ? handleResendOtp : undefined}>
                    Tidak menerima kode? <b>Kirim Ulang</b>
                  </span>
                  <span className="otp-back" onClick={() => setSignUpStep('form')}>
                    ← Kembali
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Sliding Image Door ── */}
        <div className="image-section">
          <img
            src={`${import.meta.env.BASE_URL}loginpage.webp`}
            alt="TRAMOS Logistics"
            className={`luxury-bg-img ${heroImageLoaded ? 'is-loaded' : ''}`}
            loading="eager"
            fetchPriority="high"
            decoding="async"
            onLoad={() => setHeroImageLoaded(true)}
          />
          <div className="image-overlay-gradient"></div>
        </div>

      </div>
      <div id="google-btn-hidden" style={{ position: 'absolute', top: '-9999px', left: '-9999px' }}></div>

      {showTerms && (
        <div className="terms-modal-backdrop" onMouseDown={() => setShowTerms(false)}>
          <section
            className="terms-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="terms-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header className="terms-modal-header">
              <div>
                <span className="terms-modal-brand">TRAMOS</span>
                <h2 id="terms-title">Syarat dan Ketentuan</h2>
                <p>Berlaku sejak 13 Juni 2026</p>
              </div>
              <button
                type="button"
                className="terms-close-button"
                aria-label="Tutup Syarat dan Ketentuan"
                onClick={() => setShowTerms(false)}
              >
                ×
              </button>
            </header>

            <div className="terms-modal-content">
              <div className="terms-summary">
                Dengan menggunakan TRAMOS, kamu setuju menggunakan layanan secara bertanggung
                jawab dan menjaga keamanan akun serta data operasional.
              </div>

              <article>
                <h3>1. Penggunaan layanan</h3>
                <p>
                  TRAMOS menyediakan dashboard operasional, chatbot dukungan, pemantauan layanan,
                  dan pengelolaan laporan. Layanan hanya boleh digunakan untuk kebutuhan kerja
                  yang sah dan sesuai kewenangan pengguna.
                </p>
              </article>

              <article>
                <h3>2. Akun dan keamanan</h3>
                <p>
                  Pengguna wajib memberikan informasi yang benar, menjaga kerahasiaan password
                  dan kode verifikasi, serta segera melaporkan aktivitas akun yang mencurigakan.
                  Setiap aktivitas melalui akun dianggap dilakukan oleh pemilik akun tersebut.
                </p>
              </article>

              <article>
                <h3>3. Data dan privasi</h3>
                <p>
                  TRAMOS dapat memproses identitas pengguna, nomor kontak, percakapan dukungan,
                  informasi kendaraan, lokasi yang dilaporkan, dan data tiket untuk menjalankan
                  layanan, analitik, keamanan, dan peningkatan kualitas sistem.
                </p>
              </article>

              <article>
                <h3>4. Penggunaan AI</h3>
                <p>
                  Jawaban chatbot bersifat bantuan awal dan dapat memerlukan verifikasi operator.
                  Untuk keadaan darurat, keselamatan jalan, atau keputusan operasional penting,
                  pengguna wajib mengikuti SOP perusahaan dan menghubungi petugas yang berwenang.
                </p>
              </article>

              <article>
                <h3>5. Larangan</h3>
                <p>
                  Pengguna dilarang menyalahgunakan layanan, mencoba mengakses data tanpa izin,
                  mengganggu sistem, memasukkan informasi palsu, membagikan kredensial, atau
                  menggunakan TRAMOS untuk tindakan yang melanggar hukum.
                </p>
              </article>

              <article>
                <h3>6. Ketersediaan dan perubahan layanan</h3>
                <p>
                  Layanan dapat mengalami pemeliharaan, pembaruan, atau gangguan di luar kendali.
                  Fitur dan ketentuan dapat diperbarui untuk mengikuti kebutuhan operasional,
                  keamanan, dan ketentuan hukum yang berlaku.
                </p>
              </article>

              <article>
                <h3>7. Penghentian dan penghapusan akun</h3>
                <p>
                  Akses dapat dibatasi jika terjadi pelanggaran, risiko keamanan, atau permintaan
                  organisasi. Pengguna dapat mengajukan penghapusan akun melalui menu profil,
                  dengan tetap memperhatikan kewajiban penyimpanan data operasional.
                </p>
              </article>

              <article>
                <h3>8. Dukungan</h3>
                <p>
                  Pertanyaan mengenai akun, data, atau layanan dapat disampaikan kepada
                  administrator TRAMOS atau tim dukungan perusahaan.
                </p>
              </article>
            </div>

            <footer className="terms-modal-footer">
              <button type="button" className="terms-secondary-button" onClick={() => setShowTerms(false)}>
                Tutup
              </button>
              {isSignUp && (
                <button
                  type="button"
                  className="terms-accept-button"
                  onClick={() => {
                    setAcceptedTerms(true);
                    setError('');
                    setShowTerms(false);
                  }}
                >
                  Saya Setuju
                </button>
              )}
            </footer>
          </section>
        </div>
      )}
    </div>
  );
}
