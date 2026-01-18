# 🤝 Contributing to Customer Intelligence Platform

Thank you for your interest in contributing! This document provides guidelines for contributing to the Customer Intelligence Platform.

## 🚀 Quick Start for Contributors

### 1. Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/customer-intelligence-platform.git
cd customer-intelligence-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_sentiment_analyzer.py

# Run tests in watch mode
pytest-watch
```

### 3. Code Quality Checks

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/

# Security check
bandit -r src/
```

### 4. Local Development

```bash
# Run the application locally
streamlit run app.py

# Run with debug logging
LOG_LEVEL=DEBUG streamlit run app.py

# Run demo mode (no API keys needed)
python demo.py
```

## 📋 Development Workflow

### 1. Choose an Issue
- Check the [Issues](https://github.com/yourusername/customer-intelligence-platform/issues) page
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Feature Branch
```bash
# Create and switch to new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

### 3. Make Changes
- Follow the [code style guidelines](#code-style)
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Commit Changes
```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add sentiment analysis confidence scoring

- Add statistical confidence calculation based on sample size
- Include sentiment consistency factor in scoring
- Update mock data generator to use realistic confidence ranges
- Add tests for confidence calculation logic"

# Push to your branch
git push origin feature/your-feature-name
```

### 5. Create Pull Request
- Go to GitHub and create a Pull Request
- Fill out the PR template
- Link to the issue you're solving
- Request review from maintainers

## 🎯 Code Style Guidelines

### Python Style
- Follow [PEP 8](https://pep8.org/) standards
- Use [Black](https://black.readthedocs.io/) for code formatting
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names
- Add docstrings to all functions and classes

### Type Hints
```python
# Good
def analyze_sentiment(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze sentiment of input text."""

# Avoid
def analyze_sentiment(text, config):
    # No type hints
```

### Error Handling
```python
# Good
try:
    result = llm_provider.invoke(prompt)
    validate_response(result)
    return result
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise LLMProviderError(f"Failed to get response: {e}") from e
except ValidationError as e:
    logger.error(f"Response validation failed: {e}")
    return generate_fallback_response()

# Avoid
# Generic exception handling
try:
    # code
except Exception as e:
    pass  # Silent failures
```

### Logging
```python
import structlog

logger = structlog.get_logger()

# Good
logger.info(
    "agent_completed",
    agent_name="sentiment_analyzer",
    execution_time=1.23,
    records_processed=45,
    confidence_score=0.78
)

# Avoid
print(f"Processing complete: {result}")  # No structured logging
```

## 🧪 Testing Guidelines

### Unit Tests
```python
# tests/test_sentiment_analyzer.py
import pytest
from src.agents.sentiment_analyzer import SentimentAnalyzerAgent

class TestSentimentAnalyzer:
    def test_positive_sentiment_detection(self):
        agent = SentimentAnalyzerAgent()
        result = agent.process("This product is amazing!")

        assert result["sentiment_score"] > 0.5
        assert result["overall_sentiment"] == "positive"
        assert 0.65 <= result["confidence"] <= 0.95

    def test_confidence_calculation(self):
        # Test confidence based on sample size
        assert calculate_confidence(10) < calculate_confidence(100)
        assert calculate_confidence(100) >= 0.85
```

### Integration Tests
```python
# tests/test_workflow_integration.py
def test_full_analysis_workflow():
    """Test complete analysis pipeline"""

    state = WorkflowState(
        company_name="TestCompany",
        product_name="TestProduct",
        data_sources=["reviews"]
    )

    result = orchestrator.run(state)

    # Validate all components completed
    assert result["sentiment_results"] is not None
    assert len(result["patterns"]) > 0
    assert len(result["opportunities"]) >= 3
    assert result["executive_summary"] is not None

    # Validate data consistency
    assert result["sentiment_results"]["sample_size"] == len(result["raw_data"])
```

### Mock Data Guidelines
```python
# Use realistic mock data for testing
def generate_mock_feedback(company: str, product: str) -> List[Dict]:
    """Generate realistic test data"""

    return [
        {
            "text": f"I love using {product} for my business needs",
            "rating": 5,
            "source": "review",
            "date": "2024-01-15"
        },
        {
            "text": f"{product} has some performance issues that need fixing",
            "rating": 3,
            "source": "ticket",
            "date": "2024-01-10"
        }
    ]
```

## 📚 Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints in docstrings when helpful

```python
def calculate_confidence(
    sample_size: int,
    consistency_score: float,
    data_quality: float = 0.8
) -> float:
    """Calculate confidence score for sentiment analysis.

    Args:
        sample_size: Number of feedback items analyzed
        consistency_score: Sentiment consistency (0-1 scale)
        data_quality: Data completeness score (0-1 scale)

    Returns:
        Confidence score between 0.40 and 0.95

    Raises:
        ValueError: If inputs are outside valid ranges

    Example:
        >>> calculate_confidence(50, 0.8, 0.9)
        0.82
    """
```

### README Updates
- Update README.md for new features
- Add examples to docs/FEATURES.md
- Update API documentation
- Include performance benchmarks

## 🔧 Development Tools

### Recommended VS Code Extensions
- Python
- Pylance
- Black Formatter
- Flake8
- Python Test Explorer
- GitLens

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
```

### Docker Development
```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install development dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

# Copy source code
COPY . .

# Run tests by default
CMD ["pytest"]
```

## 🚨 Issue Reporting

### Bug Reports
When reporting bugs, please include:
- **Description**: Clear description of the issue
- **Steps to reproduce**: Step-by-step instructions
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: Python version, OS, dependencies
- **Logs**: Relevant log output
- **Screenshots**: If applicable

### Feature Requests
For feature requests, please include:
- **Problem**: What problem are you trying to solve?
- **Solution**: Describe your proposed solution
- **Alternatives**: Have you considered alternatives?
- **Use case**: How would this feature be used?

## 📋 Pull Request Process

### PR Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Self-review completed
- [ ] No sensitive information committed

### PR Template
```
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass
- [ ] Ready for review
```

## 🎉 Recognition

Contributors will be recognized in:
- **README.md**: Contributors section
- **GitHub**: Repository contributors
- **Release notes**: Feature attributions
- **Documentation**: Credits section

## 📞 Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Documentation**: Check docs/ folder first
- **Community**: Join our Discord/Slack (if available)

Thank you for contributing to the Customer Intelligence Platform! 🚀
