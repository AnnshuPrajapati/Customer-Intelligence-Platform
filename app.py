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
            # Clear all previous analysis data
            keys_to_clear = ['analysis_complete', 'results', 'evaluation', 'last_company', 'last_product']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]

            run_analysis(company, product, data_sources)

    # Main content area - always show the same tab structure
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "💭 Sentiment", 
        "🔎 Patterns", 
        "💡 Opportunities", 
        "📋 Strategy"
    ])

    # Check if analysis is complete
    analysis_complete = st.session_state.get('analysis_complete', False)
    
    # Get results if available (with safe defaults)
    results = st.session_state.get('results', {}) if analysis_complete else {}
    evaluation = st.session_state.get('evaluation', {}) if analysis_complete else {}

    # TAB 1: Overview
    with tab1:
        st.header("Analysis Overview")
        
        if analysis_complete:
            # Show metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Quality", f"{evaluation.get('overall_score', 0):.1%}")
            with col2:
                st.metric("Data Processed", len(results.get('raw_data', [])))
            with col3:
                sentiment_results = results.get('sentiment_results', {})
                confidence = sentiment_results.get('confidence', 0) if isinstance(sentiment_results, dict) else 0
                st.metric("AI Confidence", f"{confidence:.1%}")

            # Performance metrics
            st.subheader("Performance Metrics")
            perf_metrics = results.get('performance_metrics', {})
            if perf_metrics:
                st.json(perf_metrics)
        else:
            # Show initial state
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

    # TAB 2: Sentiment
    with tab2:
        st.header("Sentiment Analysis")
        
        if analysis_complete:
            sentiment = results.get('sentiment_results', {})
            if sentiment and isinstance(sentiment, dict):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    sentiment_score = sentiment.get('sentiment_score', 0)
                    sentiment_color = "🟢" if sentiment_score > 0.2 else "🔴" if sentiment_score < -0.2 else "🟡"
                    st.metric(
                        "Overall Sentiment", 
                        f"{sentiment_color} {sentiment.get('overall_sentiment', 'unknown').title()}"
                    )
                
                with col2:
                    st.metric("Sentiment Score", f"{sentiment_score:.2f}")
                
                with col3:
                    st.metric("Confidence", f"{sentiment.get('confidence', 0):.1%}")

                st.subheader("Key Topics")
                topics = sentiment.get('key_topics', [])
                if topics:
                    for topic in topics:
                        st.write(f"• {topic}")
                else:
                    st.info("No key topics identified")
            else:
                st.info("No sentiment analysis results available")
        else:
            st.info("Run an analysis to see sentiment results here")

    # TAB 3: Patterns
    with tab3:
        st.header("Pattern Detection")
        
        if analysis_complete:
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
                    st.dataframe(
                        pd.DataFrame(pattern_data),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info("No patterns detected")
        else:
            st.info("Run an analysis to see detected patterns here")

    # TAB 4: Opportunities
    with tab4:
        st.header("Business Opportunities")
        
        if analysis_complete:
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
        else:
            st.info("Run an analysis to see opportunities here")

    # TAB 5: Strategy
    with tab5:
        st.header("Strategic Recommendations")
        
        if analysis_complete:
            summary = results.get('executive_summary', '')
            recommendations = results.get('strategy_recommendations', [])

            if summary:
                st.subheader("Executive Summary")
                st.write(summary)

            if recommendations and len(recommendations) > 0:
                st.subheader("Strategic Recommendations")
                st.metric("Total Recommendations", len(recommendations))

                for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                    with st.expander(f"{i}. {rec.get('action', 'Unknown action')}"):
                        st.write(f"**Category:** {rec.get('category', 'General').title()}")
                        st.write(f"**Priority:** {rec.get('priority', 'N/A')}/10")
                        st.write(f"**Timeline:** {rec.get('timeline', 'unknown').title()}")
                        st.write(f"**Expected Impact:** {rec.get('expected_impact', 'N/A')}")
            else:
                st.info("No strategic recommendations generated")
        else:
            st.info("Run an analysis to see strategy recommendations here")


def run_analysis(company: str, product: str, data_sources: list):
    """Run the customer intelligence analysis."""
    
    # Validation
    if not company or not product:
        st.error("❌ Please provide both company name and product name")
        return
    
    if not data_sources:
        st.error("❌ Please select at least one data source")
        return
    
    try:
        from src.workflow.orchestrator import CustomerIntelligenceOrchestrator
        from src.utils.metrics import WorkflowEvaluator

        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("🔧 Initializing workflow...")
        progress_bar.progress(10)
        time.sleep(0.5)  # Brief pause for UX

        # Initialize components
        orchestrator = CustomerIntelligenceOrchestrator()
        evaluator = WorkflowEvaluator()

        status_text.text("🤖 Running customer intelligence analysis...")
        progress_bar.progress(30)

        # Run analysis
        results = orchestrator.run(company, product, data_sources)

        status_text.text("📊 Evaluating results...")
        progress_bar.progress(80)

        # Ensure results is a dictionary
        if not isinstance(results, dict):
            st.error(f"❌ Analysis failed: Invalid results type ({type(results)})")
            progress_bar.empty()
            status_text.empty()
            return

        # Evaluate results
        evaluation = evaluator.evaluate_workflow_run(results)

        status_text.text("✨ Analysis complete!")
        progress_bar.progress(100)
        time.sleep(0.5)

        # Store results in session state
        st.session_state.results = results
        st.session_state.evaluation = evaluation
        st.session_state.analysis_complete = True
        st.session_state.last_company = company
        st.session_state.last_product = product

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        # Show success message
        st.success(f"✅ Analysis completed successfully for **{company} - {product}**!")
        st.balloons()  # Celebration effect

    except ImportError as e:
        st.error(f"❌ Import Error: {str(e)}")
        st.info("💡 Make sure all dependencies are installed: `pip install -r requirements.txt`")
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        st.exception(e)  # Show full stack trace in expander
        st.info("💡 Try running in demo mode: `python demo.py`")


if __name__ == "__main__":
    main()