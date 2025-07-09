#!/usr/bin/env python3
"""
Analyze and clean up imports across PagBank codebase
"""

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


class ImportAnalyzer(ast.NodeVisitor):
    """Analyze imports in Python files"""
    
    def __init__(self):
        self.imports = []
        self.from_imports = []
        self.used_names = set()
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno
            })
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        module = node.module or ''
        for alias in node.names:
            self.from_imports.append({
                'module': module,
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno
            })
        self.generic_visit(node)
        
    def visit_Name(self, node):
        self.used_names.add(node.id)
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

def analyze_file(file_path: Path) -> Dict[str, any]:
    """Analyze imports in a single file"""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        
        # Determine unused imports
        unused_imports = []
        
        for imp in analyzer.imports:
            name = imp['alias'] or imp['module'].split('.')[0]
            if name not in analyzer.used_names:
                unused_imports.append(imp)
                
        for imp in analyzer.from_imports:
            name = imp['alias'] or imp['name']
            if name not in analyzer.used_names and name != '*':
                unused_imports.append(imp)
        
        return {
            'imports': analyzer.imports,
            'from_imports': analyzer.from_imports,
            'unused_imports': unused_imports,
            'total_imports': len(analyzer.imports) + len(analyzer.from_imports),
            'unused_count': len(unused_imports)
        }
    except Exception as e:
        return {
            'error': str(e),
            'imports': [],
            'from_imports': [],
            'unused_imports': [],
            'total_imports': 0,
            'unused_count': 0
        }

def check_import_order(imports: List[Dict], from_imports: List[Dict]) -> Dict[str, any]:
    """Check if imports follow recommended order"""
    order_score = 0
    issues = []
    
    all_imports = [(imp['line'], imp['module'], 'import') for imp in imports]
    all_imports.extend([(imp['line'], imp['module'], 'from') for imp in from_imports])
    all_imports.sort()
    
    # Categories
    stdlib = {'os', 'sys', 'json', 'logging', 'datetime', 'pathlib', 'typing', 're', 'time', 'asyncio'}
    agno = {'agno'}
    
    last_category = None
    for line, module, imp_type in all_imports:
        # Determine category
        root_module = module.split('.')[0]
        
        if root_module in stdlib:
            category = 'stdlib'
        elif root_module == 'agno':
            category = 'agno'
        elif module.startswith('.') or not '.' in module:
            category = 'local'
        else:
            category = 'third_party'
            
        # Check order
        category_order = ['stdlib', 'third_party', 'agno', 'local']
        if last_category and category_order.index(category) < category_order.index(last_category):
            issues.append(f"Line {line}: {category} import after {last_category}")
            
        last_category = category
    
    return {
        'ordered': len(issues) == 0,
        'issues': issues
    }

def main():
    """Main analysis function"""
    print("🔍 PagBank Import Analysis and Cleanup")
    print("=" * 60)
    
    results = {
        'files_analyzed': 0,
        'total_imports': 0,
        'total_unused': 0,
        'files_with_unused': [],
        'import_patterns': defaultdict(int),
        'recommendations': []
    }
    
    # Find all Python files (excluding venv and archives)
    python_files = []
    for pattern in ['**/*.py']:
        for file in Path('.').glob(pattern):
            if not any(part in str(file) for part in ['.venv', '__pycache__', 'genie/archive']):
                python_files.append(file)
    
    print(f"\n📋 Analyzing {len(python_files)} Python files...")
    
    file_results = {}
    
    for file_path in python_files:
        analysis = analyze_file(file_path)
        file_results[str(file_path)] = analysis
        
        results['files_analyzed'] += 1
        results['total_imports'] += analysis['total_imports']
        results['total_unused'] += analysis['unused_count']
        
        if analysis['unused_count'] > 0:
            results['files_with_unused'].append({
                'file': str(file_path),
                'unused_count': analysis['unused_count'],
                'unused_imports': analysis['unused_imports']
            })
            
        # Track import patterns
        for imp in analysis['imports'] + analysis['from_imports']:
            module = imp.get('module', '')
            if module:
                root = module.split('.')[0]
                results['import_patterns'][root] += 1
    
    # Sort files by unused import count
    results['files_with_unused'].sort(key=lambda x: x['unused_count'], reverse=True)
    
    print(f"\n📊 Summary:")
    print(f"  Files analyzed: {results['files_analyzed']}")
    print(f"  Total imports: {results['total_imports']}")
    print(f"  Unused imports: {results['total_unused']}")
    print(f"  Files with unused imports: {len(results['files_with_unused'])}")
    
    if results['files_with_unused']:
        print(f"\n⚠️ Top files with unused imports:")
        for file_info in results['files_with_unused'][:10]:
            print(f"  - {file_info['file']}: {file_info['unused_count']} unused")
            for imp in file_info['unused_imports'][:3]:
                if 'name' in imp:
                    print(f"    Line {imp['line']}: from {imp['module']} import {imp['name']}")
                else:
                    print(f"    Line {imp['line']}: import {imp['module']}")
    
    # Check specific files for import order
    print(f"\n🔍 Checking import order in key files...")
    key_files = [
        'teams/base_team.py',
        'orchestrator/main_orchestrator.py',
        'memory/memory_manager.py'
    ]
    
    for file_name in key_files:
        file_path = Path(file_name)
        if file_path.exists():
            analysis = file_results.get(file_name, {})
            if 'imports' in analysis:
                order_check = check_import_order(
                    analysis.get('imports', []),
                    analysis.get('from_imports', [])
                )
                if order_check['ordered']:
                    print(f"  ✅ {file_name}: Import order correct")
                else:
                    print(f"  ❌ {file_name}: Import order issues")
                    for issue in order_check['issues'][:2]:
                        print(f"     - {issue}")
    
    # Generate recommendations
    print(f"\n💡 Recommendations:")
    
    if results['total_unused'] > 0:
        results['recommendations'].append({
            'priority': 'high',
            'action': 'Remove unused imports',
            'details': f"Found {results['total_unused']} unused imports across {len(results['files_with_unused'])} files"
        })
    
    # Check for commonly unused imports
    common_unused = defaultdict(int)
    for file_info in results['files_with_unused']:
        for imp in file_info['unused_imports']:
            module = imp.get('module', '') or imp.get('name', '')
            common_unused[module] += 1
    
    if common_unused:
        top_unused = sorted(common_unused.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n  Most commonly unused imports:")
        for module, count in top_unused:
            print(f"    - {module}: unused in {count} files")
    
    # Save detailed report
    report_path = Path("tmp/import_analysis_report.json")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        # Convert results to be JSON serializable
        report_data = {
            'summary': {
                'files_analyzed': results['files_analyzed'],
                'total_imports': results['total_imports'],
                'total_unused': results['total_unused'],
                'files_with_unused_count': len(results['files_with_unused'])
            },
            'files_with_unused': results['files_with_unused'][:20],  # Top 20 files
            'import_patterns': dict(results['import_patterns']),
            'recommendations': results['recommendations']
        }
        json.dump(report_data, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_path}")
    
    # Generate cleanup script
    if results['total_unused'] > 0:
        print(f"\n🔧 To clean up unused imports, run:")
        print(f"   uv run python -m autoflake --remove-all-unused-imports --in-place --recursive .")
        print(f"   uv run python -m isort .")
    
    return results

if __name__ == "__main__":
    main()