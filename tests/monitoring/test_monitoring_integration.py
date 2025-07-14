"""
Integration tests for the monitoring system
Tests the complete monitoring workflow
"""

import asyncio

from api.monitoring.metrics_collector import MetricsCollector
from api.monitoring.system_monitor import SystemMonitor
from api.monitoring.alert_manager import AlertManager
from api.monitoring.analytics_engine import AnalyticsEngine


class TestMonitoringIntegration:
    """Test monitoring system integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.metrics_collector = MetricsCollector(storage_path="test_logs/metrics")
        self.system_monitor = SystemMonitor(check_interval=1)
        self.alert_manager = AlertManager(config_path="test_logs/alerts")
        self.analytics_engine = AnalyticsEngine(storage_path="test_logs/analytics")
    
    def test_metrics_collection_flow(self):
        """Test metrics collection workflow"""
        # Start an interaction
        interaction_id = self.metrics_collector.start_interaction(
            agent_name="test_agent",
            user_id="test_user",
            session_id="test_session",
            message="Test message",
            metadata={"test": "data"}
        )
        
        assert interaction_id is not None
        assert interaction_id in self.metrics_collector.active_interactions
        
        # End the interaction successfully
        self.metrics_collector.end_interaction(
            interaction_id=interaction_id,
            success=True,
            response="Test response"
        )
        
        # Check metrics were updated
        agent_metrics = self.metrics_collector.get_agent_metrics("test_agent")
        assert agent_metrics["total_interactions"] == 1
        assert agent_metrics["successful_interactions"] == 1
        assert agent_metrics["success_rate"] == 100.0
        
        # Check interaction was removed from active
        assert interaction_id not in self.metrics_collector.active_interactions
    
    def test_system_health_monitoring(self):
        """Test system health monitoring"""
        # Get system health
        health_status = self.system_monitor.get_system_health()
        
        # Should have basic structure
        assert "status" in health_status
        assert "services" in health_status
        assert "overall_health" in health_status
        
        # Initially no services should be monitored
        assert health_status["status"] == "unknown"
    
    def test_alert_rule_evaluation(self):
        """Test alert rule evaluation"""
        # Create test metrics that should trigger alerts
        test_metrics = {
            "system": {
                "memory_usage": 95.0,  # Should trigger critical memory alert
                "cpu_usage": 85.0,     # Should trigger high CPU alert
            },
            "agents": {
                "test_agent": {
                    "success_rate": 85.0,  # Should trigger low success rate alert
                    "average_response_time": 6.0  # Should trigger high response time alert
                }
            },
            "services": {
                "database": {
                    "status": "down"  # Should trigger database down alert
                }
            }
        }
        
        # Run alert evaluation
        asyncio.run(self.alert_manager.evaluate_alerts(test_metrics))
        
        # Check that alerts were created
        active_alerts = self.alert_manager.get_alerts(status="active")
        assert len(active_alerts) > 0
        
        # Check alert history
        all_alerts = self.alert_manager.get_alerts()
        assert len(all_alerts) > 0
    
    def test_analytics_performance_report(self):
        """Test analytics performance report generation"""
        # Add some test data to metrics collector
        interaction_id = self.metrics_collector.start_interaction(
            agent_name="analytics_test_agent",
            user_id="analytics_user",
            session_id="analytics_session",
            message="Analytics test message"
        )
        
        self.metrics_collector.end_interaction(
            interaction_id=interaction_id,
            success=True,
            response="Analytics response"
        )
        
        # Generate performance report
        report = asyncio.run(
            self.analytics_engine.generate_performance_report(
                self.metrics_collector, self.system_monitor
            )
        )
        
        # Check report structure
        assert "generated_at" in report
        assert "summary" in report
        assert "performance_trends" in report
        assert "insights" in report
        assert "performance_scores" in report
        assert "recommendations" in report
        assert "detailed_metrics" in report
        
        # Check summary contains expected data
        summary = report["summary"]
        assert "total_agents" in summary
        assert "total_interactions" in summary
        assert "overall_health" in summary
    
    def test_alert_acknowledgment_flow(self):
        """Test alert acknowledgment and resolution"""
        # Create an alert
        test_metrics = {
            "system": {"memory_usage": 95.0},
            "agents": {},
            "services": {}
        }
        
        asyncio.run(self.alert_manager.evaluate_alerts(test_metrics))
        
        # Get active alerts
        active_alerts = self.alert_manager.get_alerts(status="active")
        assert len(active_alerts) > 0
        
        # Acknowledge the first alert
        alert_id = active_alerts[0]["id"]
        ack_result = self.alert_manager.acknowledge_alert(alert_id, "test_user")
        
        assert ack_result["status"] == "acknowledged"
        assert ack_result["acknowledged_by"] == "test_user"
        
        # Resolve the alert
        resolve_result = self.alert_manager.resolve_alert(alert_id)
        
        assert resolve_result["status"] == "resolved"
        
        # Check alert is no longer active
        active_alerts_after = self.alert_manager.get_alerts(status="active")
        active_ids = [a["id"] for a in active_alerts_after]
        assert alert_id not in active_ids
    
    def test_metrics_aggregation(self):
        """Test metrics aggregation functionality"""
        # Add multiple interactions
        for i in range(5):
            interaction_id = self.metrics_collector.start_interaction(
                agent_name="aggregation_agent",
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                message=f"Message {i}"
            )
            
            # Some successful, some failed
            success = i % 2 == 0
            self.metrics_collector.end_interaction(
                interaction_id=interaction_id,
                success=success,
                response=f"Response {i}" if success else None,
                error=f"Error {i}" if not success else None
            )
        
        # Check aggregated metrics
        agent_metrics = self.metrics_collector.get_agent_metrics("aggregation_agent")
        
        assert agent_metrics["total_interactions"] == 5
        assert agent_metrics["successful_interactions"] == 3  # 0, 2, 4
        assert agent_metrics["failed_interactions"] == 2      # 1, 3
        assert agent_metrics["success_rate"] == 60.0  # 3/5 * 100
    
    def test_system_metrics_collection(self):
        """Test system metrics collection"""
        system_metrics = self.metrics_collector.get_system_metrics()
        
        # Check expected fields
        assert "total_requests" in system_metrics
        assert "active_sessions" in system_metrics
        assert "memory_usage" in system_metrics
        assert "cpu_usage" in system_metrics
        assert "uptime" in system_metrics
        assert "recent_errors" in system_metrics
        assert "system_health" in system_metrics
    
    def test_analytics_trends(self):
        """Test analytics trend analysis"""
        # This test would need historical data
        # For now, test that the methods don't crash
        analytics_data = self.metrics_collector.get_analytics_data("hourly")
        assert "period" in analytics_data
        assert analytics_data["period"] == "hourly"
        
        daily_data = self.metrics_collector.get_analytics_data("daily")
        assert "period" in daily_data
        assert daily_data["period"] == "daily"
    
    def test_typification_analytics(self):
        """Test typification analytics"""
        typification_data = asyncio.run(
            self.analytics_engine.get_typification_analytics(self.metrics_collector)
        )
        
        # Check structure (placeholder data)
        assert "typification_accuracy" in typification_data
        assert "recommendations" in typification_data
        
        accuracy = typification_data["typification_accuracy"]
        assert "overall_accuracy" in accuracy
        assert "by_category" in accuracy
        assert "improvement_trend" in accuracy
        assert "misclassification_rate" in accuracy
    
    def test_versioning_analytics(self):
        """Test versioning analytics"""
        versioning_data = asyncio.run(
            self.analytics_engine.get_versioning_analytics(self.metrics_collector)
        )
        
        # Check structure (placeholder data)
        assert "version_performance" in versioning_data
        assert "recommendations" in versioning_data
        
        performance = versioning_data["version_performance"]
        assert "current_version" in performance
        assert "version_comparison" in performance
        assert "rollback_rate" in performance
        assert "version_adoption_rate" in performance
    
    def test_performance_scores(self):
        """Test performance scoring system"""
        # Add some performance data
        interaction_id = self.metrics_collector.start_interaction(
            agent_name="scoring_agent",
            user_id="scoring_user",
            session_id="scoring_session",
            message="Scoring test"
        )
        
        self.metrics_collector.end_interaction(
            interaction_id=interaction_id,
            success=True,
            response="Scoring response"
        )
        
        # Generate performance report to get scores
        report = asyncio.run(
            self.analytics_engine.generate_performance_report(
                self.metrics_collector, self.system_monitor
            )
        )
        
        # Check performance scores
        scores = report["performance_scores"]
        assert "agents" in scores
        assert "system" in scores
        assert "overall" in scores
        
        # Check overall score structure
        overall = scores["overall"]
        assert "score" in overall
        assert "grade" in overall
        assert overall["grade"] in ["A", "B", "C", "D", "F"]
    
    def test_alert_statistics(self):
        """Test alert statistics generation"""
        statistics = self.alert_manager.get_alert_statistics()
        
        # Check statistics structure
        assert "total_alerts" in statistics
        assert "active_alerts" in statistics
        assert "alerts_24h" in statistics
        assert "alerts_7d" in statistics
        assert "severity_counts_24h" in statistics
        assert "top_rules_24h" in statistics
        assert "alert_rules_enabled" in statistics
        assert "alert_rules_total" in statistics
    
    def test_comprehensive_monitoring_flow(self):
        """Test complete monitoring workflow"""
        # 1. Start some agent interactions
        interactions = []
        for i in range(3):
            interaction_id = self.metrics_collector.start_interaction(
                agent_name=f"agent_{i}",
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                message=f"Message {i}"
            )
            interactions.append(interaction_id)
        
        # 2. End interactions with different outcomes
        for i, interaction_id in enumerate(interactions):
            self.metrics_collector.end_interaction(
                interaction_id=interaction_id,
                success=i != 1,  # Make second interaction fail
                response=f"Response {i}" if i != 1 else None,
                error="Test error" if i == 1 else None
            )
        
        # 3. Check system health
        health_status = self.system_monitor.get_system_health()
        assert health_status is not None
        
        # 4. Evaluate alerts
        test_metrics = {
            "system": self.metrics_collector.get_system_metrics(),
            "agents": self.metrics_collector.get_agent_metrics(),
            "services": {}
        }
        
        asyncio.run(self.alert_manager.evaluate_alerts(test_metrics))
        
        # 5. Generate analytics report
        report = asyncio.run(
            self.analytics_engine.generate_performance_report(
                self.metrics_collector, self.system_monitor
            )
        )
        
        # 6. Verify everything worked
        assert report["summary"]["total_agents"] == 3
        assert report["summary"]["total_interactions"] >= 3
        
        # Check individual agent metrics
        agent_0_metrics = self.metrics_collector.get_agent_metrics("agent_0")
        assert agent_0_metrics["success_rate"] == 100.0
        
        agent_1_metrics = self.metrics_collector.get_agent_metrics("agent_1")
        assert agent_1_metrics["success_rate"] == 0.0  # This one failed
        
        agent_2_metrics = self.metrics_collector.get_agent_metrics("agent_2")
        assert agent_2_metrics["success_rate"] == 100.0
    
    def teardown_method(self):
        """Clean up test environment"""
        # Clean up test storage
        import shutil
        try:
            shutil.rmtree("test_logs")
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    # Run a simple test
    test = TestMonitoringIntegration()
    test.setup_method()
    
    try:
        test.test_metrics_collection_flow()
        print("✅ Metrics collection test passed")
        
        test.test_alert_rule_evaluation()
        print("✅ Alert evaluation test passed")
        
        test.test_analytics_performance_report()
        print("✅ Analytics report test passed")
        
        test.test_comprehensive_monitoring_flow()
        print("✅ Comprehensive monitoring test passed")
        
        print("\n🎉 All monitoring tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test.teardown_method()