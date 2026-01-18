"""
Workflow Orchestrator.

This module orchestrates the complete customer intelligence workflow using LangGraph,
managing the flow between all specialized agents in the correct sequence.

Features:
- Sequential agent execution with state passing
- Comprehensive error handling and recovery
- Performance metrics and latency tracking
- Hallucination prevention through validation
- Structured logging and monitoring
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph
from rich.console import Console
from rich.table import Table

from ..agents.data_collector import DataCollectorAgent
from ..agents.sentiment_analyzer import SentimentAnalyzerAgent
from ..agents.pattern_detector import PatternDetectorAgent
from ..agents.opportunity_finder import OpportunityFinderAgent
from ..agents.strategy_creator import StrategyCreatorAgent
from .state import WorkflowState, create_initial_state
from ..utils.logger import get_workflow_logger, log_workflow_start, log_workflow_complete, log_agent_execution


class WorkflowMetrics:
    """Tracks performance metrics for the workflow execution."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.agent_timings = {}
        self.errors = []
        self.warnings = []
        self.hallucination_checks = []

    def start_workflow(self):
        """Mark the start of workflow execution."""
        self.start_time = datetime.now()

    def end_workflow(self):
        """Mark the end of workflow execution."""
        self.end_time = datetime.now()

    def record_agent_timing(self, agent_name: str, duration: float, status: str):
        """Record timing and status for an agent execution."""
        self.agent_timings[agent_name] = {
            "duration": duration,
            "status": status,
            "timestamp": datetime.now()
        }

    def add_error(self, agent_name: str, error: str):
        """Record an error that occurred."""
        self.errors.append({
            "agent": agent_name,
            "error": error,
            "timestamp": datetime.now()
        })

    def add_hallucination_check(self, agent_name: str, check_result: Dict[str, Any]):
        """Record hallucination validation results."""
        self.hallucination_checks.append({
            "agent": agent_name,
            "result": check_result,
            "timestamp": datetime.now()
        })

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        total_duration = None
        if self.start_time and self.end_time:
            total_duration = (self.end_time - self.start_time).total_seconds()

        return {
            "total_duration_seconds": total_duration,
            "agent_timings": self.agent_timings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "hallucination_checks": len(self.hallucination_checks),
            "agents_completed": len([t for t in self.agent_timings.values() if t["status"] == "completed"]),
            "agents_failed": len([t for t in self.agent_timings.values() if t["status"] == "failed"])
        }


class CustomerIntelligenceOrchestrator:
    """
    Orchestrates the complete customer intelligence workflow using LangGraph.

    Advanced features:
    - Sequential agent execution with state validation
    - Comprehensive error handling and recovery
    - Performance metrics and latency tracking
    - Hallucination prevention through validation
    - Structured logging and monitoring

    Workflow: Data Collection → Sentiment Analysis → Pattern Detection → Opportunity Finding → Strategy Creation
    """

    def __init__(self):
        """Initialize the orchestrator with all agents and build the workflow graph."""
        self.console = Console()
        self.logger = get_workflow_logger("orchestrator")

        # Initialize metrics tracking
        self.metrics = WorkflowMetrics()

        # Initialize all agents
        self.console.print("[dim]Initializing agents...[/dim]")
        self.data_collector = DataCollectorAgent()
        self.sentiment_analyzer = SentimentAnalyzerAgent()
        self.pattern_detector = PatternDetectorAgent()
        self.opportunity_finder = OpportunityFinderAgent()
        self.strategy_creator = StrategyCreatorAgent()

        # Also store in dictionary for consistency
        self.agents = {
            "data_collector": self.data_collector,
            "sentiment_analyzer": self.sentiment_analyzer,
            "pattern_detector": self.pattern_detector,
            "opportunity_finder": self.opportunity_finder,
            "strategy_creator": self.strategy_creator
        }

        # Build the workflow graph
        self.console.print("[dim]Building workflow graph...[/dim]")
        self.workflow = self._build_workflow()

        self.console.print("[green]✓ Orchestrator initialized successfully[/green]")
        self.logger.info("CustomerIntelligenceOrchestrator initialized with 5 agents")

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with all agent nodes and edges.

        Returns:
            Compiled StateGraph workflow
        """
        # Create the graph with WorkflowState
        workflow = StateGraph(WorkflowState)

        # Add nodes for each agent
        workflow.add_node("collect_data", self._collect_data_node)
        workflow.add_node("analyze_sentiment", self._analyze_sentiment_node)
        workflow.add_node("detect_patterns", self._detect_patterns_node)
        workflow.add_node("find_opportunities", self._find_opportunities_node)
        workflow.add_node("create_strategy", self._create_strategy_node)

        # Define the linear workflow edges
        workflow.add_edge("collect_data", "analyze_sentiment")
        workflow.add_edge("analyze_sentiment", "detect_patterns")
        workflow.add_edge("detect_patterns", "find_opportunities")
        workflow.add_edge("find_opportunities", "create_strategy")

        # Set the entry point
        workflow.set_entry_point("collect_data")

        # Compile the graph
        compiled_workflow = workflow.compile()

        self.console.print("[dim]Workflow graph compiled with 5 agents in sequence[/dim]")

        return compiled_workflow

    def run(self, company_name: str, product_name: str, data_sources: List[str]) -> Dict[str, Any]:
        """
        Execute the complete customer intelligence workflow with comprehensive monitoring.

        Args:
            company_name: Name of the company to analyze
            product_name: Name of the product to analyze
            data_sources: List of data sources to include

        Returns:
            Final workflow state with all results and performance metrics
        """
        # Initialize metrics and logging
        workflow_id = f"{company_name.lower().replace(' ', '_')}_{int(time.time())}"
        self.logger = get_workflow_logger(workflow_id)
        self.metrics = WorkflowMetrics()

        log_workflow_start(workflow_id, {
            "company": company_name,
            "product": product_name,
            "data_sources": data_sources
        })

        try:
            self.console.print(f"\n🚀 [bold blue]Starting Customer Intelligence Analysis[/bold blue]")
            self.console.print(f"Workflow ID: [dim]{workflow_id}[/dim]")
            self.console.print(f"Company: [cyan]{company_name}[/cyan]")
            self.console.print(f"Product: [cyan]{product_name}[/cyan]")
            self.console.print(f"Data Sources: [cyan]{', '.join(data_sources)}[/cyan]\n")

            # Start timing
            self.metrics.start_workflow()
            start_time = time.time()

            # Create initial state with validation
            initial_state = create_initial_state(company_name, product_name, data_sources)

            # Pre-flight validation
            validation_result = self._validate_initial_state(initial_state)
            if not validation_result["valid"]:
                raise ValueError(f"Initial state validation failed: {validation_result['errors']}")

            # Execute the workflow
            self.console.print("🔄 Executing workflow...\n")

            final_state = self.workflow.invoke(initial_state)

            # End timing
            self.metrics.end_workflow()
            total_duration = time.time() - start_time

            # Convert to regular dict for return
            result = dict(final_state)

            # Add performance metrics
            result["performance_metrics"] = self.metrics.get_summary()
            result["workflow_id"] = workflow_id

            # Validate final results
            hallucination_report = self._validate_final_results(result)
            result["validation_report"] = hallucination_report

            # Success logging
            log_workflow_complete(workflow_id, total_duration, len(result.get("errors", [])))

            self.console.print("\n✅ [bold green]Workflow completed successfully![/bold green]")
            self._display_performance_metrics(result["performance_metrics"])
            self._display_validation_report(hallucination_report)

            return result

        except Exception as e:
            # Error handling and recovery
            error_msg = f"Workflow execution failed: {str(e)}"
            self.logger.error(error_msg)
            self.metrics.add_error("orchestrator", error_msg)

            # End timing even on failure
            self.metrics.end_workflow()

            self.console.print(f"\n❌ [bold red]Workflow failed: {error_msg}[/bold red]")

            # Return failure state with metrics
            failure_result = {
                "company_name": company_name,
                "product_name": product_name,
                "data_sources": data_sources,
                "current_step": "failed",
                "errors": [error_msg],
                "iteration_count": 0,
                "performance_metrics": self.metrics.get_summary(),
                "workflow_id": workflow_id
            }

            log_workflow_complete(workflow_id, duration=None, errors=1)
            return failure_result

    def _collect_data_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the data collection node with timing and validation."""
        agent_name = "data_collector"
        start_time = time.time()

        try:
            self.console.print("🔍 [bold]Step 1/5: Data Collection[/bold]")

            # Execute agent
            result = self.data_collector.process(dict(state))

            # Validate results
            validation = self._validate_agent_output(agent_name, result)
            if not validation["valid"]:
                self.console.print(f"⚠️  [yellow]Data collection validation warnings: {len(validation['warnings'])}[/yellow]")

            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_agent_timing(agent_name, duration, "completed")
            log_agent_execution(agent_name, "completed", duration)

            return WorkflowState(**result)

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Data collection error: {str(e)}"

            self.console.print(f"❌ [red]Data collection failed: {str(e)}[/red]")
            self.logger.error(error_msg)

            # Record failure metrics
            self.metrics.record_agent_timing(agent_name, duration, "failed")
            self.metrics.add_error(agent_name, error_msg)
            log_agent_execution(agent_name, "failed", duration, error_msg)

            # Add error to state and continue (graceful degradation)
            state_copy = dict(state)
            state_copy["errors"] = state_copy.get("errors", []) + [error_msg]
            return WorkflowState(**state_copy)

    def _analyze_sentiment_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the sentiment analysis node with timing and validation."""
        agent_name = "sentiment_analyzer"
        start_time = time.time()

        try:
            self.console.print("💭 [bold]Step 2/5: Sentiment Analysis[/bold]")
            result = self.sentiment_analyzer.process(dict(state))

            validation = self._validate_agent_output(agent_name, result)
            if not validation["valid"]:
                self.console.print(f"⚠️  [yellow]Sentiment validation warnings: {len(validation['warnings'])}[/yellow]")

            duration = time.time() - start_time
            self.metrics.record_agent_timing(agent_name, duration, "completed")
            log_agent_execution(agent_name, "completed", duration)

            return WorkflowState(**result)
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Sentiment analysis error: {str(e)}"
            self.console.print(f"❌ [red]Sentiment analysis failed: {str(e)}[/red]")
            self.logger.error(error_msg)

            self.metrics.record_agent_timing(agent_name, duration, "failed")
            self.metrics.add_error(agent_name, error_msg)
            log_agent_execution(agent_name, "failed", duration, error_msg)

            state_copy = dict(state)
            state_copy["errors"] = state_copy.get("errors", []) + [error_msg]
            return WorkflowState(**state_copy)

    def _detect_patterns_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the pattern detection node with timing and validation."""
        agent_name = "pattern_detector"
        start_time = time.time()

        try:
            self.console.print("🔎 [bold]Step 3/5: Pattern Detection[/bold]")
            result = self.pattern_detector.process(dict(state))

            validation = self._validate_agent_output(agent_name, result)
            if not validation["valid"]:
                self.console.print(f"⚠️  [yellow]Pattern validation warnings: {len(validation['warnings'])}[/yellow]")

            duration = time.time() - start_time
            self.metrics.record_agent_timing(agent_name, duration, "completed")
            log_agent_execution(agent_name, "completed", duration)

            return WorkflowState(**result)
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Pattern detection error: {str(e)}"
            self.console.print(f"❌ [red]Pattern detection failed: {str(e)}[/red]")
            self.logger.error(error_msg)

            self.metrics.record_agent_timing(agent_name, duration, "failed")
            self.metrics.add_error(agent_name, error_msg)
            log_agent_execution(agent_name, "failed", duration, error_msg)

            state_copy = dict(state)
            state_copy["errors"] = state_copy.get("errors", []) + [error_msg]
            return WorkflowState(**state_copy)

    def _find_opportunities_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the opportunity finding node with timing and validation."""
        agent_name = "opportunity_finder"
        start_time = time.time()

        try:
            self.console.print("💡 [bold]Step 4/5: Opportunity Finding[/bold]")
            result = self.opportunity_finder.process(dict(state))

            validation = self._validate_agent_output(agent_name, result)
            if not validation["valid"]:
                self.console.print(f"⚠️  [yellow]Opportunity validation warnings: {len(validation['warnings'])}[/yellow]")

            duration = time.time() - start_time
            self.metrics.record_agent_timing(agent_name, duration, "completed")
            log_agent_execution(agent_name, "completed", duration)

            return WorkflowState(**result)
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Opportunity finding error: {str(e)}"
            self.console.print(f"❌ [red]Opportunity finding failed: {str(e)}[/red]")
            self.logger.error(error_msg)

            self.metrics.record_agent_timing(agent_name, duration, "failed")
            self.metrics.add_error(agent_name, error_msg)
            log_agent_execution(agent_name, "failed", duration, error_msg)

            state_copy = dict(state)
            state_copy["errors"] = state_copy.get("errors", []) + [error_msg]
            return WorkflowState(**state_copy)

    def _create_strategy_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the strategy creation node with timing and validation."""
        agent_name = "strategy_creator"
        start_time = time.time()

        try:
            self.console.print("📊 [bold]Step 5/5: Strategy Creation[/bold]")

            # Execute agent
            result = self.strategy_creator.process(dict(state))

            # Validate results (critical for final output)
            validation = self._validate_agent_output(agent_name, result)
            if not validation["valid"]:
                self.console.print(f"⚠️  [yellow]Strategy validation warnings: {len(validation['warnings'])}[/yellow]")
                # For strategy, we want to be more strict
                if len(validation["warnings"]) > 2:
                    raise ValueError(f"Too many strategy validation warnings: {validation['warnings']}")

            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_agent_timing(agent_name, duration, "completed")
            log_agent_execution(agent_name, "completed", duration)

            return WorkflowState(**result)

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Strategy creation error: {str(e)}"

            self.console.print(f"❌ [red]Strategy creation failed: {str(e)}[/red]")
            self.logger.error(error_msg)

            # Record failure metrics
            self.metrics.record_agent_timing(agent_name, duration, "failed")
            self.metrics.add_error(agent_name, error_msg)
            log_agent_execution(agent_name, "failed", duration, error_msg)

            # Add error to state
            state_copy = dict(state)
            state_copy["errors"] = state_copy.get("errors", []) + [error_msg]
            return WorkflowState(**state_copy)

    def _validate_initial_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the initial workflow state before execution.

        Args:
            state: Initial workflow state

        Returns:
            Validation results
        """
        validation = {"valid": True, "errors": [], "warnings": []}

        # Required fields
        required = ["company_name", "product_name", "data_sources"]
        for field in required:
            if not state.get(field):
                validation["errors"].append(f"Missing required field: {field}")
                validation["valid"] = False

        # Data sources validation
        if state.get("data_sources"):
            valid_sources = ["reviews", "tickets", "surveys"]
            for source in state["data_sources"]:
                if source not in valid_sources:
                    validation["warnings"].append(f"Unknown data source: {source}")

        return validation

    def _validate_agent_output(self, agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate agent output for hallucinations and data quality.

        Args:
            agent_name: Name of the agent
            result: Agent output to validate

        Returns:
            Validation results
        """
        validation = {"valid": True, "errors": [], "warnings": []}

        try:
            if agent_name == "data_collector":
                # Validate data collection
                raw_data = result.get("raw_data", [])
                if not raw_data:
                    validation["errors"].append("No data collected")
                    validation["valid"] = False
                elif len(raw_data) < 5:
                    validation["warnings"].append("Very small dataset collected")

            elif agent_name == "sentiment_analyzer":
                # Validate sentiment analysis
                sentiment = result.get("sentiment_results", {})
                if not sentiment:
                    validation["errors"].append("No sentiment analysis results")
                    validation["valid"] = False
                elif not sentiment.get("overall_sentiment"):
                    validation["warnings"].append("Missing overall sentiment classification")

            elif agent_name == "pattern_detector":
                # Validate pattern detection
                patterns = result.get("patterns", [])
                if len(patterns) == 0:
                    validation["warnings"].append("No patterns detected")
                elif len(patterns) > 20:
                    validation["warnings"].append("Unusually high number of patterns detected")

            elif agent_name == "opportunity_finder":
                # Validate opportunity finding
                opportunities = result.get("opportunities", [])
                if len(opportunities) == 0:
                    validation["warnings"].append("No opportunities identified")
                # Check if opportunities are supported by patterns
                patterns = result.get("patterns", [])
                if patterns and len(opportunities) > len(patterns) * 2:
                    validation["warnings"].append("Too many opportunities relative to patterns detected")

            elif agent_name == "strategy_creator":
                # Validate strategy creation
                recommendations = result.get("strategy_recommendations", [])
                summary = result.get("executive_summary", "")

                if not recommendations:
                    validation["errors"].append("No strategy recommendations generated")
                    validation["valid"] = False
                elif len(recommendations) < 3:
                    validation["warnings"].append("Very few strategy recommendations")

                if not summary or len(summary) < 100:
                    validation["warnings"].append("Executive summary too short or missing")

        except Exception as e:
            validation["warnings"].append(f"Validation error: {str(e)}")

        return validation

    def _validate_final_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive hallucination and consistency checks on final results.

        Args:
            results: Complete workflow results

        Returns:
            Hallucination and validation report
        """
        report = {
            "hallucination_checks": [],
            "consistency_checks": [],
            "coverage_metrics": {},
            "overall_score": 0.0
        }

        try:
            # Check if recommendations are supported by input data
            raw_data = results.get("raw_data", [])
            recommendations = results.get("strategy_recommendations", [])
            patterns = results.get("patterns", [])

            # Coverage: % of pain points addressed
            if raw_data and recommendations:
                coverage_score = min(len(recommendations) / max(len(raw_data) * 0.1, 1), 1.0)
                report["coverage_metrics"]["pain_point_coverage"] = coverage_score
                report["consistency_checks"].append({
                    "check": "Recommendation Coverage",
                    "score": coverage_score,
                    "details": ".1%"
                })

            # Hallucination check: Are opportunities based on actual patterns?
            opportunities = results.get("opportunities", [])
            if opportunities and patterns:
                supported_opportunities = 0
                for opp in opportunities:
                    opp_text = str(opp.get("description", "")).lower()
                    supported = any(
                        pattern["description"].lower() in opp_text or
                        opp_text in pattern["description"].lower()
                        for pattern in patterns
                    )
                    if supported:
                        supported_opportunities += 1

                hallucination_rate = 1.0 - (supported_opportunities / len(opportunities))
                report["hallucination_checks"].append({
                    "check": "Opportunity Hallucination Rate",
                    "rate": hallucination_rate,
                    "details": ".1%"
                })

            # Overall validation score
            scores = []
            for check in report["consistency_checks"] + report["hallucination_checks"]:
                if "score" in check:
                    scores.append(check["score"])
                elif "rate" in check:
                    scores.append(1.0 - check["rate"])  # Convert rate to score

            if scores:
                report["overall_score"] = sum(scores) / len(scores)

        except Exception as e:
            report["hallucination_checks"].append({
                "check": "Validation Error",
                "error": str(e)
            })

        return report

    def _display_performance_metrics(self, metrics: Dict[str, Any]):
        """Display workflow performance metrics in a table."""
        table = Table(title="Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow", justify="right")

        if metrics.get("total_duration_seconds"):
            table.add_row("Total Runtime", ".2f")

        table.add_row("Agents Completed", str(metrics.get("agents_completed", 0)))
        table.add_row("Agents Failed", str(metrics.get("agents_failed", 0)))
        table.add_row("Errors", str(metrics.get("error_count", 0)))

        self.console.print(table)

    def _display_validation_report(self, report: Dict[str, Any]):
        """Display validation and hallucination check results."""
        if report.get("hallucination_checks"):
            self.console.print("\n🛡️  [bold]Validation Report[/bold]")

            for check in report["hallucination_checks"]:
                if "rate" in check:
                    rate_color = "red" if check["rate"] > 0.3 else "yellow" if check["rate"] > 0.1 else "green"
                    self.console.print(f"  {check['check']}: [{rate_color}]{check['details']}[/{rate_color}]")

            if report.get("overall_score"):
                score_color = "green" if report["overall_score"] > 0.8 else "yellow" if report["overall_score"] > 0.6 else "red"
                self.console.print(f"  Overall Validation Score: [{score_color}]{report['overall_score']:.1%}[/{score_color}]")