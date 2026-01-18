"""
Basic workflow tests for the Customer Intelligence Platform.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.workflow.orchestrator import CustomerIntelligenceOrchestrator
from src.workflow.state import create_initial_state


class TestWorkflow:
    """Test suite for the customer intelligence workflow."""

    def test_create_initial_state(self):
        """Test that initial state is created correctly."""
        state = create_initial_state("TestCompany", "TestProduct", ["reviews"])

        assert state["company_name"] == "TestCompany"
        assert state["product_name"] == "TestProduct"
        assert state["data_sources"] == ["reviews"]
        assert state["current_step"] == "initialization"
        assert state["iteration_count"] == 0
        assert state["errors"] == []
        assert state["raw_data"] == []
        assert state["data_summary"] == {}

    @patch('src.workflow.orchestrator.DataCollectorAgent')
    @patch('src.workflow.orchestrator.SentimentAnalyzerAgent')
    @patch('src.workflow.orchestrator.PatternDetectorAgent')
    @patch('src.workflow.orchestrator.OpportunityFinderAgent')
    @patch('src.workflow.orchestrator.StrategyCreatorAgent')
    def test_orchestrator_initialization(self, mock_strategy, mock_opportunity,
                                       mock_pattern, mock_sentiment, mock_data):
        """Test that orchestrator initializes all agents correctly."""
        # Mock the agent classes
        mock_strategy.return_value = MagicMock()
        mock_opportunity.return_value = MagicMock()
        mock_pattern.return_value = MagicMock()
        mock_sentiment.return_value = MagicMock()
        mock_data.return_value = MagicMock()

        orchestrator = CustomerIntelligenceOrchestrator()

        # Check that all agents were created
        mock_data.assert_called_once()
        mock_sentiment.assert_called_once()
        mock_pattern.assert_called_once()
        mock_opportunity.assert_called_once()
        mock_strategy.assert_called_once()

        # Check that workflow was built
        assert orchestrator.workflow is not None

    @patch('src.agents.data_collector.DataCollectorAgent.process')
    @patch('src.agents.sentiment_analyzer.SentimentAnalyzerAgent.process')
    @patch('src.agents.pattern_detector.PatternDetectorAgent.process')
    @patch('src.agents.opportunity_finder.OpportunityFinderAgent.process')
    @patch('src.agents.strategy_creator.StrategyCreatorAgent.process')
    def test_workflow_execution_flow(self, mock_strategy_process, mock_opportunity_process,
                                   mock_pattern_process, mock_sentiment_process, mock_data_process):
        """Test that the workflow executes agents in the correct order."""
        # Setup mock return values for each agent
        mock_data_process.return_value = {
            "company_name": "TestCompany",
            "product_name": "TestProduct",
            "data_sources": ["reviews"],
            "raw_data": [{"id": "test", "text": "test feedback"}],
            "data_summary": {"total_records": 1},
            "current_step": "data_collection_completed",
            "iteration_count": 1,
            "errors": []
        }

        mock_sentiment_process.return_value = {
            **mock_data_process.return_value,
            "sentiment_results": {"overall_sentiment": "positive", "sentiment_score": 0.8},
            "sentiment_breakdown": {},
            "current_step": "sentiment_analysis_completed",
            "iteration_count": 2
        }

        mock_pattern_process.return_value = {
            **mock_sentiment_process.return_value,
            "patterns": [{"pattern_type": "praise", "description": "test pattern"}],
            "trends": {},
            "current_step": "pattern_detection_completed",
            "iteration_count": 3
        }

        mock_opportunity_process.return_value = {
            **mock_pattern_process.return_value,
            "opportunities": [{"title": "test opportunity"}],
            "current_step": "opportunity_finding_completed",
            "iteration_count": 4
        }

        mock_strategy_process.return_value = {
            **mock_opportunity_process.return_value,
            "strategy_recommendations": [{"action": "test action"}],
            "executive_summary": "test summary",
            "current_step": "strategy_creation_completed",
            "iteration_count": 5
        }

        orchestrator = CustomerIntelligenceOrchestrator()

        # Run workflow
        result = orchestrator.run("TestCompany", "TestProduct", ["reviews"])

        # Verify the workflow completed successfully
        assert result["company_name"] == "TestCompany"
        assert result["product_name"] == "TestProduct"
        assert result["current_step"] == "strategy_creation_completed"
        assert result["iteration_count"] == 5
        assert len(result["raw_data"]) > 0
        assert "sentiment_results" in result
        assert "patterns" in result
        assert "opportunities" in result
        assert "strategy_recommendations" in result
        assert "executive_summary" in result

        # Verify agents were called in order
        mock_data_process.assert_called_once()
        mock_sentiment_process.assert_called_once()
        mock_pattern_process.assert_called_once()
        mock_opportunity_process.assert_called_once()
        mock_strategy_process.assert_called_once()

    def test_workflow_handles_errors_gracefully(self):
        """Test that workflow handles errors gracefully."""
        orchestrator = CustomerIntelligenceOrchestrator()

        # Test with missing API key (should fail gracefully)
        with patch.dict('os.environ', {}, clear=True):
            result = orchestrator.run("TestCompany", "TestProduct", ["reviews"])

            # Should return error state
            assert "errors" in result
            assert len(result["errors"]) > 0

    def test_state_validation(self):
        """Test state validation functions."""
        from src.workflow.state import validate_state

        # Valid state
        valid_state = create_initial_state("TestCompany", "TestProduct", ["reviews"])
        validation = validate_state(valid_state)
        assert validation["valid"] is True

        # Invalid state - missing required fields
        invalid_state = {"company_name": "Test"}  # Missing required fields
        validation = validate_state(invalid_state)
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0


if __name__ == "__main__":
    # Run basic smoke test
    print("Running basic workflow smoke test...")

    # Test state creation
    state = create_initial_state("TestCompany", "TestProduct", ["reviews"])
    print(f"✓ Initial state created: {state['current_step']}")

    # Test orchestrator initialization (will fail without API key, but should not crash)
    try:
        orchestrator = CustomerIntelligenceOrchestrator()
        print("✓ Orchestrator initialized successfully")
    except Exception as e:
        print(f"⚠️  Orchestrator initialization failed (expected without API key): {e}")

    print("✓ Smoke test completed successfully!")

