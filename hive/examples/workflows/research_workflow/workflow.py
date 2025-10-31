"""
Sequential Research Workflow

A multi-step workflow that demonstrates sequential processing with state passing.
Shows how to build complex research pipelines with Agno Workflows.
"""

from pathlib import Path

import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.workflow import Step, StepOutput, Workflow


def planning_step(step_input) -> StepOutput:
    """
    Step 1: Create a research plan based on the topic.

    Args:
        step_input: Contains the user's research topic

    Returns:
        StepOutput with research plan
    """
    # Initialize workflow state if needed
    if step_input.workflow_session_state is None:
        step_input.workflow_session_state = {}

    topic = step_input.message

    # Create simple agent for planning
    planner = Agent(
        name="Research Planner",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a research planner. Create a structured research plan with:
        1. Key questions to answer
        2. Areas to explore
        3. Expected outcomes

        Keep it concise and actionable.""",
    )

    response = planner.run(f"Create a research plan for: {topic}")
    plan = response.content

    # Store plan in workflow state
    step_input.workflow_session_state["plan"] = plan
    step_input.workflow_session_state["topic"] = topic

    return StepOutput(content=f"Research Plan Created:\n\n{plan}")


def research_step(step_input) -> StepOutput:
    """
    Step 2: Execute research based on the plan.

    Args:
        step_input: Contains workflow state with plan

    Returns:
        StepOutput with research findings
    """
    # Access previous state
    plan = step_input.workflow_session_state.get("plan", "")
    topic = step_input.workflow_session_state.get("topic", "")

    # Create researcher agent
    researcher = Agent(
        name="Researcher",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a research assistant. Based on the plan provided,
        gather key information and findings. Provide structured data with:
        - Main findings
        - Supporting evidence
        - Key insights""",
    )

    response = researcher.run(f"Research Topic: {topic}\n\nPlan:\n{plan}\n\nProvide research findings.")
    findings = response.content

    # Store findings in state
    step_input.workflow_session_state["findings"] = findings

    return StepOutput(content=f"Research Complete:\n\n{findings}")


def analysis_function(step_input) -> StepOutput:
    """
    Step 3: Analyze research findings (pure function example).

    Args:
        step_input: Contains workflow state with findings

    Returns:
        StepOutput with analysis
    """
    findings = step_input.workflow_session_state.get("findings", "")

    # Simple analysis logic
    analysis = f"""
ANALYSIS RESULTS:
-----------------

Data Points Found: {len(findings.split("."))}
Key Themes: [Extracted from findings]

Analysis:
{findings[:200]}...

Confidence: High
Next Steps: Proceed to summary generation
"""

    # Store analysis in state
    step_input.workflow_session_state["analysis"] = analysis

    return StepOutput(content=analysis)


def summary_step(step_input) -> StepOutput:
    """
    Step 4: Create final summary with all insights.

    Args:
        step_input: Contains complete workflow state

    Returns:
        StepOutput with final summary
    """
    topic = step_input.workflow_session_state.get("topic", "")
    plan = step_input.workflow_session_state.get("plan", "")
    findings = step_input.workflow_session_state.get("findings", "")
    analysis = step_input.workflow_session_state.get("analysis", "")

    # Create summarizer agent
    summarizer = Agent(
        name="Summarizer",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a research summarizer. Create a comprehensive summary with:
        - Executive summary
        - Key findings
        - Recommendations
        - Conclusion

        Make it clear and actionable.""",
    )

    full_context = f"""
Topic: {topic}

Plan:
{plan}

Findings:
{findings}

Analysis:
{analysis}

Create a comprehensive final summary."""

    response = summarizer.run(full_context)
    summary = response.content

    # Store final summary
    step_input.workflow_session_state["summary"] = summary

    return StepOutput(content=f"FINAL RESEARCH SUMMARY:\n\n{summary}")


def get_research_workflow(**kwargs) -> Workflow:
    """
    Create sequential research workflow with YAML configuration.

    This workflow demonstrates:
    - Sequential step execution
    - State passing between steps
    - Mix of agents and functions
    - Complete research pipeline

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

    # Create workflow with sequential steps
    workflow = Workflow(
        name=workflow_config.get("name"),
        steps=[
            Step(name="Planning", function=planning_step),
            Step(name="Research", function=research_step),
            Step(name="Analysis", function=analysis_function),
            Step(name="Summary", function=summary_step),
        ],
        **kwargs,
    )

    return workflow


# Quick test function
if __name__ == "__main__":
    print("Testing Sequential Research Workflow...")

    workflow = get_research_workflow()
    print(f"✅ Workflow created: {workflow.name}")
    print(f"✅ Steps: {len(workflow.steps)}")

    # Test with a research topic
    print("\n🔍 Starting research workflow...")
    response = workflow.run(message="The impact of AI on software development")

    print(f"\n📝 Final Result:\n{response.content}")

    # Show final state
    if hasattr(response, "workflow_session_state"):
        state = response.workflow_session_state
        print("\n📊 Workflow State:")
        print(f"  - Topic: {state.get('topic', 'N/A')}")
        print(f"  - Plan: {len(state.get('plan', ''))} chars")
        print(f"  - Findings: {len(state.get('findings', ''))} chars")
        print(f"  - Analysis: {len(state.get('analysis', ''))} chars")
        print(f"  - Summary: {len(state.get('summary', ''))} chars")
