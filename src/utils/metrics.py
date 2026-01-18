"""
Metrics and Evaluation Utilities.

This module provides comprehensive metrics tracking and evaluation capabilities
for the Customer Intelligence Platform, including hallucination detection,
performance monitoring, and business impact assessment.
"""

import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

import numpy as np


class WorkflowEvaluator:
    """
    Evaluates workflow performance, hallucination rates, and business impact.

    Tracks and analyzes:
    - Latency and performance metrics
    - Hallucination rates (unsupported recommendations)
    - Coverage metrics (pain points addressed)
    - Actionability scores (recommendations that can be implemented)
    """

    def __init__(self):
        self.metrics_history = []
        self.baseline_metrics = {}

    def evaluate_workflow_run(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive evaluation of a workflow run.

        Args:
            results: Complete workflow results

        Returns:
            Detailed evaluation report
        """
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": results.get("workflow_id", "unknown"),
            "performance_metrics": self._evaluate_performance(results),
            "hallucination_metrics": self._evaluate_hallucinations(results),
            "coverage_metrics": self._evaluate_coverage(results),
            "actionability_metrics": self._evaluate_actionability(results),
            "business_impact": self._estimate_business_impact(results),
            "overall_score": 0.0,
            "recommendations": []
        }

        # Calculate overall score
        scores = [
            evaluation["performance_metrics"].get("efficiency_score", 0),
            1.0 - evaluation["hallucination_metrics"].get("overall_hallucination_rate", 1),  # Invert for score
            evaluation["coverage_metrics"].get("overall_coverage", 0),
            evaluation["actionability_metrics"].get("overall_actionability", 0)
        ]

        evaluation["overall_score"] = np.mean([s for s in scores if s > 0])

        # Generate improvement recommendations
        evaluation["recommendations"] = self._generate_improvement_recommendations(evaluation)

        # Store in history
        self.metrics_history.append(evaluation)

        return evaluation

    def _evaluate_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate workflow performance metrics."""
        perf_metrics = results.get("performance_metrics", {})

        evaluation = {
            "total_runtime_seconds": perf_metrics.get("total_duration_seconds"),
            "agents_completed": perf_metrics.get("agents_completed", 0),
            "agents_failed": perf_metrics.get("agents_failed", 0),
            "error_rate": 0.0,
            "efficiency_score": 0.0
        }

        total_agents = evaluation["agents_completed"] + evaluation["agents_failed"]
        if total_agents > 0:
            evaluation["error_rate"] = evaluation["agents_failed"] / total_agents

        # Efficiency score based on completion rate and speed
        completion_rate = evaluation["agents_completed"] / max(total_agents, 1)
        runtime_score = min(1.0, 300.0 / max(perf_metrics.get("total_duration_seconds", 300), 30))  # Target: <5 min
        evaluation["efficiency_score"] = (completion_rate + runtime_score) / 2

        return evaluation

    def _evaluate_hallucinations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate hallucination rates - recommendations not supported by input data.

        Hallucination = recommendations that aren't grounded in the actual customer feedback.
        """
        evaluation = {
            "overall_hallucination_rate": 0.0,
            "opportunity_hallucinations": 0,
            "strategy_hallucinations": 0,
            "unsupported_claims": [],
            "confidence_score": 0.0
        }

        raw_data = results.get("raw_data", [])
        opportunities = results.get("opportunities", [])
        recommendations = results.get("strategy_recommendations", [])

        if not raw_data:
            evaluation["overall_hallucination_rate"] = 1.0
            return evaluation

        # Convert raw data to searchable text
        all_feedback_text = " ".join([
            str(item.get("text", "")) +
            str(item.get("description", "")) +
            str(item.get("comments", ""))
            for item in raw_data
        ]).lower()

        # Check opportunities against feedback
        hallucinated_opportunities = 0
        for opp in opportunities:
            opp_text = str(opp.get("description", "")).lower()
            # Check if key terms from opportunity appear in feedback
            key_terms = opp_text.split()[:5]  # First 5 words as key terms
            supported_terms = sum(1 for term in key_terms if term in all_feedback_text)
            if supported_terms / len(key_terms) < 0.3:  # Less than 30% term overlap
                hallucinated_opportunities += 1
                evaluation["unsupported_claims"].append(f"Opportunity: {opp.get('title', 'Unknown')}")

        # Check strategy recommendations
        hallucinated_recommendations = 0
        for rec in recommendations:
            rec_text = str(rec.get("rationale", "")).lower()
            key_terms = rec_text.split()[:5]
            supported_terms = sum(1 for term in key_terms if term in all_feedback_text)
            if supported_terms / len(key_terms) < 0.3:
                hallucinated_recommendations += 1
                evaluation["unsupported_claims"].append(f"Recommendation: {rec.get('action', 'Unknown')}")

        # Calculate rates
        total_opportunities = len(opportunities)
        total_recommendations = len(recommendations)

        if total_opportunities > 0:
            evaluation["opportunity_hallucinations"] = hallucinated_opportunities
            evaluation["opportunity_hallucination_rate"] = hallucinated_opportunities / total_opportunities

        if total_recommendations > 0:
            evaluation["strategy_hallucinations"] = hallucinated_recommendations
            evaluation["strategy_hallucination_rate"] = hallucinated_recommendations / total_recommendations

        # Overall hallucination rate
        total_items = total_opportunities + total_recommendations
        total_hallucinations = hallucinated_opportunities + hallucinated_recommendations
        evaluation["overall_hallucination_rate"] = total_hallucinations / max(total_items, 1)

        # Confidence score (inverse of hallucination rate)
        evaluation["confidence_score"] = 1.0 - evaluation["overall_hallucination_rate"]

        return evaluation

    def _evaluate_coverage(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate how comprehensively the analysis covers customer feedback.

        Coverage = % of pain points, issues, and feedback themes addressed.
        """
        evaluation = {
            "overall_coverage": 0.0,
            "pain_points_covered": 0,
            "total_pain_points": 0,
            "feedback_themes_covered": 0,
            "total_feedback_themes": 0,
            "coverage_breakdown": {}
        }

        raw_data = results.get("raw_data", [])
        patterns = results.get("patterns", [])
        recommendations = results.get("strategy_recommendations", [])

        if not raw_data:
            return evaluation

        # Count total feedback items with issues/pain points
        evaluation["total_pain_points"] = len([item for item in raw_data
                                             if self._has_pain_point(item)])

        # Count pain points addressed by patterns
        pain_point_patterns = [p for p in patterns
                              if p.get("pattern_type") in ["pain_point", "bug", "technical_issue"]]
        evaluation["pain_points_covered"] = len(pain_point_patterns)

        # Count feedback themes (unique topics)
        all_topics = set()
        for item in raw_data:
            topics = self._extract_topics(item)
            all_topics.update(topics)
        evaluation["total_feedback_themes"] = len(all_topics)

        # Count themes covered by patterns
        pattern_topics = set()
        for pattern in patterns:
            pattern_topics.update(self._extract_topics_from_pattern(pattern))
        evaluation["feedback_themes_covered"] = len(pattern_topics.intersection(all_topics))

        # Calculate coverage percentages
        if evaluation["total_pain_points"] > 0:
            evaluation["pain_point_coverage"] = evaluation["pain_points_covered"] / evaluation["total_pain_points"]

        if evaluation["total_feedback_themes"] > 0:
            evaluation["theme_coverage"] = evaluation["feedback_themes_covered"] / evaluation["total_feedback_themes"]

        # Overall coverage score
        coverage_scores = []
        if evaluation["pain_point_coverage"] is not None:
            coverage_scores.append(evaluation["pain_point_coverage"])
        if evaluation["theme_coverage"] is not None:
            coverage_scores.append(evaluation["theme_coverage"])

        if coverage_scores:
            evaluation["overall_coverage"] = np.mean(coverage_scores)

        return evaluation

    def _evaluate_actionability(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate how actionable the generated recommendations are.

        Actionability = % of recommendations that are specific, measurable, and feasible.
        """
        evaluation = {
            "overall_actionability": 0.0,
            "actionable_recommendations": 0,
            "total_recommendations": 0,
            "actionability_breakdown": {},
            "implementation_readiness": 0.0
        }

        recommendations = results.get("strategy_recommendations", [])
        opportunities = results.get("opportunities", [])

        all_items = recommendations + opportunities
        evaluation["total_recommendations"] = len(all_items)

        if not all_items:
            return evaluation

        actionable_count = 0
        for item in all_items:
            actionability_score = self._calculate_actionability_score(item)
            if actionability_score >= 0.7:  # Threshold for "actionable"
                actionable_count += 1

        evaluation["actionable_recommendations"] = actionable_count
        evaluation["overall_actionability"] = actionable_count / len(all_items)

        # Implementation readiness based on presence of timelines and owners
        has_timelines = sum(1 for item in all_items if item.get("timeline") != "unknown")
        has_owners = sum(1 for item in all_items if item.get("owner"))

        evaluation["implementation_readiness"] = (has_timelines + has_owners) / (2 * len(all_items))

        return evaluation

    def _estimate_business_impact(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate potential business impact of the recommendations.

        Based on opportunity impact scores, recommendation priorities, and coverage.
        """
        estimation = {
            "estimated_impact_score": 0.0,
            "potential_savings": 0,
            "revenue_opportunities": 0,
            "customer_satisfaction_improvement": 0.0,
            "implementation_effort": 0,
            "roi_estimate": 0.0
        }

        opportunities = results.get("opportunities", [])
        recommendations = results.get("strategy_recommendations", [])

        # Aggregate impact scores
        impact_scores = []
        for opp in opportunities:
            score = opp.get("impact_score", 0)
            impact_scores.append(score)

        for rec in recommendations:
            priority = rec.get("priority", 5)
            impact_scores.append(priority)

        if impact_scores:
            estimation["estimated_impact_score"] = np.mean(impact_scores) / 10.0  # Normalize to 0-1

        # Estimate customer satisfaction improvement
        sentiment_before = 0.5  # Assume neutral baseline
        sentiment_after = results.get("sentiment_results", {}).get("sentiment_score", 0) + 1  # Convert to 0-1
        sentiment_after = min(max(sentiment_after, 0), 1)  # Clamp
        estimation["customer_satisfaction_improvement"] = sentiment_after - sentiment_before

        # Rough ROI calculation
        if estimation["estimated_impact_score"] > 0:
            # Simplified: Impact score * customer satisfaction improvement
            estimation["roi_estimate"] = estimation["estimated_impact_score"] * estimation["customer_satisfaction_improvement"]

        return estimation

    def _generate_improvement_recommendations(self, evaluation: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for improving the system."""
        recommendations = []

        # Performance recommendations
        if evaluation["performance_metrics"]["error_rate"] > 0.2:
            recommendations.append("Improve error handling and agent reliability")

        if evaluation["performance_metrics"]["efficiency_score"] < 0.7:
            recommendations.append("Optimize agent execution time and workflow efficiency")

        # Hallucination recommendations
        if evaluation["hallucination_metrics"]["overall_hallucination_rate"] > 0.3:
            recommendations.append("Strengthen hallucination prevention with better grounding checks")

        if evaluation["hallucination_metrics"]["confidence_score"] < 0.7:
            recommendations.append("Improve prompt engineering for more reliable outputs")

        # Coverage recommendations
        if evaluation["coverage_metrics"]["overall_coverage"] < 0.6:
            recommendations.append("Enhance pattern detection to cover more customer feedback themes")

        # Actionability recommendations
        if evaluation["actionability_metrics"]["overall_actionability"] < 0.7:
            recommendations.append("Generate more specific and measurable recommendations")

        return recommendations

    def _has_pain_point(self, feedback_item: Dict[str, Any]) -> bool:
        """Check if feedback item contains a pain point or negative sentiment."""
        text = str(feedback_item.get("text", "") + feedback_item.get("description", "") + feedback_item.get("comments", "")).lower()

        pain_indicators = ["problem", "issue", "bug", "error", "slow", "difficult", "confusing", "broken", "doesn't work"]
        return any(indicator in text for indicator in pain_indicators)

    def _extract_topics(self, feedback_item: Dict[str, Any]) -> List[str]:
        """Extract key topics from feedback item."""
        text = str(feedback_item.get("text", "") + feedback_item.get("description", "")).lower()

        # Simple topic extraction based on keywords
        topics = []
        topic_keywords = {
            "performance": ["slow", "fast", "performance", "speed", "loading"],
            "ui": ["interface", "design", "ui", "ux", "layout", "navigation"],
            "pricing": ["price", "cost", "expensive", "cheap", "pricing", "billing"],
            "support": ["support", "help", "customer service", "response", "helpful"],
            "features": ["feature", "functionality", "capability", "tool", "option"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)

        return topics

    def _extract_topics_from_pattern(self, pattern: Dict[str, Any]) -> List[str]:
        """Extract topics from pattern description."""
        description = pattern.get("description", "").lower()
        return self._extract_topics({"text": description})

    def _calculate_actionability_score(self, item: Dict[str, Any]) -> float:
        """Calculate how actionable a recommendation or opportunity is."""
        score = 0.0
        total_criteria = 0

        # Specific action described
        if item.get("action") or item.get("description"):
            if len(str(item.get("action", "") + item.get("description", ""))) > 20:
                score += 1
            total_criteria += 1

        # Has measurable outcomes
        if item.get("success_metrics") or item.get("expected_outcome"):
            score += 1
            total_criteria += 1

        # Has timeline
        if item.get("timeline") and item["timeline"] != "unknown":
            score += 1
            total_criteria += 1

        # Has owner/responsible party
        if item.get("owner"):
            score += 1
            total_criteria += 1

        # Has effort estimate
        if item.get("effort_estimate") or item.get("effort_level"):
            score += 1
            total_criteria += 1

        return score / max(total_criteria, 1)

    def save_evaluation_report(self, evaluation: Dict[str, Any], output_dir: Path = None):
        """Save evaluation report to file."""
        if output_dir is None:
            output_dir = Path("data/output")

        output_dir.mkdir(parents=True, exist_ok=True)

        report_file = output_dir / f"evaluation_report_{evaluation['workflow_id']}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation, f, indent=2, default=str)

        return report_file

    def get_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends across multiple runs."""
        if not self.metrics_history:
            return {"error": "No evaluation history available"}

        trends = {
            "total_runs": len(self.metrics_history),
            "avg_overall_score": np.mean([e["overall_score"] for e in self.metrics_history]),
            "avg_hallucination_rate": np.mean([e["hallucination_metrics"]["overall_hallucination_rate"] for e in self.metrics_history]),
            "avg_runtime": np.mean([e["performance_metrics"]["total_runtime_seconds"] for e in self.metrics_history if e["performance_metrics"]["total_runtime_seconds"]]),
            "improvement_trend": []
        }

        # Calculate improvement trend (last 5 runs)
        recent_scores = [e["overall_score"] for e in self.metrics_history[-5:]]
        if len(recent_scores) > 1:
            trends["improvement_trend"] = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]

        return trends

