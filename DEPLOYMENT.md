# Enterprise Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the PagBank Multi-Agent System in enterprise environments. The system is designed for high availability, scalability, and security.

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[NGINX Load Balancer]
    end
    
    subgraph "Application Layer"
        APP1[App Instance 1]
        APP2[App Instance 2]
        APP3[App Instance N]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        REDIS[(Redis Cache)]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        ALERT[AlertManager]
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    
    APP1 --> PG
    APP2 --> PG
    APP3 --> PG
    
    APP1 --> REDIS
    APP2 --> REDIS
    APP3 --> REDIS
    
    PROM --> APP1
    PROM --> APP2
    PROM --> APP3
    GRAF --> PROM
    ALERT --> PROM
```

## 🚀 Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- Git
- SSL certificates for production
- 4GB+ RAM, 50GB+ storage

### One-Command Deployment

```bash
# Clone repository
git clone <repository-url>
cd pagbank-multiagents

# Deploy to staging
./deploy.sh staging v2.0.0

# Deploy to production
./deploy.sh production main
```

## 📋 Detailed Deployment Steps

### 1. Environment Setup

#### Development Environment
```bash
# Copy environment template
cp .env.example .env

# Start development stack
docker-compose up -d

# Access at http://localhost:7777
```

#### Staging Environment
```bash
# Configure staging environment
cp .env.staging .env.staging
# Edit .env.staging with your settings

# Deploy to staging
./deploy.sh staging
```

#### Production Environment
```bash
# Configure production environment
cp .env.production .env.production
# Edit .env.production with secure settings

# Deploy to production with specific version
./deploy.sh production v2.1.0
```

### 2. SSL Certificate Setup

#### Option A: Let's Encrypt (Recommended)
```bash
# Install Certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

#### Option B: Self-Signed (Development/Staging)
```bash
# Generate self-signed certificate
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### 3. Database Setup

#### PostgreSQL Configuration
```bash
# Initialize database
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE pagbank_agents;"

# Run migrations (automatically handled by Agno)
docker-compose exec app python -c "from db.session import init_db; init_db()"
```

#### Backup and Restore
```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres pagbank_agents > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres pagbank_agents < backup.sql
```

### 4. Monitoring Setup

#### Access Monitoring Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Application**: http://localhost:8000

#### Custom Alerts
Edit `monitoring/prometheus.yml` to add custom alerting rules:

```yaml
groups:
  - name: pagbank-agents
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

## 🔒 Security Configuration

### 1. API Key Management
```bash
# Generate secure API key
openssl rand -hex 32

# Set in environment
echo "API_KEY=your-generated-key" >> .env.production
```

### 2. Database Security
```bash
# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Enable SSL for database connections
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 3. Network Security
```bash
# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # Block direct database access
sudo ufw enable
```

## 📊 Performance Optimization

### 1. Application Scaling
```yaml
# docker-compose.production.yml
services:
  app:
    deploy:
      replicas: 4
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### 2. Database Tuning
```sql
-- PostgreSQL optimizations
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

### 3. Redis Configuration
```bash
# Redis memory optimization
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 🔧 Maintenance

### Daily Operations
```bash
# Check system health
./deploy.sh production main true  # Dry run

# View logs
docker-compose logs -f app

# Monitor resource usage
docker stats
```

### Weekly Maintenance
```bash
# Update dependencies
uv lock --upgrade

# Security scan
docker run --rm -v $(pwd):/app aquasec/trivy fs /app

# Database maintenance
docker-compose exec postgres vacuumdb -U postgres -d pagbank_agents --analyze
```

### Backup Strategy
```bash
# Automated daily backups
0 2 * * * /path/to/backup-script.sh

# Test backup restoration monthly
0 0 1 * * /path/to/test-restore.sh
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check logs
docker-compose logs app

# Verify environment variables
docker-compose exec app env | grep -E "(DATABASE_URL|REDIS_URL)"

# Test database connectivity
docker-compose exec app python -c "from db.session import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 2. High Memory Usage
```bash
# Check memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Restart services if needed
docker-compose restart app
```

#### 3. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Test SSL configuration
curl -I https://your-domain.com
```

### Health Checks
```bash
# Application health
curl -f http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

## 📈 Scaling Guidelines

### Horizontal Scaling
1. **Application Layer**: Scale to 2-4 instances based on CPU usage
2. **Database**: Consider read replicas for >1000 concurrent users
3. **Cache**: Redis cluster for >10GB cache requirements

### Vertical Scaling
- **Memory**: 2GB per application instance
- **CPU**: 1 core per application instance
- **Storage**: 100GB+ for production database

### Load Testing
```bash
# Install k6
sudo apt-get install k6

# Run load test
k6 run tests/load/basic-load-test.js
```

## 🔄 CI/CD Integration

### GitHub Actions
The included `.github/workflows/ci-cd.yml` provides:
- Automated testing
- Security scanning
- Docker image building
- Multi-environment deployment

### Manual Deployment
```bash
# Deploy specific version
git tag v2.1.0
git push origin v2.1.0
./deploy.sh production v2.1.0
```

## 📞 Support

### Monitoring Alerts
- **Email**: Configure SMTP in environment
- **Slack**: Set `SLACK_WEBHOOK_URL` for notifications
- **PagerDuty**: Integrate with Prometheus AlertManager

### Log Analysis
```bash
# Application logs
docker-compose logs app | grep ERROR

# Access logs
docker-compose logs nginx | grep "HTTP/1.1"

# Database logs
docker-compose logs postgres
```

### Performance Metrics
- **Response Time**: Target <500ms average
- **Throughput**: 1000+ requests/minute
- **Availability**: 99.9% uptime
- **Error Rate**: <0.1% of requests

## 📝 Additional Resources

- [Agno Framework Documentation](https://docs.phidata.com)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Docker Production Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

For technical support or deployment assistance, please refer to the repository issues or contact the development team.