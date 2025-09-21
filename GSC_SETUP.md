# Google Search Console Access Setup

## Issue
The GSC API is working, but shows 0 properties because the service account doesn't have access to your existing GSC properties.

## Service Account Email
**Add this email to your GSC properties:**
```
indexation-bot@indexation-checker-472711.iam.gserviceaccount.com
```

## Setup Steps

### 1. Go to Google Search Console
https://search.google.com/search-console

### 2. For Each Website Property:

1. **Click on the property** (e.g., austinfenceanddeck.com)
2. **Go to Settings** (gear icon in sidebar)
3. **Click "Users and permissions"**
4. **Click "Add user"**
5. **Enter email:** `indexation-bot@indexation-checker-472711.iam.gserviceaccount.com`
6. **Set permission:** "Full" or "Owner"
7. **Click "Add"**

### 3. Websites to Add Access:

- **austinfenceanddeck.com** (Austin Fence & Deck Builders)
- **austinfence.net** (Austin Fence)
- **austinfencecompany.org** (Austin Fence Company)
- **abercrombiejewelry.com** (Abercrombie Jewelry - optional)

### 4. Test Setup

Run this command to verify access:
```bash
python test_gsc_fix.py
```

**Expected result:** Should show 3-4 properties instead of 0

## After Setup

Once access is granted:
1. **Austin Fence & Deck Builders** will use GSC as primary method
2. **Much faster and more accurate** than fallback methods
3. **Real indexation data** instead of rate-limited search results
4. **All websites** can use GSC for optimal performance

## Troubleshooting

If still showing 0 properties after adding access:
1. Wait 5-10 minutes for Google to update permissions
2. Make sure you used the exact email address
3. Check that permission level is "Full" or "Owner"
4. Verify you added access to the correct property format (e.g., both `https://domain.com/` and `sc-domain:domain.com` if available)