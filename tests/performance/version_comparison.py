"""
Version comparison and baseline tracking system for Genie Agents.

This module provides comprehensive version comparison for:
- Performance regression detection
- Baseline tracking across versions
- A/B testing support
- Version rollback decision support
- Performance trend analysis
"""

import json
import sqlite3
import statistics
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import subprocess

from utils.log import logger
from tests.performance.metrics_collector import MetricsCollector, TimedOperation


@dataclass
class VersionBaseline:
    """Version baseline data structure."""
    version: str
    timestamp: datetime
    git_commit: Optional[str]
    git_branch: Optional[str]
    test_environment: Dict[str, Any]
    performance_metrics: Dict[str, float]
    system_metrics: Dict[str, float]
    test_results: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class VersionComparison:
    """Version comparison result data structure."""
    baseline_version: str
    current_version: str
    comparison_timestamp: datetime
    performance_changes: Dict[str, Dict[str, float]]  # metric_name -> {change_percent, significance}
    system_changes: Dict[str, Dict[str, float]]
    regression_alerts: List[Dict[str, Any]]
    improvement_highlights: List[Dict[str, Any]]
    overall_score: float  # -100 to 100, negative = regression
    recommendation: str  # "deploy", "review", "rollback"


class VersionComparisonEngine:
    """Version comparison and baseline tracking engine."""
    
    def __init__(self, db_path: str = "tests/performance/version_baselines.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_collector = MetricsCollector()
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for version baselines."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Version baselines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS version_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                timestamp TEXT NOT NULL,
                git_commit TEXT,
                git_branch TEXT,
                test_environment TEXT,
                performance_metrics TEXT,
                system_metrics TEXT,
                test_results TEXT,
                metadata TEXT
            )
        """)
        
        # Version comparisons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS version_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baseline_version TEXT NOT NULL,
                current_version TEXT NOT NULL,
                comparison_timestamp TEXT NOT NULL,
                performance_changes TEXT,
                system_changes TEXT,
                regression_alerts TEXT,
                improvement_highlights TEXT,
                overall_score REAL,
                recommendation TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_baselines_version ON version_baselines(version)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparisons_versions ON version_comparisons(baseline_version, current_version)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparisons_timestamp ON version_comparisons(comparison_timestamp)")
        
        conn.commit()
        conn.close()
    
    def _get_git_info(self) -> Tuple[Optional[str], Optional[str]]:
        """Get current git commit and branch."""
        try:
            # Get current commit hash
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
            
            # Get current branch
            branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
            
            return commit, branch
        except subprocess.CalledProcessError:
            return None, None
    
    def _get_test_environment(self) -> Dict[str, Any]:
        """Get current test environment info."""
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "hostname": platform.node()
        }
    
    async def create_baseline(self, 
                            version: str,
                            run_full_benchmark: bool = True,
                            metadata: Optional[Dict[str, Any]] = None) -> VersionBaseline:
        """
        Create performance baseline for a version.
        
        Args:
            version: Version identifier
            run_full_benchmark: Whether to run full benchmark suite
            metadata: Additional metadata
            
        Returns:
            VersionBaseline with performance metrics
        """
        logger.info(f"Creating baseline for version {version}")
        
        # Get git info
        git_commit, git_branch = self._get_git_info()
        
        # Get test environment
        test_environment = self._get_test_environment()
        
        # Run benchmarks if requested
        performance_metrics = {}
        system_metrics = {}
        test_results = {}
        
        if run_full_benchmark:
            from tests.performance.test_benchmark import PerformanceBenchmark
            from tests.performance.test_stress import StressTestSuite
            
            # Run performance benchmarks
            benchmark = PerformanceBenchmark()
            
            # Test all main agents
            agents_to_test = ["pagbank-specialist", "adquirencia-specialist", "emissao-specialist"]
            
            for agent_id in agents_to_test:
                logger.info(f"Benchmarking {agent_id}")
                result = await benchmark.benchmark_agent_execution(
                    agent_id=agent_id,
                    test_message=f"Baseline benchmark for {agent_id} version {version}"
                )
                
                performance_metrics[f"{agent_id}_duration"] = result.duration_seconds
                performance_metrics[f"{agent_id}_memory"] = result.memory_usage_mb
                performance_metrics[f"{agent_id}_success"] = 1.0 if result.success else 0.0
            
            # Test team routing
            logger.info("Benchmarking team routing")
            team_results = await benchmark.benchmark_team_routing(iterations=5)
            successful_team_results = [r for r in team_results if r.success]
            
            if successful_team_results:
                performance_metrics["team_routing_avg_duration"] = sum(r.duration_seconds for r in successful_team_results) / len(successful_team_results)
                performance_metrics["team_routing_success_rate"] = len(successful_team_results) / len(team_results)
            
            # Test concurrency
            logger.info("Testing concurrency")
            concurrency_result = await benchmark.benchmark_concurrency(
                agent_id="pagbank-specialist",
                concurrent_requests=10
            )
            
            performance_metrics["concurrency_rps"] = concurrency_result.requests_per_second
            performance_metrics["concurrency_success_rate"] = concurrency_result.successful_requests / concurrency_result.concurrent_requests
            performance_metrics["concurrency_avg_response_time"] = concurrency_result.average_response_time
            
            # Run stress tests
            logger.info("Running stress tests")
            stress_suite = StressTestSuite()
            
            stress_result = await stress_suite.sustained_load_test(
                agent_id="pagbank-specialist",
                requests_per_second=2.0,
                duration_seconds=30
            )
            
            performance_metrics["stress_rps"] = stress_result.requests_per_second
            performance_metrics["stress_error_rate"] = stress_result.error_rate
            performance_metrics["stress_stability_score"] = stress_result.system_stability_score
            
            # Collect system metrics
            system_metrics["memory_peak_mb"] = stress_result.memory_peak_mb
            system_metrics["cpu_peak_percent"] = stress_result.cpu_peak_percent
            
            # Test results summary
            test_results = {
                "benchmark_tests": len(agents_to_test) + 1,  # agents + team routing
                "stress_tests": 1,
                "total_requests": sum(r.request_count for r in benchmark.results),
                "overall_success_rate": len([r for r in benchmark.results if r.success]) / len(benchmark.results) * 100 if benchmark.results else 0
            }
        
        # Create baseline
        baseline = VersionBaseline(
            version=version,
            timestamp=datetime.now(timezone.utc),
            git_commit=git_commit,
            git_branch=git_branch,
            test_environment=test_environment,
            performance_metrics=performance_metrics,
            system_metrics=system_metrics,
            test_results=test_results,
            metadata=metadata or {}
        )
        
        # Save to database
        self._save_baseline(baseline)
        
        logger.info(f"Baseline created for version {version}")
        return baseline
    
    def _save_baseline(self, baseline: VersionBaseline):
        """Save baseline to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO version_baselines 
            (version, timestamp, git_commit, git_branch, test_environment,
             performance_metrics, system_metrics, test_results, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            baseline.version,
            baseline.timestamp.isoformat(),
            baseline.git_commit,
            baseline.git_branch,
            json.dumps(baseline.test_environment),
            json.dumps(baseline.performance_metrics),
            json.dumps(baseline.system_metrics),
            json.dumps(baseline.test_results),
            json.dumps(baseline.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def get_baseline(self, version: str) -> Optional[VersionBaseline]:
        """Get baseline for a version."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT version, timestamp, git_commit, git_branch, test_environment,
                   performance_metrics, system_metrics, test_results, metadata
            FROM version_baselines 
            WHERE version = ?
        """, (version,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return VersionBaseline(
            version=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            git_commit=row[2],
            git_branch=row[3],
            test_environment=json.loads(row[4]),
            performance_metrics=json.loads(row[5]),
            system_metrics=json.loads(row[6]),
            test_results=json.loads(row[7]),
            metadata=json.loads(row[8])
        )
    
    def list_baselines(self) -> List[VersionBaseline]:
        """List all baselines."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT version, timestamp, git_commit, git_branch, test_environment,
                   performance_metrics, system_metrics, test_results, metadata
            FROM version_baselines 
            ORDER BY timestamp DESC
        """)
        
        baselines = []
        for row in cursor.fetchall():
            baselines.append(VersionBaseline(
                version=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                git_commit=row[2],
                git_branch=row[3],
                test_environment=json.loads(row[4]),
                performance_metrics=json.loads(row[5]),
                system_metrics=json.loads(row[6]),
                test_results=json.loads(row[7]),
                metadata=json.loads(row[8])
            ))
        
        conn.close()
        return baselines
    
    def compare_versions(self, 
                        baseline_version: str,
                        current_version: str,
                        significance_threshold: float = 5.0) -> VersionComparison:
        """
        Compare two versions and detect regressions.
        
        Args:
            baseline_version: Baseline version to compare against
            current_version: Current version to compare
            significance_threshold: Threshold for significant changes (%)
            
        Returns:
            VersionComparison with detailed analysis
        """
        # Get baselines
        baseline = self.get_baseline(baseline_version)
        current = self.get_baseline(current_version)
        
        if not baseline:
            raise ValueError(f"Baseline not found for version {baseline_version}")
        if not current:
            raise ValueError(f"Baseline not found for version {current_version}")
        
        # Compare performance metrics
        performance_changes = {}
        for metric_name in baseline.performance_metrics:
            if metric_name in current.performance_metrics:
                baseline_value = baseline.performance_metrics[metric_name]
                current_value = current.performance_metrics[metric_name]
                
                if baseline_value != 0:
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100
                    is_significant = abs(change_percent) >= significance_threshold
                    
                    performance_changes[metric_name] = {
                        "baseline_value": baseline_value,
                        "current_value": current_value,
                        "change_percent": change_percent,
                        "significant": is_significant,
                        "direction": "improvement" if self._is_improvement(metric_name, change_percent) else "regression"
                    }
        
        # Compare system metrics
        system_changes = {}
        for metric_name in baseline.system_metrics:
            if metric_name in current.system_metrics:
                baseline_value = baseline.system_metrics[metric_name]
                current_value = current.system_metrics[metric_name]
                
                if baseline_value != 0:
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100
                    is_significant = abs(change_percent) >= significance_threshold
                    
                    system_changes[metric_name] = {
                        "baseline_value": baseline_value,
                        "current_value": current_value,
                        "change_percent": change_percent,
                        "significant": is_significant,
                        "direction": "improvement" if self._is_system_improvement(metric_name, change_percent) else "regression"
                    }
        
        # Generate alerts and highlights
        regression_alerts = []
        improvement_highlights = []
        
        # Check for significant performance regressions
        for metric_name, change in performance_changes.items():
            if change["significant"] and change["direction"] == "regression":
                regression_alerts.append({
                    "type": "performance_regression",
                    "metric": metric_name,
                    "change_percent": change["change_percent"],
                    "severity": "high" if abs(change["change_percent"]) > 20 else "medium",
                    "message": f"{metric_name} degraded by {change['change_percent']:.1f}%"
                })
            elif change["significant"] and change["direction"] == "improvement":
                improvement_highlights.append({
                    "type": "performance_improvement",
                    "metric": metric_name,
                    "change_percent": change["change_percent"],
                    "message": f"{metric_name} improved by {abs(change['change_percent']):.1f}%"
                })
        
        # Check for system regressions
        for metric_name, change in system_changes.items():
            if change["significant"] and change["direction"] == "regression":
                regression_alerts.append({
                    "type": "system_regression",
                    "metric": metric_name,
                    "change_percent": change["change_percent"],
                    "severity": "high" if abs(change["change_percent"]) > 30 else "medium",
                    "message": f"{metric_name} increased by {change['change_percent']:.1f}%"
                })
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(performance_changes, system_changes)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(overall_score, regression_alerts)
        
        # Create comparison
        comparison = VersionComparison(
            baseline_version=baseline_version,
            current_version=current_version,
            comparison_timestamp=datetime.now(timezone.utc),
            performance_changes=performance_changes,
            system_changes=system_changes,
            regression_alerts=regression_alerts,
            improvement_highlights=improvement_highlights,
            overall_score=overall_score,
            recommendation=recommendation
        )
        
        # Save comparison
        self._save_comparison(comparison)
        
        return comparison
    
    def _is_improvement(self, metric_name: str, change_percent: float) -> bool:
        """Determine if a change is an improvement for a given metric."""
        # Metrics where lower is better
        lower_is_better = [
            "duration", "memory", "error_rate", "response_time", "avg_response_time"
        ]
        
        # Metrics where higher is better
        higher_is_better = [
            "success", "rps", "success_rate", "stability_score"
        ]
        
        for pattern in lower_is_better:
            if pattern in metric_name:
                return change_percent < 0
        
        for pattern in higher_is_better:
            if pattern in metric_name:
                return change_percent > 0
        
        # Default: assume lower is better
        return change_percent < 0
    
    def _is_system_improvement(self, metric_name: str, change_percent: float) -> bool:
        """Determine if a system metric change is an improvement."""
        # System metrics where lower is better
        lower_is_better = ["memory", "cpu", "peak"]
        
        for pattern in lower_is_better:
            if pattern in metric_name:
                return change_percent < 0
        
        # Default: assume lower is better
        return change_percent < 0
    
    def _calculate_overall_score(self, 
                                performance_changes: Dict[str, Dict[str, float]],
                                system_changes: Dict[str, Dict[str, float]]) -> float:
        """
        Calculate overall score (-100 to 100).
        
        Positive = improvement, Negative = regression
        """
        scores = []
        
        # Weight performance changes more heavily
        for metric_name, change in performance_changes.items():
            if change["significant"]:
                if change["direction"] == "improvement":
                    scores.append(min(25, abs(change["change_percent"]) / 2))
                else:
                    scores.append(max(-25, -abs(change["change_percent"]) / 2))
        
        # Weight system changes less heavily
        for metric_name, change in system_changes.items():
            if change["significant"]:
                if change["direction"] == "improvement":
                    scores.append(min(15, abs(change["change_percent"]) / 4))
                else:
                    scores.append(max(-15, -abs(change["change_percent"]) / 4))
        
        if not scores:
            return 0.0
        
        return max(-100, min(100, sum(scores) / len(scores)))
    
    def _generate_recommendation(self, 
                               overall_score: float,
                               regression_alerts: List[Dict[str, Any]]) -> str:
        """Generate deployment recommendation."""
        
        # Check for critical regressions
        critical_regressions = [
            alert for alert in regression_alerts 
            if alert.get("severity") == "high"
        ]
        
        if critical_regressions:
            return "rollback"
        
        if overall_score < -20:
            return "rollback"
        elif overall_score < -5:
            return "review"
        else:
            return "deploy"
    
    def _save_comparison(self, comparison: VersionComparison):
        """Save comparison to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO version_comparisons 
            (baseline_version, current_version, comparison_timestamp,
             performance_changes, system_changes, regression_alerts,
             improvement_highlights, overall_score, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comparison.baseline_version,
            comparison.current_version,
            comparison.comparison_timestamp.isoformat(),
            json.dumps(comparison.performance_changes),
            json.dumps(comparison.system_changes),
            json.dumps(comparison.regression_alerts),
            json.dumps(comparison.improvement_highlights),
            comparison.overall_score,
            comparison.recommendation
        ))
        
        conn.commit()
        conn.close()
    
    def get_version_trends(self, metric_name: str, versions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get trends for a specific metric across versions."""
        
        if versions is None:
            baselines = self.list_baselines()
            versions = [b.version for b in baselines]
        
        trends = []
        
        for version in versions:
            baseline = self.get_baseline(version)
            if baseline and metric_name in baseline.performance_metrics:
                trends.append({
                    "version": version,
                    "timestamp": baseline.timestamp.isoformat(),
                    "value": baseline.performance_metrics[metric_name]
                })
        
        # Sort by timestamp
        trends.sort(key=lambda x: x["timestamp"])
        
        # Calculate trend
        if len(trends) >= 2:
            values = [t["value"] for t in trends]
            slope = (values[-1] - values[0]) / (len(values) - 1)
            trend_direction = "improving" if self._is_improvement(metric_name, slope) else "degrading"
        else:
            trend_direction = "insufficient_data"
        
        return {
            "metric_name": metric_name,
            "trend_direction": trend_direction,
            "data_points": trends,
            "latest_value": trends[-1]["value"] if trends else None
        }
    
    def generate_regression_report(self, 
                                 baseline_version: str,
                                 current_version: str) -> Dict[str, Any]:
        """Generate comprehensive regression report."""
        
        comparison = self.compare_versions(baseline_version, current_version)
        
        # Calculate statistics
        total_metrics = len(comparison.performance_changes) + len(comparison.system_changes)
        regression_count = len(comparison.regression_alerts)
        improvement_count = len(comparison.improvement_highlights)
        
        # Critical issues
        critical_issues = [
            alert for alert in comparison.regression_alerts 
            if alert.get("severity") == "high"
        ]
        
        return {
            "comparison": asdict(comparison),
            "summary": {
                "total_metrics_compared": total_metrics,
                "regressions_detected": regression_count,
                "improvements_detected": improvement_count,
                "critical_issues": len(critical_issues),
                "overall_score": comparison.overall_score,
                "recommendation": comparison.recommendation
            },
            "critical_issues": critical_issues,
            "key_metrics": self._extract_key_metrics(comparison),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _extract_key_metrics(self, comparison: VersionComparison) -> Dict[str, Any]:
        """Extract key metrics for summary."""
        key_metrics = {}
        
        # Key performance metrics
        key_names = [
            "pagbank-specialist_duration",
            "team_routing_avg_duration", 
            "concurrency_rps",
            "stress_error_rate",
            "stress_stability_score"
        ]
        
        for metric_name in key_names:
            if metric_name in comparison.performance_changes:
                change = comparison.performance_changes[metric_name]
                key_metrics[metric_name] = {
                    "change_percent": change["change_percent"],
                    "direction": change["direction"],
                    "significant": change["significant"]
                }
        
        return key_metrics


# CLI script for version management
if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="Genie Agents version comparison")
    parser.add_argument("--create-baseline", type=str, help="Create baseline for version")
    parser.add_argument("--compare", nargs=2, metavar=("BASELINE", "CURRENT"), 
                       help="Compare two versions")
    parser.add_argument("--list-baselines", action="store_true", 
                       help="List all baselines")
    parser.add_argument("--trends", type=str, 
                       help="Show trends for metric")
    parser.add_argument("--full-benchmark", action="store_true", 
                       help="Run full benchmark when creating baseline")
    parser.add_argument("--report", nargs=2, metavar=("BASELINE", "CURRENT"),
                       help="Generate regression report")
    
    args = parser.parse_args()
    
    engine = VersionComparisonEngine()
    
    async def main():
        if args.create_baseline:
            print(f"Creating baseline for version {args.create_baseline}")
            baseline = await engine.create_baseline(
                version=args.create_baseline,
                run_full_benchmark=args.full_benchmark
            )
            print(f"Baseline created: {baseline.version}")
        
        if args.compare:
            baseline_version, current_version = args.compare
            print(f"Comparing {baseline_version} vs {current_version}")
            comparison = engine.compare_versions(baseline_version, current_version)
            print(f"Overall score: {comparison.overall_score:.1f}")
            print(f"Recommendation: {comparison.recommendation}")
            print(f"Regressions: {len(comparison.regression_alerts)}")
            print(f"Improvements: {len(comparison.improvement_highlights)}")
        
        if args.list_baselines:
            print("Available baselines:")
            baselines = engine.list_baselines()
            for baseline in baselines:
                print(f"  {baseline.version} ({baseline.timestamp.strftime('%Y-%m-%d %H:%M')})")
        
        if args.trends:
            print(f"Trends for metric: {args.trends}")
            trends = engine.get_version_trends(args.trends)
            print(json.dumps(trends, indent=2))
        
        if args.report:
            baseline_version, current_version = args.report
            print(f"Generating regression report: {baseline_version} vs {current_version}")
            report = engine.generate_regression_report(baseline_version, current_version)
            print(json.dumps(report, indent=2))
    
    asyncio.run(main())