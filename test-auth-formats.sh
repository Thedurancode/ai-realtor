#!/bin/bash

API_KEY="becbf743529740ce932cbf00c5bedb46.LekS38R7Q9KiVoAv"

echo "Testing different auth formats with https://api.z.ai/api/coding/paas/v4"
echo ""

echo "1. Authorization: Bearer TOKEN"
curl -s -X POST "https://api.z.ai/api/coding/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hi"}]
  }' | jq -r '.choices[0].message.content' 2>/dev/null && echo "✅ SUCCESS" || echo "❌ FAILED"
echo ""

echo "2. x-api-key: TOKEN (without Bearer)"
curl -s -X POST "https://api.z.ai/api/coding/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hi"}]
  }' | jq -r '.choices[0].message.content' 2>/dev/null && echo "✅ SUCCESS" || echo "❌ FAILED"
echo ""

echo "3. api-key: TOKEN"
curl -s -X POST "https://api.z.ai/api/coding/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "api-key: ${API_KEY}" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hi"}]
  }' | jq -r '.choices[0].message.content' 2>/dev/null && echo "✅ SUCCESS" || echo "❌ FAILED"
