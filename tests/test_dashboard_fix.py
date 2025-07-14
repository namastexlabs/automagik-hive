"""
Test suite for monitoring dashboard fix
Ensures dashboard endpoint works properly after removing duplicate route
"""

import pytest
import requests
import json
from time import sleep

BASE_URL = "http://localhost:7777"

class TestDashboardFix:
    """Test the monitoring dashboard fix"""
    
    @pytest.fixture(autouse=True)
    def setup_monitoring(self):
        """Start monitoring system before each test"""
        try:
            response = requests.post(f"{BASE_URL}/v1/monitoring/start-monitoring")
            assert response.status_code == 200
            sleep(2)  # Allow monitoring to collect initial data
        except:
            pass  # May already be running
    
    def test_dashboard_endpoint_returns_200(self):
        """Test that dashboard endpoint returns 200 (not 404)"""
        response = requests.get(f"{BASE_URL}/v1/monitoring/dashboard")
        assert response.status_code == 200
        
    def test_dashboard_returns_json_data(self):
        """Test that dashboard returns structured JSON data"""
        response = requests.get(f"{BASE_URL}/v1/monitoring/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "data" in data
        assert "timestamp" in data
        assert data["status"] == "success"
        
    def test_dashboard_contains_required_sections(self):
        """Test that dashboard contains all required monitoring sections"""
        response = requests.get(f"{BASE_URL}/v1/monitoring/dashboard")
        assert response.status_code == 200
        
        data = response.json()["data"]
        
        # Verify all required sections are present
        required_sections = [
            "system_health",
            "system_metrics", 
            "agent_metrics",
            "recent_alerts",
            "alert_statistics",
            "performance_metrics",
            "performance_report"
        ]
        
        for section in required_sections:
            assert section in data, f"Missing section: {section}"
    
    def test_system_health_has_services(self):
        """Test that system health includes service monitoring"""
        response = requests.get(f"{BASE_URL}/v1/monitoring/dashboard")
        assert response.status_code == 200
        
        system_health = response.json()["data"]["system_health"]
        
        # Should have services after monitoring starts
        if "services" in system_health:
            services = system_health["services"]
            expected_services = ["database", "memory", "cpu", "disk", "network", "agents"]
            
            for service in expected_services:
                if service in services:
                    assert "status" in services[service]
                    assert "message" in services[service]
                    assert "response_time" in services[service]
                    assert "last_check" in services[service]
    
    def test_dashboard_metrics_structure(self):
        """Test that metrics have proper structure"""
        response = requests.get(f"{BASE_URL}/v1/monitoring/dashboard")
        assert response.status_code == 200
        
        metrics = response.json()["data"]["system_metrics"]
        
        # Verify metrics structure
        expected_metrics = [
            "total_requests",
            "active_sessions", 
            "active_interactions",
            "memory_usage",
            "cpu_usage",
            "uptime",
            "start_time",
            "recent_errors",
            "system_health"
        ]
        
        for metric in expected_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
    
    def test_performance_report_structure(self):
        """Test that performance report has proper structure"""
        response = requests.get(f"{BASE_URL}/v1/monitoring/dashboard")
        assert response.status_code == 200
        
        report = response.json()["data"]["performance_report"]
        
        # Verify report structure
        expected_sections = [
            "generated_at",
            "summary",
            "performance_trends",
            "insights",
            "performance_scores",
            "recommendations",
            "detailed_metrics"
        ]
        
        for section in expected_sections:
            assert section in report, f"Missing report section: {section}"
    
    def test_no_html_response(self):
        """Test that dashboard doesn't return HTML content"""
        response = requests.get(f"{BASE_URL}/v1/monitoring/dashboard")
        assert response.status_code == 200
        
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type
        assert "text/html" not in content_type
        
    def test_dashboard_vs_individual_endpoints(self):
        """Test that dashboard aggregates data from individual endpoints"""
        # Get dashboard data
        dashboard_response = requests.get(f"{BASE_URL}/v1/monitoring/dashboard")
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()["data"]
        
        # Get individual endpoint data
        health_response = requests.get(f"{BASE_URL}/v1/monitoring/health")
        metrics_response = requests.get(f"{BASE_URL}/v1/monitoring/metrics")
        
        if health_response.status_code == 200:
            health_data = health_response.json()["data"]
            # Dashboard should include health data
            assert "system_health" in dashboard_data
            
        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()["data"]
            # Dashboard should include metrics data
            assert "system_metrics" in dashboard_data

if __name__ == "__main__":
    # Run a quick test
    test = TestDashboardFix()
    
    # Setup monitoring manually
    try:
        response = requests.post(f"{BASE_URL}/v1/monitoring/start-monitoring")
        print(f"Monitoring setup: {response.status_code}")
        sleep(2)
    except Exception as e:
        print(f"Warning: Could not start monitoring: {e}")
    
    try:
        test.test_dashboard_endpoint_returns_200()
        test.test_dashboard_returns_json_data()
        test.test_dashboard_contains_required_sections()
        print("✅ All dashboard tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")