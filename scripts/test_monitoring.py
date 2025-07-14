#!/usr/bin/env python3
"""
Manual test script for the monitoring system
Run this to verify monitoring components work correctly
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.monitoring.metrics_collector import MetricsCollector
from api.monitoring.system_monitor import SystemMonitor
from api.monitoring.alert_manager import AlertManager
from api.monitoring.analytics_engine import AnalyticsEngine


async def test_metrics_collection():
    """Test metrics collection functionality"""
    print("🔍 Testing metrics collection...")
    
    collector = MetricsCollector(storage_path="test_logs/metrics")
    
    # Start some test interactions
    interactions = []
    for i in range(5):
        interaction_id = collector.start_interaction(
            agent_name="test_agent",
            user_id=f"user_{i}",
            session_id=f"session_{i}",
            message=f"Test message {i}",
            metadata={"test_run": True}
        )
        interactions.append(interaction_id)
        print(f"  Started interaction {i+1}: {interaction_id}")
    
    # End interactions with different outcomes
    for i, interaction_id in enumerate(interactions):
        success = i % 2 == 0  # Every other interaction succeeds
        collector.end_interaction(
            interaction_id=interaction_id,
            success=success,
            response=f"Response {i}" if success else None,
            error=f"Error {i}" if not success else None
        )
        print(f"  Ended interaction {i+1}: {'✅ Success' if success else '❌ Failed'}")
    
    # Check metrics
    agent_metrics = collector.get_agent_metrics("test_agent")
    print(f"  Agent metrics: {agent_metrics['total_interactions']} total, {agent_metrics['success_rate']:.1f}% success")
    
    system_metrics = collector.get_system_metrics()
    print(f"  System metrics: {system_metrics['total_requests']} total requests")
    
    return collector


async def test_system_monitoring():
    """Test system health monitoring"""
    print("\n🏥 Testing system health monitoring...")
    
    monitor = SystemMonitor(check_interval=1)
    
    # Run a few health checks
    await monitor._run_health_checks()
    
    # Get system health
    health = monitor.get_system_health()
    print(f"  Overall health: {health['overall_health']}")
    
    # Show service details
    for service_name, service_health in health['services'].items():
        status = service_health['status']
        response_time = service_health['response_time']
        print(f"  {service_name}: {status} ({response_time:.3f}s)")
    
    return monitor


async def test_alert_management():
    """Test alert management system"""
    print("\n🔔 Testing alert management...")
    
    alert_manager = AlertManager(config_path="test_logs/alerts")
    
    # Create test metrics that should trigger alerts
    test_metrics = {
        "system": {
            "memory_usage": 95.0,  # Critical
            "cpu_usage": 85.0,     # High
        },
        "agents": {
            "test_agent": {
                "success_rate": 85.0,  # Low
                "average_response_time": 6.0  # High
            }
        },
        "services": {
            "database": {
                "status": "healthy"
            }
        }
    }
    
    # Evaluate alerts
    await alert_manager.evaluate_alerts(test_metrics)
    
    # Check active alerts
    active_alerts = alert_manager.get_alerts(status="active")
    print(f"  Active alerts: {len(active_alerts)}")
    
    for alert in active_alerts:
        print(f"    - {alert['severity'].upper()}: {alert['message']}")
    
    # Test alert acknowledgment
    if active_alerts:
        alert_id = active_alerts[0]['id']
        ack_result = alert_manager.acknowledge_alert(alert_id, "test_user")
        print(f"  Acknowledged alert: {ack_result['status']}")
    
    # Show alert statistics
    stats = alert_manager.get_alert_statistics()
    print(f"  Alert statistics: {stats['total_alerts']} total, {stats['active_alerts']} active")
    
    return alert_manager


async def test_analytics_engine():
    """Test analytics engine"""
    print("\n📊 Testing analytics engine...")
    
    # Create sample collector with data
    collector = MetricsCollector(storage_path="test_logs/metrics")
    monitor = SystemMonitor(check_interval=1)
    analytics = AnalyticsEngine(storage_path="test_logs/analytics")
    
    # Add some sample data
    for i in range(10):
        interaction_id = collector.start_interaction(
            agent_name=f"agent_{i % 3}",  # 3 different agents
            user_id=f"user_{i}",
            session_id=f"session_{i}",
            message=f"Analytics test {i}"
        )
        
        collector.end_interaction(
            interaction_id=interaction_id,
            success=i % 4 != 0,  # 75% success rate
            response=f"Response {i}" if i % 4 != 0 else None,
            error=f"Error {i}" if i % 4 == 0 else None
        )
    
    # Generate performance report
    report = await analytics.generate_performance_report(collector, monitor)
    
    print(f"  Performance report generated at: {report['generated_at']}")
    print(f"  Summary: {report['summary']['total_agents']} agents, {report['summary']['total_interactions']} interactions")
    
    # Show insights
    insights = report['insights']
    print(f"  Insights: {len(insights)} insights generated")
    for insight in insights[:3]:  # Show first 3
        print(f"    - {insight['type'].upper()}: {insight['title']}")
    
    # Show performance scores
    scores = report['performance_scores']
    print(f"  Overall performance: {scores['overall']['score']:.1f} (Grade: {scores['overall']['grade']})")
    
    # Test specialized analytics
    typification = await analytics.get_typification_analytics(collector)
    print(f"  Typification accuracy: {typification['typification_accuracy']['overall_accuracy']}%")
    
    versioning = await analytics.get_versioning_analytics(collector)
    print(f"  Current version: {versioning['version_performance']['current_version']}")
    
    return analytics


async def test_integration():
    """Test complete integration"""
    print("\n🔗 Testing complete integration...")
    
    # Create all components
    collector = MetricsCollector(storage_path="test_logs/metrics")
    monitor = SystemMonitor(check_interval=1)
    alert_manager = AlertManager(config_path="test_logs/alerts")
    analytics = AnalyticsEngine(storage_path="test_logs/analytics")
    
    # Simulate realistic agent activity
    agents = ["adquirencia", "emissao", "pagbank", "human_handoff"]
    
    for i in range(20):
        agent_name = agents[i % len(agents)]
        
        interaction_id = collector.start_interaction(
            agent_name=agent_name,
            user_id=f"user_{i}",
            session_id=f"session_{i}",
            message=f"Customer message {i}",
            metadata={"channel": "web" if i % 2 == 0 else "mobile"}
        )
        
        # Simulate different response times and success rates by agent
        import random
        if agent_name == "adquirencia":
            success_rate = 0.95
            response_time = random.uniform(0.5, 2.0)
        elif agent_name == "emissao":
            success_rate = 0.88
            response_time = random.uniform(1.0, 3.0)
        elif agent_name == "pagbank":
            success_rate = 0.92
            response_time = random.uniform(0.8, 2.5)
        else:  # human_handoff
            success_rate = 0.98
            response_time = random.uniform(2.0, 5.0)
        
        # Simulate processing time
        await asyncio.sleep(response_time / 100)  # Scale down for testing
        
        success = random.random() < success_rate
        collector.end_interaction(
            interaction_id=interaction_id,
            success=success,
            response=f"Response from {agent_name}" if success else None,
            error=f"Error in {agent_name}" if not success else None
        )
    
    # Check system health
    await monitor._run_health_checks()
    health = monitor.get_system_health()
    
    # Evaluate alerts
    test_metrics = {
        "system": collector.get_system_metrics(),
        "agents": collector.get_agent_metrics(),
        "services": health['services']
    }
    
    await alert_manager.evaluate_alerts(test_metrics)
    
    # Generate comprehensive report
    report = await analytics.generate_performance_report(collector, monitor)
    
    print(f"  Integration test completed:")
    print(f"    - Total interactions: {report['summary']['total_interactions']}")
    print(f"    - Active agents: {report['summary']['total_agents']}")
    print(f"    - System health: {health['overall_health']}")
    print(f"    - Active alerts: {len(alert_manager.get_alerts(status='active'))}")
    print(f"    - Performance grade: {report['performance_scores']['overall']['grade']}")
    
    # Show agent performance breakdown
    agent_metrics = collector.get_agent_metrics()
    print(f"  Agent performance:")
    for agent_name, metrics in agent_metrics.items():
        if isinstance(metrics, dict):
            print(f"    - {agent_name}: {metrics['success_rate']:.1f}% success, {metrics['average_response_time']:.2f}s avg")


async def main():
    """Run all tests"""
    print("🚀 Starting monitoring system tests...\n")
    
    try:
        # Run individual component tests
        await test_metrics_collection()
        await test_system_monitoring()
        await test_alert_management()
        await test_analytics_engine()
        await test_integration()
        
        print("\n✅ All monitoring tests completed successfully!")
        print("\nTo access the monitoring dashboard:")
        print("1. Start the API server: uv run python api/main.py")
        print("2. Open: http://localhost:8000/v1/monitoring/dashboard")
        print("3. Check health: http://localhost:8000/v1/monitoring/health")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)