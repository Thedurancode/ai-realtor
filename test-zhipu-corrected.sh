#!/bin/bash

API_KEY="52e0b53fd6af4578a7eff17431afb603.yPPVcKJK9Vm0iuYf"

echo "Testing Zhipu API with corrected endpoint..."
echo ""

echo "1. Testing: https://open.bigmodel.cn/api/paas/v4"
curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model": "glm-4-flash", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}' | jq .

echo ""
echo "2. Testing with model: glm-4"
curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model": "glm-4", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}' | jq .

echo ""
echo "3. Testing with model: glm-3-turbo"
curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model": "glm-3-turbo", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}' | jq .
