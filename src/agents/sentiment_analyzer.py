"""
Sentiment Analyzer Agent.

This agent analyzes customer sentiment using Claude LLM to identify emotions,
sentiment scores, and key topics from customer feedback.
"""

import json
import re
from typing import Any, Dict, List

from rich.console import Console

from .base_agent import BaseAgent


class SentimentAnalyzerAgent(BaseAgent):
    """
    Sentiment Analysis Specialist agent that analyzes customer feedback emotions and sentiment.

    Uses Claude to perform comprehensive sentiment analysis including:
    - Overall sentiment (positive/negative/neutral)
    - Sentiment scores (-1.0 to 1.0)
    - Emotional analysis (frustration, delight, confusion, satisfaction)
    - Key topic extraction
    """

    def __init__(self):
        """Initialize the Sentiment Analyzer Agent with specialized system prompt."""
        system_prompt = """
        You are a Sentiment Analysis Specialist. Analyze customer feedback and respond with ONLY valid JSON.

        CRITICAL: Respond with ONLY valid JSON. No explanations, no markdown, no preamble. Start with { and end with }.

        Analyze customer feedback to determine:
        1. overall_sentiment: "positive", "negative", or "neutral"
        2. sentiment_score: -1.0 (very negative) to +1.0 (very positive)
        3. emotions: Object with intensity scores (0.0-1.0) for frustration, delight, confusion, satisfaction, anger, disappointment, excitement, indifference
        4. key_topics: Array of 3-5 key topics/themes mentioned
        5. confidence: 0.0-1.0 confidence level based on sample size and analysis clarity
        6. analysis_summary: Brief summary of sentiment analysis

        Required JSON structure:
        {
          "overall_sentiment": "positive|negative|neutral",
          "sentiment_score": -1.0 to 1.0,
          "emotions": {
            "frustration": 0.0,
            "delight": 0.0,
            "confusion": 0.0,
            "satisfaction": 0.0,
            "anger": 0.0,
            "disappointment": 0.0,
            "excitement": 0.0,
            "indifference": 0.0
          },
          "key_topics": ["topic1", "topic2", "topic3"],
          "confidence": 0.75,
          "analysis_summary": "Brief summary"
        }

        Be precise, objective, and base your analysis on the actual content of the feedback.
        """

        super().__init__(
            name="sentiment_analyzer",
            role="Sentiment Analysis Specialist",
            system_prompt=system_prompt,
            temperature=0.4  # Lower temperature for consistent analysis
        )

        self.console = Console()

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the workflow state to analyze sentiment in customer feedback.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with sentiment analysis results
        """
        try:
            self.console.print("\n[bold blue]💭 Sentiment Analysis Agent Starting...[/bold blue]")

            raw_data = state.get("raw_data", [])
            data_summary = state.get("data_summary", {})

            if not raw_data:
                self.console.print("[red]❌ No raw data found for sentiment analysis[/red]")
                state["errors"].append("No raw data available for sentiment analysis")
                return state

            self.console.print(f"Analyzing sentiment in [green]{len(raw_data)}[/green] feedback items...")

            # Analyze sentiment using Claude
            analysis_result = self._analyze_sentiment(raw_data, data_summary, state)

            # Structure the results
            structured_results = self._structure_results(analysis_result)

            # Update state
            state["sentiment_results"] = structured_results["overall"]
            state["sentiment_breakdown"] = structured_results["breakdown"]
            state["current_step"] = "sentiment_analysis_completed"
            state["iteration_count"] += 1

            self.console.print("[bold green]✅ Sentiment Analysis Complete![/bold green]")
            self._display_sentiment_summary(structured_results["overall"])

            return state

        except Exception as e:
            error_msg = f"Sentiment analysis failed: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            self.console.print(f"[bold red]❌ Error: {error_msg}[/bold red]")
            return state

    def _analyze_sentiment(self, feedback_data: List[Dict[str, Any]], data_summary: Dict[str, Any], state: Dict[str, Any]) -> str:
        """
        Send feedback data to Claude for comprehensive sentiment analysis.

        Args:
            feedback_data: List of customer feedback items
            data_summary: Summary statistics about the data

        Returns:
            Claude's JSON response as string
        """
        # Prepare feedback text for analysis
        feedback_texts = []
        for item in feedback_data[:100]:  # Increased to 100 items for better analysis
            text = self._extract_text_from_feedback(item)
            if text:
                feedback_texts.append(f"• {text[:200]}...")  # Truncate long texts

        context = f"""
        Analyzing {len(feedback_data)} customer feedback items from {data_summary.get('data_sources_processed', 'multiple')} sources.

        Feedback Summary:
        - Total Records: {data_summary.get('total_records', 0)}
        - Date Range: {data_summary.get('date_range', {}).get('earliest', 'N/A')} to {data_summary.get('date_range', {}).get('latest', 'N/A')}

        Sample Feedback:
        {chr(10).join(feedback_texts[:10])}
        """

        task = f"""
        Analyze the sentiment of this customer feedback data. Consider:
        1. Overall sentiment across all feedback
        2. Key emotional drivers (what makes customers happy/unhappy)
        3. Important topics and themes
        4. Confidence in your analysis

        Provide detailed analysis in the specified JSON format.
        """

        # Include company and product info for mock response generation
        full_context = {
            "feedback_context": context,
            "company_name": state.get("company_name", "Unknown Company"),
            "product_name": state.get("product_name", "Unknown Product")
        }
        return self.execute(task, full_context)

    def _extract_text_from_feedback(self, feedback_item: Dict[str, Any]) -> str:
        """
        Extract text content from different types of feedback items.

        Args:
            feedback_item: Individual feedback record

        Returns:
            Text content for sentiment analysis
        """
        # Try different text fields based on feedback type
        text_fields = ["text", "review_text", "description", "comments", "subject"]

        for field in text_fields:
            if field in feedback_item and feedback_item[field]:
                return str(feedback_item[field])

        # If no text field found, return empty string
        return ""

    def _structure_results(self, analysis_response: str) -> Dict[str, Any]:
        """
        Parse Claude's JSON response and structure the results.

        Args:
            analysis_response: Raw JSON string from Claude

        Returns:
            Structured sentiment analysis results
        """
        try:
            # 3-tier JSON extraction for robustness
            analysis_data = None

            # Method 1: Direct JSON parse
            try:
                analysis_data = json.loads(analysis_response.strip())
                self.logger.debug("JSON parsed directly")
            except json.JSONDecodeError:
                pass

            # Method 2: Extract from markdown code blocks
            if analysis_data is None:
                json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', analysis_response, re.DOTALL)
                if json_match:
                    try:
                        analysis_data = json.loads(json_match.group(1).strip())
                        self.logger.debug("JSON extracted from markdown block")
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
                            self.logger.debug("JSON extracted using brace matching")
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Brace matching failed: {e}")
                            raise ValueError(f"No valid JSON found in response after trying 3 methods")

            if analysis_data is None:
                raise ValueError("No JSON found in response after trying 3 parsing methods")

            # Validate required fields
            required_fields = ["overall_sentiment", "sentiment_score", "emotions", "key_topics"]
            for field in required_fields:
                if field not in analysis_data:
                    raise ValueError(f"Missing required field: {field}")

            self.logger.info(f"Successfully parsed sentiment analysis with confidence: {analysis_data.get('confidence', 'N/A')}")

            # Extract confidence with proper validation
            confidence = float(analysis_data.get("confidence", 0.75))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0.0-1.0 range

            # Create overall results summary
            overall = {
                "overall_sentiment": analysis_data["overall_sentiment"],
                "sentiment_score": analysis_data["sentiment_score"],
                "confidence": confidence,
                "analysis_summary": analysis_data.get("analysis_summary", ""),
                "total_feedback_analyzed": analysis_data.get("total_feedback_analyzed", 0)
            }

            # Create detailed breakdown
            breakdown = {
                "emotions": analysis_data["emotions"],
                "key_topics": analysis_data["key_topics"],
                "sentiment_distribution": self._calculate_sentiment_distribution(analysis_data),
                "top_emotions": self._get_top_emotions(analysis_data["emotions"])
            }

            return {
                "overall": overall,
                "breakdown": breakdown,
                "raw_analysis": analysis_data
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.warning(f"Failed to parse sentiment analysis JSON: {e}")
            self.logger.info(f"Raw response: {analysis_response[:500]}...")

            # Return fallback structure
            return {
                "overall": {
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.5,  # Higher confidence for fallback
                    "analysis_summary": "Analysis failed due to parsing error - using fallback results",
                    "total_feedback_analyzed": 0
                },
                "breakdown": {
                    "emotions": {},
                    "key_topics": [],
                    "sentiment_distribution": {},
                    "top_emotions": []
                },
                "raw_analysis": {"error": str(e), "raw_response": analysis_response}
            }

    def _calculate_sentiment_distribution(self, analysis_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate sentiment distribution percentages.

        Args:
            analysis_data: Parsed analysis data

        Returns:
            Distribution percentages for sentiment categories
        """
        sentiment = analysis_data.get("overall_sentiment", "neutral")
        score = analysis_data.get("sentiment_score", 0.0)

        # Simple distribution based on score
        if score > 0.3:
            return {"positive": 0.7, "neutral": 0.2, "negative": 0.1}
        elif score < -0.3:
            return {"positive": 0.1, "neutral": 0.2, "negative": 0.7}
        else:
            return {"positive": 0.3, "neutral": 0.4, "negative": 0.3}

    def _get_top_emotions(self, emotions: Dict[str, float], top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Get the top emotions by intensity score.

        Args:
            emotions: Dictionary of emotion scores
            top_n: Number of top emotions to return

        Returns:
            List of top emotions with scores
        """
        sorted_emotions = sorted(
            emotions.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"emotion": emotion, "intensity": score}
            for emotion, score in sorted_emotions[:top_n]
            if score > 0.1  # Only include emotions with meaningful intensity
        ]

    def _display_sentiment_summary(self, overall_results: Dict[str, Any]):
        """Display a formatted sentiment analysis summary."""
        sentiment = overall_results.get("overall_sentiment", "unknown")
        score = overall_results.get("sentiment_score", 0.0)
        confidence = overall_results.get("confidence", 0.0)

        # Color based on sentiment
        if sentiment == "positive":
            color = "green"
        elif sentiment == "negative":
            color = "red"
        else:
            color = "yellow"

        self.console.print(f"  Overall Sentiment: [bold {color}]{sentiment.upper()}[/bold {color}]")
        self.console.print(f"  Sentiment Score: {score:.2f}")
        self.console.print(f"  Confidence: {confidence:.1%}")
        self.console.print(f"  Summary: {overall_results.get('analysis_summary', 'N/A')}")