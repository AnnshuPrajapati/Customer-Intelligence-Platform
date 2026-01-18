"""
Main Entry Point.

This module provides the command-line interface for the Customer Intelligence Platform,
running the complete workflow from data collection through strategy generation.
"""

import argparse
import os
from pathlib import Path
from typing import List

import dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .utils.logger import setup_global_logging
from .utils.metrics import WorkflowEvaluator
from .workflow.orchestrator import CustomerIntelligenceOrchestrator


def main():
    """Main entry point for the Customer Intelligence Platform."""
    # Load environment variables
    dotenv.load_dotenv()

    console = Console()

    # Check for required API key (prioritize Gemini, then fallbacks)
    gemini_key = os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")

    if gemini_key:
        console.print("[green]✓ Google API key found - using Gemini AI (free tier available)![/green]")
    elif openai_key:
        console.print("[green]✓ OpenAI API key found - using GPT-4![/green]")
    elif claude_key:
        console.print("[green]✓ Anthropic API key found - using Claude![/green]")
    else:
        console.print("[yellow]⚠️  No AI API keys found - running in DEMO mode![/yellow]")
        console.print("[blue]This will use mock AI responses for demonstration purposes.[/blue]")
        console.print("")
        console.print("[cyan]To get real AI responses (free options available):[/cyan]")
        console.print("1. Visit: https://makersuite.google.com/app/apikey")
        console.print("2. Create a free Google AI API key (1M tokens/month free)")
        console.print("3. Add GOOGLE_API_KEY to your .env file")
        console.print("4. Re-run for full AI-powered analysis!")
        console.print("")
        console.print("[cyan]Alternative options:[/cyan]")
        console.print("- OpenAI: https://platform.openai.com/api-keys ($5 free credits)")
        console.print("- Anthropic: https://console.anthropic.com/ ($5 free credits)")
        console.print("")
        os.environ["MOCK_MODE"] = "true"  # Set mock mode

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Customer Intelligence Platform - Analyze customer feedback and generate strategic insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                                    # Run with defaults
  python -m src.main --company "Acme Corp" --product "Widget Pro"
  python -m src.main --sources "reviews,tickets"        # Only specific sources
        """
    )

    parser.add_argument(
        "--company",
        default="TechCorp",
        help="Company name to analyze (default: TechCorp)"
    )

    parser.add_argument(
        "--product",
        default="CloudFlow SaaS",
        help="Product name to analyze (default: CloudFlow SaaS)"
    )

    parser.add_argument(
        "--sources",
        default="reviews,tickets,surveys",
        help="Comma-separated list of data sources (default: reviews,tickets,surveys)"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_global_logging(args.log_level)

    # Initialize console for rich output
    console = Console()

    # Parse data sources
    data_sources = [s.strip() for s in args.sources.split(",")]

    # Display welcome message
    welcome_text = Text("🚀 Customer Intelligence Platform", style="bold blue")
    subtitle = Text("Transforming customer feedback into strategic insights", style="dim")
    console.print(Panel.fit(f"{welcome_text}\n{subtitle}", border_style="blue"))

    # Display configuration
    config_table = Table(title="Analysis Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="yellow")

    config_table.add_row("Company", args.company)
    config_table.add_row("Product", args.product)
    config_table.add_row("Data Sources", ", ".join(data_sources))
    config_table.add_row("Log Level", args.log_level)
    config_table.add_row("Mode", "DEMO (Mock AI)" if os.getenv("MOCK_MODE") else "AI Powered")

    console.print(config_table)
    console.print()

    if os.getenv("MOCK_MODE"):
        console.print("[blue]🎭 Running in demo mode with realistic mock responses![/blue]")
        console.print("[blue]This demonstrates the full workflow without requiring API costs.[/blue]")
        console.print()

    try:
        # Initialize orchestrator and evaluator
        console.print("[dim]Initializing workflow orchestrator...[/dim]")
        orchestrator = CustomerIntelligenceOrchestrator()

        console.print("[dim]Initializing evaluation system...[/dim]")
        evaluator = WorkflowEvaluator()

        # Run the analysis
        console.print("\n[bold green]Starting customer intelligence analysis...[/bold green]")
        results = orchestrator.run(args.company, args.product, data_sources)

        # Evaluate the results
        console.print("\n[bold blue]🔍 Evaluating workflow performance...[/bold blue]")
        evaluation = evaluator.evaluate_workflow_run(results)

        # Display results
        display_results(console, results)
        display_evaluation(console, evaluation)

        # Save reports
        save_final_report(results)
        evaluator.save_evaluation_report(evaluation)

        console.print("\n[bold green]🎉 Analysis complete! Check data/output/ for the full report.[/bold green]")
        console.print(f"[dim]Overall Quality Score: {evaluation['overall_score']:.1%}[/dim]")

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Analysis interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[bold red]❌ Fatal error: {str(e)}[/bold red]")
        console.print("[dim]Check logs/app.log for detailed error information[/dim]")
        return 1


def display_results(console: Console, results: dict):
    """
    Display analysis results in a formatted way using rich components.

    Args:
        console: Rich console instance
        results: Workflow results dictionary
    """
    # Sentiment Analysis Panel
    if results.get("sentiment_results"):
        sentiment = results["sentiment_results"]
        sentiment_panel = Panel.fit(
            f"Overall: [bold]{sentiment.get('overall_sentiment', 'unknown').upper()}[/bold]\n"
            f"Score: {sentiment.get('sentiment_score', 0.0):.2f}\n"
            f"Confidence: {sentiment.get('confidence', 0.0):.1%}\n"
            f"Summary: {sentiment.get('analysis_summary', 'N/A')}",
            title="💭 Sentiment Analysis",
            border_style="blue"
        )
        console.print(sentiment_panel)

    # Top Patterns Table
    if results.get("patterns"):
        patterns_table = Table(title="🔎 Top Patterns Detected")
        patterns_table.add_column("Type", style="cyan", no_wrap=True)
        patterns_table.add_column("Description", style="white")
        patterns_table.add_column("Frequency", style="yellow", justify="right")
        patterns_table.add_column("Severity", style="red")

        for pattern in results["patterns"][:5]:  # Show top 5
            patterns_table.add_row(
                pattern.get("pattern_type", "unknown"),
                pattern.get("description", "")[:60] + "..." if len(pattern.get("description", "")) > 60 else pattern.get("description", ""),
                str(pattern.get("frequency", 0)),
                pattern.get("severity", "unknown")
            )

        console.print(patterns_table)

    # Top Opportunities Table
    if results.get("opportunities"):
        opportunities_table = Table(title="💡 Top Opportunities")
        opportunities_table.add_column("Title", style="cyan")
        opportunities_table.add_column("Priority", style="green", justify="center")
        opportunities_table.add_column("Impact", style="yellow", justify="right")
        opportunities_table.add_column("Effort", style="magenta", justify="center")

        for opp in results["opportunities"][:5]:  # Show top 5
            opportunities_table.add_row(
                opp.get("title", "Unknown")[:40] + "..." if len(opp.get("title", "")) > 40 else opp.get("title", ""),
                opp.get("priority", "unknown").title(),
                f"{opp.get('impact_score', 0)}/10",
                opp.get("effort_estimate", "unknown").title()
            )

        console.print(opportunities_table)

    # Strategy Recommendations
    if results.get("strategy_recommendations"):
        recommendations = results["strategy_recommendations"]
        console.print(f"\n📊 [bold]Strategy Recommendations:[/bold] {len(recommendations)} total")

        for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
            console.print(f"  {i}. [cyan]{rec.get('action', 'Unknown action')}[/cyan]")
            console.print(f"     Priority: {rec.get('priority', 'N/A')}/10 | Timeline: {rec.get('timeline', 'unknown')}")

    # Executive Summary Panel
    if results.get("executive_summary"):
        summary_panel = Panel.fit(
            results["executive_summary"],
            title="📋 Executive Summary",
            border_style="green",
            padding=(1, 2)
        )
        console.print("\n" + summary_panel)

    # Data Summary
    if results.get("data_summary"):
        data_summary = results["data_summary"]
        console.print("\n📈 [bold]Data Summary:[/bold]")
        console.print(f"  Total Records: [yellow]{data_summary.get('total_records', 0)}[/yellow]")
        console.print(f"  Sources Processed: [yellow]{data_summary.get('data_sources_processed', 0)}[/yellow]")

        if "average_rating" in data_summary:
            console.print(f"  Average Rating: [yellow]{data_summary['average_rating']:.1f}⭐[/yellow]")


def display_evaluation(console: Console, evaluation: Dict[str, Any]):
    """
    Display comprehensive evaluation metrics and insights.

    Args:
        console: Rich console instance
        evaluation: Complete evaluation results
    """
    # Overall Score
    score_color = "green" if evaluation["overall_score"] > 0.8 else "yellow" if evaluation["overall_score"] > 0.6 else "red"
    console.print(f"\n🏆 [bold]Overall Quality Score: [{score_color}]{evaluation['overall_score']:.1%}[/{score_color}][/bold]")

    # Performance Metrics
    perf = evaluation["performance_metrics"]
    perf_table = Table(title="⚡ Performance Metrics")
    perf_table.add_column("Metric", style="cyan")
    perf_table.add_column("Value", style="yellow", justify="right")

    if perf.get("total_runtime_seconds"):
        perf_table.add_row("Total Runtime", ".2f")
    perf_table.add_row("Agents Completed", str(perf.get("agents_completed", 0)))
    perf_table.add_row("Error Rate", ".1%")
    perf_table.add_row("Efficiency Score", ".1%")

    console.print(perf_table)

    # Hallucination Metrics
    hall = evaluation["hallucination_metrics"]
    hall_table = Table(title="🛡️ Hallucination Analysis")
    hall_table.add_column("Check", style="cyan")
    hall_table.add_column("Result", style="yellow")

    rate_color = "red" if hall["overall_hallucination_rate"] > 0.3 else "yellow" if hall["overall_hallucination_rate"] > 0.1 else "green"
    hall_table.add_row("Overall Hallucination Rate", f"[{rate_color}]{hall['overall_hallucination_rate']:.1%}[/{rate_color}]")
    hall_table.add_row("Confidence Score", ".1%")
    hall_table.add_row("Unsupported Claims", str(len(hall.get("unsupported_claims", []))))

    console.print(hall_table)

    # Coverage Metrics
    cov = evaluation["coverage_metrics"]
    cov_table = Table(title="📊 Coverage Analysis")
    cov_table.add_column("Metric", style="cyan")
    cov_table.add_column("Value", style="yellow", justify="right")

    cov_table.add_row("Overall Coverage", ".1%")
    if cov.get("pain_point_coverage") is not None:
        cov_table.add_row("Pain Points Covered", ".1%")
    if cov.get("theme_coverage") is not None:
        cov_table.add_row("Themes Covered", ".1%")

    console.print(cov_table)

    # Business Impact
    impact = evaluation["business_impact"]
    impact_table = Table(title="💰 Business Impact Estimate")
    impact_table.add_column("Metric", style="cyan")
    impact_table.add_column("Value", style="yellow")

    impact_table.add_row("Estimated Impact Score", ".1%")
    impact_table.add_row("Satisfaction Improvement", ".1%")
    impact_table.add_row("ROI Estimate", ".1%")

    console.print(impact_table)

    # Improvement Recommendations
    if evaluation.get("recommendations"):
        console.print("\n💡 [bold]Improvement Recommendations:[/bold]")
        for i, rec in enumerate(evaluation["recommendations"], 1):
            console.print(f"  {i}. {rec}")


def save_final_report(results: dict):
    """
    Save a comprehensive final report to disk.

    Args:
        results: Complete workflow results
    """
    try:
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / "final_report.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Customer Intelligence Analysis Report\n\n")

            # Company and Product info
            f.write("## Analysis Overview\n\n")
            f.write(f"- **Company:** {results.get('company_name', 'Unknown')}\n")
            f.write(f"- **Product:** {results.get('product_name', 'Unknown')}\n")
            f.write(f"- **Data Sources:** {', '.join(results.get('data_sources', []))}\n")
            f.write(f"- **Analysis Date:** {results.get('current_step', 'Unknown')}\n")
            f.write(f"- **Workflow ID:** {results.get('workflow_id', 'Unknown')}\n\n")

            # Performance Summary
            if results.get("performance_metrics"):
                perf = results["performance_metrics"]
                f.write("## Performance Summary\n\n")
                f.write(f"- **Total Runtime:** {perf.get('total_duration_seconds', 0):.2f} seconds\n")
                f.write(f"- **Agents Completed:** {perf.get('agents_completed', 0)}\n")
                f.write(f"- **Agents Failed:** {perf.get('agents_failed', 0)}\n")
                f.write(f"- **Errors:** {perf.get('error_count', 0)}\n\n")

            # Executive Summary
            if results.get("executive_summary"):
                f.write("## Executive Summary\n\n")
                f.write(f"{results['executive_summary']}\n\n")

            # Sentiment Analysis
            if results.get("sentiment_results"):
                sentiment = results["sentiment_results"]
                f.write("## Sentiment Analysis\n\n")
                f.write(f"- **Overall Sentiment:** {sentiment.get('overall_sentiment', 'unknown').title()}\n")
                f.write(f"- **Sentiment Score:** {sentiment.get('sentiment_score', 0.0):.2f}\n")
                f.write(f"- **Confidence:** {sentiment.get('confidence', 0.0):.1%}\n")
                f.write(f"- **Summary:** {sentiment.get('analysis_summary', 'N/A')}\n\n")

            # Key Patterns
            if results.get("patterns"):
                f.write("## Key Patterns Identified\n\n")
                for i, pattern in enumerate(results["patterns"][:10], 1):
                    f.write(f"### {i}. {pattern.get('pattern_type', 'Unknown').title()}\n")
                    f.write(f"- **Description:** {pattern.get('description', 'N/A')}\n")
                    f.write(f"- **Frequency:** {pattern.get('frequency', 0)}\n")
                    f.write(f"- **Severity:** {pattern.get('severity', 'unknown').title()}\n")
                    f.write(f"- **Business Impact:** {pattern.get('business_impact', 'N/A')}\n")
                    f.write(f"- **Impact Score:** {pattern.get('impact_score', 0):.1f}\n\n")

            # Top Opportunities
            if results.get("opportunities"):
                f.write("## Strategic Opportunities\n\n")
                for i, opp in enumerate(results["opportunities"][:10], 1):
                    f.write(f"### {i}. {opp.get('title', 'Unknown Opportunity')}\n")
                    f.write(f"- **Description:** {opp.get('description', 'N/A')}\n")
                    f.write(f"- **Priority:** {opp.get('priority', 'unknown').title()}\n")
                    f.write(f"- **Impact Score:** {opp.get('impact_score', 0)}/10\n")
                    f.write(f"- **Effort Required:** {opp.get('effort_estimate', 'unknown').title()}\n")
                    f.write(f"- **Timeline:** {opp.get('timeline', 'unknown').title()}\n")
                    f.write(f"- **Priority Score:** {opp.get('priority_score', 0):.2f}\n\n")

            # Strategy Recommendations
            if results.get("strategy_recommendations"):
                f.write("## Strategic Recommendations\n\n")
                for i, rec in enumerate(results["strategy_recommendations"], 1):
                    f.write(f"### {i}. {rec.get('action', 'Unknown Action')}\n")
                    f.write(f"- **Category:** {rec.get('category', 'General').title()}\n")
                    f.write(f"- **Priority:** {rec.get('priority', 'N/A')}/10\n")
                    f.write(f"- **Timeline:** {rec.get('timeline', 'unknown').title()}\n")
                    f.write(f"- **Effort Level:** {rec.get('effort_level', 'unknown').title()}\n")
                    f.write(f"- **Expected Impact:** {rec.get('expected_impact', 'N/A')}\n")
                    f.write(f"- **Rationale:** {rec.get('rationale', 'N/A')}\n")
                    if rec.get("success_metrics"):
                        f.write(f"- **Success Metrics:** {', '.join(rec['success_metrics'])}\n")
                    if rec.get("owner"):
                        f.write(f"- **Owner:** {rec['owner']}\n")
                    f.write("\n")

            # Data Summary
            if results.get("data_summary"):
                data_summary = results["data_summary"]
                f.write("## Data Summary\n\n")
                f.write(f"- **Total Records Analyzed:** {data_summary.get('total_records', 0)}\n")
                f.write(f"- **Data Sources:** {data_summary.get('data_sources_processed', 0)}\n")

                if "average_rating" in data_summary:
                    f.write(f"- **Average Rating:** {data_summary['average_rating']:.1f}/5.0\n")

                if data_summary.get("records_by_source"):
                    f.write("- **Records by Source:**\n")
                    for source, count in data_summary["records_by_source"].items():
                        f.write(f"  - {source.title()}: {count}\n")

                if data_summary.get("date_range"):
                    date_range = data_summary["date_range"]
                    f.write(f"- **Date Range:** {date_range.get('earliest', 'N/A')} to {date_range.get('latest', 'N/A')}\n")
                    f.write(f"- **Date Span:** {date_range.get('date_span_days', 0)} days\n")

                f.write("\n")

            # Errors (if any)
            if results.get("errors"):
                f.write("## Errors Encountered\n\n")
                for error in results["errors"]:
                    f.write(f"- {error}\n")
                f.write("\n")

            # Validation Report
            if results.get("validation_report"):
                validation = results["validation_report"]
                f.write("## Validation Report\n\n")
                if validation.get("overall_score"):
                    f.write(f"- **Overall Validation Score:** {validation['overall_score']:.1%}\n")

                hallucinations = validation.get("hallucination_checks", [])
                if hallucinations:
                    f.write("- **Hallucination Analysis:**\n")
                    for check in hallucinations:
                        if "rate" in check:
                            f.write(f"  - {check['check']}: {check['rate']:.1%}\n")

                f.write("\n")

            f.write("---\n*Report generated by Customer Intelligence Platform*")

        console = Console()
        console.print(f"📄 [green]Final report saved to: {report_path}[/green]")

    except Exception as e:
        console = Console()
        console.print(f"[red]Failed to save final report: {str(e)}[/red]")


if __name__ == "__main__":
    exit(main())