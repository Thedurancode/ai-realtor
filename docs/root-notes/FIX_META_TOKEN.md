# Fix Meta Access Token - Step by Step

## Problem
Your current token has 2 issues:
1. ❌ Not active/extended
2. ❌ Missing ads_management permission

## Solution: Get Proper Token

### Step 1: Go to Meta Graph API Explorer
```
https://developers.facebook.com/tools/explorer/
```

### Step 2: Configure Token
1. **Select an app** (or create one):
   - Click "App" dropdown
   - If no app, create one:
     - Go to https://developers.facebook.com/apps/
     - Click "Create App" → "Business" → "Business Manager"
     - Name it "AI Realtor Ads"
     - Create

2. **Select User or Page token:**
   - Choose "User Token" (not Page Token)

3. **Add these permissions:**
   Check these boxes:
   - ✅ `ads_management`
   - ✅ `ads_read`
   - ✅ `read_insights`
   - ✅ `pages_show_list` (optional, for page management)
   - ✅ `pages_read_engagement` (optional)

4. **Generate Token:**
   - Click "Generate Access Token"
   - You'll see a token like: `EAAxxxxxxxxx`

5. **Extend the Token:**
   - Click the "Debug" button next to the token
   - Click "Extend Access Token" button
   - Copy the new extended token (valid for 60 days)

### Step 3: Test Your Token

Run this command:
```bash
curl "https://graph.facebook.com/v18.0/me/adaccounts?access_token=YOUR_NEW_TOKEN"
```

Should return your ad accounts (not an error).

### Step 4: Update .env File

Replace your token in `.env`:
```bash
META_ACCESS_TOKEN=EAAxxxxxx (your new extended token)
META_AD_ACCOUNT_ID=act_1229918789122014
```

---

## Alternative: Use Facebook Business Manager

If Graph API Explorer doesn't work, use Business Suite:

1. Go to: https://business.facebook.com/
2. Open Business Settings → Brand Safety → System Users
3. Add a system user (or use your admin account)
4. Generate token with ads_management permission
5. Copy token

---

## Quick Check: Is Your Account an Ad Account?

Run this:
```bash
curl "https://graph.facebook.com/v18.0/act_1229918789122014?access_token=YOUR_TOKEN&fields=name,account_id"
```

If it returns account details ✅, your account is valid.
If it returns an error ❌, it might be a personal account, not an ad account.

---

## After Fixing Token

Once you have the extended token with proper permissions:

1. Update `.env`:
```bash
META_ACCESS_TOKEN=your_new_token_here
META_AD_ACCOUNT_ID=act_1229918789122014
```

2. Test launch:
```bash
./scripts/launch_facebook_ad.sh
```

3. Your ad will go live! 🚀
