#!/bin/bash
# Quick script to check Prowlarr setup

echo "Checking Prowlarr API Key setup..."
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "✅ .env file found"
    if grep -q "PROWLARR_API_KEY" .env; then
        echo "✅ PROWLARR_API_KEY found in .env"
        KEY=$(grep "PROWLARR_API_KEY" .env | cut -d '=' -f2)
        if [ -z "$KEY" ] || [ "$KEY" = "" ]; then
            echo "❌ PROWLARR_API_KEY is empty in .env"
            echo "   Add your API key: PROWLARR_API_KEY=your_key_here"
        else
            echo "✅ PROWLARR_API_KEY has a value"
        fi
    else
        echo "❌ PROWLARR_API_KEY not found in .env"
        echo "   Add: PROWLARR_API_KEY=your_key_here"
    fi
else
    echo "❌ .env file not found"
fi

echo ""
echo "To get your Prowlarr API key:"
echo "1. Open http://localhost:9696"
echo "2. Go to Settings → General"
echo "3. Copy the API Key"
echo "4. Add to .env: PROWLARR_API_KEY=your_key"
echo "5. Restart: docker compose restart fastapi"



