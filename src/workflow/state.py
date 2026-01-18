"""
Workflow State Management.

This module defines the state management for the LangGraph-based customer
intelligence workflow, including state schemas and state transitions.
"""

from typing import Any, Dict, List, TypedDict
from datetime import datetime


class WorkflowState(TypedDict):
    """
    Main workflow state for the customer intelligence platform.

    This TypedDict defines the structure of the state that flows through
    the LangGraph workflow, tracking the complete pipeline from data collection
    through strategy generation.
    """

    # INPUT FIELDS
    company_name: str
    product_name: str
    data_sources: List[str]  # ['reviews', 'tickets', 'surveys']

    # DATA COLLECTION AGENT OUTPUT
    raw_data: List[Dict[str, Any]]  # Customer feedback items
    data_summary: Dict[str, Any]    # Counts, sources, etc.

    # SENTIMENT AGENT OUTPUT
    sentiment_results: Dict[str, Any]   # Overall sentiment, score, emotions
    sentiment_breakdown: Dict[str, Any]

    # PATTERN DETECTION AGENT OUTPUT
    patterns: List[Dict[str, Any]]  # Detected patterns/trends
    trends: Dict[str, Any]

    # OPPORTUNITY AGENT OUTPUT
    opportunities: List[Dict[str, Any]]  # Product opportunities

    # STRATEGY AGENT OUTPUT
    strategy_recommendations: List[Dict[str, Any]]
    executive_summary: str

    # METADATA
    current_step: str
    iteration_count: int
    errors: List[str]



def create_initial_state(company_name: str, product_name: str,
                        data_sources: List[str]) -> WorkflowState:
    """
    Create an initial workflow state.

    Args:
        company_name: Name of the company
        product_name: Name of the product
        data_sources: List of data sources to analyze

    Returns:
        Initial workflow state
    """
    return WorkflowState(
        # INPUT FIELDS
        company_name=company_name,
        product_name=product_name,
        data_sources=data_sources,

        # DATA COLLECTION AGENT OUTPUT - Initialized as empty
        raw_data=[],
        data_summary={},

        # SENTIMENT AGENT OUTPUT - Initialized as empty
        sentiment_results={},
        sentiment_breakdown={},

        # PATTERN DETECTION AGENT OUTPUT - Initialized as empty
        patterns=[],
        trends={},

        # OPPORTUNITY AGENT OUTPUT - Initialized as empty
        opportunities=[],

        # STRATEGY AGENT OUTPUT - Initialized as empty
        strategy_recommendations=[],
        executive_summary="",

        # METADATA
        current_step="initialization",
        iteration_count=0,
        errors=[]
    )


def update_agent_results(state: WorkflowState, agent_name: str,
                        results: Dict[str, Any]) -> WorkflowState:
    """
    Update the results of a specific agent in the workflow.

    Args:
        state: Current workflow state
        agent_name: Name of the agent
        results: Results from the agent

    Returns:
        Updated workflow state
    """
    # Map agent names to their result fields in the state
    agent_result_mapping = {
        "data_collection": ["raw_data", "data_summary"],
        "sentiment": ["sentiment_results", "sentiment_breakdown"],
        "pattern_detection": ["patterns", "trends"],
        "opportunity": ["opportunities"],
        "strategy": ["strategy_recommendations", "executive_summary"]
    }

    if agent_name in agent_result_mapping:
        result_fields = agent_result_mapping[agent_name]
        for field in result_fields:
            if field in results:
                state[field] = results[field]  # type: ignore

    # Update current step and iteration count
    state["current_step"] = f"{agent_name}_completed"
    state["iteration_count"] += 1

    return state




def add_error(state: WorkflowState, error_message: str) -> WorkflowState:
    """
    Add an error message to the workflow state.

    Args:
        state: Current workflow state
        error_message: Error message string

    Returns:
        Updated workflow state with error added
    """
    state["errors"].append(error_message)
    return state


def validate_state(state: WorkflowState) -> Dict[str, Any]:
    """
    Validate the workflow state for consistency and completeness.

    Args:
        state: Workflow state to validate

    Returns:
        Validation results
    """
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }

    # Check required input fields
    required_fields = ["company_name", "product_name", "data_sources", "current_step"]
    for field in required_fields:
        if field not in state or state[field] is None or state[field] == "":
            validation_results["errors"].append(f"Missing required field: {field}")
            validation_results["valid"] = False

    # Check data_sources is a list and not empty
    if not isinstance(state.get("data_sources"), list) or len(state.get("data_sources", [])) == 0:
        validation_results["errors"].append("data_sources must be a non-empty list")
        validation_results["valid"] = False

    # Check iteration_count is non-negative
    if state.get("iteration_count", 0) < 0:
        validation_results["errors"].append("iteration_count must be non-negative")
        validation_results["valid"] = False

    # Validate current_step values
    valid_steps = [
        "initialization", "data_collection", "sentiment_analysis",
        "pattern_detection", "opportunity_finding", "strategy_creation",
        "data_collection_completed", "sentiment_completed", "pattern_detection_completed",
        "opportunity_completed", "strategy_completed", "completed"
    ]
    if state.get("current_step") not in valid_steps:
        validation_results["warnings"].append(f"Unexpected current_step: {state.get('current_step')}")

    return validation_results


def get_state_summary(state: WorkflowState) -> Dict[str, Any]:
    """
    Generate a summary of the current workflow state.

    Args:
        state: Workflow state

    Returns:
        State summary dictionary
    """
    # Check if pipeline is complete by verifying all output fields have data
    pipeline_complete = (
        len(state.get("raw_data", [])) > 0 and
        len(state.get("sentiment_results", {})) > 0 and
        len(state.get("patterns", [])) > 0 and
        len(state.get("opportunities", [])) > 0 and
        len(state.get("strategy_recommendations", [])) > 0 and
        state.get("executive_summary", "") != ""
    )

    return {
        "company_name": state.get("company_name"),
        "product_name": state.get("product_name"),
        "data_sources": state.get("data_sources"),
        "current_step": state.get("current_step"),
        "iteration_count": state.get("iteration_count"),
        "error_count": len(state.get("errors", [])),
        "data_collected": len(state.get("raw_data", [])) > 0,
        "sentiment_analyzed": len(state.get("sentiment_results", {})) > 0,
        "patterns_detected": len(state.get("patterns", [])) > 0,
        "opportunities_found": len(state.get("opportunities", [])) > 0,
        "strategy_generated": len(state.get("strategy_recommendations", [])) > 0 and state.get("executive_summary", "") != "",
        "pipeline_complete": pipeline_complete
    }
