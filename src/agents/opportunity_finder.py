"""
Opportunity Finder Agent.

This agent identifies product and business opportunities based on customer feedback
patterns, transforming insights into actionable recommendations.
"""

import json
from typing import Any, Dict, List

from rich.console import Console

from .base_agent import BaseAgent


class OpportunityFinderAgent(BaseAgent):
    """
    Opportunity Finding Specialist agent that transforms patterns into opportunities.

    Analyzes patterns and customer feedback to identify:
    - Product improvement opportunities
    - Feature development ideas
    - Service enhancement suggestions
    - Market positioning opportunities
    """

    def __init__(self):
        """Initialize the Opportunity Finder Agent with specialized system prompt."""
        system_prompt = """
        You are an Opportunity Finding Specialist. Transform customer feedback patterns into actionable business opportunities.

        Your role is to:
        1. Analyze pain points and convert them into product improvement opportunities
        2. Identify feature requests and assess their business value
        3. Find market gaps and competitive advantages
        4. Prioritize opportunities by impact and feasibility
        5. Consider implementation effort and timeline
        6. Estimate potential business outcomes

        For each opportunity, evaluate:
        - Business impact (high/medium/low)
        - Implementation effort (small/medium/large)
        - Timeline for delivery
        - Supporting evidence from customer feedback
        - Expected outcomes and success metrics

        Output your analysis as valid JSON with this exact structure:
        {
          "opportunities": [
            {
              "title": "Clear, actionable opportunity name",
              "description": "Detailed description of the opportunity",
              "category": "product|feature|service|support|pricing|marketing",
              "priority": "high|medium|low",
              "impact_score": 1-10,
              "effort_estimate": "small|medium|large",
              "timeline": "immediate|short-term|long-term",
              "supporting_data": ["evidence1", "evidence2", "evidence3"],
              "expected_outcome": "Expected business impact and benefits",
              "success_metrics": ["metric1", "metric2"],
              "risks": ["risk1", "risk2"]
            }
          ],
          "opportunity_summary": {
            "total_opportunities": 5,
            "high_impact_count": 2,
            "quick_wins": 1,
            "strategic_initiatives": 2,
            "categories_covered": ["product", "feature", "support"]
          },
          "implementation_roadmap": {
            "immediate_actions": ["action1", "action2"],
            "short_term_goals": ["goal1", "goal2"],
            "long_term_vision": "Overall strategic direction"
          }
        }

        Focus on opportunities that drive customer satisfaction and business growth.
        """

        super().__init__(
            name="opportunity_finder",
            role="Opportunity Finding Specialist",
            system_prompt=system_prompt,
            temperature=0.6  # Creative opportunity identification
        )

        self.console = Console()

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the workflow state to identify business opportunities.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with opportunity findings
        """
        try:
            self.console.print("\n[bold blue]💡 Opportunity Finder Agent Starting...[/bold blue]")

            patterns = state.get("patterns", [])
            sentiment_results = state.get("sentiment_results", {})
            trends = state.get("trends", {})

            if not patterns:
                self.console.print("[red]❌ No patterns found for opportunity identification[/red]")
                state["errors"].append("No patterns available for opportunity finding")
                return state

            self.console.print(f"Analyzing [green]{len(patterns)}[/green] patterns for opportunities...")

            # Find opportunities using Claude
            opportunity_analysis = self._find_opportunities(patterns, sentiment_results, trends, state)

            # Structure and rank opportunities
            opportunities = self._structure_opportunities(opportunity_analysis)
            ranked_opportunities = self._rank_opportunities(opportunities)

            # Update state
            state["opportunities"] = ranked_opportunities
            state["current_step"] = "opportunity_finding_completed"
            state["iteration_count"] += 1

            self.console.print("[bold green]✅ Opportunity Finding Complete![/bold green]")
            self._display_opportunity_summary(ranked_opportunities)

            return state

        except Exception as e:
            error_msg = f"Opportunity finding failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            self.console.print(f"[bold red]❌ Error: {error_msg}[/bold red]")
            return state

    def _find_opportunities(self, patterns: List[Dict[str, Any]],
                          sentiment_context: Dict[str, Any],
                          trends: Dict[str, Any],
                          state: Dict[str, Any]) -> str:
        """
        Send pattern data to Claude for opportunity identification and analysis.

        Args:
            patterns: Detected patterns from customer feedback
            sentiment_context: Overall sentiment analysis results
            trends: Trend analysis data

        Returns:
            Claude's JSON response as string
        """
        # Prepare patterns summary for Claude
        patterns_summary = []
        for pattern in patterns[:15]:  # Limit for token efficiency
            summary = f"• {pattern['pattern_type']}: {pattern['description']} (freq: {pattern['frequency']}, severity: {pattern['severity']})"
            patterns_summary.append(summary)

        context = f"""
        Analyzing {len(patterns)} customer feedback patterns for business opportunities.

        Sentiment Overview:
        - Overall Sentiment: {sentiment_context.get('overall_sentiment', 'unknown')}
        - Sentiment Score: {sentiment_context.get('sentiment_score', 0.0)}
        - Key Topics: {sentiment_context.get('key_topics', [])}

        Trend Summary:
        - Total Patterns: {trends.get('total_patterns', 0)}
        - High Impact Patterns: {trends.get('high_impact_patterns', 0)}
        - Critical Issues: {trends.get('critical_patterns', 0)}

        Key Patterns:
        {chr(10).join(patterns_summary)}
        """

        task = f"""
        Transform these customer feedback patterns into actionable business opportunities. Consider:

        1. Pain points → Product improvements or service enhancements
        2. Feature requests → New product capabilities
        3. Positive patterns → Areas to double down on
        4. Technical issues → Quality improvements
        5. Market gaps → Competitive advantages

        For each opportunity, assess:
        - Business impact and priority
        - Implementation effort and feasibility
        - Timeline and resource requirements
        - Supporting evidence and expected outcomes
        - Potential risks and success metrics

        Focus on opportunities that will drive customer satisfaction and business growth.
        Provide comprehensive opportunity analysis in the specified JSON format.
        """

        # Include company and product info for mock response generation
        full_context = {
            "opportunity_context": context,
            "company_name": state.get("company_name", "Unknown Company"),
            "product_name": state.get("product_name", "Unknown Product")
        }
        return self.execute(task, full_context)

    def _structure_opportunities(self, analysis_response: str) -> List[Dict[str, Any]]:
        """
        Parse Claude's JSON response and structure the opportunities.

        Args:
            analysis_response: Raw JSON string from Claude

        Returns:
            List of structured opportunity dictionaries
        """
        try:
            # Extract JSON from response
            json_start = analysis_response.find('{')
            json_end = analysis_response.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_str = analysis_response[json_start:json_end]
            analysis_data = json.loads(json_str)

            opportunities = analysis_data.get("opportunities", [])

            # Validate and enhance opportunities
            validated_opportunities = []
            for opp in opportunities:
                if self._validate_opportunity(opp):
                    enhanced_opp = self._enhance_opportunity(opp)
                    validated_opportunities.append(enhanced_opp)

            return validated_opportunities

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.warning(f"Failed to parse opportunity analysis JSON: {e}")
            self.logger.info(f"Raw response: {analysis_response[:500]}...")

            # Return fallback opportunities
            return self._generate_fallback_opportunities()

    def _validate_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """
        Validate that an opportunity has all required fields.

        Args:
            opportunity: Opportunity dictionary to validate

        Returns:
            True if opportunity is valid
        """
        required_fields = ["title", "description", "category", "priority", "impact_score"]
        return all(field in opportunity and opportunity[field] for field in required_fields)

    def _enhance_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance opportunity with additional calculated fields.

        Args:
            opportunity: Opportunity dictionary to enhance

        Returns:
            Enhanced opportunity dictionary
        """
        # Ensure impact_score is numeric
        if isinstance(opportunity.get("impact_score"), str):
            # Convert string scores to numbers
            score_map = {"high": 8, "medium": 5, "low": 3}
            opportunity["impact_score"] = score_map.get(opportunity["impact_score"].lower(), 5)

        # Add effort score for prioritization
        effort_map = {"small": 1, "medium": 2, "large": 3}
        effort_score = effort_map.get(opportunity.get("effort_estimate", "medium").lower(), 2)
        opportunity["effort_score"] = effort_score

        # Calculate priority score (impact / effort)
        priority_score = opportunity["impact_score"] / effort_score
        opportunity["priority_score"] = round(priority_score, 2)

        # Add timeline score for sorting
        timeline_map = {"immediate": 3, "short-term": 2, "long-term": 1}
        timeline_score = timeline_map.get(opportunity.get("timeline", "short-term").lower(), 2)
        opportunity["timeline_score"] = timeline_score

        return opportunity

    def _rank_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank opportunities by priority score and other factors.

        Args:
            opportunities: List of opportunity dictionaries

        Returns:
            Ranked list of opportunities
        """
        # Sort by priority score (impact/effort), then by impact score, then by timeline
        ranked = sorted(opportunities,
                       key=lambda x: (x.get("priority_score", 0),
                                    x.get("impact_score", 0),
                                    x.get("timeline_score", 0)),
                       reverse=True)

        # Add ranking position
        for i, opp in enumerate(ranked, 1):
            opp["rank"] = i

        return ranked

    def _generate_fallback_opportunities(self) -> List[Dict[str, Any]]:
        """
        Generate basic fallback opportunities when analysis fails.

        Returns:
            List of basic opportunity dictionaries
        """
        return [
            {
                "title": "Customer Feedback Analysis",
                "description": "Implement systematic customer feedback analysis to identify improvement areas",
                "category": "product",
                "priority": "high",
                "impact_score": 7,
                "effort_estimate": "medium",
                "timeline": "short-term",
                "supporting_data": ["General customer feedback patterns"],
                "expected_outcome": "Better understanding of customer needs and preferences",
                "success_metrics": ["Customer satisfaction improvement"],
                "risks": ["Resource allocation for analysis"],
                "effort_score": 2,
                "priority_score": 3.5,
                "timeline_score": 2,
                "rank": 1
            }
        ]

    def _display_opportunity_summary(self, opportunities: List[Dict[str, Any]]):
        """Display a formatted opportunity finding summary."""
        if not opportunities:
            self.console.print("  No opportunities identified")
            return

        self.console.print(f"  Opportunities Found: [bold cyan]{len(opportunities)}[/bold cyan]")

        # Show top 3 opportunities
        for i, opp in enumerate(opportunities[:3], 1):
            title = opp.get("title", "Unknown")
            priority = opp.get("priority", "unknown")
            impact = opp.get("impact_score", 0)
            category = opp.get("category", "general")

            # Color based on priority
            if priority == "high":
                color = "green"
            elif priority == "medium":
                color = "yellow"
            else:
                color = "red"

            self.console.print(f"    {i}. [{color}]{title}[/{color}] ({category}) - Impact: {impact}/10")