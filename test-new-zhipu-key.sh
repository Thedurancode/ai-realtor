#!/bin/bash

# Test new Zhipu API Key

API_KEY="52e0b53fd6af4578a7eff17431afb603.yPPVcKJK9Vm0iuYf"

echo "Testing new Zhipu API Key..."
echo "API Key: ${API_KEY:0:20}..."
echo ""

models=(
  "glm-4-flash"
  "glm-4"
  "glm-4-plus"
  "glm-3-turbo"
)

echo "Testing different models:"
echo ""

for model in "${models[@]}"; do
  echo -n "  Testing $model... "
  response=$(curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
      \"model\": \"$model\",
      \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}],
      \"max_tokens\": 5
    }")

  if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
    error_msg=$(echo "$response" | jq -r '.error.message')
    echo "❌ $error_msg"
  elif echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    content=$(echo "$response" | jq -r '.choices[0].message.content')
    echo "✅ Works! Response: $content"
    echo ""
    echo "🎉 SUCCESS! Model $model is working with this API key"
    exit 0
  fi
done

echo ""
echo "❌ No working model found"
