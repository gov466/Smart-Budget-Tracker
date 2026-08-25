# 🔍 Troubleshoot Wellness Log Save Issues

## ❌ Error: "Failed to save wellness log!"

The app can't connect to Google Sheets. Let's fix it!

---

## 🎯 Quick Checklist

- [ ] Streamlit Secrets configured?
- [ ] Service account JSON added?
- [ ] Google Sheet shared with service account?
- [ ] Internet connection working?
- [ ] Google Sheet ID correct?

---

## 🛠️ Step-by-Step Fixes

### **FIX #1: Check Streamlit Secrets (CRITICAL)**

**Local (Development):**
```
1. Create file: .streamlit/secrets.toml
2. Add your service account JSON:

[gsheet]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_KEY_ID"
private_key = "YOUR_PRIVATE_KEY"
client_email = "YOUR_EMAIL"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"

ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

**Streamlit Cloud:**
1. Go to app settings
2. Click "Secrets"
3. Paste entire secrets.toml content
4. Save & redeploy

### **FIX #2: Verify Service Account Email**

Get your service account email:
```bash
# From your service account JSON file
grep "client_email" service-account.json
# Output: "rtm-analyzer@PROJECT_ID.iam.gserviceaccount.com"
```

### **FIX #3: Share Google Sheet with Service Account**

1. Open your Google Sheet
2. Click "Share" (top right)
3. Paste service account email
4. Give **Editor** access
5. Click "Share"
6. ✅ Important: Uncheck "Notify people" (it's a robot!)

### **FIX #4: Check Google Sheet ID**

In your app, find this line:
```python
SPREADSHEET_ID = "1tzRTNtq3N-QPabBSowhmzYXuxHR9bimvYTn1z0wjuQs"
```

Verify it matches your sheet:
1. Open your Google Sheet
2. Copy ID from URL:
   ```
   https://docs.google.com/spreadsheets/d/COPY_THIS_PART/edit
   ```
3. Should match `SPREADSHEET_ID` in app

### **FIX #5: Check Google Sheets API Enabled**

1. Go to https://console.cloud.google.com/
2. Go to "APIs & Services"
3. Search "Google Sheets API"
4. Click it
5. Verify "Enabled" (blue)
6. If not, click "Enable"

---

## 📊 Error Messages Explained

### **"credentials" in error**
```
❌ Issue: Service account JSON not in Streamlit Secrets
✅ Fix: Add secrets.toml with full JSON
```

### **"404" in error**
```
❌ Issue: Sheet ID doesn't exist or is wrong
✅ Fix: Double-check SPREADSHEET_ID matches your sheet
```

### **"permission denied"**
```
❌ Issue: Service account not shared on sheet
✅ Fix: Share sheet with service account (Editor access)
```

### **"Quota exceeded"**
```
❌ Issue: Too many API calls in short time
✅ Fix: Wait 60 seconds & try again (or use updated app with caching)
```

---

## ✅ Verification Steps

**After fixing, test with this:**

1. Click 🍽️ Nutrition Tracker tab
2. Click ✅ Daily Wellness Log tab
3. Fill in some data
4. Click "💾 Save Daily Log"
5. Look for detailed error message

**Error should now show:**
- ✅ Specific error type
- ✅ Suggested fix
- ✅ What to check

---

## 🆘 Advanced Troubleshooting

### **Check if Google Sheets API works:**

Run this Python code locally:
```python
import gspread
from gspread.oauth2 import ServiceAccountCredentials

# Load your service account JSON
creds = ServiceAccountCredentials.from_service_account_file(
    'service-account.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

# Try to access Google Sheets
gc = gspread.authorize(creds)
sheet = gc.open_by_key('YOUR_SHEET_ID')  # Use your actual ID

print("✅ Google Sheets API works!")
```

### **Test Service Account Access:**

```python
# Check if service account can read sheet
try:
    worksheet = sheet.worksheet('Settings')
    data = worksheet.get_all_values()
    print(f"✅ Can read sheet! Data rows: {len(data)}")
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 📝 Common Mistakes

1. ❌ Sharing sheet with **wrong email** (not the service account)
2. ❌ Secrets file in wrong location (should be `.streamlit/secrets.toml`)
3. ❌ Secrets file has **wrong format** (must be TOML, not JSON)
4. ❌ API **not enabled** in Google Cloud
5. ❌ Service account has **Viewer** access instead of **Editor**
6. ❌ Sheet ID from different sheet
7. ❌ Trying before Streamlit Cloud secrets sync (wait 1 min after saving)

---

## 🔄 Fallback Mode

**NEW:** If Google Sheets fails, the app now:
- ✅ Shows detailed error message
- ✅ Saves to local cache automatically
- ✅ Shows helpful fix suggestions
- ✅ Retries on next save

**Your data is NOT lost!** It's saved locally until connection works.

---

## 🎯 If Still Failing

1. **Check console errors**
   - Open browser dev tools (F12)
   - Look for JavaScript errors
   - Check Network tab for 4xx/5xx responses

2. **Try the test script above**
   - If test fails, it's a credentials issue
   - If test works, it's an app configuration issue

3. **Check Streamlit logs**
   - Terminal where you ran streamlit
   - Look for detailed error messages

4. **Contact Support with:**
   - Error message (from app)
   - Streamlit version: `streamlit --version`
   - Python version: `python --version`
   - Whether test script works

---

## ✅ You're Configured When

- ✅ Service account email shared on sheet
- ✅ Secrets.toml configured locally
- ✅ Secrets added to Streamlit Cloud
- ✅ Google Sheets API enabled
- ✅ SPREADSHEET_ID matches your sheet
- ✅ First save shows "✅ Saved!"

---

## 📞 Quickest Fix

**If you just want it working NOW:**

Option 1: Use fallback mode
- App now saves locally if Google Sheets fails
- Data is safe!
- Can retry later when connection fixed

Option 2: Fix secrets
- Most common issue
- Takes 5 minutes
- Then it works forever

---

**Follow the steps above and it will work!** 💪
