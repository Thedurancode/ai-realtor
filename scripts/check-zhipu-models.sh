#!/bin/bash

# Check Zhipu API for available models

API_KEY="52e0b53fd6af4578a7eff17431afb603.yPPVcKJK9Vm0iuYf"

echo "Checking Zhipu API models..."
echo ""

# Try the coding plan endpoint
echo "1. Testing coding plan endpoint:"
curl -s -X POST "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "test"}]
  }' | jq .

echo ""
echo "2. Testing standard endpoint:"
curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "test"}]
  }' | jq .

echo ""
echo "3. Testing with alternative model names:"

# Try different model name formats
models=(
  "glm-4-flash"
  "glm4-flash"
  "GLM-4-FLASH"
  "chatglm3-6b"
)

for model in "${models[@]}"; do
  echo -n "  Trying $model... "

  response=$(curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
      \"model\": \"$model\",
      \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}],
      \"max_tokens\": 5
    }")

  if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    echo "✅ WORKS!"
    echo "$response" | jq .
    exit 0
  elif echo "$response" | jq -e '.error' > /dev/null 2>&1; then
    echo "Error: $(echo "$response" | jq -r '.error.message' | head -c 50)"
  else
    echo "Unknown response"
  fi
done
