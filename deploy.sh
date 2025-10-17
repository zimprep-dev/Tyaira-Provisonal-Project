#!/bin/bash
# Tyaira Quick Deployment Script for AWS Ubuntu
# Run this after pushing code changes to GitHub

set -e  # Exit on any error

echo "🚀 Starting deployment..."

# Navigate to project directory
cd /home/ubuntu/Tyaira-Provisonal-Project

# Pull latest code from GitHub
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
flask db upgrade

# Restart the application service
echo "🔄 Restarting application..."
sudo systemctl restart tyaira

# Check service status
echo "✅ Checking service status..."
sudo systemctl status tyaira --no-pager

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your app should now be running with the latest changes."
