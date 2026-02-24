#!/bin/bash

API_KEY="becbf743529740ce932cbf00c5bedb46.LekS38R7Q9KiVoAv"

echo "Testing different z.ai endpoint formats..."
echo ""

echo "1. Anthropic v1/messages (WORKS):"
curl -s -X POST "https://api.z.ai/api/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "model": "glm-4.7",
    "max_tokens": 20,
    "messages": [{"role": "user", "content": "Hi"}]
  }' | jq -r '.content[0].text' 2>/dev/null || echo "Failed"
echo ""

echo "2. Chat completions format (Nanobot might use):"
curl -s -X POST "https://api.z.ai/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hi"}]
  }' | jq .
echo ""

echo "3. Alternative endpoint:"
curl -s -X POST "https://api.z.ai/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hi"}]
  }' | jq .
