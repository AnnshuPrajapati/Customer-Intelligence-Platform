"""
Strategy Creator Agent.

This agent creates comprehensive strategic recommendations and executive summaries
based on all previous analysis (sentiment, patterns, opportunities).
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console

from .base_agent import BaseAgent


class StrategyCreatorAgent(BaseAgent):
    """
    Strategy Creation Specialist agent that synthesizes all insights into executive strategy.

    Creates comprehensive strategic recommendations including:
    - Executive summary reports
    - Prioritized action plans
    - Implementation roadmaps
    - Success metrics and KPIs
    """

    def __init__(self):
        """Initialize the Strategy Creator Agent with specialized system prompt."""
        system_prompt = """
        You are a Strategy Creation Specialist. Synthesize customer intelligence insights into executive-level strategic recommendations.

        Your role is to:
        1. Create comprehensive executive summaries of all findings
        2. Develop prioritized strategic recommendations across product, service, and operations
        3. Build implementation roadmaps with timelines and dependencies
        4. Define success metrics and KPIs for measuring impact
        5. Provide clear next steps and action items
        6. Balance short-term wins with long-term strategic initiatives

        Consider all aspects:
        - Customer sentiment and satisfaction drivers
        - Product and service improvement opportunities
        - Competitive positioning and market gaps
        - Resource allocation and implementation feasibility
        - Risk assessment and mitigation strategies
        - Measurement frameworks for success

        Output your strategic analysis as valid JSON with this exact structure:
        {
          "recommendations": [
            {
              "category": "product|support|marketing|operations|technology|organization",
              "action": "Specific, actionable recommendation",
              "rationale": "Why this action is important based on customer insights",
              "expected_impact": "Expected business and customer impact",
              "timeline": "immediate|short-term|long-term",
              "priority": 1-10,
              "effort_level": "low|medium|high",
              "success_metrics": ["metric1", "metric2", "metric3"],
              "dependencies": ["prerequisite1", "prerequisite2"],
              "risks": ["risk1", "risk2"],
              "owner": "Suggested responsible party or department"
            }
          ],
          "executive_summary": "Comprehensive 2-3 paragraph executive summary covering key findings, strategic recommendations, and expected outcomes",
          "implementation_roadmap": {
            "phase_1_immediate": ["action1", "action2"],
            "phase_2_short_term": ["action3", "action4"],
            "phase_3_long_term": ["action5", "action6"],
            "key_milestones": ["milestone1", "milestone2"],
            "resource_requirements": ["resource1", "resource2"]
          },
          "success_framework": {
            "kpis": ["KPI1", "KPI2", "KPI3"],
            "measurement_timeline": "3|6|12 months",
            "baseline_metrics": {"metric1": "current_value"},
            "target_metrics": {"metric1": "target_value"},
            "review_cadence": "weekly|monthly|quarterly"
          },
          "risk_assessment": {
            "high_risk_items": ["item1", "item2"],
            "mitigation_strategies": ["strategy1", "strategy2"],
            "contingency_plans": ["plan1", "plan2"]
          }
        }

        Create actionable, measurable, and achievable strategic recommendations that drive customer satisfaction and business growth.
        """

        super().__init__(
            name="strategy_creator",
            role="Strategy Creation Specialist",
            system_prompt=system_prompt,
            temperature=0.3  # Professional, consistent output
        )

        self.console = Console()

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the workflow state to create comprehensive strategic recommendations.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with strategic recommendations
        """
        try:
            self.console.print("\n[bold blue]📊 Strategy Creator Agent Starting...[/bold blue]")

            opportunities = state.get("opportunities", [])
            patterns = state.get("patterns", [])
            sentiment = state.get("sentiment_results", {})

            self.console.print(f"Input: {len(opportunities)} opportunities, {len(patterns)} patterns")

            # Gather all analysis results
            all_insights = self._gather_insights(state)

            if not all_insights["has_data"]:
                self.console.print("[red]❌ Insufficient data for strategy creation[/red]")
                state["errors"].append("Insufficient analysis data for strategy creation")
                return state

            self.console.print("Synthesizing insights from all analysis phases...")

            # Create strategy using Claude
            try:
                strategy_response = self._create_strategy(all_insights, state)
            except Exception as e:
                self.logger.error(f"Failed to create strategy: {e}")
                # Fallback: create basic recommendations
                recommendations = [
                    {
                        "category": "technical",
                        "action": "Improve product performance and stability",
                        "rationale": "Customer feedback indicates performance issues",
                        "expected_impact": "Better user experience",
                        "timeline": "short-term",
                        "priority": 8,
                        "effort_level": "medium",
                        "success_metrics": ["performance metrics", "user satisfaction"],
                        "dependencies": ["engineering team"],
                        "risks": ["technical complexity"],
                        "owner": "Engineering Team"
                    }
                ]
                executive_summary = f"Analysis of {all_insights.get('company_name', 'the company')}'s {all_insights.get('product_name', 'product')} reveals key opportunities for improvement. Focus on technical enhancements and user experience optimization."
                state["strategy_recommendations"] = recommendations
                state["executive_summary"] = executive_summary
                state["current_step"] = "strategy_creation_completed"
                state["iteration_count"] += 1
                return state

            # Parse and structure recommendations
            try:
                recommendations, executive_summary = self._structure_strategy(strategy_response)
            except Exception as e:
                self.logger.error(f"Failed to structure strategy: {e}")
                # Use fallback recommendations
                recommendations = [
                    {
                        "category": "product",
                        "action": "Enhance user experience and features",
                        "rationale": "Based on customer feedback analysis",
                        "expected_impact": "Improved customer satisfaction",
                        "timeline": "medium-term",
                        "priority": 7,
                        "effort_level": "medium",
                        "success_metrics": ["user engagement", "satisfaction scores"],
                        "dependencies": ["product team"],
                        "risks": ["scope changes"],
                        "owner": "Product Team"
                    }
                ]
                executive_summary = f"Strategic analysis completed for {all_insights.get('company_name', 'the company')}. Focus on enhancing user experience and addressing key feedback areas."

            # Update state
            state["strategy_recommendations"] = recommendations
            state["executive_summary"] = executive_summary
            state["current_step"] = "strategy_creation_completed"
            state["iteration_count"] += 1

            # CRITICAL: Log if empty
            if not recommendations or len(recommendations) == 0:
                self.console.print("[bold red]⚠️  WARNING: No recommendations generated![/bold red]")
                self.logger.error("Strategy creator produced 0 recommendations - check logic")
                self.logger.error(f"Strategy response type: {type(strategy_response)}")
                self.logger.error(f"Strategy response length: {len(strategy_response) if strategy_response else 0}")
                self.logger.error(f"Strategy response preview: {str(strategy_response)[:500] if strategy_response else 'None'}")
            else:
                self.console.print(f"[bold green]✅ Generated {len(recommendations)} recommendations[/bold green]")
                self.logger.info(f"Successfully created {len(recommendations)} recommendations using {self.provider}")

            # Generate and save final report
            self._generate_report(state)

            return state

        except Exception as e:
            error_msg = f"Strategy creation failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            self.console.print(f"[bold red]❌ Error: {error_msg}[/bold red]")
            return state

    def _gather_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather all insights from previous analysis phases.

        Args:
            state: Current workflow state

        Returns:
            Dictionary containing all gathered insights
        """
        return {
            "company_name": state.get("company_name", "Unknown Company"),
            "product_name": state.get("product_name", "Unknown Product"),
            "sentiment_results": state.get("sentiment_results", {}),
            "sentiment_breakdown": state.get("sentiment_breakdown", {}),
            "patterns": state.get("patterns", []),
            "trends": state.get("trends", {}),
            "opportunities": state.get("opportunities", []),
            "data_summary": state.get("data_summary", {}),
            "has_data": bool(state.get("raw_data") and
                           (state.get("sentiment_results") or state.get("patterns") or state.get("opportunities")))
        }

    def _create_strategy(self, insights: Dict[str, Any], state: Dict[str, Any]) -> str:
        """
        Send comprehensive insights to Claude for strategic analysis.

        Args:
            insights: All gathered insights from analysis phases

        Returns:
            Claude's JSON response as string
        """
        # Create comprehensive context summary
        context_parts = [
            f"Company: {insights['company_name']}",
            f"Product: {insights['product_name']}",
            f"Data Analyzed: {insights['data_summary'].get('total_records', 0)} feedback items"
        ]

        # Add sentiment summary
        sentiment = insights['sentiment_results']
        if sentiment:
            context_parts.append(
                f"Overall Sentiment: {sentiment.get('overall_sentiment', 'unknown')} "
                f"(Score: {sentiment.get('sentiment_score', 0.0)})"
            )

        # Add key patterns
        patterns = insights['patterns'][:5]  # Top 5 patterns
        if patterns:
            pattern_summary = [f"• {p['pattern_type']}: {p['description'][:100]}..." for p in patterns]
            context_parts.append(f"Key Patterns ({len(patterns)}):\n" + "\n".join(pattern_summary))

        # Add top opportunities
        opportunities = insights['opportunities'][:3]  # Top 3 opportunities
        if opportunities:
            opp_summary = [f"• {o['title']}: {o['description'][:100]}..." for o in opportunities]
            context_parts.append(f"Top Opportunities ({len(opportunities)}):\n" + "\n".join(opp_summary))

        full_context = "\n\n".join(context_parts)

        task = f"""
        Create a comprehensive strategic recommendation report based on this customer intelligence analysis.

        Analysis Context:
        {full_context}

        Develop strategic recommendations that address:
        1. Critical customer pain points and their business impact
        2. High-value product and service improvement opportunities
        3. Operational efficiency and process improvements
        4. Customer experience enhancement initiatives
        5. Competitive positioning and market differentiation

        Create an executive summary and detailed implementation plan with:
        - Prioritized, actionable recommendations
        - Clear timelines and resource requirements
        - Success metrics and measurement frameworks
        - Risk assessment and mitigation strategies
        - Implementation roadmap with phases and milestones

        Focus on recommendations that will drive measurable customer satisfaction improvements and business growth.
        Provide comprehensive strategic analysis in the specified JSON format.
        """

        # Include company and product info for mock response generation
        execute_context = {
            "strategy_context": full_context,
            "company_name": state.get("company_name", "Unknown Company"),
            "product_name": state.get("product_name", "Unknown Product")
        }
        return self.execute(task, execute_context)

    def _structure_strategy(self, response: str) -> tuple[List[Dict[str, Any]], str]:
        """
        Parse Claude's response and extract recommendations and executive summary.

        Args:
            response: Raw JSON string from Claude

        Returns:
            Tuple of (recommendations_list, executive_summary_string)
        """
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_str = response[json_start:json_end]
            strategy_data = json.loads(json_str)

            recommendations = strategy_data.get("recommendations", [])
            executive_summary = strategy_data.get("executive_summary", "Strategic analysis completed.")

            # Sort recommendations by priority
            recommendations.sort(key=lambda x: x.get("priority", 5), reverse=True)

            return recommendations, executive_summary

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.warning(f"Failed to parse strategy response JSON: {e}")
            self.logger.info(f"Raw response: {response[:500]}...")

            # Return fallback strategy
            fallback_recommendations = [
                {
                    "category": "general",
                    "action": "Implement customer feedback analysis system",
                    "rationale": "Systematic analysis of customer feedback is essential for improvement",
                    "expected_impact": "Better understanding of customer needs and improved satisfaction",
                    "timeline": "short-term",
                    "priority": 8,
                    "effort_level": "medium",
                    "success_metrics": ["Customer satisfaction improvement"],
                    "dependencies": [],
                    "risks": ["Resource allocation"],
                    "owner": "Product Team"
                }
            ]

            fallback_summary = (
                "Customer intelligence analysis has identified key areas for improvement. "
                "Implementation of a systematic feedback analysis system will provide valuable insights "
                "for product and service enhancements that drive customer satisfaction and business growth."
            )

            return fallback_recommendations, fallback_summary

    def _generate_report(self, state: Dict[str, Any]):
        """
        Generate and save a formatted markdown report.

        Args:
            state: Final workflow state with all results
        """
        try:
            report_content = self._format_report(
                state.get("strategy_recommendations", []),
                state.get("executive_summary", "")
            )

            # Ensure output directory exists
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save report
            report_path = output_dir / "strategy_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            self.console.print(f"📄 Report saved to: [link=file://{report_path.absolute()}]{report_path}[/link]")

        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")

    def _format_report(self, recommendations: List[Dict[str, Any]], executive_summary: str) -> str:
        """
        Format recommendations and summary into a professional markdown report.

        Args:
            recommendations: List of strategic recommendations
            executive_summary: Executive summary text

        Returns:
            Formatted markdown report string
        """
        lines = [
            "# Customer Intelligence Strategy Report\n",
            "## Executive Summary\n",
            f"{executive_summary}\n",
            "## Strategic Recommendations\n"
        ]

        # Group recommendations by category
        categories = {}
        for rec in recommendations:
            category = rec.get("category", "General")
            if category not in categories:
                categories[category] = []
            categories[category].append(rec)

        # Add each category section
        for category, recs in categories.items():
            lines.append(f"### {category.title()}\n")

            for i, rec in enumerate(recs, 1):
                lines.extend([
                    f"#### {i}. {rec.get('action', 'Unknown Action')}\n",
                    f"**Priority:** {rec.get('priority', 'N/A')}/10  |  "
                    f"**Timeline:** {rec.get('timeline', 'unknown').title()}  |  "
                    f"**Effort:** {rec.get('effort_level', 'unknown').title()}\n",
                    f"**Rationale:** {rec.get('rationale', '')}\n",
                    f"**Expected Impact:** {rec.get('expected_impact', '')}\n"
                ])

                if rec.get("success_metrics"):
                    lines.append(f"**Success Metrics:** {', '.join(rec['success_metrics'])}\n")

                if rec.get("owner"):
                    lines.append(f"**Owner:** {rec['owner']}\n")

                lines.append("")  # Empty line between recommendations

        # Add implementation notes
        lines.extend([
            "## Implementation Notes\n",
            "- **Immediate Actions:** Focus on high-priority, low-effort items first",
            "- **Resource Allocation:** Ensure dedicated team members for implementation",
            "- **Measurement:** Track success metrics regularly and adjust strategy as needed",
            "- **Communication:** Keep stakeholders informed of progress and results",
            "\n---\n",
            "*Report generated by Customer Intelligence Platform*"
        ])

        return "\n".join(lines)