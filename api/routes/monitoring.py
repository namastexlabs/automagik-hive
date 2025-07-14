"""
Monitoring API routes for the PagBank Multi-Agent System
Provides real-time monitoring, analytics, and alerting endpoints
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

from api.monitoring.metrics_collector import metrics_collector
from api.monitoring.system_monitor import system_monitor
from api.monitoring.alert_manager import alert_manager
from api.monitoring.analytics_engine import analytics_engine

logger = logging.getLogger(__name__)

monitoring_router = APIRouter(tags=["Monitoring"], prefix="/monitoring")

@monitoring_router.get("/dashboard", response_class=HTMLResponse)
async def get_monitoring_dashboard():
    """Serve the monitoring dashboard HTML"""
    try:
        dashboard_path = Path(__file__).parent / "dashboard.html"
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read(), status_code=200)
        else:
            raise HTTPException(status_code=404, detail="Dashboard not found")
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/health")
async def get_system_health():
    """Get overall system health status"""
    try:
        health_status = system_monitor.get_system_health()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": health_status,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/health/{service_name}")
async def get_service_health(service_name: str):
    """Get health status for a specific service"""
    try:
        service_health = system_monitor.get_service_health(service_name)
        
        if "error" in service_health:
            raise HTTPException(status_code=404, detail=service_health["error"])
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": service_health,
                "timestamp": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/metrics")
async def get_system_metrics():
    """Get comprehensive system metrics"""
    try:
        system_metrics = metrics_collector.get_system_metrics()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": system_metrics,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/metrics/agents")
async def get_agent_metrics(agent_name: Optional[str] = Query(None, description="Specific agent name")):
    """Get agent performance metrics"""
    try:
        agent_metrics = metrics_collector.get_agent_metrics(agent_name)
        
        if agent_name and "error" in agent_metrics:
            raise HTTPException(status_code=404, detail=agent_metrics["error"])
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": agent_metrics,
                "timestamp": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/analytics")
async def get_analytics_data(
    period: str = Query("hourly", description="Analytics period: hourly or daily")
):
    """Get analytics data for dashboard"""
    try:
        analytics_data = metrics_collector.get_analytics_data(period)
        
        if "error" in analytics_data:
            raise HTTPException(status_code=400, detail=analytics_data["error"])
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": analytics_data,
                "timestamp": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/performance-report")
async def get_performance_report():
    """Get comprehensive performance report with insights"""
    try:
        performance_report = await analytics_engine.generate_performance_report(
            metrics_collector, system_monitor
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": performance_report,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/alerts")
async def get_alerts(
    status: Optional[str] = Query(None, description="Alert status filter: active, resolved"),
    limit: int = Query(50, description="Maximum number of alerts to return")
):
    """Get alerts with optional filtering"""
    try:
        alerts = alert_manager.get_alerts(status=status, limit=limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": alerts,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledged_by: str):
    """Acknowledge an alert"""
    try:
        result = alert_manager.acknowledge_alert(alert_id, acknowledged_by)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        result = alert_manager.resolve_alert(alert_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/alerts/rules")
async def get_alert_rules():
    """Get all alert rules configuration"""
    try:
        rules = alert_manager.get_alert_rules()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": rules,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting alert rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.put("/alerts/rules/{rule_name}")
async def update_alert_rule(rule_name: str, rule_updates: Dict[str, Any]):
    """Update an alert rule"""
    try:
        result = alert_manager.update_alert_rule(rule_name, rule_updates)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/alerts/statistics")
async def get_alert_statistics():
    """Get alert statistics and trends"""
    try:
        statistics = alert_manager.get_alert_statistics()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": statistics,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics for all services"""
    try:
        performance_metrics = system_monitor.get_performance_metrics()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/analytics/typification")
async def get_typification_analytics():
    """Get typification accuracy analytics"""
    try:
        typification_analytics = await analytics_engine.get_typification_analytics(metrics_collector)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": typification_analytics,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting typification analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/analytics/versioning")
async def get_versioning_analytics():
    """Get versioning effectiveness analytics"""
    try:
        versioning_analytics = await analytics_engine.get_versioning_analytics(metrics_collector)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": versioning_analytics,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting versioning analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.get("/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        # Collect all necessary data for dashboard
        dashboard_data = {
            "system_health": system_monitor.get_system_health(),
            "system_metrics": metrics_collector.get_system_metrics(),
            "agent_metrics": metrics_collector.get_agent_metrics(),
            "recent_alerts": alert_manager.get_alerts(status="active", limit=10),
            "alert_statistics": alert_manager.get_alert_statistics(),
            "performance_metrics": system_monitor.get_performance_metrics(),
            "performance_report": await analytics_engine.generate_performance_report(
                metrics_collector, system_monitor
            )
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.post("/start-monitoring")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start the monitoring system"""
    try:
        # Start monitoring in background
        background_tasks.add_task(system_monitor.start_monitoring)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Monitoring system started",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.post("/stop-monitoring")
async def stop_monitoring():
    """Stop the monitoring system"""
    try:
        system_monitor.stop_monitoring()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Monitoring system stopped",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_router.post("/evaluate-alerts")
async def evaluate_alerts(background_tasks: BackgroundTasks):
    """Manually trigger alert evaluation"""
    try:
        # Get current metrics
        system_metrics = metrics_collector.get_system_metrics()
        agent_metrics = metrics_collector.get_agent_metrics()
        system_health = system_monitor.get_system_health()
        
        # Prepare metrics for alert evaluation
        evaluation_metrics = {
            "system": system_metrics,
            "agents": agent_metrics,
            "services": system_health.get("services", {})
        }
        
        # Evaluate alerts in background
        background_tasks.add_task(alert_manager.evaluate_alerts, evaluation_metrics)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Alert evaluation triggered",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error evaluating alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time monitoring (optional)
@monitoring_router.websocket("/ws/realtime")
async def websocket_realtime_monitoring(websocket):
    """WebSocket endpoint for real-time monitoring updates"""
    import asyncio
    
    await websocket.accept()
    
    try:
        while True:
            # Send real-time updates every 10 seconds
            await asyncio.sleep(10)
            
            # Get current metrics
            data = {
                "type": "metrics_update",
                "timestamp": datetime.now().isoformat(),
                "system_health": system_monitor.get_system_health(),
                "system_metrics": metrics_collector.get_system_metrics(),
                "active_alerts": alert_manager.get_alerts(status="active", limit=5)
            }
            
            await websocket.send_json(data)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()