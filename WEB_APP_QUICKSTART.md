# Smart Budget Tracker Web App - Quick Start

## 2-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r web_requirements.txt
```

### Step 2: Set API Key
```bash
# macOS/Linux
export ANTHROPIC_API_KEY='sk-ant-xxxxx'

# Windows PowerShell
$env:ANTHROPIC_API_KEY='sk-ant-xxxxx'
```

### Step 3: Start Server
```bash
python web_server.py
```

**Output:**
```
Smart Budget Tracker Web Server
=======================================================

🚀 Server starting...

📱 Access from phone:
   1. On same WiFi: http://192.168.1.X:5000
   2. Replace X with your computer's IP
   3. To find IP: ipconfig (Windows) or ifconfig (Mac/Linux)

💻 Access from computer: http://localhost:5000
```

---

## Find Your Computer's IP

### Windows (PowerShell)
```powershell
ipconfig
# Look for "IPv4 Address" under your WiFi adapter
# Example: 192.168.1.50
```

### Mac/Linux (Terminal)
```bash
ifconfig
# Look for "inet" under your WiFi adapter (en0 or wlan0)
# Example: 192.168.1.50
```

---

## Access from Phone

1. **Same WiFi Network:**
   - Phone connected to same WiFi as computer
   - Open browser on phone
   - Type: `http://192.168.1.X:5000` (replace X with your IP)
   - Start uploading receipts!

2. **From Outside:**
   - (Requires ngrok or port forwarding setup - advanced)
   - For now, use same WiFi

---

## What You Can Do

### 📸 Upload Receipt
1. Tap "Upload Receipt Photo"
2. Take photo with camera
3. App extracts items + prices
4. Auto-categorizes expense

### 📊 View Results
- See extracted receipt details
- View total amount
- See category (Groceries, Dining, etc.)

### 📈 View History
- Click "View History"
- See all expenses
- Monthly prediction
- Category breakdown
- AI recommendations

---

## File Structure

```
smart_budget_tracker/
├─ web_server.py          (main Flask app)
├─ web_requirements.txt    (dependencies)
├─ expenses.json           (auto-created, stores data)
├─ uploads/                (auto-created, temp receipt photos)
└─ templates/
   ├─ index.html           (upload page)
   ├─ results.html         (results page)
   └─ history.html         (dashboard/history)
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Upload page |
| `/upload` | POST | Process receipt |
| `/results` | GET | Latest results |
| `/history` | GET | Historical dashboard |
| `/api/expenses` | GET | JSON data |
| `/api/export` | GET | Download all data |

---

## Troubleshooting

### "Connection refused" on phone
- Ensure phone is on same WiFi as computer
- Check IP address is correct
- Verify web server is running

### "Page not found" 404
- Check you're using correct IP address
- Try `http://192.168.1.X:5000/` (with trailing slash)
- Restart server

### Receipt extraction fails
- Use clear, well-lit photo
- Ensure receipt is fully visible
- Try JPG format

### "API key not found"
```bash
export ANTHROPIC_API_KEY='sk-ant-xxxxx'
python web_server.py
```

---

## Features

✅ **Receipt Upload** — Camera or gallery  
✅ **Auto Extraction** — Claude Vision gets details  
✅ **Auto Categorization** — Groceries, Dining, etc.  
✅ **Real-time Results** — Instant feedback  
✅ **Historical Tracking** — All expenses stored  
✅ **Dashboard** — Charts + analytics  
✅ **Predictions** — Monthly forecast  
✅ **Recommendations** — AI savings tips  
✅ **Export** — Download all data as JSON  

---

## Tips

1. **Take good photos** — Clear, full receipt, good lighting
2. **Log daily** — Better predictions with more data
3. **Review categories** — Check auto-categorization makes sense
4. **Export regularly** — Keep backups of your data
5. **Monitor predictions** — See spending trends over time

---

## Next Steps

1. ✅ Set up server
2. ✅ Connect phone to WiFi
3. ✅ Visit http://192.168.1.X:5000
4. ✅ Upload first receipt
5. ✅ Check history dashboard
6. ✅ Review recommendations

---

**Start tracking spending smartly!** 💰📱

