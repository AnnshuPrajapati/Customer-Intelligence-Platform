# Customer Intelligence & Strategy Platform 🚀

*A multi-agent system built with LangGraph and AI that analyzes customer feedback and generates strategic insights.*

## 🌟 Features

- **Multi-Agent AI Pipeline**: Data Collection → Sentiment Analysis → Pattern Detection → Opportunity Finding → Strategy Generation
- **Multiple AI Providers**: Gemini (Google, free tier), GPT-4 (OpenAI), Claude (Anthropic), Ollama (Local)
- **Advanced Evaluation**: Hallucination detection, coverage metrics, actionability scores
- **Beautiful Web Interface**: Streamlit app for easy deployment
- **Comprehensive Reports**: Markdown reports with executive summaries
- **Enterprise-Ready**: Error handling, logging, monitoring, scalability

## 🚀 Quick Start (3 Options)

### Option 1: FREE Gemini Deployment (Recommended)

```bash
# 1. Clone and setup
git clone <repo-url>
cd customer-intelligence-platform

# 2. Run Gemini deployment script
python deploy_gemini.py

# 3. Follow prompts to get FREE Gemini API key
# 4. Run the analysis
python -m src.main --company "YourCompany" --product "YourProduct"
```

**Gemini Benefits:**
- ✅ **FREE tier**: 60 requests/minute, 1M tokens/month
- ✅ **No credit card** required
- ✅ **Google account** sign-in only
- ✅ **Reliable** and fast responses

### Option 2: Web App Deployment

```bash
# Install with web interface
pip install -r requirements.txt

# Get Gemini API key from: https://makersuite.google.com/app/apikey
# Add to .env: GOOGLE_API_KEY=your_key_here

# Run web app
streamlit run app.py

# Open browser to localhost:8501
```

### Option 3: Demo Mode (No API Required)

```bash
# Run with realistic mock responses
python demo.py

# Or use setup script
python setup.py
python demo.py
```

## 📊 What You Get

### 1. Customer Sentiment Analysis
```
💭 Overall Sentiment: POSITIVE (Score: 0.73)
   Key Topics: performance, user_interface, pricing
   Emotions: satisfaction (40%), delight (20%), confusion (10%)
```

### 2. Pattern Detection
```
🔎 Patterns Found: 12
   • Performance Issues (freq: 15, severity: high)
   • UI Navigation Problems (freq: 8, severity: medium)
   • Feature Requests (freq: 12, severity: medium)
```

### 3. Business Opportunities
```
💡 Top Opportunities:
   1. Performance Optimization Initiative (Impact: 9/10)
   2. Mobile Experience Enhancement (Impact: 7/10)
   3. User Interface Redesign (Impact: 8/10)
```

### 4. Strategic Recommendations
```
📊 Executive Summary:
Customer intelligence analysis reveals that performance optimization and mobile experience
improvements are critical priorities. The data shows consistent feedback about slow loading
times and mobile usability issues. Implementing these recommendations will drive significant
customer satisfaction improvements.
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Collector │ -> │ Sentiment Agent  │ -> │ Pattern Agent   │
│                 │    │                 │    │                 │
│ • Reviews       │    │ • Claude/GPT-4  │    │ • Theme Analysis │
│ • Support       │    │ • Emotions      │    │ • Pain Points    │
│ • Surveys       │    │ • Topics        │    │ • Trends         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌─────────────────┐         │
│ Opportunity     │ <- │  Strategy       │ <--------┘
│ Finder Agent    │    │  Creator Agent  │
│                 │    │                 │
│ • Business      │    │ • Executive     │
│   Opportunities │    │   Summary       │
│ • Impact Scores │    │ • Action Plan   │
└─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Choose your AI provider
GOOGLE_API_KEY=your_gemini_key_here        # FREE tier available
OPENAI_API_KEY=your_gpt4_key_here          # $5 free credits
ANTHROPIC_API_KEY=your_claude_key_here     # Optional - paid, high quality

# Application settings
LOG_LEVEL=INFO
MAX_ITERATIONS=3
```

### Sample Data Included

- **15 Customer Reviews**: Amazon, Best Buy, etc. (1-5 star ratings)
- **15 Support Tickets**: Various categories and priorities
- **10 Survey Responses**: NPS scores and open feedback

## 📈 Advanced Features

### Performance Metrics
- **Latency Tracking**: Agent execution times
- **Success Rates**: Completion percentages
- **Error Monitoring**: Failure analysis

### Quality Evaluation
- **Hallucination Detection**: Prevents AI fabrications
- **Coverage Analysis**: % of customer issues addressed
- **Actionability Scoring**: Feasibility of recommendations

### Business Impact
- **ROI Estimation**: Expected return on investments
- **Customer Satisfaction**: Predicted improvements
- **Priority Scoring**: Impact vs effort analysis

## 🚀 Deployment Options

### 1. Local Development
```bash
python -m src.main --company "Tesla" --product "Electric Vehicles"
```

### 2. Web Application
```bash
streamlit run app.py
# Access at http://localhost:8501
```

### 3. Docker Deployment
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### 4. Cloud Deployment (RECOMMENDED: Railway)
- **Railway**: ⭐ **Easiest & Most Reliable** - See `DEPLOY_RAILWAY.md`
- **Streamlit Cloud**: Free tier available
- **Heroku**: Easy Python deployment
- **Vercel**: For web interface

## 🎯 Use Cases

### Customer Success Teams
- Identify pain points before they escalate
- Proactively address customer needs
- Measure satisfaction improvements

### Product Teams
- Validate feature priorities with real data
- Discover unmet customer needs
- Guide product roadmap decisions

### Support Teams
- Categorize and prioritize tickets
- Identify common resolution patterns
- Improve first-call resolution rates

### Executive Leadership
- Data-driven strategic decisions
- Customer-centric business planning
- ROI-focused investment decisions

## 🔍 API Provider Comparison

| Provider | Cost | Quality | Speed | Free Tier |
|----------|------|---------|-------|-----------|
| **Gemini** | FREE | Excellent | Fast | 1M tokens/month |
| GPT-4 | $0.0015/1K | Excellent | Fast | $5 credits |
| Claude | $0.003/1K | Best | Fast | None |
| Ollama | FREE | Good | Variable | Unlimited |

## 📋 Troubleshooting

### Common Issues

**"No API key found"**
```bash
# Add to .env file
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"Connection timeout"**
- Check internet connection
- Verify API key is correct
- Try different AI provider

### Debug Mode
```bash
# Enable detailed logging
LOG_LEVEL=DEBUG python -m src.main --company "Test"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - feel free to use commercially!

---

## 🎉 Getting Started

**Ready to analyze customer feedback?**

```bash
# 1. Get FREE Gemini API key
python deploy_gemini.py

# 2. Run your first analysis
python -m src.main --company "YourCompany" --product "YourProduct"

# 3. View beautiful reports in data/output/
```

**Transform customer feedback into strategic business decisions!** 🚀✨