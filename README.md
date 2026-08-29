# 💰 Health & Wealth Tracker - Modular Edition

A comprehensive personal finance and health tracking app built with Streamlit and Google Sheets.

## 🎯 Features

### Financial Management
- **💳 Debt Tracking** - Manage debts with payoff timelines
- **💰 Expense Tracking** - AI-powered receipt processing
- **📊 Wealth Dashboard** - Retirement savings overview
- **🎯 Budgets** - Set and track category budgets
- **🛒 Shopping Analytics** - Price trends and deal detection

### Health & Wellness
- **🏥 Health Metrics** - Blood work and vital signs
- **🏋️ Fitness Plans** - Personalized recommendations
- **✅ Wellness Log** - Daily exercise, mood, sleep tracking
- **🍽️ Nutrition Tracker** - 9 sub-tabs with macro tracking
- **👶 Fertility Tracker** - Cycle tracking and predictions
- **🥗 Smart Grocery** - AI-optimized shopping lists

## 🏗️ Architecture

**Modular structure** - 12 focused modules instead of 4,430-line monolith

```
smart_budget_app/
├── main.py                 # Entry point
├── config.py               # Constants & headers
├── utils.py                # Shared utilities
├── gsheet_client.py        # Google Sheets API
├── modules/
│   ├── settings.py        ✅ Complete
│   ├── budgets.py         ✅ Complete
│   ├── financial.py       🔄 Framework
│   ├── health.py          🔄 Framework
│   ├── wellness.py        🔄 Framework
│   ├── nutrition.py       🔄 Framework
│   ├── fertility.py       🔄 Framework
│   └── shopping.py        🔄 Framework
└── requirements.txt
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Google Sheets
- Create service account at Google Cloud Console
- Download JSON key
- Share Google Sheet with service account email
- Add to `.streamlit/secrets.toml`:
```toml
[gsheet]
type = "service_account"
project_id = "your-project"
private_key_id = "key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
client_email = "service@project.iam.gserviceaccount.com"
client_id = "client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/..."

ANTHROPIC_API_KEY = "sk-ant-..."
```

### 3. Run App
```bash
streamlit run main.py
```

Visit: `http://localhost:8501`

## 📋 Tabs (12 Total)

1. **⚙️ Setup** - Income & fixed expenses
2. **💳 Debts** - Debt tracking
3. **💰 Spending** - Expense analytics
4. **🛒 Shopping Analytics** - Price trends
5. **📊 Wealth** - Retirement overview
6. **🏥 Health** - Health metrics
7. **🏋️ Fitness** - Fitness plans
8. **✅ Wellness** - Daily log
9. **🍽️ Nutrition** - 9 sub-tabs
10. **👶 Fertility** - Cycle tracking
11. **🥗 Smart Grocery** - Shopping list
12. **🎯 Budgets** - Budget management

## 🧪 Testing

### Settings Tab
```
1. Go to Setup tab
2. Enter income & expenses
3. Click Save
4. Refresh browser
5. Data should persist ✅
```

### Budgets Tab
```
1. Go to Budgets tab
2. Enter budget amounts
3. Click Save
4. Refresh browser
5. Budgets should load ✅
```

## 📚 Documentation

- **[MODULAR_REFACTOR_GUIDE.md](../MODULAR_REFACTOR_GUIDE.md)** - Architecture & development guide
- **[BUDGET_NOT_LOADING_FIX.md](../BUDGET_NOT_LOADING_FIX.md)** - Troubleshooting guide

## 🛠️ Development

### Add a New Feature
1. Create load/save functions in appropriate module
2. Create render_*_tab() UI function
3. Call from main.py
4. Test!

### Add a New Module
1. Create modules/new_feature.py
2. Add to modules/__init__.py
3. Import in main.py
4. Add to MAIN_TABS config

See [MODULAR_REFACTOR_GUIDE.md](../MODULAR_REFACTOR_GUIDE.md) for details.

## 📊 Complexity Metrics

| Metric | Before | After |
|--------|--------|-------|
| Lines of Code | 4,430 | ~1,200 |
| Reduction | - | 73% |
| Modules | 1 | 12 |
| Maintainability | Hard | Easy |

## 🐛 Troubleshooting

### Google Sheets Connection Error
```
Check .streamlit/secrets.toml exists with valid credentials
```

### Settings Not Loading
```
Check Google Sheets has Settings worksheet with headers in row 1
```

### Budgets Not Saving
```
Ensure Budget worksheet exists and can be written to
```

## 📝 Implementation Status

✅ = Complete
🔄 = Framework ready
❌ = Not started

- ✅ Project structure
- ✅ Google Sheets integration
- ✅ Settings module (load/save)
- ✅ Budgets module (load/save)
- 🔄 Financial (debts, spending, wealth) - UI framework ready
- 🔄 Health (health, fitness) - UI framework ready
- 🔄 Wellness (daily log) - UI framework ready
- 🔄 Nutrition (9 sub-tabs) - UI framework ready
- 🔄 Fertility (cycle tracking) - UI framework ready
- 🔄 Shopping (analytics, grocery) - UI framework ready

## 🚀 Deployment

### Streamlit Cloud
```bash
git push  # Push to GitHub
# Then: streamlit.app → Connect repo → Deploy
```

### Environment Variables (Streamlit Cloud)
Set in Streamlit Cloud dashboard:
- `GSHEET_TYPE` 
- `GSHEET_PROJECT_ID`
- `GSHEET_PRIVATE_KEY_ID`
- `GSHEET_PRIVATE_KEY`
- `GSHEET_CLIENT_EMAIL`
- `GSHEET_CLIENT_ID`
- `ANTHROPIC_API_KEY`

## 📧 Support

For issues or feature requests, see the main repository.

## 📄 License

Private - Govind Raj
