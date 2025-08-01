"""
Template Workflow - Comprehensive Agno Workflows 2.0 Example
============================================================

This template demonstrates all key features of Agno Workflows 2.0:
- Step-based architecture with sequential execution
- Session state management across steps
- Factory function pattern for workflow creation
- Proper error handling and validation
- Integration with Agno storage and event systems
"""

import json
from datetime import UTC, datetime

from agno.agent import Agent
from agno.workflow.v2 import Step, Workflow
from agno.workflow.v2.types import StepInput, StepOutput

from lib.config.models import get_default_model_id, resolve_model
from lib.logging import logger


def create_template_model():
    """Create model for template workflow using dynamic resolution"""

    return resolve_model(
        model_id=get_default_model_id(),  # Use environment-based default
        temperature=0.7,
        max_tokens=1000,
    )


def create_validation_agent() -> Agent:
    """Create validation agent for input processing"""
    return Agent(
        name="Template Validator",
        model=create_template_model(),
        description="Validates and processes template workflow inputs",
        instructions=[
            "You are a template workflow validator.",
            "Analyze the input and ensure it meets basic requirements.",
            "Provide structured validation results with confidence scores.",
            "Be thorough but concise in your analysis.",
        ],
    )


def create_processing_agent() -> Agent:
    """Create main processing agent"""
    return Agent(
        name="Template Processor",
        model=create_template_model(),
        description="Processes validated inputs using template workflow logic",
        instructions=[
            "You are a template workflow processor.",
            "Take validated input and perform the main processing logic.",
            "Use information from previous workflow steps when available.",
            "Provide detailed processing results.",
        ],
    )


def create_finalizer_agent() -> Agent:
    """Create workflow finalizer agent"""
    return Agent(
        name="Template Finalizer",
        model=create_template_model(),
        description="Finalizes template workflow execution and provides summary",
        instructions=[
            "You are a template workflow finalizer.",
            "Review all previous workflow steps and provide a comprehensive summary.",
            "Include validation results, processing outcomes, and final recommendations.",
            "Ensure all workflow objectives have been met.",
        ],
    )


# Step executor functions
def execute_validation_step(step_input: StepInput) -> StepOutput:
    """Execute input validation step"""
    input_message = step_input.message
    if not input_message:
        raise ValueError("Input message is required for validation")

    logger.info("Executing template validation step...")

    validator = create_validation_agent()
    response = validator.run(
        f"Validate this input for template workflow:\n\n{input_message}"
    )

    if not response.content:
        raise ValueError("Invalid validation response")

    # Extract validation results
    validation_data = {
        "input_valid": True,
        "input_length": len(input_message),
        "validation_timestamp": datetime.now(UTC).isoformat(),
        "validation_notes": str(response.content),
        "original_input": input_message,
    }

    logger.info(
        f"📊 Validation completed - Input length: {validation_data['input_length']} characters"
    )

    return StepOutput(content=json.dumps(validation_data))


def execute_processing_step(step_input: StepInput) -> StepOutput:
    """Execute main processing step"""
    # Get validation results from previous step
    previous_output = step_input.get_step_output("validation_step")
    if not previous_output:
        raise ValueError("Previous validation step output not found")

    validation_data = json.loads(previous_output.content)
    original_input = validation_data["original_input"]

    logger.info("Executing template processing step...")

    processor = create_processing_agent()

    processing_context = f"""
    Validation Results: {validation_data["validation_notes"]}
    Input Length: {validation_data["input_length"]} characters
    Original Input: {original_input}

    Please process this input according to template workflow requirements.
    """

    response = processor.run(processing_context)

    if not response.content:
        raise ValueError("Invalid processing response")

    # Create processing results
    processing_data = {
        "processing_result": str(response.content),
        "processing_timestamp": datetime.now(UTC).isoformat(),
        "input_metadata": validation_data,
        "workflow_step": "processing",
        "success": True,
    }

    logger.info("Processing step completed successfully")

    return StepOutput(content=json.dumps(processing_data))


def execute_completion_step(step_input: StepInput) -> StepOutput:
    """Execute workflow completion and finalization step"""
    # Get processing results from previous step
    previous_output = step_input.get_step_output("processing_step")
    if not previous_output:
        raise ValueError("Previous processing step output not found")

    processing_data = json.loads(previous_output.content)

    logger.info("Executing template completion step...")

    finalizer = create_finalizer_agent()

    completion_context = f"""
    Workflow Execution Summary:

    Validation Results: {processing_data["input_metadata"]["validation_notes"]}
    Processing Results: {processing_data["processing_result"]}

    Please provide a comprehensive workflow completion summary.
    """

    response = finalizer.run(completion_context)

    if not response.content:
        raise ValueError("Invalid completion response")

    # Create final results
    completion_data = {
        "workflow_summary": str(response.content),
        "completion_timestamp": datetime.now(UTC).isoformat(),
        "total_steps_executed": 3,
        "workflow_status": "completed",
        "validation_metadata": processing_data["input_metadata"],
        "processing_metadata": {
            "processing_result": processing_data["processing_result"],
            "processing_timestamp": processing_data["processing_timestamp"],
        },
        "success": True,
    }

    logger.info("Template workflow completed successfully")

    return StepOutput(content=json.dumps(completion_data))


# Factory function to create workflow
def get_template_workflow_workflow(**kwargs) -> Workflow:
    """Factory function to create template workflow"""

    # Create workflow with step-based architecture
    workflow = Workflow(
        name="template_workflow",
        description="Template workflow demonstrating all Agno Workflows 2.0 features",
        steps=[
            Step(
                name="validation_step",
                description="Validate input parameters and workflow configuration",
                executor=execute_validation_step,
                max_retries=3,
            ),
            Step(
                name="processing_step",
                description="Process the main workflow logic with validated input",
                executor=execute_processing_step,
                max_retries=3,
            ),
            Step(
                name="completion_step",
                description="Complete workflow execution and provide final results",
                executor=execute_completion_step,
                max_retries=2,
            ),
        ],
        **kwargs,
    )

    logger.info("Template Workflow initialized successfully")
    return workflow


# For backward compatibility and direct testing
template_workflow = get_template_workflow_workflow()


if __name__ == "__main__":
    # Test the workflow
    import asyncio

    async def test_template_workflow():
        """Test template workflow execution"""

        test_input = """
        This is a test input for the template workflow.
        It demonstrates the step-based execution pattern with:
        - Input validation
        - Main processing logic
        - Workflow completion and summary

        The workflow should process this input through all three steps
        and provide a comprehensive summary of the execution.
        """

        # Create workflow instance
        workflow = get_template_workflow_workflow()

        logger.info("Testing template workflow...")
        logger.info(f"🤖 Input length: {len(test_input)} characters")

        # Run workflow
        result = await workflow.arun(message=test_input.strip())

        logger.info("Template workflow execution completed:")
        logger.info(f"🤖 {result.content if hasattr(result, 'content') else result}")

    # Run test
    asyncio.run(test_template_workflow())
