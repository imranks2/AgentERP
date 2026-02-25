import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import analytics from '../services/analytics';
import { Zap, ArrowRight, Eye, EyeOff } from 'lucide-react';
import '../styles/auth.css';

function LoginPage() {
  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    analytics.pageView('login');
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      navigate(user?.is_platform_admin ? '/admin' : '/dashboard');
    }
  }, [isAuthenticated, user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const userData = await login(email, password);
      analytics.formSubmit('login', true);
      navigate(userData?.is_platform_admin ? '/admin' : '/dashboard');
    } catch (err) {
      const message = err.response?.data?.error || 'Login failed. Please check your credentials.';
      setError(message);
      analytics.formSubmit('login', false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container auth-container-compact">
        <div className="auth-left">
          <div className="auth-brand">
            <Link to="/" className="nav-logo">
              <Zap size={24} />
              <span>AgentERP</span>
            </Link>
          </div>
          <div className="auth-hero">
            <h1>Welcome back</h1>
            <p>Log in to access your organisation's ERP platform.</p>
          </div>
        </div>

        <div className="auth-right">
          <form className="auth-form" onSubmit={handleSubmit}>
            <h2>Log in</h2>

            {error && <div className="form-error">{error}</div>}

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                required
                placeholder="you@company.com"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(''); }}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="input-with-icon">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="Your password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(''); }}
                />
                <button
                  type="button"
                  className="input-icon-btn"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button type="submit" className="btn-primary btn-full" disabled={loading}>
              {loading ? 'Logging in...' : 'Log In'}
              {!loading && <ArrowRight size={18} />}
            </button>

            <p className="auth-footer-text">
              Don't have an account? <Link to="/signup">Sign up free</Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
