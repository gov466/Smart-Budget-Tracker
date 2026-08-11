# Smart Budget Tracker - Streamlit Cloud Deployment Guide

## ✨ Why Streamlit?

✅ **Simple** — One Python file, no HTML/templates  
✅ **Free** — Streamlit Cloud hosting (completely free)  
✅ **Fast** — Auto-deploys from GitHub  
✅ **Mobile-friendly** — Works perfectly on phone  
✅ **Always on** — No laptop needed  
✅ **Instant UI** — Streamlit handles all the design  

---

## 📋 Prerequisites

1. ✅ GitHub account (you have this)
2. ✅ Streamlit account (free, takes 2 min)
3. ✅ Anthropic API key (you have this)

---

## 🚀 Deploy in 5 Steps

### Step 1: Update Your GitHub Repo

Delete old Flask files and add Streamlit version:

```bash
# Navigate to your budget-tracker repo
cd path/to/smart-budget-tracker

# Delete old files
rm -rf web_server.py templates/ web_requirements.txt

# Copy new Streamlit files
# streamlit_app.py
# streamlit_requirements.txt

# Commit and push
git add .
git commit -m "Switch to Streamlit - simpler deployment"
git push origin main
```

---

### Step 2: Update requirements.txt

Replace `web_requirements.txt` with `streamlit_requirements.txt`:

```txt
anthropic>=0.21.0
streamlit>=1.28.0
Pillow>=10.0.0
```

---

### Step 3: Create `.streamlit/config.toml`

Create this file in your repo (Streamlit configuration):

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f0f0"
textColor = "#333333"
font = "sans serif"

[client]
showErrorDetails = true

[logger]
level = "info"
```

---

### Step 4: Sign Up for Streamlit Cloud

1. Go to **https://streamlit.io/cloud**
2. Click **"Sign up"**
3. Choose **"Sign up with GitHub"**
4. Authorize Streamlit to access your GitHub
5. Done! ✅

---

### Step 5: Deploy Your App

1. Go to **https://share.streamlit.io**
2. Click **"New app"**
3. Fill in:
   - **GitHub repo:** your-username/smart-budget-tracker
   - **Branch:** main
   - **Main file path:** streamlit_app.py
4. Click **"Deploy"**
5. Wait 2-3 minutes... ⏳
6. **APP GOES LIVE!** 🎉

---

## 🔑 Set Environment Variable

After deployment:

1. Click **"Settings"** (⚙️) in top right
2. Click **"Secrets"**
3. Add your API key:
   ```
   ANTHROPIC_API_KEY = "sk-ant-xxxxx"
   ```
4. Click **"Save"**
5. App auto-restarts with the key ✅

---

## 🌐 Access Your App

After deployment:

**Public URL:** `https://share.streamlit.io/your-username/smart-budget-tracker`

Or simpler domain: Streamlit generates a custom URL like:
`https://budget-tracker-govind.streamlit.app`

### From Phone:
- Any WiFi or mobile data
- Just visit the URL
- Start uploading receipts! 📱

---

## ✅ What You Get

✅ **Mobile upload page** — Camera or gallery  
✅ **Receipt extraction** — Claude Vision processes  
✅ **Results display** — Merchant, items, total  
✅ **History tab** — All expenses + dashboard  
✅ **Category charts** — Visual breakdown  
✅ **Predictions** — Monthly forecast  
✅ **Recommendations** — AI savings tips  
✅ **Export data** — Download as JSON  
✅ **Always on** — 24/7 without laptop  
✅ **Free** — $0/month  

---

## 🔄 Update Your App

After deployment, any changes to `streamlit_app.py` auto-deploy:

```bash
# Make changes
# Commit and push
git push origin main

# Streamlit detects changes
# Auto-redeploys in 1-2 minutes
# Done! ✅
```

---

## 📊 File Structure (Final)

```
smart-budget-tracker/
├─ streamlit_app.py              (main app)
├─ streamlit_requirements.txt     (dependencies)
├─ .streamlit/
│  └─ config.toml                (styling)
├─ expenses.json                 (auto-created)
└─ README.md
```

---

## 🆘 Troubleshooting

### "API key not found"
- Check Settings → Secrets
- Verify key starts with `sk-ant-`
- Re-save and wait 1 min for restart

### "ModuleNotFoundError: streamlit"
- Check `streamlit_requirements.txt` in repo root
- Streamlit Cloud reads this to install dependencies

### "App won't load"
- Check Logs tab in Streamlit Cloud
- Common issue: typo in API key

### "Upload doesn't work"
- Check environment variables are set
- Try refreshing browser
- Check Streamlit Cloud logs

---

## 🎯 Next Steps

1. ✅ Update GitHub repo with Streamlit files
2. ✅ Sign up for Streamlit Cloud
3. ✅ Deploy your app (5 minutes)
4. ✅ Set API key in secrets
5. ✅ Test from phone
6. ✅ Start tracking receipts!

---

## 💡 Tips

- **Secrets are auto-encrypted** on Streamlit Cloud
- **Free tier unlimited** for personal projects
- **Auto-redeploys** on GitHub push
- **Persistent storage** (expenses.json stays)
- **Works offline** for uploads (processes when online)

---

## 🚀 You're Done!

Your Budget Tracker is now:
- ✅ Live 24/7
- ✅ Accessible from anywhere
- ✅ Mobile-friendly
- ✅ Completely free
- ✅ No laptop needed

**Visit your app URL and start uploading receipts!** 📱💰

---

**Questions?** Check Streamlit Cloud docs: https://docs.streamlit.io/streamlit-cloud
