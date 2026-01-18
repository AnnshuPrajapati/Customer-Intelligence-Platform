# 🚀 Deployment Guide

## Quick Deploy Options

### Option 1: Railway (Recommended - 5 minutes)

**Railway provides free tier with custom domains and SSL**

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Link to existing project (or create new)
railway link

# 4. Set environment variables
railway variables set GOOGLE_API_KEY=your_gemini_api_key_here

# 5. Deploy
railway up

# 6. Get your URL
railway domain
```

**Railway Benefits:**
- ✅ **Free tier**: 512MB RAM, 1GB storage
- ✅ **Custom domains** with SSL
- ✅ **Environment management**
- ✅ **Logs and monitoring**
- ✅ **Auto-scaling**

### Option 2: Streamlit Cloud (Free)

**Deploy directly from GitHub**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Select `app.py` as main file
4. Add secrets: `GOOGLE_API_KEY`
5. Deploy

**Streamlit Cloud Benefits:**
- ✅ **Free tier** available
- ✅ **GitHub integration**
- ✅ **Automatic deployments**
- ✅ **Shareable links**

### Option 3: Heroku (Paid)

```bash
# 1. Install Heroku CLI
# Download from heroku.com

# 2. Login
heroku login

# 3. Create app
heroku create your-app-name

# 4. Set environment variables
heroku config:set GOOGLE_API_KEY=your_key_here

# 5. Deploy
git push heroku main
```

### Option 4: Docker + Any Cloud

```bash
# 1. Build Docker image
docker build -t customer-intelligence .

# 2. Run locally
docker run -p 8501:8501 -e GOOGLE_API_KEY=your_key customer-intelligence

# 3. Deploy to any cloud (AWS, GCP, Azure, DigitalOcean)
```

## Environment Configuration

### Required Environment Variables

```bash
# Primary LLM (Free)
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional LLMs (for fallback)
OPENAI_API_KEY=your_gpt4_key_here      # $5 free credits
ANTHROPIC_API_KEY=your_claude_key_here # Paid

# Application Settings
LOG_LEVEL=INFO
MAX_ITERATIONS=3

# Streamlit Settings (Railway auto-configures)
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Getting API Keys

#### Google Gemini (Free)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Create API key
4. **Free tier**: 60 requests/minute, 1M tokens/month

#### OpenAI GPT-4
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create account
3. Add payment method
4. **Free credits**: $5 for new users

#### Anthropic Claude
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create account
3. Add payment method
4. **Paid service**: Usage-based pricing

## Local Development

### Prerequisites

```bash
# Python 3.11+
python --version

# Git
git --version

# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/customer-intelligence-platform.git
cd customer-intelligence-platform

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Run locally
streamlit run app.py
```

### Development Commands

```bash
# Run with debug logging
LOG_LEVEL=DEBUG streamlit run app.py

# Run tests
pytest tests/

# Format code
black src/
flake8 src/

# Run demo mode (no API keys needed)
python demo.py
```

## Production Deployment Checklist

### Pre-Deployment
- [ ] **API Keys**: All required keys configured
- [ ] **Environment**: Variables set correctly
- [ ] **Dependencies**: requirements.txt up to date
- [ ] **Tests**: All tests passing
- [ ] **Security**: No secrets in code

### Deployment Steps
- [ ] **Build**: Application builds successfully
- [ ] **Health Check**: `/health` endpoint responds
- [ ] **Database**: Any required data connections
- [ ] **Environment**: Variables loaded correctly
- [ ] **Logging**: Logs are being captured

### Post-Deployment
- [ ] **URL**: Application accessible
- [ ] **Functionality**: Core features working
- [ ] **Performance**: Response times acceptable
- [ ] **Monitoring**: Error tracking configured
- [ ] **Backup**: Deployment successful

## Troubleshooting Deployment

### Common Issues

#### "No API key found"
```bash
# Check environment variables
echo $GOOGLE_API_KEY

# For Railway
railway variables

# For local .env
cat .env
```

#### "Port already in use"
```bash
# Find process using port 8501
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run app.py --server.port=8502
```

#### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print(sys.path)"
```

#### "Memory limit exceeded"
- **Railway**: Upgrade to Pro plan ($10/month)
- **Heroku**: Increase dyno size
- **Optimize**: Reduce batch sizes or implement streaming

#### "Timeout errors"
```bash
# Increase timeout in railway.json
{
  "deploy": {
    "healthcheckTimeout": 900
  }
}
```

### Railway-Specific Issues

#### "Build failed"
```bash
# Check build logs
railway logs

# Common fixes:
# - Add missing dependencies to requirements.txt
# - Ensure Python version compatibility
# - Check file paths in railway.json
```

#### "Application crashed"
```bash
# Check application logs
railway logs --app

# Common fixes:
# - Missing environment variables
# - Port configuration issues
# - Memory limits exceeded
```

### Performance Optimization

#### Railway Optimization
```json
{
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false",
    "healthcheckPath": "/",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

#### Memory Optimization
```python
# In app.py
import gc

# Force garbage collection after heavy operations
gc.collect()
```

#### Caching Strategies
```python
# Cache LLM responses
@st.cache_data(ttl=3600)  # 1 hour cache
def analyze_company(company, product):
    return orchestrator.run(company, product, data_sources)
```

## Security Best Practices

### API Key Management
- ✅ **Never commit keys** to version control
- ✅ **Use environment variables** or secret managers
- ✅ **Rotate keys regularly**
- ✅ **Restrict API permissions** to minimum required

### Application Security
- ✅ **Input validation** on all user inputs
- ✅ **Rate limiting** to prevent abuse
- ✅ **HTTPS only** in production
- ✅ **Regular dependency updates**

### Data Protection
- ✅ **No sensitive data** stored in logs
- ✅ **Input sanitization** before processing
- ✅ **Output validation** before display
- ✅ **GDPR compliance** for data handling

## Monitoring & Maintenance

### Health Checks
```python
# Add to app.py
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Railway health check endpoint
@app.route("/health")
def health():
    return health_check()
```

### Logging Configuration
```python
# Structured logging
import structlog

logger = structlog.get_logger()

# Log important events
logger.info("analysis_started", company=company, product=product)
logger.error("api_call_failed", provider="gemini", error=str(e))
```

### Backup & Recovery
- **Code**: Git version control
- **Configuration**: Environment variable backups
- **Data**: Regular exports if applicable
- **Deployments**: Keep multiple environments

## Cost Optimization

### Free Tier Limits
- **Gemini**: 1M tokens/month, 60 requests/minute
- **Railway**: 512MB RAM, 1GB storage
- **Streamlit Cloud**: 1GB RAM, community support

### Usage Monitoring
```python
# Track API usage
api_usage = {
    'gemini_tokens': 0,
    'gpt4_tokens': 0,
    'requests': 0
}

# Log usage for cost tracking
logger.info("api_usage", **api_usage)
```

### Scaling Strategies
- **Vertical**: Increase Railway plan ($10→$25→$50)
- **Horizontal**: Multiple Railway instances
- **Optimization**: Cache results, reduce LLM calls
- **Hybrid**: Mix free/paid providers based on load

This deployment guide ensures your Customer Intelligence Platform runs reliably in production with optimal performance and cost efficiency.
