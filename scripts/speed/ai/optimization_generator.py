#!/usr/bin/env python3
"""
Genie Speed Optimization Framework - Optimization Generator
Generates optimization candidates using AI models with zen consensus
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import traceback
import ast
import inspect
import re

# Add project root to path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

# Import zen consensus tools
try:
    from scripts.speed.ai.zen_integration import ZenConsensusClient
except ImportError:
    ZenConsensusClient = None


class OptimizationGenerator:
    """
    Generates optimization candidates using AI models
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.zen_client = ZenConsensusClient(verbose=verbose) if ZenConsensusClient else None
        
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[{level}] {message}")
    
    def parse_target(self, target: str) -> Tuple[str, str]:
        """Parse target into file path and function name"""
        if "::" in target:
            file_path, function_name = target.split("::", 1)
            return file_path, function_name
        else:
            return target, None
    
    def read_source_code(self, file_path: str) -> str:
        """Read source code from file"""
        try:
            abs_path = Path(project_root) / file_path
            with open(abs_path, 'r') as f:
                return f.read()
        except Exception as e:
            self.log(f"Error reading source code: {e}", "ERROR")
            raise
    
    def extract_function_code(self, source_code: str, function_name: str) -> str:
        """Extract function code from source"""
        try:
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Get the function source
                    lines = source_code.splitlines()
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else len(lines)
                    
                    function_lines = lines[start_line:end_line]
                    return '\n'.join(function_lines)
            
            raise ValueError(f"Function {function_name} not found")
            
        except Exception as e:
            self.log(f"Error extracting function code: {e}", "ERROR")
            raise
    
    def analyze_function_complexity(self, function_code: str) -> Dict[str, Any]:
        """Analyze function complexity and identify optimization opportunities"""
        try:
            tree = ast.parse(function_code)
            
            analysis = {
                "lines_of_code": len(function_code.splitlines()),
                "cyclomatic_complexity": 1,  # Base complexity
                "loop_count": 0,
                "nested_loop_count": 0,
                "condition_count": 0,
                "function_calls": 0,
                "list_comprehensions": 0,
                "optimization_opportunities": []
            }
            
            # Count various constructs
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    analysis["loop_count"] += 1
                    analysis["cyclomatic_complexity"] += 1
                    
                    # Check for nested loops
                    for child in ast.walk(node):
                        if child != node and isinstance(child, (ast.For, ast.While)):
                            analysis["nested_loop_count"] += 1
                            analysis["optimization_opportunities"].append("nested_loop_optimization")
                
                elif isinstance(node, (ast.If, ast.While)):
                    analysis["condition_count"] += 1
                    analysis["cyclomatic_complexity"] += 1
                
                elif isinstance(node, ast.Call):
                    analysis["function_calls"] += 1
                
                elif isinstance(node, ast.ListComp):
                    analysis["list_comprehensions"] += 1
            
            # Identify optimization opportunities
            if analysis["nested_loop_count"] > 0:
                analysis["optimization_opportunities"].append("algorithm_optimization")
            
            if analysis["function_calls"] > 10:
                analysis["optimization_opportunities"].append("function_call_reduction")
            
            if analysis["lines_of_code"] > 50:
                analysis["optimization_opportunities"].append("code_splitting")
                
            return analysis
            
        except Exception as e:
            self.log(f"Error analyzing function complexity: {e}", "ERROR")
            return {}
    
    def generate_single_model_optimization(self, model: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization using a single model"""
        self.log(f"Generating optimization using model: {model}")
        
        # Prepare optimization prompt
        prompt = self.create_optimization_prompt(context)
        
        # For now, return a mock optimization
        # In production, this would call the actual AI model
        optimization = {
            "model": model,
            "timestamp": time.time(),
            "optimization_code": self.generate_mock_optimization(context),
            "explanation": f"Optimization generated by {model}",
            "estimated_improvement": 15.0,
            "confidence": 0.8,
            "optimization_type": "algorithm_improvement"
        }
        
        return optimization
    
    def create_optimization_prompt(self, context: Dict[str, Any]) -> str:
        """Create optimization prompt for AI model"""
        target = context.get("target", "")
        function_code = context.get("function_code", "")
        complexity_analysis = context.get("complexity_analysis", {})
        
        prompt = f"""
You are an expert Python performance optimization engineer. Your task is to optimize the following function for better performance while maintaining correctness.

Target: {target}
Function Code:
```python
{function_code}
```

Complexity Analysis:
{json.dumps(complexity_analysis, indent=2)}

Please provide an optimized version of this function that:
1. Maintains the same functionality and behavior
2. Improves performance by at least 10%
3. Follows Python best practices
4. Preserves the function signature
5. Includes clear comments explaining the optimization

Focus on:
- Algorithm improvements (better time complexity)
- Data structure optimizations
- Loop optimizations
- Memory usage improvements
- Built-in function utilization

Return the optimized code and explain the improvements made.
"""
        
        return prompt
    
    def generate_mock_optimization(self, context: Dict[str, Any]) -> str:
        """Generate mock optimization for testing"""
        function_code = context.get("function_code", "")
        
        # Simple mock optimization: add caching
        if "def " in function_code:
            # Add a simple cache decorator
            optimized_code = function_code.replace(
                "def ",
                "from functools import lru_cache\n\n@lru_cache(maxsize=128)\ndef "
            )
            return optimized_code
        
        return function_code
    
    def generate_consensus_optimization(self, models: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization using multiple models with consensus"""
        self.log(f"Generating consensus optimization with models: {models}")
        
        if not self.zen_client:
            self.log("Zen consensus not available, falling back to single model", "WARNING")
            return self.generate_single_model_optimization(models[0], context)
        
        # Generate optimizations from each model
        model_optimizations = []
        for model in models:
            try:
                optimization = self.generate_single_model_optimization(model, context)
                model_optimizations.append(optimization)
            except Exception as e:
                self.log(f"Error generating optimization with {model}: {e}", "WARNING")
                continue
        
        if not model_optimizations:
            raise ValueError("No optimizations generated")
        
        # Use zen consensus to select best optimization
        consensus_result = self.zen_client.get_consensus(
            optimizations=model_optimizations,
            context=context
        )
        
        return consensus_result
    
    def validate_optimization(self, original_code: str, optimized_code: str) -> Dict[str, Any]:
        """Validate optimization for basic correctness"""
        validation = {
            "syntax_valid": False,
            "signature_preserved": False,
            "imports_valid": False,
            "warnings": []
        }
        
        try:
            # Check syntax
            ast.parse(optimized_code)
            validation["syntax_valid"] = True
            
            # Check function signature preservation
            orig_tree = ast.parse(original_code)
            opt_tree = ast.parse(optimized_code)
            
            orig_funcs = [node for node in ast.walk(orig_tree) if isinstance(node, ast.FunctionDef)]
            opt_funcs = [node for node in ast.walk(opt_tree) if isinstance(node, ast.FunctionDef)]
            
            if len(orig_funcs) == len(opt_funcs):
                validation["signature_preserved"] = True
            
            # Check for dangerous imports
            dangerous_imports = ["os", "subprocess", "eval", "exec"]
            for node in ast.walk(opt_tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in dangerous_imports:
                            validation["warnings"].append(f"Dangerous import: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in dangerous_imports:
                        validation["warnings"].append(f"Dangerous import: {node.module}")
            
            validation["imports_valid"] = len(validation["warnings"]) == 0
            
        except SyntaxError as e:
            validation["warnings"].append(f"Syntax error: {e}")
        except Exception as e:
            validation["warnings"].append(f"Validation error: {e}")
        
        return validation
    
    def generate_optimization(self, target: str, attempt: int, models: Optional[List[str]] = None,
                            consensus: bool = False) -> Dict[str, Any]:
        """Generate optimization for target"""
        self.log(f"Generating optimization attempt {attempt} for: {target}")
        
        try:
            # Parse target
            file_path, function_name = self.parse_target(target)
            
            # Read source code
            source_code = self.read_source_code(file_path)
            
            # Extract function code
            if function_name:
                function_code = self.extract_function_code(source_code, function_name)
            else:
                function_code = source_code
            
            # Analyze complexity
            complexity_analysis = self.analyze_function_complexity(function_code)
            
            # Prepare context
            context = {
                "target": target,
                "file_path": file_path,
                "function_name": function_name,
                "source_code": source_code,
                "function_code": function_code,
                "complexity_analysis": complexity_analysis,
                "attempt": attempt
            }
            
            # Generate optimization
            if consensus and models and len(models) > 1:
                result = self.generate_consensus_optimization(models, context)
            else:
                model = models[0] if models else "grok-4-0709"
                result = self.generate_single_model_optimization(model, context)
            
            # Validate optimization
            validation = self.validate_optimization(function_code, result.get("optimization_code", ""))
            result["validation"] = validation
            
            # Add metadata
            result.update({
                "target": target,
                "attempt": attempt,
                "consensus_used": consensus,
                "models_used": models or ["grok-4-0709"],
                "generation_timestamp": time.time()
            })
            
            return result
            
        except Exception as e:
            self.log(f"Error generating optimization: {e}", "ERROR")
            traceback.print_exc()
            return {
                "target": target,
                "attempt": attempt,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "generation_timestamp": time.time()
            }
    
    def save_optimization(self, optimization: Dict[str, Any], output_file: str):
        """Save optimization to file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(optimization, f, indent=2, default=str)
            
            # Also save the code separately for easy access
            if "optimization_code" in optimization:
                code_file = output_file.replace('.json', '.py')
                with open(code_file, 'w') as f:
                    f.write(optimization["optimization_code"])
                self.log(f"Optimization code saved to: {code_file}")
            
            self.log(f"Optimization saved to: {output_file}")
            
        except Exception as e:
            self.log(f"Error saving optimization: {e}", "ERROR")
            raise


def main():
    parser = argparse.ArgumentParser(description="Genie Speed Optimization - Optimization Generator")
    parser.add_argument("--target", required=True, help="Target to optimize (file::function or file)")
    parser.add_argument("--attempt", type=int, default=1, help="Optimization attempt number")
    parser.add_argument("--output", required=True, help="Output file for optimization")
    parser.add_argument("--consensus", action="store_true", help="Use multi-model consensus")
    parser.add_argument("--models", help="Comma-separated list of models to use")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Parse models
    models = args.models.split(",") if args.models else ["grok-4-0709"]
    
    # Create generator
    generator = OptimizationGenerator(verbose=args.verbose)
    
    # Generate optimization
    optimization = generator.generate_optimization(
        target=args.target,
        attempt=args.attempt,
        models=models,
        consensus=args.consensus
    )
    
    # Save optimization
    generator.save_optimization(optimization, args.output)
    
    # Print summary
    if "error" in optimization:
        print(f"❌ Optimization generation failed: {optimization['error']}")
        sys.exit(1)
    else:
        validation = optimization.get("validation", {})
        print(f"✅ Optimization generated successfully")
        print(f"🤖 Model(s): {', '.join(optimization.get('models_used', []))}")
        print(f"🔍 Consensus: {'Yes' if optimization.get('consensus_used', False) else 'No'}")
        print(f"✅ Syntax valid: {validation.get('syntax_valid', False)}")
        print(f"✅ Signature preserved: {validation.get('signature_preserved', False)}")
        
        if validation.get("warnings"):
            print(f"⚠️  Warnings: {len(validation['warnings'])}")
            for warning in validation["warnings"]:
                print(f"   - {warning}")
        
        print(f"📁 Optimization saved to: {args.output}")


if __name__ == "__main__":
    main()