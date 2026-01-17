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

        Args:
            task: The task description
            context: Context information

        Returns:
            Mock response string
        """
        agent_name = self.name

        if agent_name == "data_collector":
            return '{"total_records": 45, "data_sources_processed": 3, "average_rating": 3.8}'

        elif agent_name == "sentiment_analyzer":
            return '''{
                "overall_sentiment": "mixed",
                "sentiment_score": 0.2,
                "emotions": {
                    "satisfaction": 0.4,
                    "frustration": 0.3,
                    "delight": 0.2,
                    "confusion": 0.1
                },
                "key_topics": ["performance", "user_interface", "pricing"],
                "confidence": 0.75,
                "analysis_summary": "Customer feedback shows mixed sentiments with moderate satisfaction levels. Key concerns include performance and user interface, while pricing receives generally positive feedback."
            }'''

        elif agent_name == "pattern_detector":
            return '''{
                "patterns": [
                    {
                        "pattern_type": "pain_point",
                        "description": "Customers frequently report slow loading times and performance issues",
                        "frequency": 12,
                        "severity": "high",
                        "examples": ["App takes forever to load", "Performance is terrible on mobile"],
                        "business_impact": "High user frustration leading to potential churn",
                        "impact_score": 8.5
                    },
                    {
                        "pattern_type": "feature_request",
                        "description": "Multiple requests for dark mode and mobile app improvements",
                        "frequency": 8,
                        "severity": "medium",
                        "examples": ["Please add dark mode", "Mobile app needs better navigation"],
                        "business_impact": "Enhancing user experience and modern features",
                        "impact_score": 6.2
                    }
                ]
            }'''

        elif agent_name == "opportunity_finder":
            return '''{
                "opportunities": [
                    {
                        "title": "Performance Optimization Initiative",
                        "description": "Address loading time and performance complaints through targeted optimizations",
                        "category": "technical",
                        "priority": "high",
                        "impact_score": 9,
                        "effort_estimate": "medium",
                        "timeline": "short-term",
                        "supporting_data": ["performance complaints", "loading time feedback"],
                        "expected_outcome": "Improved user satisfaction and reduced churn",
                        "success_metrics": ["page load time reduction", "user satisfaction increase"],
                        "priority_score": 4.5
                    },
                    {
                        "title": "Mobile Experience Enhancement",
                        "description": "Improve mobile app navigation and user interface based on feedback",
                        "category": "product",
                        "priority": "medium",
                        "impact_score": 7,
                        "effort_estimate": "medium",
                        "timeline": "short-term",
                        "supporting_data": ["mobile navigation issues", "UI improvement requests"],
                        "expected_outcome": "Better mobile user experience and engagement",
                        "success_metrics": ["mobile session duration", "app store ratings"],
                        "priority_score": 3.5
                    }
                ]
            }'''

        elif agent_name == "strategy_creator":
            return '''{
                "recommendations": [
                    {
                        "category": "technical",
                        "action": "Implement performance optimization plan focusing on loading times",
                        "rationale": "Performance issues are the most frequent complaint and highest impact area",
                        "expected_impact": "Reduce user frustration and improve retention rates",
                        "timeline": "immediate",
                        "priority": 9,
                        "effort_level": "medium",
                        "success_metrics": ["page load time < 2s", "user satisfaction > 4.0"],
                        "dependencies": ["engineering team availability"],
                        "risks": ["complex technical challenges"],
                        "owner": "Engineering Team"
                    },
                    {
                        "category": "product",
                        "action": "Launch mobile app redesign project",
                        "rationale": "Mobile experience feedback indicates significant usability issues",
                        "expected_impact": "Improve mobile user engagement and satisfaction",
                        "timeline": "short-term",
                        "priority": 7,
                        "effort_level": "high",
                        "success_metrics": ["mobile retention rate", "app store rating improvement"],
                        "dependencies": ["design team resources", "user testing"],
                        "risks": ["scope creep", "timeline delays"],
                        "owner": "Product Team"
                    }
                ],
                "executive_summary": "Customer intelligence analysis reveals that performance optimization and mobile experience improvements are critical priorities. The data shows consistent feedback about slow loading times and mobile usability issues. Implementing these recommendations will address the most impactful customer pain points and drive significant improvements in user satisfaction and retention.",
                "implementation_roadmap": {
                    "phase_1_immediate": ["Performance audit and optimization plan"],
                    "phase_2_short_term": ["Mobile redesign kickoff", "Performance improvements deployment"],
                    "phase_3_long_term": ["Advanced mobile features", "Performance monitoring system"],
                    "key_milestones": ["Performance improvements live", "Mobile redesign completed"],
                    "resource_requirements": ["Engineering team", "Design team", "QA resources"]
                }
            }'''

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
