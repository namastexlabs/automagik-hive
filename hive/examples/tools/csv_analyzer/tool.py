"""
CSV Analyzer Tool

A pandas-based tool for analyzing CSV files and generating statistics.
Demonstrates data analysis tool patterns.
"""

from pathlib import Path
from typing import Any

import yaml

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  pandas not installed - tool will run in limited mode")


class CSVAnalyzerTool:
    """
    CSV analysis tool with comprehensive statistics generation.

    Features:
    - Basic statistics (count, mean, std, min, max)
    - Data type detection
    - Missing value analysis
    - Duplicate detection
    - Column correlations (optional)
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialize CSV analyzer tool.

        Args:
            config_path: Path to config.yaml (defaults to same directory)
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for CSV analysis. Install with: uv add pandas")

        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        # Load configuration
        with open(config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.tool_config = self.config.get("tool", {})
        self.params = self.tool_config.get("parameters", {})
        self.analysis_options = self.tool_config.get("analysis_options", {})

    def analyze(self, file_path: str, delimiter: str | None = None, columns: list[str] | None = None) -> dict[str, Any]:
        """
        Analyze CSV file and generate comprehensive report.

        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter (defaults to config)
            columns: Specific columns to analyze (None = all)

        Returns:
            Dict with analysis results
        """
        try:
            # Validate file
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"status": "error", "error": f"File not found: {file_path}"}

            # Check file size
            file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
            max_size = self.params.get("max_file_size_mb", 50)
            if file_size_mb > max_size:
                return {"status": "error", "error": f"File too large: {file_size_mb:.2f}MB (max: {max_size}MB)"}

            # Read CSV
            delim = delimiter or self.params.get("default_delimiter", ",")
            encoding = self.params.get("encoding", "utf-8")

            df = pd.read_csv(file_path, delimiter=delim, encoding=encoding)

            # Filter columns if specified
            if columns:
                missing_cols = [c for c in columns if c not in df.columns]
                if missing_cols:
                    return {"status": "error", "error": f"Columns not found: {missing_cols}"}
                df = df[columns]

            # Run analysis
            analysis = self._run_analysis(df, file_path_obj.name)

            return {
                "status": "success",
                "file": str(file_path_obj),
                "file_size_mb": round(file_size_mb, 2),
                "analysis": analysis,
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "file": file_path}

    def _run_analysis(self, df: pd.DataFrame, filename: str) -> dict[str, Any]:
        """
        Run comprehensive analysis on dataframe.

        Args:
            df: Pandas DataFrame
            filename: Name of CSV file

        Returns:
            Dict with analysis results
        """
        analysis = {
            "filename": filename,
            "overview": self._get_overview(df),
        }

        # Add optional analyses based on configuration
        if self.analysis_options.get("include_basic_stats", True):
            analysis["statistics"] = self._get_statistics(df)

        if self.analysis_options.get("include_data_types", True):
            analysis["data_types"] = self._get_data_types(df)

        if self.analysis_options.get("include_missing_values", True):
            analysis["missing_values"] = self._get_missing_values(df)

        if self.analysis_options.get("include_duplicates", True):
            analysis["duplicates"] = self._get_duplicates(df)

        if self.analysis_options.get("include_correlations", False):
            analysis["correlations"] = self._get_correlations(df)

        # Generate insights
        analysis["insights"] = self._generate_insights(df, analysis)

        return analysis

    def _get_overview(self, df: pd.DataFrame) -> dict[str, Any]:
        """Get basic overview of dataset."""
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        }

    def _get_statistics(self, df: pd.DataFrame) -> dict[str, Any]:
        """Get descriptive statistics for numeric columns."""
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if not numeric_cols:
            return {"note": "No numeric columns found"}

        stats = df[numeric_cols].describe().to_dict()

        return {"numeric_columns": numeric_cols, "statistics": stats}

    def _get_data_types(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze data types in dataset."""
        dtype_counts = df.dtypes.value_counts().to_dict()

        return {
            "by_column": df.dtypes.astype(str).to_dict(),
            "summary": {str(k): int(v) for k, v in dtype_counts.items()},
        }

    def _get_missing_values(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze missing values."""
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)

        cols_with_missing = missing[missing > 0].to_dict()
        pct_with_missing = missing_pct[missing_pct > 0].to_dict()

        return {
            "total_missing": int(missing.sum()),
            "columns_with_missing": len(cols_with_missing),
            "by_column": {
                col: {"count": int(cols_with_missing[col]), "percentage": float(pct_with_missing[col])}
                for col in cols_with_missing
            },
        }

    def _get_duplicates(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze duplicate rows."""
        duplicates = df.duplicated()
        dup_count = duplicates.sum()

        return {
            "total_duplicates": int(dup_count),
            "percentage": round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "has_duplicates": dup_count > 0,
        }

    def _get_correlations(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculate correlations between numeric columns."""
        numeric_df = df.select_dtypes(include=["number"])

        if numeric_df.shape[1] < 2:
            return {"note": "Need at least 2 numeric columns for correlation"}

        # Get top correlations
        corr_matrix = numeric_df.corr()

        # Find strongest correlations (excluding self-correlation)
        correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                correlations.append(
                    {
                        "column1": corr_matrix.columns[i],
                        "column2": corr_matrix.columns[j],
                        "correlation": round(corr_matrix.iloc[i, j], 3),
                    }
                )

        # Sort by absolute correlation
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "top_correlations": correlations[:10],  # Top 10
            "correlation_matrix": corr_matrix.to_dict(),
        }

    def _generate_insights(self, df: pd.DataFrame, analysis: dict[str, Any]) -> list[str]:
        """Generate human-readable insights from analysis."""
        insights = []

        # Overview insights
        overview = analysis.get("overview", {})
        insights.append(
            f"Dataset contains {overview.get('total_rows', 0):,} rows and {overview.get('total_columns', 0)} columns"
        )

        # Missing values
        if "missing_values" in analysis:
            missing = analysis["missing_values"]
            if missing["total_missing"] > 0:
                insights.append(
                    f"Found {missing['total_missing']:,} missing values across {missing['columns_with_missing']} columns"
                )
            else:
                insights.append("No missing values detected - data quality is good")

        # Duplicates
        if "duplicates" in analysis:
            dup = analysis["duplicates"]
            if dup["has_duplicates"]:
                insights.append(f"Found {dup['total_duplicates']:,} duplicate rows ({dup['percentage']}%)")
            else:
                insights.append("No duplicate rows found")

        # Data types
        if "data_types" in analysis:
            dtype_summary = analysis["data_types"].get("summary", {})
            numeric_count = dtype_summary.get("int64", 0) + dtype_summary.get("float64", 0)
            if numeric_count > 0:
                insights.append(f"Dataset has {numeric_count} numeric columns suitable for statistical analysis")

        # Strong correlations
        if "correlations" in analysis:
            top_corrs = analysis["correlations"].get("top_correlations", [])
            if top_corrs:
                strongest = top_corrs[0]
                insights.append(
                    f"Strongest correlation: {strongest['column1']} and {strongest['column2']} ({strongest['correlation']})"
                )

        return insights


# Factory function for tool registry
def get_csv_analyzer_tool(**kwargs) -> CSVAnalyzerTool:
    """
    Create CSV analyzer tool instance.

    Args:
        **kwargs: Runtime overrides

    Returns:
        CSVAnalyzerTool: Configured tool instance
    """
    return CSVAnalyzerTool()


# Quick test function
if __name__ == "__main__":
    import os
    import tempfile

    print("Testing CSV Analyzer Tool...")

    # Create tool
    tool = get_csv_analyzer_tool()
    print(f"✅ Tool created: {tool.tool_config.get('name')}")
    print(f"✅ Version: {tool.tool_config.get('version')}")

    # Create sample CSV for testing
    print("\n📊 Creating sample CSV...")
    sample_data = """name,age,salary,department,years_experience
John Doe,30,75000,Engineering,5
Jane Smith,28,72000,Engineering,4
Bob Johnson,35,85000,Engineering,8
Alice Williams,32,78000,Engineering,6
Charlie Brown,29,73000,Marketing,3
Diana Prince,31,76000,Marketing,5
Eve Wilson,33,80000,Sales,7
Frank Miller,30,74000,Sales,4
Grace Lee,28,71000,Sales,3
Henry Davis,34,82000,Engineering,9"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(sample_data)
        temp_file = f.name

    try:
        # Run analysis
        print(f"📈 Analyzing CSV: {temp_file}\n")
        result = tool.analyze(temp_file)

        if result["status"] == "success":
            print("✅ Analysis completed successfully\n")

            analysis = result["analysis"]

            # Print overview
            print("📊 OVERVIEW:")
            overview = analysis["overview"]
            print(f"  Rows: {overview['total_rows']:,}")
            print(f"  Columns: {overview['total_columns']}")
            print(f"  Memory: {overview['memory_usage_mb']:.2f} MB")

            # Print statistics
            if "statistics" in analysis:
                print("\n📈 STATISTICS:")
                stats = analysis["statistics"]
                print(f"  Numeric columns: {', '.join(stats['numeric_columns'])}")

            # Print missing values
            if "missing_values" in analysis:
                print("\n🔍 MISSING VALUES:")
                missing = analysis["missing_values"]
                print(f"  Total: {missing['total_missing']}")
                print(f"  Columns affected: {missing['columns_with_missing']}")

            # Print duplicates
            if "duplicates" in analysis:
                print("\n🔄 DUPLICATES:")
                dup = analysis["duplicates"]
                print(f"  Total: {dup['total_duplicates']}")
                print(f"  Percentage: {dup['percentage']}%")

            # Print insights
            print("\n💡 INSIGHTS:")
            for insight in analysis.get("insights", []):
                print(f"  • {insight}")

        else:
            print(f"❌ Analysis failed: {result.get('error')}")

    finally:
        # Cleanup
        os.unlink(temp_file)
        print("\n✅ Test completed")
