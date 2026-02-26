#!/bin/bash
# Test your Meta credentials before launching ads

echo "🔍 Testing Meta Credentials"
echo ""

TOKEN="${1:-$META_ACCESS_TOKEN}"
ACCOUNT="act_1229918789122014"

if [ -z "$TOKEN" ]; then
  echo "❌ Usage: $0 <access_token>"
  echo ""
  echo "Or set META_ACCESS_TOKEN environment variable"
  exit 1
fi

echo "Token: ${TOKEN:0:20}..."
echo "Account: $ACCOUNT"
echo ""

# Test 1: Can we read ad accounts?
echo "Test 1: Reading ad accounts..."
RESPONSE=$(curl -s "https://graph.facebook.com/v18.0/me/adaccounts?access_token=$TOKEN")

if echo "$RESPONSE" | grep -q "error"; then
  echo "❌ FAILED - Token invalid or missing permissions"
  echo ""
  echo "Error details:"
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""
  echo "📖 Fix: Follow the guide in FIX_META_TOKEN.md"
  exit 1
else
  echo "✅ PASSED - Token has ads_read permission"
fi
echo ""

# Test 2: Can we access the specific ad account?
echo "Test 2: Accessing ad account $ACCOUNT..."
RESPONSE=$(curl -s "https://graph.facebook.com/v18.0/$ACCOUNT?access_token=$TOKEN&fields=name,account_id,status")

if echo "$RESPONSE" | grep -q "error"; then
  echo "❌ FAILED - Cannot access ad account"
  echo ""
  echo "Error details:"
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""
  echo "Possible issues:"
  echo "  - Account ID is wrong (should be act_XXXXXXXXX)"
  echo "  - Token doesn't have permission for this account"
  echo "  - Account might be disabled"
  exit 1
else
  echo "✅ PASSED - Can access ad account"
  ACCOUNT_NAME=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('name', 'Unknown'))" 2>/dev/null)
  echo "   Account Name: $ACCOUNT_NAME"
fi
echo ""

# Test 3: Check permissions
echo "Test 3: Checking token permissions..."
PERM_CHECK=$(curl -s "https://graph.facebook.com/v18.0/me/permissions?access_token=$TOKEN")

if echo "$PERM_CHECK" | grep -q "ads_management"; then
  echo "✅ PASSED - Has ads_management permission"
else
  echo "❌ FAILED - Missing ads_management permission"
  echo ""
  echo "Current permissions:"
  echo "$PERM_CHECK" | python3 -m json.tool | grep -A1 "permission" | head -10
  echo ""
  echo "📖 Fix: Re-generate token with ads_management permission"
  exit 1
fi
echo ""

echo "✨ All tests passed! Your credentials are ready to launch ads."
echo ""
echo "Next step:"
echo "  ./scripts/launch_facebook_ad.sh"
