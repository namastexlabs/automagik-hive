"""
Dynamic Model Parameter Resolver

This module provides truly dynamic parameter resolution for Agno models
by introspecting the actual model classes at runtime to determine what
parameters they accept. No hardcoded lists, no manual maintenance.

This ensures compatibility with any Agno version automatically.
"""

import inspect
from typing import Any, Dict, Set, Type
from lib.logging import logger


class DynamicModelResolver:
    """
    Dynamically resolves which parameters a model class accepts
    by introspecting its __init__ method at runtime.
    
    This eliminates the need for hardcoded parameter lists and
    automatically adapts to Agno API changes.
    """
    
    def __init__(self):
        self._param_cache: Dict[str, Set[str]] = {}
        
    def get_valid_parameters(self, model_class: Type) -> Set[str]:
        """
        Get the set of valid parameters for a model class.
        
        Args:
            model_class: The model class to introspect
            
        Returns:
            Set of parameter names the class accepts
        """
        class_name = f"{model_class.__module__}.{model_class.__name__}"
        
        # Check cache first
        if class_name in self._param_cache:
            return self._param_cache[class_name]
        
        try:
            # Get the signature of the __init__ method
            sig = inspect.signature(model_class.__init__)
            
            # Extract parameter names (excluding 'self')
            params = {
                param_name
                for param_name, param in sig.parameters.items()
                if param_name != "self"
            }
            
            # Cache the result
            self._param_cache[class_name] = params
            
            logger.debug(
                f"Discovered {len(params)} parameters for {class_name}: {sorted(params)}"
            )
            
            return params
            
        except Exception as e:
            logger.warning(
                f"Failed to introspect {class_name}: {e}. Using fallback approach."
            )
            # Return empty set to trigger fallback behavior
            return set()
    
    def filter_parameters_for_model(
        self, 
        model_class: Type,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filter parameters to only include those accepted by the model class.
        
        Args:
            model_class: The model class to filter for
            parameters: Dictionary of all parameters
            
        Returns:
            Dictionary containing only parameters the model accepts
        """
        valid_params = self.get_valid_parameters(model_class)
        
        if not valid_params:
            # Fallback: try instantiation and handle errors
            return self._filter_by_trial(model_class, parameters)
        
        # Filter to only valid parameters
        filtered = {
            key: value
            for key, value in parameters.items()
            if key in valid_params
        }
        
        logger.debug(
            f"Filtered {len(parameters)} params to {len(filtered)} valid params for {model_class.__name__}"
        )
        
        return filtered
    
    def _filter_by_trial(
        self,
        model_class: Type,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback approach: try instantiation and progressively remove problematic parameters.
        
        This is slower but ensures compatibility even when introspection fails.
        """
        filtered_params = parameters.copy()
        problematic_params = set()
        
        max_attempts = 10  # Prevent infinite loops
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Try to instantiate with current parameters
                test_instance = model_class(**filtered_params)
                # Success! Return the working parameter set
                logger.debug(
                    f"Trial instantiation succeeded with {len(filtered_params)} parameters"
                )
                return filtered_params
                
            except TypeError as e:
                # Parse error message to find problematic parameter
                error_msg = str(e)
                
                # Common error patterns
                if "unexpected keyword argument" in error_msg:
                    # Extract the parameter name from error message
                    # E.g., "unexpected keyword argument 'output_model'"
                    parts = error_msg.split("'")
                    if len(parts) >= 2:
                        bad_param = parts[1]
                        if bad_param in filtered_params:
                            problematic_params.add(bad_param)
                            del filtered_params[bad_param]
                            logger.debug(
                                f"Removed problematic parameter '{bad_param}' from model config"
                            )
                            attempt += 1
                            continue
                
                # If we can't parse the error, give up
                logger.warning(
                    f"Could not parse TypeError to identify problematic parameter: {e}"
                )
                break
                
            except Exception as e:
                # Other errors - can't handle automatically
                logger.warning(
                    f"Unexpected error during trial instantiation: {e}"
                )
                break
        
        # Return whatever we managed to filter
        if problematic_params:
            logger.info(
                f"Filtered out {len(problematic_params)} incompatible parameters: {problematic_params}"
            )
        
        return filtered_params
    
    def clear_cache(self):
        """Clear the parameter cache."""
        self._param_cache.clear()
        logger.debug("Dynamic model resolver cache cleared")


# Global instance
_resolver = DynamicModelResolver()


def filter_model_parameters(model_class: Type, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter parameters to only include those accepted by the model class.
    
    This is the main entry point for dynamic parameter filtering.
    """
    return _resolver.filter_parameters_for_model(model_class, parameters)


def clear_resolver_cache():
    """Clear the global resolver cache."""
    _resolver.clear_cache()