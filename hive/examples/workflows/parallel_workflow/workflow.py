"""
Parallel Processing Workflow

Demonstrates concurrent execution of multiple steps using Agno's Parallel() feature.
Shows how to process multiple data sources simultaneously and merge results.
"""

import time
from pathlib import Path

import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.workflow import Parallel, Step, StepOutput, Workflow


def preparation_step(step_input) -> StepOutput:
    """
    Step 1: Prepare data sources and processing parameters.

    Args:
        step_input: Contains the processing request

    Returns:
        StepOutput with preparation details
    """
    # Initialize workflow state
    if step_input.workflow_session_state is None:
        step_input.workflow_session_state = {}

    request = step_input.message

    # Define data sources to process
    data_sources = [
        {"id": "source1", "name": "User Database", "type": "database", "records": 1000},
        {"id": "source2", "name": "API Logs", "type": "logs", "records": 5000},
        {"id": "source3", "name": "Analytics Data", "type": "analytics", "records": 3000},
    ]

    # Store sources in workflow state
    step_input.workflow_session_state["sources"] = data_sources
    step_input.workflow_session_state["request"] = request
    step_input.workflow_session_state["start_time"] = time.time()

    prep_summary = f"""
Data sources prepared for parallel processing:
- Source 1: {data_sources[0]["name"]} ({data_sources[0]["records"]} records)
- Source 2: {data_sources[1]["name"]} ({data_sources[1]["records"]} records)
- Source 3: {data_sources[2]["name"]} ({data_sources[2]["records"]} records)

Total Records: {sum(s["records"] for s in data_sources)}
Processing Request: {request}
"""

    return StepOutput(content=prep_summary)


def process_source1(step_input) -> StepOutput:
    """
    Parallel Step 1: Process first data source.

    Args:
        step_input: Contains workflow state with sources

    Returns:
        StepOutput with processing results
    """
    sources = step_input.workflow_session_state.get("sources", [])
    source = sources[0] if sources else {}

    # Simulate processing
    start = time.time()
    time.sleep(0.5)  # Simulated processing time
    elapsed = time.time() - start

    result = {
        "source_id": source.get("id"),
        "source_name": source.get("name"),
        "records_processed": source.get("records"),
        "processing_time": elapsed,
        "status": "success",
        "insights": f"Analyzed {source.get('records')} records from {source.get('name')}",
    }

    # Store in state
    if "results" not in step_input.workflow_session_state:
        step_input.workflow_session_state["results"] = []
    step_input.workflow_session_state["results"].append(result)

    return StepOutput(content=f"✅ {source.get('name')}: {result['insights']}")


def process_source2(step_input) -> StepOutput:
    """
    Parallel Step 2: Process second data source.

    Args:
        step_input: Contains workflow state with sources

    Returns:
        StepOutput with processing results
    """
    sources = step_input.workflow_session_state.get("sources", [])
    source = sources[1] if len(sources) > 1 else {}

    # Simulate processing (longer than source1)
    start = time.time()
    time.sleep(0.8)  # Different processing time
    elapsed = time.time() - start

    result = {
        "source_id": source.get("id"),
        "source_name": source.get("name"),
        "records_processed": source.get("records"),
        "processing_time": elapsed,
        "status": "success",
        "insights": f"Processed {source.get('records')} log entries from {source.get('name')}",
    }

    # Store in state
    if "results" not in step_input.workflow_session_state:
        step_input.workflow_session_state["results"] = []
    step_input.workflow_session_state["results"].append(result)

    return StepOutput(content=f"✅ {source.get('name')}: {result['insights']}")


def process_source3(step_input) -> StepOutput:
    """
    Parallel Step 3: Process third data source.

    Args:
        step_input: Contains workflow state with sources

    Returns:
        StepOutput with processing results
    """
    sources = step_input.workflow_session_state.get("sources", [])
    source = sources[2] if len(sources) > 2 else {}

    # Simulate processing
    start = time.time()
    time.sleep(0.6)  # Different processing time
    elapsed = time.time() - start

    result = {
        "source_id": source.get("id"),
        "source_name": source.get("name"),
        "records_processed": source.get("records"),
        "processing_time": elapsed,
        "status": "success",
        "insights": f"Extracted analytics from {source.get('records')} data points",
    }

    # Store in state
    if "results" not in step_input.workflow_session_state:
        step_input.workflow_session_state["results"] = []
    step_input.workflow_session_state["results"].append(result)

    return StepOutput(content=f"✅ {source.get('name')}: {result['insights']}")


def aggregation_step(step_input) -> StepOutput:
    """
    Step 3: Aggregate all parallel processing results.

    Args:
        step_input: Contains workflow state with all results

    Returns:
        StepOutput with aggregated data
    """
    results = step_input.workflow_session_state.get("results", [])
    start_time = step_input.workflow_session_state.get("start_time", time.time())

    # Calculate statistics
    total_records = sum(r["records_processed"] for r in results)
    total_processing_time = time.time() - start_time
    avg_time_per_source = sum(r["processing_time"] for r in results) / len(results) if results else 0

    # Aggregate insights
    aggregation = {
        "total_sources": len(results),
        "total_records": total_records,
        "total_time": total_processing_time,
        "avg_time_per_source": avg_time_per_source,
        "time_saved": (sum(r["processing_time"] for r in results) - total_processing_time),
        "all_results": results,
    }

    # Store aggregation
    step_input.workflow_session_state["aggregation"] = aggregation

    summary = f"""
AGGREGATION COMPLETE:
--------------------
Sources Processed: {aggregation["total_sources"]}
Total Records: {aggregation["total_records"]:,}
Total Processing Time: {aggregation["total_time"]:.2f}s
Average Time Per Source: {aggregation["avg_time_per_source"]:.2f}s
Time Saved by Parallel Processing: {aggregation["time_saved"]:.2f}s

Individual Results:
"""
    for r in results:
        summary += f"\n  • {r['source_name']}: {r['records_processed']} records in {r['processing_time']:.2f}s"

    return StepOutput(content=summary)


def report_step(step_input) -> StepOutput:
    """
    Step 4: Generate final report with AI analysis.

    Args:
        step_input: Contains complete workflow state

    Returns:
        StepOutput with final report
    """
    aggregation = step_input.workflow_session_state.get("aggregation", {})
    request = step_input.workflow_session_state.get("request", "")
    results = step_input.workflow_session_state.get("results", [])

    # Create report generator agent
    reporter = Agent(
        name="Report Generator",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a data analysis report generator. Create a professional report with:
        - Executive Summary
        - Key Findings
        - Performance Metrics
        - Recommendations

        Keep it concise and actionable.""",
    )

    context = f"""
Processing Request: {request}

Aggregation Results:
- Sources: {aggregation.get("total_sources", 0)}
- Records: {aggregation.get("total_records", 0):,}
- Processing Time: {aggregation.get("total_time", 0):.2f}s
- Time Saved: {aggregation.get("time_saved", 0):.2f}s

Source Details:
"""
    for r in results:
        context += f"\n- {r['source_name']}: {r['insights']}"

    context += "\n\nGenerate a comprehensive processing report."

    response = reporter.run(context)
    report = response.content

    # Store final report
    step_input.workflow_session_state["report"] = report

    return StepOutput(content=f"FINAL PROCESSING REPORT:\n\n{report}")


def get_parallel_workflow(**kwargs) -> Workflow:
    """
    Create parallel processing workflow with YAML configuration.

    This workflow demonstrates:
    - Parallel step execution for efficiency
    - Processing multiple data sources concurrently
    - Result aggregation from parallel steps
    - Performance benefits of parallelization

    Args:
        **kwargs: Runtime overrides (session_id, user_id, etc.)

    Returns:
        Workflow: Configured workflow instance
    """
    # Load YAML configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    workflow_config = config.get("workflow", {})

    # Create workflow with parallel steps
    workflow = Workflow(
        name=workflow_config.get("name"),
        steps=[
            Step(name="Preparation", function=preparation_step),
            Parallel(
                Step(name="ProcessSource1", function=process_source1),
                Step(name="ProcessSource2", function=process_source2),
                Step(name="ProcessSource3", function=process_source3),
            ),
            Step(name="Aggregation", function=aggregation_step),
            Step(name="Report", function=report_step),
        ],
        **kwargs,
    )

    return workflow


# Quick test function
if __name__ == "__main__":
    print("Testing Parallel Processing Workflow...")

    workflow = get_parallel_workflow()
    print(f"✅ Workflow created: {workflow.name}")
    print(f"✅ Steps: {len(workflow.steps)}")

    # Test with a processing request
    print("\n⚡ Starting parallel processing workflow...")
    start_time = time.time()

    response = workflow.run(message="Process all data sources for monthly analytics report")

    elapsed = time.time() - start_time

    print(f"\n📝 Final Report:\n{response.content}")

    # Show performance benefits
    if hasattr(response, "workflow_session_state"):
        state = response.workflow_session_state
        aggregation = state.get("aggregation", {})
        print("\n⚡ Performance Metrics:")
        print(f"  - Total Workflow Time: {elapsed:.2f}s")
        print(f"  - Sources Processed: {aggregation.get('total_sources', 0)}")
        print(f"  - Records Processed: {aggregation.get('total_records', 0):,}")
        print(f"  - Time Saved by Parallel Execution: {aggregation.get('time_saved', 0):.2f}s")
        print(f"  - Efficiency Gain: {(aggregation.get('time_saved', 0) / elapsed * 100):.1f}%")
