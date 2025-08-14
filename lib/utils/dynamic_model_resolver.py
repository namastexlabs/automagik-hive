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
        
        Uses trial instantiation to ensure compatibility when introspection fails.
        Works by attempting to create a test instance and removing parameters that cause errors.
        """
        filtered_params = parameters.copy()
        problematic_params = set()
        
        max_attempts = 15  # Increased to handle more complex parameter sets
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Try to instantiate with current parameters
                # Note: We only test the constructor, we don't need a working instance
                test_instance = model_class(**filtered_params)
                
                # Success! Return the working parameter set
                logger.debug(
                    f"✅ Trial instantiation succeeded with {len(filtered_params)} parameters for {model_class.__name__}"
                )
                if problematic_params:
                    logger.info(
                        f"🔧 Successfully filtered out {len(problematic_params)} incompatible parameters: {sorted(problematic_params)}"
                    )
                return filtered_params
                
            except TypeError as e:
                # Parse error message to find problematic parameter
                error_msg = str(e)
                
                # Enhanced error pattern matching
                bad_param = None
                
                if "unexpected keyword argument" in error_msg:
                    # E.g., "unexpected keyword argument 'output_model'"
                    parts = error_msg.split("'")
                    if len(parts) >= 2:
                        bad_param = parts[1]
                        
                elif "got an unexpected keyword argument" in error_msg:
                    # Alternative format: "Constructor() got an unexpected keyword argument 'param'"
                    parts = error_msg.split("'")
                    if len(parts) >= 2:
                        bad_param = parts[1]
                        
                elif "takes" in error_msg and "positional argument" in error_msg:
                    # Handle cases where too many positional args provided
                    # This is less common but can happen with certain parameter combinations
                    logger.debug(f"Positional argument error, trying to remove least essential parameters")
                    # Remove non-essential parameters in order of importance
                    for param_to_try in ['timeout', 'retries', 'max_tokens']:
                        if param_to_try in filtered_params:
                            bad_param = param_to_try
                            break
                
                if bad_param and bad_param in filtered_params:
                    problematic_params.add(bad_param)
                    del filtered_params[bad_param]
                    logger.debug(
                        f"🔧 Removed problematic parameter '{bad_param}' from {model_class.__name__} config"
                    )
                    attempt += 1
                    continue
                else:
                    # If we can't parse the error or parameter not found, give up
                    logger.warning(
                        f"⚠️ Could not parse TypeError for {model_class.__name__}: {e}"
                    )
                    break
                
            except Exception as e:
                # Other errors - might be due to missing required parameters or invalid values
                # These are not parameter compatibility issues, so we stop filtering
                logger.debug(
                    f"⚠️ Non-TypeError during trial instantiation for {model_class.__name__}: {type(e).__name__}: {e}"
                )
                break
        
        # Return whatever we managed to filter, even if not perfect
        if problematic_params:
            logger.info(
                f"🔧 Filtered out {len(problematic_params)} incompatible parameters from {model_class.__name__}: {sorted(problematic_params)}"
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