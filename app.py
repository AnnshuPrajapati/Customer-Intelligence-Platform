#!/usr/bin/env python3
"""
Customer Intelligence Platform - Web App
Streamlit interface for easy deployment and use
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import sys
import os
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    st.set_page_config(
        page_title="Customer Intelligence Platform",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🚀 Customer Intelligence Platform")
    st.markdown("*Transform customer feedback into strategic insights*")

    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")

        company = st.text_input("Company Name", value="TechCorp", placeholder="Enter company name")
        product = st.text_input("Product Name", value="CloudFlow SaaS", placeholder="Enter product name")

        data_sources = st.multiselect(
            "Data Sources",
            ["reviews", "tickets", "surveys"],
            default=["reviews", "tickets", "surveys"]
        )

        if st.button("🚀 Run Analysis", type="primary"):
            # Clear previous analysis state only
            st.session_state.analysis_complete = False
            if 'results' in st.session_state:
                del st.session_state.results
            if 'evaluation' in st.session_state:
                del st.session_state.evaluation

            run_analysis(company, product, data_sources)

    # Main content area - always show the same tab structure
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "💭 Sentiment", "🔎 Patterns", "💡 Opportunities", "📋 Strategy"])

    if st.session_state.get('analysis_complete', False):
        # Analysis completed - show results in tabs
        results = st.session_state.get('results', {})
        evaluation = st.session_state.get('evaluation', {})

        with tab1:
            st.header("Analysis Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Quality", f"{evaluation.get('overall_score', 0):.1%}")
            with col2:
                st.metric("Data Processed", len(results.get('raw_data', [])))
            with col3:
                st.metric("AI Confidence", f"{results.get('sentiment_results', {}).get('confidence', 0):.1%}")

            # Performance metrics
            st.subheader("Performance Metrics")
            perf_metrics = results.get('performance_metrics', {})
            if perf_metrics:
                st.json(perf_metrics)

        with tab2:
            st.header("Sentiment Analysis")
            sentiment = results.get('sentiment_results', {})
            if sentiment:
                col1, col2, col3 = st.columns(3)
                with col1:
                    sentiment_color = "🟢" if sentiment.get('sentiment_score', 0) > 0.2 else "🔴" if sentiment.get('sentiment_score', 0) < -0.2 else "🟡"
                    st.metric("Overall Sentiment", f"{sentiment_color} {sentiment.get('overall_sentiment', 'unknown').title()}")
                with col2:
                    st.metric("Sentiment Score", f"{sentiment.get('sentiment_score', 0):.2f}")
                with col3:
                    st.metric("Confidence", f"{sentiment.get('confidence', 0):.1%}")

                st.subheader("Key Topics")
                topics = sentiment.get('key_topics', [])
                if topics:
                    for topic in topics:
                        st.write(f"• {topic}")
            else:
                st.info("No sentiment analysis results available")

        with tab3:
            st.header("Pattern Detection")
            patterns = results.get('patterns', [])
            if patterns:
                st.metric("Patterns Detected", len(patterns))

                # Display patterns in a table
                pattern_data = []
                for pattern in patterns[:10]:  # Show top 10
                    pattern_data.append({
                        "Type": pattern.get('pattern_type', 'unknown'),
                        "Description": pattern.get('description', '')[:100] + "...",
                        "Frequency": pattern.get('frequency', 0),
                        "Severity": pattern.get('severity', 'unknown'),
                        "Impact Score": pattern.get('impact_score', 0)
                    })

                if pattern_data:
                    st.dataframe(pd.DataFrame(pattern_data))
            else:
                st.info("No patterns detected")

        with tab4:
            st.header("Business Opportunities")
            opportunities = results.get('opportunities', [])
            if opportunities:
                st.metric("Opportunities Identified", len(opportunities))

                for i, opp in enumerate(opportunities[:5], 1):  # Show top 5
                    with st.expander(f"{i}. {opp.get('title', 'Unknown')}"):
                        st.write(f"**Description:** {opp.get('description', '')}")
                        st.write(f"**Priority:** {opp.get('priority', 'unknown').title()}")
                        st.write(f"**Impact Score:** {opp.get('impact_score', 0)}/10")
                        st.write(f"**Effort:** {opp.get('effort_estimate', 'unknown').title()}")
            else:
                st.info("No opportunities identified")

        with tab5:
            st.header("Strategic Recommendations")
            summary = results.get('executive_summary', '')
            recommendations = results.get('strategy_recommendations', [])

            if summary:
                st.subheader("Executive Summary")
                st.write(summary)

            if recommendations:
                st.subheader("Strategic Recommendations")
                st.metric("Total Recommendations", len(recommendations))

                for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                    with st.expander(f"{i}. {rec.get('action', 'Unknown action')}"):
                        st.write(f"**Category:** {rec.get('category', 'General').title()}")
                        st.write(f"**Priority:** {rec.get('priority', 'N/A')}/10")
                        st.write(f"**Timeline:** {rec.get('timeline', 'unknown').title()}")
                        st.write(f"**Expected Impact:** {rec.get('expected_impact', 'N/A')}")
            else:
                st.info("No strategic recommendations available")

    else:
        # No analysis completed - show initial interface
        with tab1:
            st.header("Analysis Overview")
            st.info("👈 Configure your analysis in the sidebar and click 'Run Analysis' to begin")

            # Show sample data preview
            st.subheader("Sample Data Available")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Customer Reviews", "15", "Realistic samples")
            with col2:
                st.metric("Support Tickets", "15", "Various categories")
            with col3:
                st.metric("Survey Responses", "10", "NPS & feedback")

            st.markdown("""
            ### What This Platform Does:
            1. **Collects** customer feedback from multiple sources
            2. **Analyzes** sentiment and emotions using AI
            3. **Detects** patterns and recurring themes
            4. **Identifies** business opportunities
            5. **Generates** strategic recommendations
            """)

        with tab2:
            st.header("Sentiment Analysis")
            st.info("Run an analysis to see sentiment results here")

        with tab3:
            st.header("Pattern Detection")
            st.info("Run an analysis to see detected patterns here")

        with tab4:
            st.header("Business Opportunities")
            st.info("Run an analysis to see opportunities here")

        with tab5:
            st.header("Strategic Recommendations")
            st.info("Run an analysis to see strategy recommendations here")

def run_analysis(company: str, product: str, data_sources: list):
    """Run the customer intelligence analysis."""
    try:
        from src.workflow.orchestrator import CustomerIntelligenceOrchestrator
        from src.utils.metrics import WorkflowEvaluator

        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Initializing workflow...")
        progress_bar.progress(10)

        # Initialize components
        orchestrator = CustomerIntelligenceOrchestrator()
        evaluator = WorkflowEvaluator()

        status_text.text("Running customer intelligence analysis...")
        progress_bar.progress(30)

        # Run analysis
        results = orchestrator.run(company, product, data_sources)

        # Debug: Check what orchestrator returned
        print(f"DEBUG: orchestrator.run() returned type: {type(results)}")
        print(f"DEBUG: orchestrator.run() returned value: {results}")

        status_text.text("Evaluating results...")
        progress_bar.progress(80)

        # Debug: Check results type
        print(f"DEBUG: results type: {type(results)}")
        print(f"DEBUG: results value: {results}")

        # Evaluate results
        evaluation = evaluator.evaluate_workflow_run(results)

        status_text.text("Analysis complete!")
        progress_bar.progress(100)

        # Store results in session state
        st.session_state.results = results
        st.session_state.evaluation = evaluation
        st.session_state.analysis_complete = True
        st.session_state.last_company = company
        st.session_state.last_product = product


        # Clear progress indicators first
        progress_bar.empty()
        status_text.empty()

        st.success(f"✅ Analysis completed successfully for {company} - {product}!")

    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        st.info("💡 Try running in demo mode: `python demo.py`")

if __name__ == "__main__":
    main()

