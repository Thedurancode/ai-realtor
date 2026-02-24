#!/bin/bash

API_KEY="becbf743529740ce932cbf00c5bedb46.LekS38R7Q9KiVoAv"

echo "Testing z.ai API endpoint..."
echo "API Key: ${API_KEY}"
echo ""

echo "1. Testing Anthropic format:"
curl -s -X POST "https://api.z.ai/api/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 20,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
echo ""
echo ""

echo "2. Testing with different model:"
curl -s -X POST "https://api.z.ai/api/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 20,
    "messages": [{"role": "user", "content": "Hi"}]
  }'
echo ""
echo ""

echo "3. Testing OpenAI format:"
curl -s -X POST "https://api.z.ai/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
