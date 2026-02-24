#!/bin/bash

# Test Zhipu API Key

echo "Testing Zhipu API Key..."
echo ""

API_KEY="becbf743529740ce932cbf00c5bedb46.LekS38R7Q9KiVoAv"

echo "1. Testing Zhipu GLM-4 API..."
curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }' | jq .

echo ""
echo "2. Testing Coding Plan API..."
curl -s -X POST "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }' | jq .

echo ""
echo "Done!"
