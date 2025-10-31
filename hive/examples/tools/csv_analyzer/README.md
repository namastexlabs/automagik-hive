# CSV Analyzer Tool

A pandas-based tool for analyzing CSV files and generating comprehensive statistics, insights, and data quality reports.

## Overview

This tool provides automated CSV analysis:

- **Overview Statistics** - Row/column counts, memory usage
- **Descriptive Statistics** - Mean, median, std dev for numeric columns
- **Data Type Analysis** - Column type detection and summary
- **Missing Value Detection** - Identify and quantify null values
- **Duplicate Detection** - Find duplicate rows
- **Correlation Analysis** - Relationships between numeric columns (optional)
- **Automated Insights** - Human-readable findings

## When to Use This Tool

Use the CSV analyzer when:

- Exploring new datasets
- Validating data quality
- Generating data reports
- Identifying data issues
- Understanding data distributions
- Building data pipelines

**Examples:**
- Data quality audits
- Dataset exploration
- ETL validation
- Report generation
- Data profiling
- Pre-processing analysis

## Structure

```
csv-analyzer/
├── config.yaml     # Tool configuration
├── tool.py         # Pandas-based implementation
└── README.md       # This file
```

## Setup

### Install Dependencies

```bash
# Add pandas to project
uv add pandas

# Or for development
uv add --dev pandas
```

### Configure Options

Edit `config.yaml`:

```yaml
parameters:
  max_file_size_mb: 50      # Max CSV size
  max_rows_display: 100     # Display limit
  default_delimiter: ","    # CSV delimiter
  encoding: "utf-8"         # File encoding

analysis_options:
  include_basic_stats: true        # Descriptive statistics
  include_data_types: true         # Type analysis
  include_missing_values: true     # Null detection
  include_duplicates: true         # Duplicate check
  include_correlations: false      # Correlation matrix (expensive)
```

## Usage

### Basic Analysis

```python
from my_test_project.ai.tools.examples.csv_analyzer.tool import get_csv_analyzer_tool

# Create analyzer
analyzer = get_csv_analyzer_tool()

# Analyze CSV file
result = analyzer.analyze("data/sales.csv")

if result["status"] == "success":
    analysis = result["analysis"]

    # Access overview
    print(f"Rows: {analysis['overview']['total_rows']}")
    print(f"Columns: {analysis['overview']['total_columns']}")

    # Access insights
    for insight in analysis["insights"]:
        print(f"• {insight}")
```

### Analyze Specific Columns

```python
# Analyze only specific columns
result = analyzer.analyze(
    file_path="data/users.csv",
    columns=["age", "salary", "department"]
)
```

### Custom Delimiter

```python
# For tab-separated or other delimiters
result = analyzer.analyze(
    file_path="data/export.tsv",
    delimiter="\t"
)
```

### Complete Analysis Report

```python
result = analyzer.analyze("data/dataset.csv")

if result["status"] == "success":
    analysis = result["analysis"]

    # File info
    print(f"File: {result['file']}")
    print(f"Size: {result['file_size_mb']} MB\n")

    # Overview
    overview = analysis["overview"]
    print(f"Rows: {overview['total_rows']:,}")
    print(f"Columns: {overview['total_columns']}")
    print(f"Memory: {overview['memory_usage_mb']:.2f} MB\n")

    # Statistics
    if "statistics" in analysis:
        stats = analysis["statistics"]
        print(f"Numeric columns: {len(stats['numeric_columns'])}")

    # Data quality
    if "missing_values" in analysis:
        missing = analysis["missing_values"]
        print(f"Missing values: {missing['total_missing']:,}")

    if "duplicates" in analysis:
        dup = analysis["duplicates"]
        print(f"Duplicates: {dup['total_duplicates']:,} ({dup['percentage']}%)")

    # Insights
    print("\nKey Insights:")
    for insight in analysis["insights"]:
        print(f"  • {insight}")
```

## Integration with Agents

### Data Analysis Agent

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from my_test_project.ai.tools.examples.csv_analyzer.tool import get_csv_analyzer_tool

def get_data_analyst_agent(**kwargs):
    analyzer = get_csv_analyzer_tool()

    def analyze_csv(file_path: str):
        """Analyze CSV file and return insights."""
        result = analyzer.analyze(file_path)
        if result["status"] == "success":
            return result["analysis"]["insights"]
        return [f"Error: {result.get('error')}"]

    return Agent(
        name="Data Analyst",
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[analyze_csv],
        instructions="""You are a data analyst. Use the analyze_csv tool
        to examine datasets and provide insights.""",
        **kwargs
    )

# Usage
agent = get_data_analyst_agent()
response = agent.run("Analyze the file data/sales_2024.csv")
```

### Workflow with CSV Analysis

```python
from agno.workflow import Workflow, Step, StepOutput

analyzer = get_csv_analyzer_tool()

def analyze_and_report(step_input) -> StepOutput:
    """Analyze CSV and generate report."""

    file_path = step_input.message

    # Run analysis
    result = analyzer.analyze(file_path)

    if result["status"] == "success":
        analysis = result["analysis"]

        # Generate report
        report = f"""
CSV Analysis Report
==================

File: {result['file']}
Rows: {analysis['overview']['total_rows']:,}
Columns: {analysis['overview']['total_columns']}

Key Findings:
"""
        for insight in analysis["insights"]:
            report += f"\n• {insight}"

        return StepOutput(content=report)
    else:
        return StepOutput(content=f"Analysis failed: {result['error']}")

workflow = Workflow(
    name="CSV Analysis Workflow",
    steps=[Step(name="Analyze", function=analyze_and_report)]
)
```

## Analysis Features

### Overview Statistics

```python
overview = {
    "total_rows": 10000,
    "total_columns": 15,
    "columns": ["name", "age", "salary", ...],
    "memory_usage_mb": 1.2
}
```

### Descriptive Statistics

For numeric columns:
- Count, mean, std dev
- Min, 25%, 50%, 75%, max
- Follows pandas `.describe()` format

### Data Type Analysis

```python
data_types = {
    "by_column": {
        "name": "object",
        "age": "int64",
        "salary": "float64"
    },
    "summary": {
        "object": 5,
        "int64": 4,
        "float64": 6
    }
}
```

### Missing Value Analysis

```python
missing_values = {
    "total_missing": 127,
    "columns_with_missing": 3,
    "by_column": {
        "email": {
            "count": 45,
            "percentage": 4.5
        },
        "phone": {
            "count": 82,
            "percentage": 8.2
        }
    }
}
```

### Duplicate Detection

```python
duplicates = {
    "total_duplicates": 15,
    "percentage": 1.5,
    "has_duplicates": True
}
```

### Correlation Analysis

```python
correlations = {
    "top_correlations": [
        {
            "column1": "age",
            "column2": "salary",
            "correlation": 0.857
        },
        {
            "column1": "experience",
            "column2": "salary",
            "correlation": 0.742
        }
    ],
    "correlation_matrix": {...}
}
```

### Automated Insights

Human-readable findings:
```
• Dataset contains 10,000 rows and 15 columns
• No missing values detected - data quality is good
• Found 15 duplicate rows (1.5%)
• Dataset has 10 numeric columns suitable for statistical analysis
• Strongest correlation: age and salary (0.857)
```

## Configuration Options

### File Size Limits

```yaml
parameters:
  max_file_size_mb: 50  # Reject files larger than this
```

### Analysis Toggles

```yaml
analysis_options:
  include_basic_stats: true        # Fast
  include_data_types: true         # Fast
  include_missing_values: true     # Fast
  include_duplicates: true         # Medium
  include_correlations: false      # Slow for large datasets
```

### Encoding Options

```yaml
parameters:
  encoding: "utf-8"        # utf-8, latin-1, etc.
  default_delimiter: ","   # , ; \t |
```

## Performance Considerations

### File Size Recommendations

- **Small (< 10MB)**: All analyses enabled
- **Medium (10-50MB)**: Disable correlations
- **Large (> 50MB)**: Use column filtering

### Optimization Tips

```python
# Analyze specific columns only
result = analyzer.analyze(
    file_path="large_file.csv",
    columns=["col1", "col2", "col3"]  # Subset
)

# Disable expensive operations
# Edit config.yaml:
analysis_options:
  include_correlations: false  # Skip for speed
```

### Memory Management

Tool automatically:
- Checks file size before loading
- Reports memory usage
- Rejects oversized files

## Error Handling

```python
result = analyzer.analyze("data/file.csv")

if result["status"] == "error":
    error = result["error"]

    # Common errors:
    # - "File not found: ..."
    # - "File too large: X MB (max: Y MB)"
    # - "Columns not found: [...]"
    # - CSV parsing errors

    print(f"Analysis failed: {error}")
else:
    # Process successful result
    analysis = result["analysis"]
```

## Testing

Run the standalone test:

```bash
cd /home/cezar/automagik/automagik-hive/my-test-project
python -m ai.tools.examples.csv_analyzer.tool
```

Expected output:
- Tool initialization
- Sample CSV creation
- Complete analysis
- Statistics, missing values, duplicates
- Automated insights

## Integration with Tool Registry

Add to your tool registry:

```python
from ai.tools.examples.csv_analyzer.tool import get_csv_analyzer_tool

tools = {
    "csv-analyzer": get_csv_analyzer_tool,
    # ... other tools
}
```

## Related Examples

- **research-workflow** - Use CSV analysis in research pipelines
- **parallel-workflow** - Analyze multiple CSVs concurrently
- **slack-notifier** - Send analysis results to Slack

## Best Practices

1. **Check file size first** - Avoid loading huge files
2. **Filter columns** - Analyze only what you need
3. **Handle errors gracefully** - Always check status
4. **Disable expensive operations** - For large datasets
5. **Document insights** - Store findings for reference
6. **Version analysis config** - Track what was analyzed
7. **Cache results** - Don't re-analyze same file

## Troubleshooting

**"pandas not installed"**
```bash
uv add pandas
```

**"File too large" errors**
- Increase `max_file_size_mb` in config
- Or filter to specific columns
- Consider chunked processing for truly large files

**Encoding errors**
```python
# Try different encoding
result = analyzer.analyze(
    file_path="file.csv",
    delimiter=","
)
# Or change in config.yaml
```

**Memory errors**
- Reduce `max_file_size_mb`
- Use column filtering
- Disable correlation analysis
- Process file in chunks (custom implementation)

**Missing columns error**
```python
# Check available columns first
result = analyzer.analyze("file.csv")
available = result["analysis"]["overview"]["columns"]
print(f"Available columns: {available}")
```

## Advanced Usage

### Batch Analysis

```python
import glob

analyzer = get_csv_analyzer_tool()

# Analyze all CSVs in directory
results = []
for file in glob.glob("data/*.csv"):
    result = analyzer.analyze(file)
    results.append(result)

# Aggregate insights
all_insights = []
for r in results:
    if r["status"] == "success":
        all_insights.extend(r["analysis"]["insights"])
```

### Custom Insights

Extend the tool:

```python
class CustomCSVAnalyzer(CSVAnalyzerTool):
    def _generate_insights(self, df, analysis):
        # Call parent method
        insights = super()._generate_insights(df, analysis)

        # Add custom insights
        if df["age"].mean() > 30:
            insights.append("Average age exceeds 30 years")

        return insights
```

### Export Analysis

```python
import json

result = analyzer.analyze("data/file.csv")

if result["status"] == "success":
    # Export to JSON
    with open("analysis_report.json", "w") as f:
        json.dump(result, f, indent=2)
```

## Learn More

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Data Analysis with Pandas](https://pandas.pydata.org/docs/user_guide/)
- [CSV Format Specification](https://tools.ietf.org/html/rfc4180)
- [Agno Tools Documentation](https://docs.agno.com/tools/)
