#!/bin/bash
set -e

echo "🚀 Starting deployment..."

cd /var/www/esteemcbt

echo "📦 Pulling latest code..."
git pull origin main-working

echo "🐳 Rebuilding Docker containers..."
docker compose down
docker compose build --no-cache
docker compose up -d

echo "⏳ Waiting for web container to be ready..."
sleep 5

echo "🗄️ Running migrations..."
docker compose exec web python manage.py migrate --noinput

echo "📁 Collecting static files..."
docker compose exec web python manage.py collectstatic --noinput

echo "✅ Deployment complete!"
docker compose ps
