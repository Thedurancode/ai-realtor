#!/bin/bash

# Test different Zhipu models

API_KEY="becbf743529740ce932cbf00c5bedb46.LekS38R7Q9KiVoAv"

echo "Testing different Zhipu models..."
echo ""

models=(
  "glm-4-flash"
  "glm-4"
  "glm-4-plus"
  "glm-4-all"
  "glm-3-turbo"
)

for model in "${models[@]}"; do
  echo "Testing model: $model"
  response=$(curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
      \"model\": \"$model\",
      \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}],
      \"max_tokens\": 5
    }")

  if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
    echo "  ❌ Error: $(echo "$response" | jq -r '.error.message')"
  elif echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    echo "  ✅ Works! Response: $(echo "$response" | jq -r '.choices[0].message.content')"
    break
  fi
  echo ""
done
