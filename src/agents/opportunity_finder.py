"""
Opportunity Finder Agent.

This agent identifies product and business opportunities based on customer feedback
patterns, transforming insights into actionable recommendations.
"""

import json
import re
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
        You are an Opportunity Finding Specialist. Transform customer feedback patterns into actionable business opportunities. Respond with ONLY valid JSON.

        CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no preamble. Start with { and end with }.

        Generate 5-8 specific, unique opportunities based on the actual patterns provided. Each opportunity must be different and address specific customer needs. NO generic opportunities like 'Improve customer satisfaction'.

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
            temperature=0.7  # Increased for more varied, creative opportunities
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
        # Prepare detailed patterns summary for Claude (increased to 20 patterns)
        patterns_summary = []
        pattern_stats = {
            "pain_points": 0,
            "feature_requests": 0,
            "bug_reports": 0,
            "usability_issues": 0,
            "critical_patterns": 0,
            "high_impact": 0
        }

        for pattern in patterns[:20]:  # Increased limit for better context
            pattern_type = pattern.get('pattern_type', 'unknown')
            severity = pattern.get('severity', 'medium')
            impact_score = pattern.get('impact_score', 0)

            # Count pattern types and severity
            if pattern_type == 'pain_point':
                pattern_stats['pain_points'] += 1
            elif pattern_type == 'feature_request':
                pattern_stats['feature_requests'] += 1
            elif pattern_type == 'bug_report':
                pattern_stats['bug_reports'] += 1
            elif pattern_type == 'usability_issue':
                pattern_stats['usability_issues'] += 1

            if severity == 'critical':
                pattern_stats['critical_patterns'] += 1
            if impact_score >= 7:
                pattern_stats['high_impact'] += 1

            # Include examples if available
            examples = pattern.get('examples', [])
            examples_str = f" Examples: {examples[:2]}" if examples else ""

            summary = f"• {pattern_type}: {pattern['description']} (freq: {pattern['frequency']}, severity: {severity}, impact: {impact_score}){examples_str}"
            patterns_summary.append(summary)

        context = f"""
        Analyzing {len(patterns)} customer feedback patterns for {state.get('company_name', 'Unknown Company')}'s {state.get('product_name', 'Unknown Product')} to identify business opportunities.

        Sentiment Overview:
        - Overall Sentiment: {sentiment_context.get('overall_sentiment', 'unknown')}
        - Sentiment Score: {sentiment_context.get('sentiment_score', 0.0)}
        - Key Topics: {sentiment_context.get('key_topics', [])}

        Pattern Statistics:
        - Total Patterns: {len(patterns)}
        - Pain Points: {pattern_stats['pain_points']}
        - Feature Requests: {pattern_stats['feature_requests']}
        - Bug Reports: {pattern_stats['bug_reports']}
        - Usability Issues: {pattern_stats['usability_issues']}
        - Critical Severity: {pattern_stats['critical_patterns']}
        - High Impact (7+): {pattern_stats['high_impact']}

        Key Patterns (Top 20):
        {chr(10).join(patterns_summary)}
        """

        task = f"""
        Transform these specific customer feedback patterns into 5-8 actionable business opportunities for {state.get('company_name', 'the company')}'s {state.get('product_name', 'product')}.

        CRITICAL REQUIREMENTS:
        - Generate EXACTLY 5-8 unique, specific opportunities
        - Each opportunity must address a SPECIFIC pattern from the list above
        - NO generic opportunities like "Improve customer satisfaction"
        - Each opportunity must have a clear, actionable title and detailed description
        - Base opportunities directly on the pain points, feature requests, and issues identified

        For each opportunity, assess:
        - Business impact and priority (high/medium/low)
        - Implementation effort (small/medium/large)
        - Timeline (immediate/short-term/long-term)
        - Supporting evidence from the specific patterns above
        - Expected outcomes and success metrics
        - Potential risks

        Focus on opportunities that will drive customer satisfaction and business growth. Be specific and actionable.
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
            # 3-tier JSON extraction for robustness
            analysis_data = None

            # Method 1: Direct JSON parse
            try:
                analysis_data = json.loads(analysis_response.strip())
                self.logger.debug("Opportunity JSON parsed directly")
            except json.JSONDecodeError:
                pass

            # Method 2: Extract from markdown code blocks
            if analysis_data is None:
                json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', analysis_response, re.DOTALL)
                if json_match:
                    try:
                        analysis_data = json.loads(json_match.group(1).strip())
                        self.logger.debug("Opportunity JSON extracted from markdown block")
                    except json.JSONDecodeError:
                        pass

            # Method 3: Brace-matching algorithm
            if analysis_data is None:
                json_start = analysis_response.find('{')
                if json_start != -1:
                    brace_count = 0
                    json_end = json_start

                    for i, char in enumerate(analysis_response[json_start:], json_start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break

                    if json_end > json_start:
                        json_str = analysis_response[json_start:json_end]
                        try:
                            analysis_data = json.loads(json_str)
                            self.logger.debug("Opportunity JSON extracted using brace matching")
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Opportunity brace matching failed: {e}")
                            raise ValueError(f"No valid JSON found in opportunity response after trying 3 methods")

            if analysis_data is None:
                raise ValueError("No JSON found in opportunity response after trying 3 parsing methods")

            opportunities = analysis_data.get("opportunities", [])

            # Validate and enhance opportunities
            validated_opportunities = []
            for i, opp in enumerate(opportunities):
                if self._validate_opportunity(opp):
                    enhanced_opp = self._enhance_opportunity(opp)
                    validated_opportunities.append(enhanced_opp)
                    self.logger.debug(f"Validated opportunity {i+1}: {opp.get('title', 'Unknown')}")
                else:
                    self.logger.warning(f"Invalid opportunity {i+1}: {opp.get('title', 'Unknown')} - missing required fields")

            return validated_opportunities

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.warning(f"Failed to parse opportunity analysis JSON: {e}")
            self.logger.info(f"Raw response: {analysis_response[:500]}...")

            # Generate pattern-based fallback opportunities
            self.logger.warning("Using pattern-based fallback opportunities")
            return self._generate_pattern_based_opportunities(state)

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

    def _generate_pattern_based_opportunities(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate pattern-based fallback opportunities when analysis fails.

        Args:
            state: Workflow state containing patterns and context

        Returns:
            List of pattern-based opportunity dictionaries
        """
        patterns = state.get("patterns", [])
        company_name = state.get("company_name", "Unknown Company")
        product_name = state.get("product_name", "Unknown Product")

        opportunities = []

        # Generate opportunities based on available patterns
        for i, pattern in enumerate(patterns[:5]):  # Use up to 5 patterns
            pattern_type = pattern.get('pattern_type', 'pain_point')
            description = pattern.get('description', 'General improvement area')

            if pattern_type == 'pain_point':
                title = f"Address {description.lower()}"
                category = "product"
                priority = "high"
                impact_score = 8
            elif pattern_type == 'feature_request':
                title = f"Implement {description.lower()}"
                category = "feature"
                priority = "medium"
                impact_score = 7
            elif pattern_type == 'bug_report':
                title = f"Fix {description.lower()}"
                category = "technical"
                priority = "high"
                impact_score = 8
            else:
                title = f"Improve {description.lower()}"
                category = "product"
                priority = "medium"
                impact_score = 6

            opportunity = {
                "title": title,
                "description": f"Address the customer need: {description}",
                "category": category,
                "priority": priority,
                "impact_score": impact_score,
                "effort_estimate": "medium",
                "timeline": "short-term",
                "supporting_data": [f"Pattern: {description}"],
                "expected_outcome": f"Improved customer experience for {company_name}'s {product_name}",
                "success_metrics": ["Customer satisfaction", "Usage metrics"],
                "risks": ["Implementation complexity", "Resource requirements"],
                "effort_score": 2,
                "priority_score": impact_score / 2,
                "timeline_score": 2,
                "rank": i + 1
            }
            opportunities.append(opportunity)

        # If no patterns available, fall back to generic opportunities
        if not opportunities:
            self.logger.warning("No patterns available, using generic fallback opportunities")
            opportunities = self._generate_fallback_opportunities()

        return opportunities

    def _generate_fallback_opportunities(self) -> List[Dict[str, Any]]:
        """
        Generate basic fallback opportunities when no patterns are available.

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