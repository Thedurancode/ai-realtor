#!/bin/bash

API_KEY="52e0b53fd6af4578a7eff17431afb603.yPPVcKJK9Vm0iuYf"

echo "Testing ALL possible Zhipu model names..."
echo ""

# All known Zhipu models
models=(
  "glm-4-flash"
  "glm-4"
  "glm-4-plus"
  "glm-4-all"
  "glm-3-turbo"
  "glm4-flash"
  "glm4"
  "chatglm3-6b"
  "chatglm3"
  "glm-4-0520"
  "glm-4-0920"
  "glm-4-air"
  "glm-4-0520"
  "glm-turbo"
)

for model in "${models[@]}"; do
  echo -n "  Testing $model... "

  response=$(curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}], \"max_tokens\": 5}")

  if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    content=$(echo "$response" | jq -r '.choices[0].message.content')
    echo "✅ WORKS! Response: $content"
    echo ""
    echo "🎉 SUCCESS! Use model: $model"
    exit 0
  elif echo "$response" | jq -e '.error' > /dev/null 2>&1; then
    error=$(echo "$response" | jq -r '.error.message')
    echo "❌ $error"
  else
    echo "? Unknown response"
  fi
done

echo ""
echo "❌ No working model found for this API key"
echo ""
echo "The Zhipu account needs to:"
echo "1. Activate the account at https://open.bigmodel.cn/"
echo "2. Or recharge/add balance"
echo "3. Or apply for API access"
