"""
Alert management system for monitoring notifications
Handles alert configuration, routing, and delivery
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import smtplib
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str
    threshold: float
    severity: AlertSeverity
    message_template: str
    cooldown_minutes: int = 15
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AlertManager:
    """
    Alert management system
    Handles alert rules, notifications, and delivery
    """
    
    def __init__(self, config_path: str = "logs/alerts"):
        self.config_path = Path(config_path)
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: Dict[str, AlertRule] = {}
        
        # Alert delivery handlers
        self.delivery_handlers: Dict[str, Callable] = {
            'log': self._deliver_log,
            'email': self._deliver_email,
            'webhook': self._deliver_webhook,
            'whatsapp': self._deliver_whatsapp
        }
        
        # Cooldown tracking
        self.rule_cooldowns: Dict[str, datetime] = {}
        
        # Configuration
        self.config = self._load_config()
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load alert configuration"""
        config_file = self.config_path / "alert_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading alert config: {e}")
        
        # Default configuration
        return {
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'recipients': []
            },
            'webhook': {
                'enabled': False,
                'url': '',
                'headers': {}
            },
            'whatsapp': {
                'enabled': False,
                'instance': '',
                'recipient': ''
            },
            'delivery_methods': ['log']  # Default to log only
        }
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                name="high_memory_usage",
                condition="memory_usage > threshold",
                threshold=85.0,
                severity=AlertSeverity.HIGH,
                message_template="High memory usage detected: {memory_usage:.1f}%",
                cooldown_minutes=15
            ),
            AlertRule(
                name="critical_memory_usage",
                condition="memory_usage > threshold",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                message_template="Critical memory usage detected: {memory_usage:.1f}%",
                cooldown_minutes=5
            ),
            AlertRule(
                name="high_cpu_usage",
                condition="cpu_usage > threshold",
                threshold=80.0,
                severity=AlertSeverity.HIGH,
                message_template="High CPU usage detected: {cpu_usage:.1f}%",
                cooldown_minutes=15
            ),
            AlertRule(
                name="low_agent_success_rate",
                condition="agent_success_rate < threshold",
                threshold=90.0,
                severity=AlertSeverity.HIGH,
                message_template="Low agent success rate: {agent_name} at {success_rate:.1f}%",
                cooldown_minutes=30
            ),
            AlertRule(
                name="high_response_time",
                condition="response_time > threshold",
                threshold=5.0,
                severity=AlertSeverity.MEDIUM,
                message_template="High response time detected: {agent_name} at {response_time:.2f}s",
                cooldown_minutes=20
            ),
            AlertRule(
                name="database_connection_failed",
                condition="database_status == 'down'",
                threshold=0.0,
                severity=AlertSeverity.CRITICAL,
                message_template="Database connection failed: {error_message}",
                cooldown_minutes=5
            ),
            AlertRule(
                name="service_down",
                condition="service_status == 'down'",
                threshold=0.0,
                severity=AlertSeverity.CRITICAL,
                message_template="Service down: {service_name} - {error_message}",
                cooldown_minutes=5
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule
    
    async def evaluate_alerts(self, metrics: Dict[str, Any]):
        """Evaluate metrics against alert rules"""
        current_time = datetime.now()
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule_name in self.rule_cooldowns:
                cooldown_end = self.rule_cooldowns[rule_name] + timedelta(minutes=rule.cooldown_minutes)
                if current_time < cooldown_end:
                    continue
            
            # Evaluate rule condition
            should_alert = await self._evaluate_rule_condition(rule, metrics)
            
            if should_alert:
                # Create alert
                alert = await self._create_alert(rule, metrics)
                
                # Set cooldown
                self.rule_cooldowns[rule_name] = current_time
                
                # Deliver alert
                await self._deliver_alert(alert)
    
    async def _evaluate_rule_condition(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Evaluate if an alert rule condition is met"""
        try:
            # Memory usage alerts
            if rule.name in ["high_memory_usage", "critical_memory_usage"]:
                memory_usage = metrics.get('system', {}).get('memory_usage', 0)
                return memory_usage > rule.threshold
            
            # CPU usage alerts
            elif rule.name == "high_cpu_usage":
                cpu_usage = metrics.get('system', {}).get('cpu_usage', 0)
                return cpu_usage > rule.threshold
            
            # Agent success rate alerts
            elif rule.name == "low_agent_success_rate":
                agents = metrics.get('agents', {})
                for agent_name, agent_data in agents.items():
                    if isinstance(agent_data, dict) and 'success_rate' in agent_data:
                        if agent_data['success_rate'] < rule.threshold:
                            return True
                return False
            
            # Response time alerts
            elif rule.name == "high_response_time":
                agents = metrics.get('agents', {})
                for agent_name, agent_data in agents.items():
                    if isinstance(agent_data, dict) and 'average_response_time' in agent_data:
                        if agent_data['average_response_time'] > rule.threshold:
                            return True
                return False
            
            # Database connection alerts
            elif rule.name == "database_connection_failed":
                services = metrics.get('services', {})
                database_status = services.get('database', {}).get('status', 'unknown')
                return database_status == 'down'
            
            # Service down alerts
            elif rule.name == "service_down":
                services = metrics.get('services', {})
                for service_name, service_data in services.items():
                    if isinstance(service_data, dict) and service_data.get('status') == 'down':
                        return True
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {e}")
            return False
    
    async def _create_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> Alert:
        """Create an alert instance"""
        alert_id = f"{rule.name}_{int(datetime.now().timestamp())}"
        
        # Format message with metrics
        message = self._format_alert_message(rule, metrics)
        
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            message=message,
            timestamp=datetime.now(),
            metadata={
                'rule_threshold': rule.threshold,
                'metrics_snapshot': metrics
            }
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Keep history limited
        if len(self.alert_history) > 1000:
            self.alert_history.pop(0)
        
        logger.info(f"Alert created: {alert.id} - {alert.message}")
        return alert
    
    def _format_alert_message(self, rule: AlertRule, metrics: Dict[str, Any]) -> str:
        """Format alert message with metrics data"""
        try:
            # Extract relevant metrics for formatting
            format_data = {}
            
            # System metrics
            system_metrics = metrics.get('system', {})
            format_data.update({
                'memory_usage': system_metrics.get('memory_usage', 0),
                'cpu_usage': system_metrics.get('cpu_usage', 0)
            })
            
            # Agent metrics
            agents = metrics.get('agents', {})
            for agent_name, agent_data in agents.items():
                if isinstance(agent_data, dict):
                    format_data.update({
                        'agent_name': agent_name,
                        'success_rate': agent_data.get('success_rate', 0),
                        'response_time': agent_data.get('average_response_time', 0)
                    })
                    break  # Use first agent for formatting
            
            # Service metrics
            services = metrics.get('services', {})
            for service_name, service_data in services.items():
                if isinstance(service_data, dict):
                    format_data.update({
                        'service_name': service_name,
                        'error_message': service_data.get('message', 'Unknown error')
                    })
                    break  # Use first service for formatting
            
            return rule.message_template.format(**format_data)
            
        except Exception as e:
            logger.error(f"Error formatting alert message: {e}")
            return f"Alert: {rule.name} - {rule.message_template}"
    
    async def _deliver_alert(self, alert: Alert):
        """Deliver alert through configured channels"""
        delivery_methods = self.config.get('delivery_methods', ['log'])
        
        for method in delivery_methods:
            if method in self.delivery_handlers:
                try:
                    await self.delivery_handlers[method](alert)
                except Exception as e:
                    logger.error(f"Error delivering alert via {method}: {e}")
    
    async def _deliver_log(self, alert: Alert):
        """Deliver alert via logging"""
        log_message = f"ALERT [{alert.severity.value.upper()}] {alert.message}"
        
        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical(log_message)
        elif alert.severity == AlertSeverity.HIGH:
            logger.error(log_message)
        elif alert.severity == AlertSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    async def _deliver_email(self, alert: Alert):
        """Deliver alert via email"""
        email_config = self.config.get('email', {})
        
        if not email_config.get('enabled', False):
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = email_config['username']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"[{alert.severity.value.upper()}] PagBank System Alert"
            
            body = f"""
            Alert Details:
            - Rule: {alert.rule_name}
            - Severity: {alert.severity.value.upper()}
            - Message: {alert.message}
            - Timestamp: {alert.timestamp.isoformat()}
            - Alert ID: {alert.id}
            
            This is an automated alert from the PagBank Multi-Agent System monitoring.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    async def _deliver_webhook(self, alert: Alert):
        """Deliver alert via webhook"""
        webhook_config = self.config.get('webhook', {})
        
        if not webhook_config.get('enabled', False):
            return
        
        try:
            import httpx
            
            payload = {
                'alert_id': alert.id,
                'rule_name': alert.rule_name,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metadata': alert.metadata
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_config['url'],
                    json=payload,
                    headers=webhook_config.get('headers', {}),
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook alert sent for {alert.id}")
                else:
                    logger.error(f"Webhook alert failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    async def _deliver_whatsapp(self, alert: Alert):
        """Deliver alert via WhatsApp"""
        whatsapp_config = self.config.get('whatsapp', {})
        
        if not whatsapp_config.get('enabled', False):
            return
        
        try:
            # Import WhatsApp MCP tools
            from mcp__send_whatsapp_message__send_text_message import send_text_message
            
            message = "🚨 *PagBank System Alert*\n\n"
            message += f"*Severity:* {alert.severity.value.upper()}\n"
            message += f"*Rule:* {alert.rule_name}\n"
            message += f"*Message:* {alert.message}\n"
            message += f"*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"*Alert ID:* {alert.id}"
            
            await send_text_message(
                instance=whatsapp_config['instance'],
                number=whatsapp_config['recipient'],
                message=message
            )
            
            logger.info(f"WhatsApp alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp alert: {e}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
        """Acknowledge an alert"""
        if alert_id not in self.active_alerts:
            return {'error': f'Alert {alert_id} not found'}
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        
        return {
            'status': 'acknowledged',
            'alert_id': alert_id,
            'acknowledged_by': acknowledged_by,
            'acknowledged_at': alert.acknowledged_at.isoformat()
        }
    
    def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        """Resolve an alert"""
        if alert_id not in self.active_alerts:
            return {'error': f'Alert {alert_id} not found'}
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        logger.info(f"Alert {alert_id} resolved")
        
        return {
            'status': 'resolved',
            'alert_id': alert_id,
            'resolved_at': alert.resolved_at.isoformat()
        }
    
    def get_alerts(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get alerts with optional status filter"""
        if status == 'active':
            alerts = list(self.active_alerts.values())
        else:
            alerts = self.alert_history
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        alerts = alerts[:limit]
        
        # Convert to dict format
        return [
            {
                'id': alert.id,
                'rule_name': alert.rule_name,
                'severity': alert.severity.value,
                'message': alert.message,
                'status': alert.status.value,
                'timestamp': alert.timestamp.isoformat(),
                'acknowledged_by': alert.acknowledged_by,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            for alert in alerts
        ]
    
    def get_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get all alert rules"""
        return {
            name: {
                'name': rule.name,
                'condition': rule.condition,
                'threshold': rule.threshold,
                'severity': rule.severity.value,
                'message_template': rule.message_template,
                'cooldown_minutes': rule.cooldown_minutes,
                'enabled': rule.enabled
            }
            for name, rule in self.alert_rules.items()
        }
    
    def update_alert_rule(self, rule_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an alert rule"""
        if rule_name not in self.alert_rules:
            return {'error': f'Rule {rule_name} not found'}
        
        rule = self.alert_rules[rule_name]
        
        # Update allowed fields
        if 'threshold' in updates:
            rule.threshold = float(updates['threshold'])
        if 'enabled' in updates:
            rule.enabled = bool(updates['enabled'])
        if 'cooldown_minutes' in updates:
            rule.cooldown_minutes = int(updates['cooldown_minutes'])
        if 'message_template' in updates:
            rule.message_template = str(updates['message_template'])
        
        return {
            'status': 'updated',
            'rule_name': rule_name,
            'rule': {
                'name': rule.name,
                'condition': rule.condition,
                'threshold': rule.threshold,
                'severity': rule.severity.value,
                'message_template': rule.message_template,
                'cooldown_minutes': rule.cooldown_minutes,
                'enabled': rule.enabled
            }
        }
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Count alerts by time period
        alerts_24h = [a for a in self.alert_history if a.timestamp >= last_24h]
        alerts_7d = [a for a in self.alert_history if a.timestamp >= last_7d]
        
        # Count by severity
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([a for a in alerts_24h if a.severity == severity])
        
        return {
            'total_alerts': len(self.alert_history),
            'active_alerts': len(self.active_alerts),
            'alerts_24h': len(alerts_24h),
            'alerts_7d': len(alerts_7d),
            'severity_counts_24h': severity_counts,
            'top_rules_24h': self._get_top_alert_rules(alerts_24h),
            'alert_rules_enabled': sum(1 for rule in self.alert_rules.values() if rule.enabled),
            'alert_rules_total': len(self.alert_rules)
        }
    
    def _get_top_alert_rules(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Get top alert rules by frequency"""
        rule_counts = {}
        for alert in alerts:
            rule_counts[alert.rule_name] = rule_counts.get(alert.rule_name, 0) + 1
        
        # Sort by count
        sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'rule_name': rule_name, 'count': count}
            for rule_name, count in sorted_rules[:10]  # Top 10
        ]

# Global alert manager instance
alert_manager = AlertManager()