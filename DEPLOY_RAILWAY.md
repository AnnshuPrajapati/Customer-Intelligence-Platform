# 🚂 Deploying to Railway

## Quick Deployment Guide

### Option 1: Deploy via Railway Dashboard (Easiest)

1. **Sign up/Login to Railway**
   - Go to https://railway.app
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose this repository

3. **Configure Environment Variables**
   - In your Railway project, go to "Variables" tab
   - Add these variables:
     ```
     GOOGLE_API_KEY=your_gemini_api_key_here
     LOG_LEVEL=INFO
     MAX_ITERATIONS=3
     ```
   - Railway will automatically use `railway.json` for configuration

4. **Deploy**
   - Railway will automatically detect the Streamlit app
   - The build will start automatically
   - Wait for deployment to complete

5. **View Your App**
   - Click on your service
   - Find the "Public URL" or generate a domain
   - Your app will be live at that URL!

### Option 2: Deploy via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize project (if not already done)
railway init

# Link to existing project (or create new one)
railway link

# Set environment variables
railway variables set GOOGLE_API_KEY=your_key_here
railway variables set LOG_LEVEL=INFO
railway variables set MAX_ITERATIONS=3

# Deploy
railway up

# Get your app URL
railway domain
```

### Option 3: Deploy via GitHub Integration

1. **Push to GitHub** (if not already)
   ```bash
   git add .
   git commit -m "Ready for Railway deployment"
   git push origin main
   ```

2. **Connect Repository**
   - In Railway dashboard, click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your repos
   - Select this repository

3. **Railway will auto-detect:**
   - ✅ `railway.json` configuration
   - ✅ `Procfile` for start command
   - ✅ Python runtime from `runtime.txt`

4. **Add Secrets**
   - Go to "Variables" tab
   - Add `GOOGLE_API_KEY` as a secret

5. **Your app deploys automatically!**
   - Railway builds on every push to main
   - View logs in real-time
   - Access your app via the generated domain

## Viewing Your Railway Deployment

### In Railway Dashboard:
1. Go to https://railway.app/dashboard
2. Click on your project
3. Click on the service (your Streamlit app)
4. View:
   - **Logs**: Real-time deployment and app logs
   - **Metrics**: CPU, Memory, Network usage
   - **Deployments**: History of all deployments
   - **Settings**: Configuration and environment variables

### Access Your App:
- **Public Domain**: Railway provides a public URL like `https://your-app.up.railway.app`
- **Custom Domain**: Add your own domain in the "Settings" → "Networking" tab
- **Share**: Use the public URL to share your app with others

## Railway Configuration

Your `railway.json` includes:
- ✅ Nixpacks builder (auto-detects Python)
- ✅ Build command: `pip install -r requirements.txt`
- ✅ Start command: Streamlit with proper port binding
- ✅ Health check configuration
- ✅ Restart policy for reliability

## Troubleshooting

### App not loading?
1. Check logs in Railway dashboard
2. Verify `GOOGLE_API_KEY` is set correctly
3. Check that port is set to `$PORT` (Railway sets this automatically)

### Build failing?
1. Check `requirements.txt` is present and valid
2. Verify Python version in `runtime.txt` is supported
3. Check build logs for specific errors

### Environment variables not working?
1. Make sure variables are set in Railway dashboard
2. Variables prefixed with `STREAMLIT_` are for Streamlit config
3. Restart deployment after changing variables

## Monitoring Your App

Railway provides:
- 📊 **Metrics**: CPU, Memory, Network in real-time
- 📝 **Logs**: Application logs with search
- 🔄 **Deployments**: Track all deployments
- 🚨 **Alerts**: Set up notifications for failures

## Cost

Railway offers:
- **Free tier**: $5 credit/month (plenty for small apps)
- **Pay as you go**: Only pay for what you use
- **Hobby plan**: $20/month for more resources

Your Streamlit app should run comfortably on the free tier!

---

**Need help?** Check Railway docs: https://docs.railway.app
