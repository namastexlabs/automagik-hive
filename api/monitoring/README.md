# PagBank Multi-Agent System - Monitoring & Analytics

This monitoring system provides comprehensive real-time monitoring, performance analytics, and alerting for the PagBank Multi-Agent System.

## Features

### 📊 Real-Time Monitoring
- **System Health Monitoring**: CPU, memory, disk usage, network connectivity
- **Agent Performance Tracking**: Response times, success rates, error rates
- **Database Health Checks**: Connection status, query performance
- **Active Session Monitoring**: Real-time session count and activity

### 🔔 Intelligent Alerting
- **Configurable Alert Rules**: Memory usage, CPU usage, agent performance thresholds
- **Multiple Delivery Methods**: Email, Webhook, WhatsApp, Log-based alerts
- **Alert Cooldown**: Prevents alert spam with configurable cooldown periods
- **Alert Acknowledgment**: Track who acknowledged alerts and when

### 📈 Advanced Analytics
- **Performance Trends**: Hourly and daily performance analysis
- **Agent Comparison**: Compare performance across different agents
- **Anomaly Detection**: Identify unusual patterns in system behavior
- **Predictive Insights**: Recommendations for performance optimization

### 🎯 Specialized Analytics
- **Typification Analytics**: Track accuracy of request classification
- **Versioning Analytics**: Monitor agent version performance and rollback rates
- **Business Intelligence**: Insights into customer interaction patterns

### 🖥️ Interactive Dashboard
- **Real-Time Dashboard**: Live updates of system status and metrics
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Customizable Views**: Focus on specific metrics or time periods
- **Export Capabilities**: Download reports and metrics data

## API Endpoints

### Health & Status
- `GET /v1/monitoring/health` - Overall system health
- `GET /v1/monitoring/health/{service_name}` - Specific service health
- `GET /v1/monitoring/dashboard` - Interactive monitoring dashboard

### Metrics & Analytics
- `GET /v1/monitoring/metrics` - System-wide metrics
- `GET /v1/monitoring/metrics/agents` - Agent performance metrics
- `GET /v1/monitoring/analytics` - Analytics data (hourly/daily)
- `GET /v1/monitoring/performance-report` - Comprehensive performance report

### Alerts & Notifications
- `GET /v1/monitoring/alerts` - List active/resolved alerts
- `POST /v1/monitoring/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `POST /v1/monitoring/alerts/{alert_id}/resolve` - Resolve alert
- `GET /v1/monitoring/alerts/rules` - View alert rules
- `PUT /v1/monitoring/alerts/rules/{rule_name}` - Update alert rule

### Specialized Analytics
- `GET /v1/monitoring/analytics/typification` - Typification accuracy analytics
- `GET /v1/monitoring/analytics/versioning` - Version performance analytics

### System Control
- `POST /v1/monitoring/start-monitoring` - Start monitoring system
- `POST /v1/monitoring/stop-monitoring` - Stop monitoring system
- `POST /v1/monitoring/evaluate-alerts` - Manually trigger alert evaluation

## Configuration

### Environment Variables

```bash
# Monitoring Features
MONITORING_METRICS_ENABLED=true
MONITORING_HEALTH_CHECKS_ENABLED=true
MONITORING_ALERTING_ENABLED=true
MONITORING_ANALYTICS_ENABLED=true
MONITORING_DASHBOARD_ENABLED=true

# Performance Thresholds
MONITORING_RESPONSE_TIME_WARNING=2.0
MONITORING_RESPONSE_TIME_CRITICAL=5.0
MONITORING_SUCCESS_RATE_WARNING=95.0
MONITORING_SUCCESS_RATE_CRITICAL=90.0
MONITORING_MEMORY_WARNING=80.0
MONITORING_MEMORY_CRITICAL=90.0
MONITORING_CPU_WARNING=80.0
MONITORING_CPU_CRITICAL=95.0

# Intervals & Retention
MONITORING_COLLECTION_INTERVAL=30
MONITORING_HEALTH_CHECK_INTERVAL=30
MONITORING_ALERT_COOLDOWN=15
MONITORING_METRICS_RETENTION_DAYS=30

# Storage Paths
MONITORING_METRICS_STORAGE=logs/metrics
MONITORING_ALERT_STORAGE=logs/alerts
MONITORING_ANALYTICS_STORAGE=logs/analytics

# Email Notifications
MONITORING_EMAIL_ENABLED=false
MONITORING_EMAIL_SMTP_SERVER=smtp.gmail.com
MONITORING_EMAIL_SMTP_PORT=587
MONITORING_EMAIL_USERNAME=your-email@gmail.com
MONITORING_EMAIL_PASSWORD=your-app-password
MONITORING_EMAIL_RECIPIENTS=admin@company.com,ops@company.com

# Webhook Notifications
MONITORING_WEBHOOK_ENABLED=false
MONITORING_WEBHOOK_URL=https://your-webhook-url.com/alerts
MONITORING_WEBHOOK_TOKEN=your-webhook-token

# WhatsApp Notifications
MONITORING_WHATSAPP_ENABLED=false
MONITORING_WHATSAPP_INSTANCE=your-evolution-instance
MONITORING_WHATSAPP_RECIPIENT=5511999999999
```

## Quick Start

### 1. Install Dependencies

```bash
# Install required packages
uv add psutil numpy pandas

# Or install development dependencies
uv add --dev pytest pytest-asyncio pytest-mock
```

### 2. Start the System

The monitoring system starts automatically with the FastAPI application:

```bash
# Start the API server
uv run python api/main.py

# Or use uvicorn directly
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the Dashboard

Open your browser and navigate to:
- **Dashboard**: http://localhost:8000/v1/monitoring/dashboard
- **API Docs**: http://localhost:8000/docs

### 4. Monitor System Health

```bash
# Check system health
curl http://localhost:8000/v1/monitoring/health

# Get agent metrics
curl http://localhost:8000/v1/monitoring/metrics/agents

# View active alerts
curl http://localhost:8000/v1/monitoring/alerts?status=active
```

## Alert Rules

### Default Alert Rules

| Rule Name | Condition | Threshold | Severity | Description |
|-----------|-----------|-----------|----------|-------------|
| `high_memory_usage` | Memory > 85% | 85% | HIGH | High memory usage detected |
| `critical_memory_usage` | Memory > 95% | 95% | CRITICAL | Critical memory usage detected |
| `high_cpu_usage` | CPU > 80% | 80% | HIGH | High CPU usage detected |
| `low_agent_success_rate` | Success rate < 90% | 90% | HIGH | Low agent success rate |
| `high_response_time` | Response time > 5s | 5s | MEDIUM | High response time detected |
| `database_connection_failed` | DB status = down | N/A | CRITICAL | Database connection failed |
| `service_down` | Service status = down | N/A | CRITICAL | Service is down |

### Custom Alert Rules

You can create custom alert rules by updating the configuration:

```python
# Example: Custom alert rule
custom_rule = AlertRule(
    name="custom_performance_alert",
    condition="custom_metric > threshold",
    threshold=100.0,
    severity=AlertSeverity.MEDIUM,
    message_template="Custom alert: {metric_name} is {value}",
    cooldown_minutes=30
)

alert_manager.alert_rules["custom_performance_alert"] = custom_rule
```

## Integration with Agent System

### Automatic Agent Tracking

The monitoring system automatically tracks agent interactions:

```python
# In your agent code
from api.monitoring.metrics_collector import metrics_collector

# Start tracking
interaction_id = metrics_collector.start_interaction(
    agent_name="pagbank_agent",
    user_id="user123",
    session_id="session456",
    message="User message",
    metadata={"context": "additional_info"}
)

# End tracking
metrics_collector.end_interaction(
    interaction_id=interaction_id,
    success=True,
    response="Agent response"
)
```

### Custom Metrics

Add custom metrics to track specific business logic:

```python
# Example: Track custom business metrics
metrics_collector.add_custom_metric(
    metric_name="payment_processing_time",
    value=2.5,
    unit="seconds",
    tags={"payment_type": "credit_card"}
)
```

## Analytics & Reporting

### Performance Reports

Generate comprehensive performance reports:

```python
# Get performance report
report = await analytics_engine.generate_performance_report(
    metrics_collector, system_monitor
)

# Report contains:
# - System health summary
# - Agent performance trends
# - Insights and recommendations
# - Performance scores
```

### Trend Analysis

Analyze performance trends over time:

```python
# Get hourly trends
hourly_data = metrics_collector.get_analytics_data('hourly')

# Get daily trends
daily_data = metrics_collector.get_analytics_data('daily')
```

### Typification Analytics

Track request classification accuracy:

```python
# Get typification analytics
typification_data = await analytics_engine.get_typification_analytics(
    metrics_collector
)

# Contains:
# - Overall accuracy
# - Accuracy by category
# - Improvement trends
# - Misclassification analysis
```

## Architecture

### Components

1. **MetricsCollector**: Collects and stores agent interaction metrics
2. **SystemMonitor**: Monitors system health and resources
3. **AlertManager**: Manages alert rules and notifications
4. **AnalyticsEngine**: Provides advanced analytics and insights
5. **MonitoringSystemManager**: Coordinates all monitoring components

### Data Flow

```
Agent Interactions → MetricsCollector → Storage
                ↓
System Resources → SystemMonitor → Health Checks
                ↓
Metrics Data → AlertManager → Notifications
                ↓
Analytics Engine → Dashboard → Users
```

### Storage

- **Metrics**: Stored in JSON Lines format for easy processing
- **Alerts**: In-memory with configurable persistence
- **Analytics**: Cached with TTL for performance

## Performance Considerations

### Resource Usage

- **CPU**: Minimal impact, runs background tasks every 30 seconds
- **Memory**: Approximately 50-100MB for typical usage
- **Storage**: Configurable retention (default 30 days)

### Scalability

- **Horizontal**: Can be deployed across multiple instances
- **Vertical**: Handles thousands of concurrent agent interactions
- **Storage**: Supports both local filesystem and cloud storage

## Troubleshooting

### Common Issues

1. **Monitoring Not Starting**
   - Check if required dependencies are installed
   - Verify storage paths are writable
   - Check for port conflicts

2. **Alerts Not Firing**
   - Verify alert rules are enabled
   - Check threshold configurations
   - Ensure metrics are being collected

3. **Dashboard Not Loading**
   - Verify API endpoints are accessible
   - Check CORS configuration
   - Ensure monitoring system is running

### Debug Mode

Enable debug logging for detailed monitoring information:

```python
import logging
logging.getLogger('api.monitoring').setLevel(logging.DEBUG)
```

### Health Check

Verify system health:

```bash
# Check monitoring system status
curl http://localhost:8000/v1/monitoring/health

# Expected response:
{
    "status": "success",
    "data": {
        "overall_health": "healthy",
        "services": {...},
        "last_check": "2024-01-15T10:30:00Z"
    }
}
```

## Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `uv sync`
3. Run tests: `uv run pytest tests/`
4. Start development server: `uv run python api/main.py`

### Testing

```bash
# Run all monitoring tests
uv run pytest tests/monitoring/

# Run specific test files
uv run pytest tests/monitoring/test_metrics_collector.py
uv run pytest tests/monitoring/test_alert_manager.py
```

### Code Quality

```bash
# Format code
uv run ruff format api/monitoring/

# Check linting
uv run ruff check api/monitoring/

# Type checking
uv run mypy api/monitoring/
```

## Support

For issues, questions, or feature requests:

1. Check the troubleshooting section
2. Review the API documentation
3. Create an issue in the repository
4. Contact the development team

## License

This monitoring system is part of the PagBank Multi-Agent System and follows the same license terms.