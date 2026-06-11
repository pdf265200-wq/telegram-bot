#!/bin/bash
# Railway Deployment Script

echo "🚀 Preparing deployment to Railway..."
echo "=================================="

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔑 Login to Railway..."
railway login

# Initialize project (if not already)
if [ ! -f "railway.json" ]; then
    echo "📁 Initializing Railway project..."
    railway init
fi

# Set environment variables
echo "🔧 Setting environment variables..."
railway variables set BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
railway variables set ADMIN_IDS="YOUR_ADMIN_ID"
railway variables set LOG_LEVEL="INFO"
railway variables set PYTHON_VERSION="3.12"

# Deploy
echo "📤 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo ""
echo "📝 Important:"
echo "1. Update BOT_TOKEN in Railway dashboard"
echo "2. Update ADMIN_IDS in Railway dashboard"
echo "3. Check logs: railway logs"
