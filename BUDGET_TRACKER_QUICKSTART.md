# Smart Budget Tracker - Quick Start

## 1-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r budget_tracker_requirements.txt
```

### Step 2: Set API Key
```bash
# macOS/Linux
export ANTHROPIC_API_KEY='sk-ant-xxxxx'

# Windows PowerShell
$env:ANTHROPIC_API_KEY='sk-ant-xxxxx'
```

### Step 3: Run Demo
```bash
python smart_budget_tracker.py
```

**What happens:**
1. Analyzes 5 sample expenses
2. Generates spending summary
3. Creates predictions
4. Provides recommendations
5. Saves JSON report

---

## Using with Real Receipt Photos

### Option 1: Interactive Mode (Coming Soon)
```python
from smart_budget_tracker import BudgetTracker

tracker = BudgetTracker()

# Process receipt image
tracker.process_receipt("receipt.jpg")

# Get summary
summary = tracker.get_summary()

# Save to file
tracker.save_to_file("my_budget.json")
```

### Option 2: Batch Processing
```bash
# Process all JPEGs in folder
python smart_budget_tracker.py --folder ./receipts
```

---

## Features

### 1. Receipt Extraction
- 📸 Takes receipt photo
- 🤖 Claude Vision extracts: merchant, items, total, date
- ✅ Automatic expense categorization

### 2. Spending Analysis
- 📊 Total spent & daily average
- 🏷️ Category breakdown with percentages
- 📈 Spending trends & patterns

### 3. Smart Predictions
- 🔮 Predict next month's spending
- 📉 Category-level forecasts
- 🎯 Confidence scoring

### 4. Recommendations
- 💡 Personalized savings tips
- ⚠️ Anomaly detection (unusual spending)
- 📱 Specific, actionable advice

---

## Output Files

After running, you get:
```
budget_summary_20260808_120000.json
├─ analysis (spending metrics)
├─ predictions (future forecasts)
├─ recommendations (AI suggestions)
├─ anomalies (unusual purchases)
└─ expenses (all transactions)
```

---

## Dashboard

1. Open `budget_dashboard.html` in browser
2. Click "Load Budget Data"
3. Select JSON file from tracker
4. View interactive visualizations:
   - Category breakdown chart
   - Monthly prediction chart
   - Spending metrics
   - Insights & recommendations

---

## Categories Supported

- Groceries
- Dining
- Transportation
- Utilities
- Entertainment
- Shopping
- Healthcare
- Other

---

## Cost

Claude API usage per receipt:
- ~200 tokens = ~$0.001
- 100 receipts/month = ~$0.10

**Essentially free!** 💰

---

## Tips

1. **Photo quality matters** — Clear, well-lit receipt photos work best
2. **Consistent tracking** — Log receipts daily for better predictions
3. **Review anomalies** — Check unusual spending detections
4. **Export regularly** — Save JSON reports for record-keeping

---

## Troubleshooting

### "API key not found"
```bash
export ANTHROPIC_API_KEY='sk-ant-xxxxx'
python smart_budget_tracker.py
```

### "Image processing failed"
- Use clear photo in good lighting
- Try JPEG format
- Ensure receipt is fully visible

### "No output file created"
Check that you have write permissions in current directory

---

## Next Steps

1. ✅ Run demo to understand workflow
2. ✅ Take receipt photo with phone
3. ✅ Process your first real expense
4. ✅ Open dashboard to visualize
5. ✅ Track weekly for patterns

---

**Start tracking today!** 💰📱
