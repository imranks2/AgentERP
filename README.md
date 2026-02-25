# AgentERP - AI-Native Enterprise Resource Planning

An AI-first, multi-tenant SaaS ERP platform that learns from every user interaction. Built with a modern tech stack and designed to surpass legacy systems in both functionality and usability.

## Phase 1 - Multi-Tenant Foundation

This phase delivers the core SaaS infrastructure:

### Backend
- **Tenant Management** - Registration, lifecycle states (trial, active, suspended, churned)
- **Subscription Plans** - Free, Standard, Premium with feature gating
- **Tenant Isolation** - Strict `tenant_id` scoping across all data
- **Authentication** - JWT-based auth with access/refresh tokens
- **SaaS Admin Panel** - Platform-wide dashboard and tenant management APIs
- **Analytics Capture** - Event tracking for AI training pipeline

### Frontend
- **Landing Page** - Product showcase with features and pricing
- **Sign-Up Flow** - Tenant registration with auto-login
- **Login Page** - Secure authentication
- **Admin Dashboard** - Tenant list, subscription overview, analytics (platform admins)
- **Tenant Dashboard** - Organisation overview, subscription details, getting started guide

## Tech Stack

| Layer          | Technologies                                       |
|----------------|---------------------------------------------------|
| Backend        | Python, Flask, SQLAlchemy, PostgreSQL, Redis       |
| Frontend       | React 18, React Router, Axios, Lucide Icons        |
| Auth           | Flask-JWT-Extended (JWT access/refresh tokens)     |
| Infrastructure | Docker, Docker Compose, Nginx                      |

## Quick Start

### Prerequisites
- Docker & Docker Compose

### Run with Docker

```bash
docker-compose up --build
```

Access: Frontend at `http://localhost:3000`, API at `http://localhost:5000/api/health`

### Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://agenterp:agenterp_secret@localhost:5432/agenterp
python seed.py   # Initialise database and seed data
python run.py    # Start server on :5000
```

**Frontend:**
```bash
cd frontend
npm install
npm start        # Start dev server on :3000
```

### Default Admin Credentials
- Email: `admin@agenterp.com`
- Password: `admin123`

## API Endpoints

| Method | Endpoint                          | Description              |
|--------|-----------------------------------|--------------------------|
| POST   | `/api/auth/register`              | Register new tenant      |
| POST   | `/api/auth/login`                 | Login                    |
| GET    | `/api/auth/me`                    | Get current user         |
| GET    | `/api/tenants/`                   | List tenants (admin)     |
| PUT    | `/api/tenants/:id/status`         | Change tenant status     |
| GET    | `/api/subscriptions/plans`        | List plans (public)      |
| POST   | `/api/subscriptions/subscribe`    | Subscribe to plan        |
| GET    | `/api/admin/dashboard`            | Platform dashboard       |
| POST   | `/api/analytics/track`            | Track event              |
| GET    | `/api/health`                     | Health check             |

## Roadmap

- [x] Phase 1 - Multi-Tenant Foundation
- [ ] Phase 2 - Organisation Hierarchy
- [ ] Phase 3 - ERP Micro-Kernel Module System
- [ ] Phase 4 - Modern React Frontend (Complete UI)
- [ ] Phase 5 - Authentication & Authorization
- [ ] Phase 6 - Event-Driven Architecture
- [ ] Phase 7 - AI & Agentic Layer
- [ ] Phase 8 - Enterprise Core ERP Modules
- [ ] Phase 9 - Advanced AI & Self-Learning