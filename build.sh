#!/bin/bash
set -e

echo "🚀 Starting build process..."

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

echo "✅ Build completed successfully!"