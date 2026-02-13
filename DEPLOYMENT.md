# CUSTOS Backend Deployment Guide

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+ (optional, for caching)
- Node.js 18+ (for frontend)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/custos-school-management-system.git
cd custos-school-management-system
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required Environment Variables:**

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/custos

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# Celery (optional)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# AI Providers
OPENAI_API_KEY=your-openai-key
GOOGLE_API_KEY=your-google-key

# Payment Gateway
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

#### Database Migration

```bash
alembic upgrade head
```

#### Initialize Database (Optional)

```bash
python init_db.py
```

### 3. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Celery Worker (Optional)

```bash
celery -A app.core.celery_app worker --loglevel=info
```

### 5. Run Celery Beat (Optional)

```bash
celery -A app.core.celery_app beat --loglevel=info
```

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
docker-compose up -d
```

**Services:**

- `api` - FastAPI backend (port 8000)
- `postgres` - PostgreSQL database (port 5432)
- `redis` - Redis cache (port 6379)
- `celery_worker` - Background task worker
- `celery_beat` - Scheduled task scheduler

### Build Custom Image

```bash
docker build -t custos-backend .
docker run -p 8000:8000 --env-file .env custos-backend
```

---

## ☁️ Production Deployment

### Option 1: Traditional Server (Ubuntu)

#### 1. Install Dependencies

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql-14 redis-server nginx
```

#### 2. Setup Application

```bash
cd /opt
git clone <repo-url> custos
cd custos
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configure Systemd Service

Create `/etc/systemd/system/custos.service`:

```ini
[Unit]
Description=CUSTOS FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/custos
Environment="PATH=/opt/custos/venv/bin"
ExecStart=/opt/custos/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4. Configure Nginx

Create `/etc/nginx/sites-available/custos`:

```nginx
server {
    listen 80;
    server_name api.custos.school;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 5. Enable and Start Services

```bash
sudo systemctl enable custos
sudo systemctl start custos
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### Option 2: Cloud Platforms

#### AWS Elastic Beanstalk

```bash
eb init -p python-3.11 custos-backend
eb create custos-prod
eb deploy
```

#### Google Cloud Run

```bash
gcloud run deploy custos-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Heroku

```bash
heroku create custos-backend
git push heroku main
heroku ps:scale web=1
```

#### Railway

```bash
railway init
railway up
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Suite

```bash
pytest tests/test_hostel_api.py -v
```

### Run Integration Tests

```bash
pytest -m integration
```

---

## 📊 Monitoring

### Health Checks

- Basic: `GET /health`
- Detailed: `GET /health/detailed`
- Readiness: `GET /health/ready`
- Liveness: `GET /health/live`

### Prometheus Metrics

- Endpoint: `GET /metrics`
- Grafana Dashboard: Import `monitoring/grafana-dashboard.json`

### Logging

Logs are written to:

- Console (development)
- File: `logs/custos.log` (production)
- Sentry (errors only)

---

## 🔒 Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Backup database regularly

---

## 🔧 Performance Optimization

### Database

- Indexes created automatically (see `app/core/db_indexes.py`)
- Connection pooling configured
- Query optimization enabled

### Caching

- Redis caching for frequent queries
- Cache TTL: 5 minutes (configurable)
- Automatic cache invalidation

### Background Tasks

- Celery for async operations
- Email sending
- Report generation
- Scheduled tasks

---

## 📝 API Documentation

Once running, access:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U postgres -h localhost -d custos
```

### Redis Connection Issues

```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping
```

### Migration Issues

```bash
# Check current version
alembic current

# View migration history
alembic history

# Rollback one version
alembic downgrade -1
```

---

## 📞 Support

- Documentation: https://docs.custos.school
- Issues: https://github.com/your-org/custos/issues
- Email: support@custos.school
