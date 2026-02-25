import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import analytics from '../services/analytics';
import {
  Zap, Shield, BarChart3, Globe, Brain, Layers,
  ArrowRight, Check, ChevronRight
} from 'lucide-react';
import '../styles/landing.css';

function LandingPage() {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    analytics.pageView('landing');
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      navigate(user?.is_platform_admin ? '/admin' : '/dashboard');
    }
  }, [isAuthenticated, user, navigate]);

  const features = [
    {
      icon: <Brain size={28} />,
      title: 'AI-First Design',
      description: 'Every interaction trains the system. Get smarter recommendations, anomaly detection, and autonomous agents that improve over time.',
    },
    {
      icon: <Layers size={28} />,
      title: 'Modular Architecture',
      description: 'Activate only what you need. Inventory, Sales, Purchasing, Accounting, HR, CRM — pick your modules and scale as you grow.',
    },
    {
      icon: <Shield size={28} />,
      title: 'Enterprise Security',
      description: 'Multi-tenant isolation, role-based access control, and complete audit trails. Your data stays yours.',
    },
    {
      icon: <Globe size={28} />,
      title: 'Global Ready',
      description: 'Multi-currency, multi-language, and multi-jurisdiction support from day one. Operate anywhere in the world.',
    },
    {
      icon: <BarChart3 size={28} />,
      title: 'Real-Time Analytics',
      description: 'Dashboards with KPIs, drill-down reports, and AI-powered insights that help you make better decisions faster.',
    },
    {
      icon: <Zap size={28} />,
      title: 'Lightning Fast',
      description: 'Modern tech stack with React and Flask. Smooth animations, instant search, and a command palette (⌘K) for power users.',
    },
  ];

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Perfect for exploring',
      features: ['Up to 3 users', '1 GB storage', 'Inventory & Sales modules', 'Basic reports', 'Community support'],
      cta: 'Start Free',
      highlighted: false,
    },
    {
      name: 'Standard',
      price: '$49.99',
      period: '/month',
      description: 'For growing businesses',
      features: ['Up to 25 users', '50 GB storage', 'All core modules', 'AI Assistant (100 queries/mo)', 'Custom fields', 'Priority support'],
      cta: 'Start Free Trial',
      highlighted: true,
    },
    {
      name: 'Premium',
      price: '$149.99',
      period: '/month',
      description: 'Enterprise scale',
      features: ['Unlimited users', '500 GB storage', 'All modules, unlimited', 'Unlimited AI Assistant', 'Dedicated support', 'Custom integrations'],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  return (
    <div className="landing">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="nav-container">
          <Link to="/" className="nav-logo">
            <Zap size={24} />
            <span>AgentERP</span>
          </Link>
          <div className="nav-links">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <Link to="/login" className="nav-link-login">Log In</Link>
            <Link to="/signup" className="nav-btn-signup">
              Start Free <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-container">
          <div className="hero-badge">
            <Zap size={14} />
            AI-Native ERP Platform
          </div>
          <h1>
            The ERP that <span className="gradient-text">learns</span> from you
          </h1>
          <p className="hero-subtitle">
            AgentERP is a next-generation enterprise platform that gets smarter with every interaction.
            Modular, secure, and designed for modern businesses that refuse to settle for legacy systems.
          </p>
          <div className="hero-actions">
            <Link to="/signup" className="btn-primary">
              Start Free Trial
              <ArrowRight size={18} />
            </Link>
            <a href="#features" className="btn-secondary">
              See Features
              <ChevronRight size={18} />
            </a>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-number">14</span>
              <span className="stat-label">day free trial</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-number">6+</span>
              <span className="stat-label">core modules</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-number">∞</span>
              <span className="stat-label">scalability</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="features-section">
        <div className="section-container">
          <div className="section-header">
            <h2>Built for the future of business</h2>
            <p>Everything you need to run your organisation, powered by AI that evolves with you.</p>
          </div>
          <div className="features-grid">
            {features.map((feature, i) => (
              <div key={i} className="feature-card">
                <div className="feature-icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="pricing-section">
        <div className="section-container">
          <div className="section-header">
            <h2>Simple, transparent pricing</h2>
            <p>Start free and scale as your business grows. No hidden fees.</p>
          </div>
          <div className="pricing-grid">
            {plans.map((plan, i) => (
              <div key={i} className={`pricing-card ${plan.highlighted ? 'highlighted' : ''}`}>
                {plan.highlighted && <div className="pricing-badge">Most Popular</div>}
                <h3>{plan.name}</h3>
                <p className="pricing-description">{plan.description}</p>
                <div className="pricing-price">
                  <span className="price">{plan.price}</span>
                  <span className="period">{plan.period}</span>
                </div>
                <ul className="pricing-features">
                  {plan.features.map((f, j) => (
                    <li key={j}>
                      <Check size={16} />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/signup"
                  className={`pricing-cta ${plan.highlighted ? 'primary' : 'secondary'}`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="section-container">
          <h2>Ready to transform your business?</h2>
          <p>Join forward-thinking organisations using AI-native ERP.</p>
          <Link to="/signup" className="btn-primary btn-large">
            Get Started for Free
            <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-container">
          <div className="footer-brand">
            <div className="nav-logo">
              <Zap size={20} />
              <span>AgentERP</span>
            </div>
            <p>AI-Native Enterprise Resource Planning</p>
          </div>
          <div className="footer-links">
            <div className="footer-column">
              <h4>Product</h4>
              <a href="#features">Features</a>
              <a href="#pricing">Pricing</a>
            </div>
            <div className="footer-column">
              <h4>Company</h4>
              <a href="#about">About</a>
              <a href="#contact">Contact</a>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2026 AgentERP. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
