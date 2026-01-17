"""
Pattern Detector Agent.

This agent identifies patterns, trends, and recurring themes in customer feedback
using Claude LLM to find pain points, feature requests, and behavioral patterns.
"""

import json
from typing import Any, Dict, List
from collections import Counter

from rich.console import Console

from .base_agent import BaseAgent


class PatternDetectorAgent(BaseAgent):
    """
    Pattern Detection Specialist agent that finds recurring themes and trends.

    Analyzes customer feedback to identify:
    - Pain points and frustrations
    - Feature requests and suggestions
    - Positive patterns and praises
    - Bugs and technical issues
    - Trends over time
    """

    def __init__(self):
        """Initialize the Pattern Detector Agent with specialized system prompt."""
        system_prompt = """
        You are a Pattern Detection Specialist. Analyze customer feedback to identify:

        1. Recurring themes and patterns across multiple feedback items
        2. Pain points (what frustrates or disappoints customers)
        3. Feature requests and suggestions for improvement
        4. Positive patterns (what customers love)
        5. Technical issues and bugs
        6. Trends and changes over time
        7. Categorize patterns by severity (critical/high/medium/low)

        For each pattern, provide:
        - Pattern type (pain_point, feature_request, praise, bug, trend)
        - Clear description of the pattern
        - Frequency (how often it appears)
        - Severity level
        - Representative examples/quotes
        - Potential business impact

        Output your analysis as valid JSON with this exact structure:
        {
          "patterns": [
            {
              "pattern_type": "pain_point|feature_request|praise|bug|trend",
              "description": "Clear description of the pattern",
              "frequency": 5,
              "severity": "critical|high|medium|low",
              "examples": ["quote1", "quote2", "quote3"],
              "business_impact": "Description of potential impact",
              "affected_users": "estimate of users affected"
            }
          ],
          "trend_analysis": {
            "overall_trend": "improving|declining|stable",
            "key_changes": ["change1", "change2"],
            "seasonal_patterns": ["pattern1", "pattern2"]
          },
          "summary_statistics": {
            "total_patterns_identified": 10,
            "patterns_by_type": {"pain_point": 3, "feature_request": 2, "praise": 4, "bug": 1},
            "average_severity_score": 2.5
          }
        }

        Focus on actionable insights that can drive product and service improvements.
        """

        super().__init__(
            name="pattern_detector",
            role="Pattern Detection Specialist",
            system_prompt=system_prompt,
            temperature=0.5  # Balanced creativity and consistency
        )

        self.console = Console()

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the workflow state to detect patterns in customer feedback.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with pattern detection results
        """
        try:
            self.console.print("\n[bold blue]🔎 Pattern Detection Agent Starting...[/bold blue]")

            raw_data = state.get("raw_data", [])
            sentiment_results = state.get("sentiment_results", {})

            if not raw_data:
                self.console.print("[red]❌ No raw data found for pattern detection[/red]")
                state["errors"].append("No raw data available for pattern detection")
                return state

            self.console.print(f"Analyzing patterns in [green]{len(raw_data)}[/green] feedback items...")

            # Detect patterns using Claude
            pattern_analysis = self._detect_patterns(raw_data, sentiment_results)

            # Structure the results
            structured_patterns = self._structure_patterns(pattern_analysis)

            # Create trends summary
            trends = self._create_trends_summary(structured_patterns, raw_data)

            # Update state
            state["patterns"] = structured_patterns
            state["trends"] = trends
            state["current_step"] = "pattern_detection_completed"
            state["iteration_count"] += 1

            self.console.print("[bold green]✅ Pattern Detection Complete![/bold green]")
            self._display_pattern_summary(structured_patterns)

            return state

        except Exception as e:
            error_msg = f"Pattern detection failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            self.console.print(f"[bold red]❌ Error: {error_msg}[/bold red]")
            return state

    def _detect_patterns(self, feedback_data: List[Dict[str, Any]], sentiment_context: Dict[str, Any]) -> str:
        """
        Send feedback data to Claude for comprehensive pattern analysis.

        Args:
            feedback_data: List of customer feedback items
            sentiment_context: Sentiment analysis results for context

        Returns:
            Claude's JSON response as string
        """
        # Prepare feedback sample for analysis
        feedback_sample = []
        for item in feedback_data[:30]:  # Sample for token efficiency
            text = self._extract_text_from_feedback(item)
            if text:
                feedback_sample.append(f"• {text[:150]}...")

        context = f"""
        Analyzing {len(feedback_data)} customer feedback items.

        Sentiment Context:
        - Overall Sentiment: {sentiment_context.get('overall_sentiment', 'unknown')}
        - Sentiment Score: {sentiment_context.get('sentiment_score', 0.0)}
        - Key Topics: {sentiment_context.get('key_topics', [])}

        Sample Feedback:
        {chr(10).join(feedback_sample)}
        """

        task = f"""
        Identify patterns, trends, and recurring themes in this customer feedback. Focus on:

        1. Pain points that appear multiple times
        2. Feature requests and suggestions
        3. Positive patterns (what works well)
        4. Technical issues or bugs
        5. Trends in customer satisfaction
        6. Changes in feedback themes over time

        Look for actionable insights that can drive product improvements.
        Provide detailed pattern analysis in the specified JSON format.
        """

        return self.execute(task, {"pattern_context": context})

    def _extract_text_from_feedback(self, feedback_item: Dict[str, Any]) -> str:
        """
        Extract text content from feedback items for pattern analysis.

        Args:
            feedback_item: Individual feedback record

        Returns:
            Text content for analysis
        """
        text_fields = ["text", "review_text", "description", "comments", "subject"]

        for field in text_fields:
            if field in feedback_item and feedback_item[field]:
                return str(feedback_item[field])

        return ""

    def _structure_patterns(self, analysis_response: str) -> List[Dict[str, Any]]:
        """
        Parse Claude's JSON response and structure the patterns.

        Args:
            analysis_response: Raw JSON string from Claude

        Returns:
            List of structured pattern dictionaries
        """
        try:
            # Extract JSON from response
            json_start = analysis_response.find('{')
            json_end = analysis_response.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_str = analysis_response[json_start:json_end]
            analysis_data = json.loads(json_str)

            patterns = analysis_data.get("patterns", [])

            # Validate and enhance patterns
            validated_patterns = []
            for pattern in patterns:
                if self._validate_pattern(pattern):
                    enhanced_pattern = self._enhance_pattern(pattern)
                    validated_patterns.append(enhanced_pattern)

            # Sort by severity and frequency
            validated_patterns.sort(key=lambda x: (self._severity_score(x["severity"]), x["frequency"]), reverse=True)

            return validated_patterns

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.warning(f"Failed to parse pattern analysis JSON: {e}")
            self.logger.info(f"Raw response: {analysis_response[:500]}...")

            # Return fallback patterns based on basic analysis
            return self._generate_fallback_patterns()

    def _validate_pattern(self, pattern: Dict[str, Any]) -> bool:
        """
        Validate that a pattern has all required fields.

        Args:
            pattern: Pattern dictionary to validate

        Returns:
            True if pattern is valid
        """
        required_fields = ["pattern_type", "description", "frequency", "severity", "examples"]
        return all(field in pattern and pattern[field] for field in required_fields)

    def _enhance_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance pattern with additional calculated fields.

        Args:
            pattern: Pattern dictionary to enhance

        Returns:
            Enhanced pattern dictionary
        """
        # Add impact score based on severity and frequency
        severity_multiplier = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        base_score = severity_multiplier.get(pattern["severity"], 1)
        impact_score = min(base_score * pattern["frequency"] * 0.1, 10.0)

        pattern["impact_score"] = round(impact_score, 2)
        pattern["business_impact"] = pattern.get("business_impact", f"Estimated impact score: {impact_score}")

        return pattern

    def _severity_score(self, severity: str) -> int:
        """
        Convert severity string to numeric score for sorting.

        Args:
            severity: Severity level string

        Returns:
            Numeric severity score
        """
        severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        return severity_map.get(severity, 1)

    def _generate_fallback_patterns(self) -> List[Dict[str, Any]]:
        """
        Generate basic fallback patterns when analysis fails.

        Returns:
            List of basic pattern dictionaries
        """
        return [
            {
                "pattern_type": "general_feedback",
                "description": "General customer feedback patterns detected",
                "frequency": 1,
                "severity": "medium",
                "examples": ["Various customer comments"],
                "business_impact": "General insights available",
                "affected_users": "unknown",
                "impact_score": 1.0
            }
        ]

    def _create_trends_summary(self, patterns: List[Dict[str, Any]], raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a trends summary based on patterns and raw data.

        Args:
            patterns: Detected patterns
            raw_data: Original feedback data

        Returns:
            Trends summary dictionary
        """
        # Count pattern types
        pattern_types = Counter(pattern["pattern_type"] for pattern in patterns)

        # Calculate severity distribution
        severity_counts = Counter(pattern["severity"] for pattern in patterns)

        # Calculate average impact score
        impact_scores = [p.get("impact_score", 0) for p in patterns]
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0

        return {
            "total_patterns": len(patterns),
            "pattern_distribution": dict(pattern_types),
            "severity_distribution": dict(severity_counts),
            "average_impact_score": round(avg_impact, 2),
            "high_impact_patterns": len([p for p in patterns if p.get("impact_score", 0) > 5.0]),
            "critical_patterns": len([p for p in patterns if p.get("severity") == "critical"]),
            "top_pattern_types": pattern_types.most_common(3)
        }

    def _display_pattern_summary(self, patterns: List[Dict[str, Any]]):
        """Display a formatted pattern detection summary."""
        if not patterns:
            self.console.print("  No patterns detected")
            return

        self.console.print(f"  Patterns Found: [bold cyan]{len(patterns)}[/bold cyan]")

        # Show top 3 patterns
        for i, pattern in enumerate(patterns[:3], 1):
            pattern_type = pattern.get("pattern_type", "unknown")
            severity = pattern.get("severity", "unknown")
            frequency = pattern.get("frequency", 0)

            # Color based on severity
            if severity == "critical":
                color = "red"
            elif severity == "high":
                color = "yellow"
            else:
                color = "green"

            self.console.print(f"    {i}. [{color}]{pattern_type}[/{color}] ({frequency}x) - {pattern.get('description', '')[:60]}...")