"""
Base Agent class for the Customer Intelligence Platform.

This module defines the abstract base class that all specialized agents must inherit from.
Provides common functionality including Claude LLM integration, logging, and error handling.
"""

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

        Supports: Anthropic Claude → OpenAI GPT-4 → Google Gemini → Ollama → Mock fallback

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
        Initialize LLM with fallback chain: Claude → GPT-4 → Gemini → Ollama → Mock

        Returns:
            Tuple of (llm_instance, provider_name)
        """
        import os

        # 1. Try Anthropic Claude (most expensive but best quality)
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            try:
                llm = ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    temperature=self.temperature,
                    max_tokens=4096
                )
                # Test the connection
                llm.invoke("test")
                return llm, "Anthropic Claude"
            except Exception as e:
                self.logger.warning(f"Claude initialization failed: {e}")

        # 2. Try OpenAI GPT-4 (very affordable, great quality)
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                llm = ChatOpenAI(
                    model="gpt-4o-mini",  # Cheapest GPT-4 model
                    temperature=self.temperature,
                    max_tokens=4096
                )
                # Test the connection
                llm.invoke("test")
                return llm, "OpenAI GPT-4"
            except Exception as e:
                self.logger.warning(f"GPT-4 initialization failed: {e}")

        # 3. Try Google Gemini (new SDK - preferred)
        if GOOGLE_GENAI_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            try:
                # Configure the new Google GenAI client
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

                # Test the connection
                client = genai.Client()
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents="Test connection"
                )

                # Return a wrapper that uses the new API
                return GeminiWrapper(client), "Google Gemini (New API)"
            except Exception as e:
                self.logger.warning(f"New Gemini API failed: {e}")

        # 4. Try Google Gemini (LangChain fallback)
        if GOOGLE_LANGCHAIN_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            try:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",  # Fast and free tier
                    temperature=self.temperature,
                    max_tokens=4096
                )
                # Test the connection
                llm.invoke("test")
                return llm, "Google Gemini (LangChain)"
            except Exception as e:
                self.logger.warning(f"Gemini LangChain fallback failed: {e}")

        # 4. Try Ollama (completely free, local models)
        if OLLAMA_AVAILABLE:
            try:
                llm = ChatOllama(
                    model="llama3.1",  # Free local model
                    temperature=self.temperature
                )
                # Test the connection
                llm.invoke("test")
                return llm, "Ollama Local"
            except Exception as e:
                self.logger.warning(f"Ollama initialization failed: {e}")

        # 5. Fallback to mock mode (completely free)
        self.logger.warning(f"No LLM providers available, using mock mode for agent '{self.name}'")
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
            summary = summary_templates[company_hash % len(summary_templates)]

            return f'''{{
                "overall_sentiment": "{sentiment}",
                "sentiment_score": {score:.1f},
                "emotions": {json.dumps(emotions)},
                "key_topics": {json.dumps(topics)},
                "confidence": 0.75,
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
            # Generate opportunities based on detected patterns
            patterns = context.get('patterns', [])
            if not patterns:
                patterns = [
                    {"pattern_type": "pain_point", "description": "Performance issues"},
                    {"pattern_type": "feature_request", "description": "Mobile improvements"}
                ]

            opportunities = []
            for i, pattern in enumerate(patterns[:2]):  # Use up to 2 patterns
                if pattern["pattern_type"] == "pain_point":
                    title = "Performance Optimization Initiative"
                    description = f"Address {pattern['description'].lower()} through targeted optimizations"
                    category = "technical"
                    priority = "high"
                    impact = 8 + (company_hash % 3)  # 8-10
                elif pattern["pattern_type"] == "feature_request":
                    title = "Feature Enhancement Program"
                    description = f"Implement requested {pattern['description'].lower()} to improve user experience"
                    category = "product"
                    priority = "medium"
                    impact = 6 + (company_hash % 3)  # 6-8
                elif pattern["pattern_type"] == "bug_report":
                    title = "Stability Improvement Project"
                    description = f"Fix reported {pattern['description'].lower()} to improve reliability"
                    category = "technical"
                    priority = "high"
                    impact = 7 + (company_hash % 4)  # 7-10
                else:
                    title = "User Experience Enhancement"
                    description = f"Improve {pattern['description'].lower()} based on user feedback"
                    category = "product"
                    priority = "medium"
                    impact = 5 + (company_hash % 4)  # 5-8

                opportunities.append({
                    "title": title,
                    "description": description,
                    "category": category,
                    "priority": priority,
                    "impact_score": impact,
                    "effort_estimate": "medium",
                    "timeline": "short-term",
                    "supporting_data": [pattern["description"][:50] + "..."],
                    "expected_outcome": f"Improved user experience for {company}'s {product}",
                    "success_metrics": ["user satisfaction", "engagement metrics"],
                    "priority_score": impact / 2
                })

            return json.dumps({"opportunities": opportunities})

        elif agent_name == "strategy_creator":
            # Generate strategy based on patterns and opportunities
            patterns = context.get('patterns', [])
            opportunities = context.get('opportunities', [])

            recommendations = []
            for i, opp in enumerate(opportunities[:2]):  # Use up to 2 opportunities
                priority = 8 + (company_hash % 3) - i  # High priority for first, slightly lower for second
                timeline_options = ["immediate", "short-term", "medium-term"]
                timeline = timeline_options[(company_hash + i) % len(timeline_options)]

                category = opp.get('category', 'technical')
                action = opp.get('title', 'Improvement initiative')
                rationale = opp.get('description', 'Based on customer feedback analysis')

                if category == "technical":
                    owner = "Engineering Team"
                    dependencies = ["engineering team availability", "technical resources"]
                    risks = ["complex technical challenges", "integration issues"]
                    metrics = ["performance metrics", "user satisfaction scores"]
                else:
                    owner = "Product Team"
                    dependencies = ["design team resources", "user research"]
                    risks = ["scope creep", "timeline delays"]
                    metrics = ["user engagement", "feature adoption rates"]

                recommendations.append({
                    "category": category,
                    "action": f"Implement {action.lower()} for {product}",
                    "rationale": f"{rationale} - critical feedback from {company} customers",
                    "expected_impact": opp.get('expected_outcome', 'Improve user experience'),
                    "timeline": timeline,
                    "priority": priority,
                    "effort_level": "medium",
                    "success_metrics": metrics,
                    "dependencies": dependencies,
                    "risks": risks,
                    "owner": owner
                })

            # Generate company-specific executive summary
            summary_templates = [
                f"Customer intelligence analysis for {company}'s {product} reveals critical priorities in performance and user experience. The data shows consistent feedback about key issues that need immediate attention. Implementing these recommendations will address the most impactful customer pain points.",
                f"Analysis of {company} customer feedback indicates that {product} requires focused improvements in user experience and technical performance. The insights provide clear direction for enhancing customer satisfaction and driving business growth.",
                f"Strategic review of {product} feedback shows opportunities for significant improvements in user satisfaction and product quality. The recommended actions prioritize high-impact changes that will directly address customer needs."
            ]
            executive_summary = summary_templates[company_hash % len(summary_templates)]

            # Generate implementation roadmap
            roadmap = {
                "phase_1_immediate": ["Critical issue assessment", "Quick wins implementation"],
                "phase_2_short_term": [f"{product} core improvements", "User feedback integration"],
                "phase_3_long_term": ["Advanced features", "Scalability enhancements"],
                "key_milestones": ["Initial improvements deployed", "Major updates completed"],
                "resource_requirements": ["Engineering team", "Product team", "Design resources"]
            }

            return json.dumps({
                "recommendations": recommendations,
                "executive_summary": executive_summary,
                "implementation_roadmap": roadmap
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
