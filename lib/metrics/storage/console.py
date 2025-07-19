"""
Console Storage Backend

Outputs metrics to console with structured formatting
"""
import json
import logging
from typing import Dict, Any
from .base import MetricsStorage


class ConsoleMetricsStorage(MetricsStorage):
    """Console-based metrics storage backend"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize console storage"""
        super().__init__(config)
        self.logger = logging.getLogger("metrics")
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _validate_config(self) -> None:
        """Console storage requires no specific configuration"""
        pass
    
    def store_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """
        Store metrics data to console output
        
        Args:
            metrics_data: Dictionary containing metrics information
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        try:
            # Format metrics for readable console output
            formatted_output = self._format_metrics(metrics_data)
            self.logger.info(f"METRICS: {formatted_output}")
            return True
        except Exception as e:
            self.handle_storage_error(e, metrics_data)
            return False
    
    def is_available(self) -> bool:
        """Console storage is always available"""
        return True
    
    def _format_metrics(self, metrics_data: Dict[str, Any]) -> str:
        """
        Format metrics for console output
        
        Args:
            metrics_data: Raw metrics data
            
        Returns:
            Formatted string for console output
        """
        try:
            # Extract key information for readable output
            agent_name = metrics_data.get("agent_name", "unknown")
            execution_type = metrics_data.get("execution_type", "unknown")
            timestamp = metrics_data.get("timestamp", "unknown")
            
            metrics = metrics_data.get("metrics", {})
            
            # Build summary line
            summary_parts = [
                f"agent={agent_name}",
                f"type={execution_type}",
                f"time={timestamp}"
            ]
            
            # Add key metrics if available
            if isinstance(metrics, dict):
                if "input_tokens" in metrics:
                    summary_parts.append(f"tokens_in={metrics['input_tokens']}")
                if "output_tokens" in metrics:
                    summary_parts.append(f"tokens_out={metrics['output_tokens']}")
                if "time" in metrics:
                    summary_parts.append(f"duration={metrics['time']}")
            
            return " | ".join(summary_parts)
            
        except Exception:
            # Fallback to JSON if formatting fails
            return json.dumps(metrics_data, separators=(',', ':'))