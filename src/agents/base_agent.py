"""
Base Agent class for the Customer Intelligence Platform.

This module defines the abstract base class that all specialized agents must inherit from.
Provides common functionality including Claude LLM integration, logging, and error handling.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# Try to import available LLM providers
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.genai as genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_LANGCHAIN_AVAILABLE = True
except ImportError:
    GOOGLE_LANGCHAIN_AVAILABLE = False

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class GeminiWrapper:
    """
    Wrapper for Google GenAI SDK to maintain compatibility with LangChain-style interface.
    """

    def __init__(self, client):
        self.client = client

    def invoke(self, messages):
        """
        Convert LangChain-style messages to Google GenAI format and call the API.

        Args:
            messages: List of message dictionaries or string

        Returns:
            Response object with .content attribute
        """
        # Extract content from messages
        if isinstance(messages, list) and len(messages) > 0:
            # LangChain format: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            system_content = ""
            user_content = ""

            for msg in messages:
                if msg.get("role") == "system":
                    system_content = msg.get("content", "")
                elif msg.get("role") == "user":
                    user_content = msg.get("content", "")

            # Combine system and user content
            if system_content and user_content:
                content = f"System: {system_content}\n\nUser: {user_content}"
            else:
                content = user_content or system_content
        else:
            # Direct string content
            content = str(messages)

        # Call Gemini API
        response = self.client.models.generate_content(
            model="gemini-1.5-flash",
            contents=content
        )

        # Return LangChain-compatible response
        class LangChainResponse:
            def __init__(self, text):
                self.content = text

        return LangChainResponse(response.text)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Customer Intelligence Platform.

    All specialized agents (DataCollector, SentimentAnalyzer, etc.) must inherit from this class
    and implement the process() method. Provides Claude LLM integration with common functionality.
    """

    def __init__(self, name: str, role: str, system_prompt: str,
                 tools: Optional[List[Any]] = None, temperature: float = 0.7):
        """
        Initialize the base agent with multi-provider LLM support.

        Supports: Google Gemini → OpenAI GPT-4 → Anthropic Claude → Ollama → Mock fallback

        Args:
            name: Unique name identifier for the agent
            role: Role description of the agent (e.g., "Data Collection Specialist")
            system_prompt: System prompt that defines the agent's behavior
            tools: Optional list of tools the agent can use
            temperature: Temperature parameter for LLM (default 0.7)
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.temperature = temperature

        # Set up logging
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        self.logger.setLevel(logging.INFO)

        # Initialize LLM with provider fallback chain
        self.llm, self.provider = self._initialize_llm()
        self.logger.info(f"Initialized {self.provider} LLM for agent '{self.name}'")

    def _initialize_llm(self):
        """
        Initialize LLM with fallback chain: Gemini → GPT-4 → Claude → Ollama → Mock

        Returns:
            Tuple of (llm_instance, provider_name)
        """
        import os

        # ADD DEBUGGING
        self.logger.info("=" * 80)
        self.logger.info(f"🔍 INITIALIZING LLM FOR AGENT: {self.name}")
        self.logger.info(f"GOOGLE_API_KEY present: {bool(os.getenv('GOOGLE_API_KEY'))}")
        self.logger.info(f"GOOGLE_API_KEY length: {len(os.getenv('GOOGLE_API_KEY', ''))}")
        self.logger.info(f"GOOGLE_GENAI_AVAILABLE: {GOOGLE_GENAI_AVAILABLE}")
        self.logger.info(f"GOOGLE_LANGCHAIN_AVAILABLE: {GOOGLE_LANGCHAIN_AVAILABLE}")
        self.logger.info(f"ANTHROPIC_AVAILABLE: {ANTHROPIC_AVAILABLE}")
        self.logger.info(f"OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")
        self.logger.info("=" * 80)

        # 1. Try Google Gemini (new SDK - now preferred, free tier available)
        if GOOGLE_GENAI_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            try:
                self.logger.info("🚀 Attempting to initialize Gemini (new API)...")
                # Initialize the new Google GenAI client
                client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

                self.logger.info("🧪 Testing Gemini connection...")
                # Test the connection
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents="Test connection"
                )

                self.logger.info("✅ Gemini (new API) initialized successfully!")
                self.logger.info(f"Test response: {response.text[:100]}...")
                # Return a wrapper that uses the new API
                return GeminiWrapper(client), "Google Gemini (New API)"
            except Exception as e:
                self.logger.error(f"❌ Gemini new API failed: {str(e)}")
                self.logger.exception(e)

        # 2. Try Google Gemini (LangChain fallback)
        if GOOGLE_LANGCHAIN_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            try:
                self.logger.info("🚀 Attempting Gemini LangChain fallback...")
                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",  # Fast and free tier
                    temperature=self.temperature,
                    max_tokens=4096
                )
                self.logger.info("🧪 Testing Gemini LangChain connection...")
                # Test the connection
                llm.invoke("test")
                self.logger.info("✅ Gemini LangChain initialized successfully!")
                return llm, "Google Gemini (LangChain)"
            except Exception as e:
                self.logger.error(f"❌ Gemini LangChain failed: {str(e)}")
                self.logger.exception(e)

        # 3. Try OpenAI GPT-4 (affordable, great quality)
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.logger.info("🚀 Attempting OpenAI GPT-4 initialization...")
                llm = ChatOpenAI(
                    model="gpt-4o-mini",  # Cheapest GPT-4 model
                    temperature=self.temperature,
                    max_tokens=4096
                )
                self.logger.info("🧪 Testing OpenAI connection...")
                # Test the connection
                llm.invoke("test")
                self.logger.info("✅ OpenAI GPT-4 initialized successfully!")
                return llm, "OpenAI GPT-4"
            except Exception as e:
                self.logger.error(f"❌ GPT-4 initialization failed: {str(e)}")
                self.logger.exception(e)

        # 4. Try Anthropic Claude (most expensive, best quality - last resort)
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.logger.info("🚀 Attempting Anthropic Claude initialization...")
                llm = ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    temperature=self.temperature,
                    max_tokens=4096
                )
                self.logger.info("🧪 Testing Claude connection...")
                # Test the connection
                llm.invoke("test")
                self.logger.info("✅ Anthropic Claude initialized successfully!")
                return llm, "Anthropic Claude"
            except Exception as e:
                self.logger.error(f"❌ Claude initialization failed: {str(e)}")
                self.logger.exception(e)

        # 5. Try Ollama (completely free, local models)
        if OLLAMA_AVAILABLE:
            try:
                self.logger.info("🚀 Attempting Ollama local model initialization...")
                llm = ChatOllama(
                    model="llama3.1",  # Free local model
                    temperature=self.temperature
                )
                self.logger.info("🧪 Testing Ollama connection...")
                # Test the connection
                llm.invoke("test")
                self.logger.info("✅ Ollama local model initialized successfully!")
                return llm, "Ollama Local"
            except Exception as e:
                self.logger.error(f"❌ Ollama initialization failed: {str(e)}")
                self.logger.exception(e)

        # 6. Fallback to mock mode (completely free)
        self.logger.warning("⚠️ " + "=" * 76)
        self.logger.warning(f"⚠️ NO LLM PROVIDERS AVAILABLE FOR AGENT '{self.name}'")
        self.logger.warning("⚠️ USING MOCK MODE - RESULTS WILL BE SYNTHETIC")
        self.logger.warning("⚠️ " + "=" * 76)
        return None, "Mock Mode"

    def execute(self, task: str, context: Dict[str, Any]) -> str:
        """
        Execute a task using the Claude LLM with proper formatting and error handling.
        Falls back to mock responses if API is not available.

        Args:
            task: The task description to execute
            context: Dictionary containing context information for the task

        Returns:
            String response from Claude or mock response

        Raises:
            Exception: If both LLM and mock fallback fail
        """
        try:
            # Log provider status
            if self.provider == "Mock Mode":
                self.logger.warning(f"⚠️ Agent '{self.name}' using MOCK MODE (no LLM available)")
            else:
                self.logger.debug(f"Agent '{self.name}' using {self.provider}")
            # Format the task with context
            formatted_task = self._format_task(task, context)

            # Check if we're in mock mode (no LLM available)
            if self.llm is None or self.provider == "Mock Mode":
                self.logger.info(f"Using mock response for agent '{self.name}' ({self.provider})")
                return self._generate_mock_response(task, context)

            # Create messages for Claude
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": formatted_task}
            ]

            self.logger.info(f"Executing task for agent '{self.name}': {task[:100]}...")

            # Call Claude
            response = self.llm.invoke(messages)

            # Extract response content
            result = response.content if hasattr(response, 'content') else str(response)

            self.logger.info(f"Successfully completed task for agent '{self.name}'")
            return result

        except Exception as e:
            error_msg = f"Failed to execute task for agent '{self.name}': {str(e)}"
            self.logger.error(error_msg)

            # Try mock fallback if API fails
            if "api" in str(e).lower() or "anthropic" in str(e).lower() or "key" in str(e).lower():
                self.logger.warning(f"API call failed, using mock response for agent '{self.name}'")
                try:
                    return self._generate_mock_response(task, context)
                except Exception as mock_error:
                    self.logger.error(f"Mock fallback also failed: {str(mock_error)}")

            # Add error to context for potential retry or fallback
            if "errors" in context and isinstance(context["errors"], list):
                context["errors"].append(error_msg)

            raise Exception(error_msg) from e

    def _generate_mock_response(self, task: str, context: Dict[str, Any]) -> str:
        """
        Generate realistic mock responses when API is not available.
        Responses vary based on company and product context.

        Args:
            task: The task description
            context: Context information

        Returns:
            Mock response string
        """
        agent_name = self.name


        company = context.get('company_name', 'Unknown Company')
        product = context.get('product_name', 'Unknown Product')

        # Generate company-specific variations
        import random
        company_hash = hash(company + product) % 1000
        random.seed(company_hash)

        if agent_name == "data_collector":
            # Vary data collection based on company
            base_records = 35 + (company_hash % 15)  # 35-50 records
            rating_variation = (company_hash % 20 - 10) / 100  # ±0.1 variation
            avg_rating = 3.5 + rating_variation

            return f'{{"total_records": {base_records}, "data_sources_processed": 3, "average_rating": {avg_rating:.1f}}}'

        elif agent_name == "sentiment_analyzer":
            # Vary sentiment based on company/product
            sentiment_options = ["mixed", "positive", "negative"]
            sentiment = sentiment_options[company_hash % len(sentiment_options)]

            score_variation = (company_hash % 40 - 20) / 100  # ±0.2 variation
            score = 0.2 + score_variation

            # Company-specific topics
            topic_sets = [
                ["performance", "user_interface", "pricing"],
                ["customer_support", "features", "reliability"],
                ["mobile_experience", "speed", "usability"],
                ["integration", "documentation", "scalability"]
            ]
            topics = topic_sets[company_hash % len(topic_sets)]

            # Vary emotions
            emotions = {
                "satisfaction": 0.3 + (company_hash % 30) / 100,
                "frustration": 0.2 + (company_hash % 25) / 100,
                "delight": 0.15 + (company_hash % 20) / 100,
                "confusion": 0.1 + (company_hash % 15) / 100
            }

            summary_templates = [
                f"Customer feedback shows {sentiment} sentiments with moderate satisfaction levels. Key concerns include {topics[0]} and {topics[1]}, while {topics[2]} receives generally positive feedback.",
                f"Analysis of {company}'s {product} shows {sentiment} overall sentiment. Customers appreciate {topics[2]} but struggle with {topics[0]} and {topics[1]} issues.",
                f"Feedback for {product} indicates {sentiment} sentiment with focus on {topics[0]}, {topics[1]}, and {topics[2]} aspects of the product."
            ]
            # PROPER CONFIDENCE CALCULATION BASED ON DATA QUALITY
            # Get actual sample size from context
            feedback_data = context.get('feedback_data', [])
            raw_data = context.get('raw_data', [])
            data_summary = context.get('data_summary', {})

            # Determine actual sample size
            if 'sample_size' in context:
                sample_size = context['sample_size']
            elif feedback_data:
                sample_size = len(feedback_data)
            elif raw_data:
                sample_size = len(raw_data)
            else:
                sample_size = data_summary.get('total_records', 40)

            # Base confidence on sample size
            if sample_size >= 100:
                base_confidence = 0.85
            elif sample_size >= 50:
                base_confidence = 0.75
            elif sample_size >= 20:
                base_confidence = 0.65
            else:
                base_confidence = 0.50

            # Adjust for sentiment consistency
            if sentiment == "mixed":
                consistency_adjustment = -0.10
            else:
                consistency_adjustment = 0.05

            # Final confidence
            confidence = base_confidence + consistency_adjustment
            confidence = max(0.40, min(0.95, confidence))
            confidence = round(confidence, 2)

            # Log for debugging
            self.logger.debug(f"Confidence calc: sample={sample_size}, base={base_confidence}, sentiment={sentiment}, adjustment={consistency_adjustment}, final={confidence}")

            # Summary with confidence indication
            confidence_level = "high" if confidence >= 0.75 else "moderate" if confidence >= 0.60 else "low"
            summary_templates = [
                f"Customer feedback shows {sentiment} sentiments with {confidence_level} confidence ({confidence:.0%}). Analysis based on {sample_size} feedback items. Key concerns include {topics[0]} and {topics[1]}, while {topics[2]} receives positive feedback.",
                f"Analysis of {company}'s {product} shows {sentiment} sentiment with {confidence:.0%} certainty from {sample_size} items. Customers appreciate {topics[2]} but struggle with {topics[0]} and {topics[1]}.",
                f"Feedback for {product} indicates {sentiment} sentiment (confidence: {confidence:.0%}) across {sample_size} data points on {topics[0]}, {topics[1]}, and {topics[2]}."
            ]
            summary = summary_templates[company_hash % len(summary_templates)]

            return f'''{{
                "overall_sentiment": "{sentiment}",
                "sentiment_score": {score:.2f},
                "emotions": {json.dumps(emotions)},
                "key_topics": {json.dumps(topics)},
                "confidence": {confidence},
                "sample_size": {sample_size},
                "analysis_summary": "{summary}"
            }}'''

        elif agent_name == "pattern_detector":
            # Vary patterns based on company
            pattern_types = ["pain_point", "feature_request", "bug_report", "usability_issue"]
            pattern1_type = pattern_types[company_hash % len(pattern_types)]
            pattern2_type = pattern_types[(company_hash + 1) % len(pattern_types)]

            # Company-specific pattern descriptions
            pattern_descriptions = {
                "pain_point": [
                    f"Customers frequently report slow loading times and performance issues with {product}",
                    f"Users struggle with complex navigation and confusing interface in {product}",
                    f"Pricing concerns and value proposition questions for {company}'s {product}"
                ],
                "feature_request": [
                    f"Multiple requests for mobile app improvements and responsive design for {product}",
                    f"Customers want better integration options and API access for {product}",
                    f"Feature requests for advanced analytics and reporting in {product}"
                ],
                "bug_report": [
                    f"Frequent crash reports and stability issues in {product}",
                    f"Data sync problems and consistency issues with {product}",
                    f"Login and authentication problems reported for {product}"
                ],
                "usability_issue": [
                    f"Complex user interface causing confusion with {product}",
                    f"Learning curve too steep for new users of {product}",
                    f"Mobile responsiveness issues with {product}"
                ]
            }

            pattern1_desc = pattern_descriptions[pattern1_type][company_hash % len(pattern_descriptions[pattern1_type])]
            pattern2_desc = pattern_descriptions[pattern2_type][(company_hash + 1) % len(pattern_descriptions[pattern2_type])]

            freq1 = 8 + (company_hash % 10)  # 8-18
            freq2 = 6 + ((company_hash + 3) % 8)  # 6-14

            return f'''{{
                "patterns": [
                    {{
                        "pattern_type": "{pattern1_type}",
                        "description": "{pattern1_desc}",
                        "frequency": {freq1},
                        "severity": "high",
                        "examples": ["Example issue 1", "Example issue 2"],
                        "business_impact": "Significant user impact",
                        "impact_score": {7.5 + (company_hash % 20) / 10:.1f}
                    }},
                    {{
                        "pattern_type": "{pattern2_type}",
                        "description": "{pattern2_desc}",
                        "frequency": {freq2},
                        "severity": "medium",
                        "examples": ["Feature request 1", "Feature request 2"],
                        "business_impact": "Enhancement opportunity",
                        "impact_score": {5.0 + (company_hash % 30) / 10:.1f}
                    }}
                ]
            }}'''

        elif agent_name == "opportunity_finder":
            # Generate 5-8 varied opportunities based on company context

            patterns = context.get('patterns', [])

            # Generate 5-8 opportunities with company-specific variations
            num_opportunities = 5 + (company_hash % 4)  # 5-8 opportunities
            opportunities = []

            # Diverse opportunity templates - company name and product integrated
            opportunity_templates = [
                {
                    "titles": [
                        f"Optimize {product} Performance and Scalability",
                        f"Enhance {product} Speed for {company} Users",
                        f"Improve {product} Response Times and Reliability",
                        f"Boost {product} System Efficiency"
                    ],
                    "descriptions": [
                        f"Address performance bottlenecks in {product} through targeted optimization",
                        f"Implement caching and database optimization for {product}",
                        f"Reduce latency and improve response times across {product}",
                        f"Scale {product} infrastructure to handle growing {company} user base"
                    ],
                    "category": "technical",
                    "priority": "high",
                    "base_impact": 8
                },
                {
                    "titles": [
                        f"Develop Advanced {product} Mobile Experience",
                        f"Build {product} Native Mobile Apps for {company}",
                        f"Enhance {product} Mobile Responsiveness",
                        f"Launch {product} iOS and Android Applications"
                    ],
                    "descriptions": [
                        f"Create dedicated mobile applications for {product} to improve user engagement",
                        f"Implement responsive design improvements for {product} mobile web",
                        f"Add offline capabilities to {product} mobile experience",
                        f"Optimize {product} for mobile-first {company} customers"
                    ],
                    "category": "product",
                    "priority": "high",
                    "base_impact": 7
                },
                {
                    "titles": [
                        f"Redesign {product} User Interface for {company}",
                        f"Modernize {product} User Experience",
                        f"Simplify {product} Navigation and Workflow",
                        f"Enhance {product} Visual Design and Usability"
                    ],
                    "descriptions": [
                        f"Conduct UX research and redesign {product} interface based on {company} user feedback",
                        f"Simplify complex workflows in {product} to reduce learning curve",
                        f"Implement modern design patterns to improve {product} aesthetics",
                        f"Improve information architecture in {product} for better discoverability"
                    ],
                    "category": "design",
                    "priority": "medium",
                    "base_impact": 6
                },
                {
                    "titles": [
                        f"Fix Critical {product} Stability Issues",
                        f"Resolve {product} Bug Backlog for {company}",
                        f"Eliminate {product} Crash Reports",
                        f"Address {product} Data Integrity Problems"
                    ],
                    "descriptions": [
                        f"Prioritize and fix high-severity bugs affecting {product} stability",
                        f"Implement comprehensive testing to prevent {product} regressions",
                        f"Address root causes of {product} crashes and errors",
                        f"Improve error handling and recovery in {product}"
                    ],
                    "category": "technical",
                    "priority": "high",
                    "base_impact": 9
                },
                {
                    "titles": [
                        f"Expand {product} Integration Ecosystem",
                        f"Build {product} API Platform for {company}",
                        f"Add Third-Party Integrations to {product}",
                        f"Enable {product} Webhook System"
                    ],
                    "descriptions": [
                        f"Develop comprehensive API documentation for {product} integrations",
                        f"Build integrations with popular tools used by {company} customers",
                        f"Create webhook system for real-time {product} data synchronization",
                        f"Enable Zapier/Make integrations for {product} workflow automation"
                    ],
                    "category": "product",
                    "priority": "medium",
                    "base_impact": 7
                },
                {
                    "titles": [
                        f"Strengthen {product} Security Infrastructure",
                        f"Implement {product} Advanced Authentication for {company}",
                        f"Enhance {product} Data Encryption",
                        f"Achieve {product} SOC 2 Compliance"
                    ],
                    "descriptions": [
                        f"Implement enterprise-grade security features in {product}",
                        f"Add multi-factor authentication and SSO to {product}",
                        f"Enhance data encryption at rest and in transit for {product}",
                        f"Complete security audits and compliance certifications for {product}"
                    ],
                    "category": "security",
                    "priority": "high",
                    "base_impact": 8
                },
                {
                    "titles": [
                        f"Improve {product} Onboarding Experience",
                        f"Create {product} Interactive Tutorials for {company}",
                        f"Enhance {product} Documentation and Help Center",
                        f"Build {product} Knowledge Base"
                    ],
                    "descriptions": [
                        f"Design interactive onboarding flow to reduce {product} time-to-value",
                        f"Create video tutorials and guides for {product} key features",
                        f"Improve help documentation based on {company} support tickets",
                        f"Implement in-app guidance and tooltips in {product}"
                    ],
                    "category": "support",
                    "priority": "medium",
                    "base_impact": 6
                },
                {
                    "titles": [
                        f"Add Advanced Analytics to {product}",
                        f"Build {product} Reporting Dashboard for {company}",
                        f"Implement {product} Data Export Features",
                        f"Create {product} Custom Report Builder"
                    ],
                    "descriptions": [
                        f"Develop comprehensive analytics dashboard for {product} users",
                        f"Add customizable reporting capabilities to {product}",
                        f"Enable data export in multiple formats from {product}",
                        f"Implement real-time metrics and KPI tracking in {product}"
                    ],
                    "category": "product",
                    "priority": "medium",
                    "base_impact": 7
                }
            ]

            # Generate unique opportunities
            for i in range(num_opportunities):
                template_idx = (company_hash + i * 17) % len(opportunity_templates)
                template = opportunity_templates[template_idx]

                # Select varied title and description
                title_idx = (company_hash + i * 7) % len(template["titles"])
                desc_idx = (company_hash + i * 11) % len(template["descriptions"])

                title = template["titles"][title_idx]
                description = template["descriptions"][desc_idx]

                # Vary impact scores (3-10 range)
                impact_variation = (company_hash + i * 13) % 5  # 0-4
                impact = template["base_impact"] + impact_variation - 2
                impact = max(3, min(10, impact))

                # Vary effort based on impact
                if impact >= 8:
                    effort_options = ["medium", "large", "large"]
                elif impact >= 6:
                    effort_options = ["small", "medium", "medium"]
                else:
                    effort_options = ["small", "small", "medium"]
                effort = effort_options[(company_hash + i) % len(effort_options)]

                # Vary timeline
                timeline_options = ["immediate", "short-term", "short-term", "long-term"]
                timeline = timeline_options[(company_hash + i * 19) % len(timeline_options)]

                # Calculate priority based on impact and effort
                if impact >= 8 and effort in ["small", "medium"]:
                    priority = "high"
                elif impact >= 6:
                    priority = "medium"
                else:
                    priority = "low"

                # Build supporting data from patterns if available
                supporting_data = []
                if patterns and i < len(patterns):
                    supporting_data.append(patterns[i].get("description", "Customer feedback pattern")[:80])
                else:
                    supporting_data.append(f"{company} customer feedback analysis #{i+1}")

                opportunities.append({
                    "title": title,
                    "description": description,
                    "category": template["category"],
                    "priority": priority,
                    "impact_score": impact,
                    "effort_estimate": effort,
                    "timeline": timeline,
                    "supporting_data": supporting_data,
                    "expected_outcome": f"Enhanced {product} experience for {company} customers",
                    "success_metrics": ["user satisfaction score", "engagement rate", "feature adoption"],
                    "risks": ["resource constraints", "timeline pressure"]
                })

            return json.dumps({"opportunities": opportunities})

        elif agent_name == "strategy_creator":
            # Get actual context for company-specific strategy
            patterns = context.get('patterns', [])
            opportunities = context.get('opportunities', [])
            sentiment_results = context.get('sentiment_results', {})

            self.logger.info(f"Strategy creator mock: {len(opportunities)} opportunities, {len(patterns)} patterns")

            # CRITICAL FIX: Generate 5-8 recommendations, not just 2
            # Use ALL opportunities, not just first 2
            num_recommendations = min(len(opportunities), 5 + (company_hash % 4))  # 5-8 recommendations

            recommendations = []

            for i, opp in enumerate(opportunities[:num_recommendations]):
                category = opp.get('category', 'product')
                title = opp.get('title', 'Improvement initiative')
                description = opp.get('description', '')
                impact = opp.get('impact_score', 5)
                effort = opp.get('effort_estimate', 'medium')
                timeline = opp.get('timeline', 'short-term')

                # Map category to owner
                owner_map = {
                    "technical": "Engineering Team",
                    "product": "Product Team",
                    "design": "Design Team",
                    "support": "Customer Success Team",
                    "security": "Security Team",
                    "marketing": "Marketing Team"
                }
                owner = owner_map.get(category, "Product Team")

                # Create specific action incorporating company/product
                action = f"{title}"  # Keep original title

                # Enhanced rationale with company context
                rationale = f"{description} This addresses critical needs identified in {company}'s customer feedback analysis and will significantly improve {product} user satisfaction."

                # Impact statement based on score
                if impact >= 8:
                    expected_impact = f"High impact - Will significantly improve user satisfaction and reduce churn for {company} customers. Expected to drive measurable improvements in key metrics."
                elif impact >= 6:
                    expected_impact = f"Medium impact - Notable enhancement to {product} functionality and user experience. Will address common pain points reported by {company} users."
                else:
                    expected_impact = f"Incremental impact - Steady improvement to {product} capabilities. Contributes to overall platform quality for {company}."

                # Success metrics
                metrics = [
                    "User satisfaction score (NPS)",
                    "Feature adoption rate",
                    "Customer retention improvement",
                    "Support ticket reduction"
                ]

                # Dependencies
                dependencies = [
                    f"{owner} capacity and resources",
                    "Technical infrastructure readiness",
                    "User research and validation",
                    "Stakeholder alignment"
                ]

                # Risks based on effort
                risk_map = {
                    "small": ["Timeline pressure", "Resource availability"],
                    "medium": ["Scope creep risk", "Integration complexity", "User adoption challenges"],
                    "large": ["Technical complexity", "Extended timeline", "Budget constraints", "Change management"]
                }
                risks = risk_map.get(effort, ["Implementation challenges", "Resource constraints"])

                # Priority decreases for each subsequent recommendation
                priority = max(1, 10 - i)
                if impact >= 8:
                    priority = min(10, priority + 1)  # Boost high-impact items

                recommendations.append({
                    "category": category,
                    "action": action,
                    "rationale": rationale,
                    "expected_impact": expected_impact,
                    "timeline": timeline,
                    "priority": priority,
                    "effort_level": effort,
                    "success_metrics": metrics[:3],
                    "dependencies": dependencies[:3],
                    "risks": risks[:3],
                    "owner": owner
                })

            # CRITICAL FIX: Data-driven executive summary, not generic templates
            sentiment = sentiment_results.get('overall_sentiment', 'mixed')
            confidence = sentiment_results.get('confidence', 0.75)
            sentiment_score = sentiment_results.get('sentiment_score', 0.0)

            # Get actual insights from data
            num_patterns = len(patterns)
            num_opportunities = len(opportunities)

            # Extract real issues from patterns
            critical_issues = []
            for pattern in patterns[:3]:
                if pattern.get('severity') in ['critical', 'high']:
                    desc = pattern.get('description', '')
                    if desc:
                        # Get first meaningful phrase (up to 60 chars)
                        critical_issues.append(desc[:60].strip())

            # Get top opportunity titles
            top_opportunity_titles = [opp.get('title', '') for opp in opportunities[:3]]

            # Build sentiment phrase
            if sentiment == "positive":
                sentiment_phrase = f"positive customer sentiment (score: {sentiment_score:.2f}, confidence: {confidence:.0%})"
                outlook = "Strong foundation for continued growth"
            elif sentiment == "negative":
                sentiment_phrase = f"concerning negative feedback (score: {sentiment_score:.2f}, confidence: {confidence:.0%})"
                outlook = "Urgent action required to address customer concerns"
            else:
                sentiment_phrase = f"mixed customer sentiment (score: {sentiment_score:.2f}, confidence: {confidence:.0%})"
                outlook = "Balanced approach needed to address varying customer needs"

            # Priority areas from recommendations
            high_priority = sum(1 for r in recommendations if r['priority'] >= 8)
            immediate = sum(1 for r in recommendations if r['timeline'] == 'immediate')

            # CONSTRUCT DATA-DRIVEN EXECUTIVE SUMMARY
            executive_summary = f"""Customer intelligence analysis for {company}'s {product} reveals {sentiment_phrase}.



Our analysis identified {num_patterns} distinct patterns across customer feedback, leading to {num_opportunities} strategic opportunities for improvement. {outlook}.



Key findings include: {'. '.join(critical_issues[:2]) if critical_issues else 'performance optimization needs and user experience enhancements'}. These insights directly inform our strategic recommendations.



Priority initiatives: {', '.join(top_opportunity_titles[:3]) if top_opportunity_titles else 'system improvements and feature development'}. We recommend {len(recommendations)} specific actions, with {high_priority} high-priority items requiring immediate attention.



Implementation of these recommendations will directly address validated customer pain points and drive measurable improvements in satisfaction, retention, and product-market fit for {company}."""

            # Implementation roadmap
            roadmap = {
                "phase_1_immediate": [
                    f"Launch critical fixes for {product} ({immediate} immediate actions identified)",
                    f"Deploy quick wins to address top customer pain points",
                    f"Establish metrics tracking for {company} customer satisfaction"
                ],
                "phase_2_short_term": [
                    f"Roll out {product} core improvements (30-90 days)",
                    f"Implement top {min(3, len(recommendations))} priority recommendations",
                    f"Integrate continuous feedback mechanisms"
                ],
                "phase_3_long_term": [
                    f"Complete {product} strategic transformation (90+ days)",
                    f"Scale successful initiatives across {company} platform",
                    f"Build advanced capabilities based on validated market demand"
                ],
                "key_milestones": [
                    f"Week 4: Critical {product} improvements deployed to {company} users",
                    f"Week 12: Major feature updates and optimizations completed",
                    f"Week 24: Full strategic roadmap delivered and validated"
                ],
                "resource_requirements": [
                    recommendations[0]['owner'] if recommendations else "Product Team",
                    "Engineering resources (2-3 full-time developers)",
                    "Design and UX support (1 designer)",
                    "QA and testing resources",
                    "Project management and coordination"
                ]
            }

            self.logger.info(f"Generated {len(recommendations)} recommendations for {company}")

            return json.dumps({
                "recommendations": recommendations,
                "executive_summary": executive_summary,
                "implementation_roadmap": roadmap,
                "total_recommendations": len(recommendations),
                "high_priority_count": high_priority,
                "immediate_actions": immediate,
                "estimated_timeline": "12-24 weeks for comprehensive implementation",
                "success_probability": "High - based on validated customer feedback and clear priorities"
            })

        else:
            return f"Mock response for {agent_name}: Task completed successfully with sample data."

    def _format_task(self, task: str, context: Dict[str, Any]) -> str:
        """
        Format a task with context information for better Claude understanding.

        Args:
            task: The raw task description
            context: Dictionary containing context information

        Returns:
            Formatted task string with context
        """
        formatted_parts = [f"Task: {task}"]

        # Add relevant context information
        if "company_name" in context:
            formatted_parts.append(f"Company: {context['company_name']}")
        if "product_name" in context:
            formatted_parts.append(f"Product: {context['product_name']}")
        if "data_sources" in context:
            formatted_parts.append(f"Data Sources: {', '.join(context['data_sources'])}")
        if "current_step" in context:
            formatted_parts.append(f"Current Pipeline Step: {context['current_step']}")

        # Add any additional context that's relevant
        additional_context = []
        for key, value in context.items():
            if key not in ["company_name", "product_name", "data_sources", "current_step", "errors"] and value:
                if isinstance(value, (list, dict)):
                    additional_context.append(f"{key}: {str(value)[:200]}...")
                else:
                    additional_context.append(f"{key}: {value}")

        if additional_context:
            formatted_parts.append("Additional Context:")
            formatted_parts.extend(f"- {item}" for item in additional_context[:5])  # Limit to 5 items

        return "\n\n".join(formatted_parts)

    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method that each agent must implement.

        Takes the current workflow state, performs the agent's specific processing,
        and returns the updated state with results.

        Args:
            state: Current workflow state dictionary

        Returns:
            Updated workflow state dictionary with agent results
        """
        pass
