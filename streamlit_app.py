"""
Health & Wealth Tracker with Google Sheets Integration
======================================================

Features:
1. Monthly income tracking (both salaries)
2. Fixed expenses (auto-deducted monthly)
3. Debt management & payoff tracking
4. Variable spending (receipts)
5. Health tracking (blood tests, metrics)
6. Smart grocery recommendations
7. Complete financial dashboard
8. Data stored in Google Sheets (PERSISTENT!)

Run: streamlit run streamlit_app.py
"""

import streamlit as st
import gspread
import json
import os
import base64
from datetime import datetime, timedelta
from collections import defaultdict
from PIL import Image
import anthropic
import pandas as pd

# Google Sheets configuration
SPREADSHEET_ID = "1tzRTNtq3N-QPabBSowhmzYXuxHR9bimvYTn1z0wjuQs"

def get_gsheet_client():
    """Connect to Google Sheets using credentials from Streamlit secrets"""
    try:
        creds = st.secrets["gsheet"]
        gc = gspread.service_account_from_dict(creds)
        return gc.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        st.error(f"❌ Error connecting to Google Sheets: {str(e)}")
        st.info("Make sure Streamlit Secrets are set up correctly!")
        return None

def get_or_create_worksheet(sheet, name):
    """Get worksheet by name or create if it doesn't exist"""
    try:
        return sheet.worksheet(name)
    except:
        return sheet.add_worksheet(title=name, rows=1000, cols=20)

def load_settings():
    """Load settings from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return {}
        ws = get_or_create_worksheet(sheet, "Settings")
        data = ws.get_all_records()
        if data:
            return data[0]
        return {}
    except:
        return {}

def load_expenses():
    """Load expenses from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return []
        ws = get_or_create_worksheet(sheet, "Expenses")
        return ws.get_all_records()
    except:
        return []

def load_debts():
    """Load debts from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return []
        ws = get_or_create_worksheet(sheet, "Debts")
        records = ws.get_all_records()
        # Convert string numbers to float
        for record in records:
            if 'principal' in record and record['principal']:
                record['principal'] = float(record['principal'])
            if 'monthly_payment' in record and record['monthly_payment']:
                record['monthly_payment'] = float(record['monthly_payment'])
            if 'interest_rate' in record and record['interest_rate']:
                record['interest_rate'] = float(record['interest_rate'])
        return records
    except:
        return []

def load_health():
    """Load health metrics from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return []
        ws = get_or_create_worksheet(sheet, "Health")
        return ws.get_all_records()
    except:
        return []

def load_budgets():
    """Load budgets from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return {}
        ws = get_or_create_worksheet(sheet, "Budget")
        data = ws.get_all_records()
        if data:
            return data[0]
        return {}
    except:
        return {}

def save_debt_to_gsheet(debt):
    """Add new debt to Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            st.error("Cannot connect to Google Sheets")
            return False
        
        ws = get_or_create_worksheet(sheet, "Debts")
        
        # Get headers and add row
        row = [
            debt.get('name', ''),
            debt.get('principal', ''),
            debt.get('monthly_payment', ''),
            debt.get('interest_rate', ''),
            debt.get('months_to_payoff', ''),
            debt.get('created_date', '')
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error saving debt: {str(e)}")
        return False

def save_expense_to_gsheet(expense):
    """Add new expense to Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        ws = get_or_create_worksheet(sheet, "Expenses")
        
        row = [
            expense.get('merchant', ''),
            expense.get('date', ''),
            expense.get('total', ''),
            expense.get('category', ''),
            expense.get('uploaded_at', '')
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error saving expense: {str(e)}")
        return False

def save_health_to_gsheet(health_entry):
    """Add health metric to Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        ws = get_or_create_worksheet(sheet, "Health")
        
        row = [
            health_entry.get('date', ''),
            health_entry.get('metric', ''),
            health_entry.get('value', ''),
            health_entry.get('unit', ''),
            health_entry.get('normal_range', ''),
            health_entry.get('added_at', '')
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error saving health: {str(e)}")
        return False

def save_settings_to_gsheet(settings):
    """Save settings to Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        ws = get_or_create_worksheet(sheet, "Settings")
        
        # Clear existing data
        ws.clear()
        
        # Add header
        headers = list(settings.keys())
        ws.append_row(headers)
        
        # Add data
        values = [str(settings.get(k, '')) for k in headers]
        ws.append_row(values)
        return True
    except Exception as e:
        st.error(f"Error saving settings: {str(e)}")
        return False

def extract_receipt(image_bytes):
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
        
        prompt = """Extract receipt information. Output ONLY valid JSON.
{
    "merchant": "Store name",
    "date": "YYYY-MM-DD",
    "items": [
        {"name": "Item name", "quantity": 1, "price": 0.00}
    ],
    "total": 0.00
}
Be precise. Only output JSON."""
        
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt}
                ],
            }],
        )
        
        return json.loads(message.content[0].text)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def categorize_expense(receipt):
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        merchant = receipt.get('merchant', '').lower()
        items = [item.get('name', '').lower() for item in receipt.get('items', [])]
        items_text = ', '.join(items[:3])
        
        prompt = f"""Categorize into ONE: Groceries, Dining, Transportation, Utilities, Entertainment, Shopping, Healthcare, Other
Merchant: {merchant}
Items: {items_text}
Output ONLY category name."""
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}]
        )
        
        category = message.content[0].text.strip()
        valid = ['Groceries', 'Dining', 'Transportation', 'Utilities', 'Entertainment', 'Shopping', 'Healthcare', 'Other']
        return category if any(cat in category for cat in valid) else 'Other'
    except:
        return 'Other'

def analyze_health_metrics(health_list):
    """Analyze health metrics"""
    if not health_list:
        return None
    
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
        latest = health_list[-1] if health_list else {}
        metrics_text = '\n'.join([f"- {k}: {v}" for k, v in latest.items() if k not in ['date', 'added_at']])
        
        prompt = f"""Analyze these health metrics and provide brief assessment.

Metrics:
{metrics_text}

Provide ONLY a JSON response with this structure:
{{
    "overall_status": "Good/Fair/Concerning",
    "flags": ["High cholesterol", "Good blood pressure"],
    "recommendations": ["Reduce salt intake", "Increase fiber"],
    "diet_guidance": "What food groups to focus on or avoid"
}}"""
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(message.content[0].text)
    except:
        return None

def calculate_monthly_finances(expenses, settings, debts):
    """Calculate complete monthly financial overview"""
    your_salary = float(settings.get('your_salary', 0))
    wife_salary = float(settings.get('wife_salary', 0))
    total_income = your_salary + wife_salary
    
    fixed_expenses = {}
    fixed_total = 0
    for key in settings:
        if key.startswith('fixed_'):
            try:
                amount = float(settings[key])
                expense_name = key.replace('fixed_', '').replace('_', ' ').title()
                fixed_expenses[expense_name] = amount
                fixed_total += amount
            except:
                pass
    
    debt_total = 0
    for debt in debts:
        try:
            debt_total += float(debt.get('monthly_payment', 0))
        except:
            pass
    
    today = datetime.now()
    month_start = today.replace(day=1)
    
    variable_total = 0
    variable_by_category = defaultdict(float)
    for exp in expenses:
        try:
            exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
            if exp_date >= month_start:
                amt = float(exp.get('total', 0))
                variable_total += amt
                cat = exp.get('category', 'Other')
                variable_by_category[cat] += amt
        except:
            pass
    
    return {
        'your_salary': your_salary,
        'wife_salary': wife_salary,
        'total_income': total_income,
        'fixed_expenses': fixed_expenses,
        'fixed_total': fixed_total,
        'debt_payments': debt_total,
        'variable_total': variable_total,
        'variable_by_category': dict(variable_by_category),
        'available_after_fixed_debt': total_income - fixed_total - debt_total,
        'remaining': total_income - fixed_total - debt_total - variable_total
    }

# Page config
st.set_page_config(
    page_title="🏥 Health & Wealth Tracker",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'settings' not in st.session_state:
    st.session_state.settings = load_settings()
if 'expenses' not in st.session_state:
    st.session_state.expenses = load_expenses()
if 'debts' not in st.session_state:
    st.session_state.debts = load_debts()
if 'health_metrics' not in st.session_state:
    st.session_state.health_metrics = load_health()
if 'budgets' not in st.session_state:
    st.session_state.budgets = load_budgets()

# Main UI
st.title("🏥 Health & Wealth Tracker")
st.markdown("Complete life management: Finance + Health + Smart Nutrition (Data in Google Sheets ☁️)")

tabs = st.tabs(["⚙️ Setup", "💳 Debts", "💰 Spending", "📊 Wealth", "🏥 Health", "🥗 Smart Grocery", "🎯 Budgets"])

with tabs[0]:  # Setup
    st.markdown("### Monthly Income & Fixed Expenses Setup")
    
    st.markdown("#### 💵 Monthly Income")
    col1, col2 = st.columns(2)
    with col1:
        your_sal = st.number_input("Your Salary (CAD)", min_value=0.0, value=float(st.session_state.settings.get('your_salary', 0)), step=100.0)
    with col2:
        wife_sal = st.number_input("Wife's Salary (CAD)", min_value=0.0, value=float(st.session_state.settings.get('wife_salary', 0)), step=100.0)
    
    st.markdown("#### 🏠 Fixed Monthly Expenses")
    
    fixed_items = {
        'fixed_rent': 'Rent/Mortgage',
        'fixed_car_payment': 'Car Payment',
        'fixed_car_insurance': 'Car Insurance',
        'fixed_mobile': 'Mobile/Phone',
        'fixed_utilities': 'Utilities (Hydro, Gas, Internet)',
        'fixed_groceries_budget': 'Groceries Budget',
        'fixed_tfsa': 'TFSA Transfer',
        'fixed_rrsp': 'RRSP Transfer',
        'fixed_india_transfer': 'Money to India',
        'fixed_other': 'Other Fixed Expense'
    }
    
    fixed_values = {}
    for key, label in fixed_items.items():
        fixed_values[key] = st.number_input(label, min_value=0.0, value=float(st.session_state.settings.get(key, 0)), step=50.0)
    
    if st.button("💾 Save Income & Fixed Expenses"):
        st.session_state.settings['your_salary'] = your_sal
        st.session_state.settings['wife_salary'] = wife_sal
        for key, val in fixed_values.items():
            st.session_state.settings[key] = val
        if save_settings_to_gsheet(st.session_state.settings):
            st.success("✅ Saved to Google Sheets!")
        else:
            st.error("❌ Error saving")

with tabs[1]:  # Debts
    st.markdown("### Debt Tracking & Management")
    
    st.markdown("#### ➕ Add New Debt")
    with st.form("add_debt_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            debt_name = st.text_input("Debt Name", placeholder="CC Debt / Car Loan / etc", key="debt_name_input")
        with col2:
            principal = st.number_input("Principal Remaining (CAD)", min_value=0.0, step=100.0, key="principal_input")
        with col3:
            monthly_payment = st.number_input("Monthly Payment (CAD)", min_value=0.0, step=50.0, key="monthly_payment_input")
        with col4:
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, step=0.1, key="interest_rate_input")
        
        submitted = st.form_submit_button("➕ Add Debt", use_container_width=True)
        if submitted:
            if debt_name and principal > 0 and monthly_payment > 0:
                months_to_payoff = int(principal / monthly_payment) if monthly_payment > 0 else 0
                new_debt = {
                    'name': debt_name,
                    'principal': principal,
                    'monthly_payment': monthly_payment,
                    'interest_rate': interest_rate,
                    'months_to_payoff': months_to_payoff,
                    'created_date': datetime.now().isoformat()
                }
                if save_debt_to_gsheet(new_debt):
                    st.session_state.debts.append(new_debt)
                    st.success(f"✅ {debt_name} added! Payoff timeline: {months_to_payoff} months")
                else:
                    st.error("Error saving debt")
            else:
                st.warning("Please fill in all fields (name, principal > 0, monthly payment > 0)")
    
    st.markdown("#### 📋 Your Debts")
    if st.session_state.debts:
        total_debt = 0
        total_monthly_payment = 0
        
        for debt in st.session_state.debts:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{debt.get('name', 'N/A')}**")
            with col2:
                st.write(f"${debt.get('principal', 0):.2f}")
            with col3:
                st.write(f"${debt.get('monthly_payment', 0):.2f}/mo")
            with col4:
                st.write(f"{debt.get('months_to_payoff', 0)} months")
            
            try:
                total_debt += float(debt.get('principal', 0))
                total_monthly_payment += float(debt.get('monthly_payment', 0))
            except:
                pass
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Debt", f"${total_debt:.2f}")
        with col2:
            st.metric("Total Monthly Payment", f"${total_monthly_payment:.2f}")
        with col3:
            max_months = max([d.get('months_to_payoff', 0) for d in st.session_state.debts], default=0)
            st.metric("Debt-Free Timeline", f"{max_months} months")
    else:
        st.info("No debts tracked yet. Add one above!")

with tabs[2]:  # Spending
    st.markdown("### 📸 Track Variable Spending (Receipts)")
    
    uploaded_file = st.file_uploader("Upload Receipt", type=["jpg", "jpeg", "png", "gif", "webp"], key="receipt_upload")
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
        
        if st.button("🤖 Process Receipt"):
            with st.spinner("Processing..."):
                receipt = extract_receipt(uploaded_file.getvalue())
                
                if receipt:
                    category = categorize_expense(receipt)
                    receipt['category'] = category
                    receipt['uploaded_at'] = datetime.now().isoformat()
                    
                    if save_expense_to_gsheet(receipt):
                        st.session_state.expenses.append(receipt)
                        st.success("✅ Receipt processed!")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Store", receipt.get('merchant', 'N/A'))
                        with col2:
                            st.metric("Total", f"${receipt.get('total', 0):.2f}")
                        with col3:
                            st.metric("Category", category)
                    else:
                        st.error("Error saving receipt to Google Sheets")

with tabs[3]:  # Wealth Dashboard
    st.markdown("### 📊 Complete Financial Dashboard")
    
    finances = calculate_monthly_finances(st.session_state.expenses, st.session_state.settings, st.session_state.debts)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Income", f"${finances['total_income']:.2f}")
    with col2:
        st.metric("Fixed + Debt", f"${finances['fixed_total'] + finances['debt_payments']:.2f}")
    with col3:
        st.metric("Variable Spent", f"${finances['variable_total']:.2f}")
    with col4:
        st.metric("Remaining", f"${finances['remaining']:.2f}")
    
    st.markdown("#### 📥 Income")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"Your Salary: **${finances['your_salary']:.2f}**")
    with col2:
        st.write(f"Wife's Salary: **${finances['wife_salary']:.2f}**")
    with col3:
        st.write(f"**Total: ${finances['total_income']:.2f}**")
    
    st.markdown("#### 🔧 Fixed Monthly Expenses")
    if finances['fixed_expenses']:
        for expense, amount in finances['fixed_expenses'].items():
            st.write(f"• {expense}: ${amount:.2f}")
        st.write(f"**Subtotal: ${finances['fixed_total']:.2f}**")
    
    st.markdown("#### 💳 Debt Payments")
    if st.session_state.debts:
        for debt in st.session_state.debts:
            st.write(f"• {debt.get('name', 'N/A')}: ${debt.get('monthly_payment', 0):.2f}")
        st.write(f"**Subtotal: ${finances['debt_payments']:.2f}**")
        
        total_debt = sum(float(d.get('principal', 0)) for d in st.session_state.debts)
        max_months = max([d.get('months_to_payoff', 0) for d in st.session_state.debts], default=0)
        st.success(f"🎯 **DEBT-FREE IN {max_months} MONTHS!** (Total debt: ${total_debt:.2f})")

with tabs[4]:  # Health
    st.markdown("### 🏥 Health Tracking & Analysis")
    
    st.markdown("#### 📊 Enter Health Metrics")
    with st.form("add_health_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_date = st.date_input("Test Date", key="metric_date")
        with col2:
            metric_name = st.text_input("Metric Name (e.g., Cholesterol, Blood Sugar)", key="metric_name")
        with col3:
            metric_type = st.selectbox("Type", ["Blood Test", "Blood Pressure", "Weight/BMI", "Other"], key="metric_type")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_value = st.number_input("Value", step=0.1, key="metric_value")
        with col2:
            metric_unit = st.text_input("Unit (mg/dL, mmol/L, etc)", key="metric_unit")
        with col3:
            metric_normal = st.text_input("Normal Range (e.g., 120-200)", key="metric_normal")
        
        submitted = st.form_submit_button("✅ Add Health Metric", use_container_width=True)
        if submitted:
            health_entry = {
                'date': str(metric_date),
                'metric': metric_name,
                'value': metric_value,
                'unit': metric_unit,
                'normal_range': metric_normal,
                'type': metric_type,
                'added_at': datetime.now().isoformat()
            }
            if save_health_to_gsheet(health_entry):
                st.session_state.health_metrics.append(health_entry)
                st.success("✅ Health metric saved!")
    
    st.markdown("#### 📈 Health Analysis")
    if st.session_state.health_metrics:
        latest_analysis = analyze_health_metrics(st.session_state.health_metrics)
        
        if latest_analysis:
            status = latest_analysis.get('overall_status', 'Unknown')
            status_emoji = "✅" if status == "Good" else "⚠️" if status == "Fair" else "🔴"
            st.write(f"**Overall Status: {status_emoji} {status}**")
            
            if latest_analysis.get('flags'):
                st.write("**⚠️ Flags:**")
                for flag in latest_analysis.get('flags', []):
                    st.write(f"  • {flag}")
            
            st.markdown("**💡 Health Recommendations:**")
            for rec in latest_analysis.get('recommendations', []):
                st.write(f"  • {rec}")
        
        st.markdown("#### 📋 Your Metrics History")
        for metric in reversed(st.session_state.health_metrics[-10:]):
            st.write(f"**{metric.get('date')}** - {metric.get('metric')}: {metric.get('value')} {metric.get('unit')} (Normal: {metric.get('normal_range')})")

with tabs[5]:  # Smart Grocery
    st.markdown("### 🥗 Smart Grocery Recommendations")
    st.info("📊 Add health metrics and upload grocery receipts to get personalized recommendations!")

with tabs[6]:  # Budgets
    st.markdown("### 🎯 Set Monthly Budgets")
    
    categories = ['Groceries', 'Dining', 'Transportation', 'Entertainment', 'Shopping', 'Healthcare']
    
    for cat in categories:
        current = st.session_state.budgets.get(cat, 0)
        budget = st.number_input(f"{cat} Budget (CAD)", min_value=0.0, value=float(current), step=10.0)
        st.session_state.budgets[cat] = budget
    
    if st.button("💾 Save Budgets"):
        if save_settings_to_gsheet(st.session_state.budgets):
            st.success("✅ Budgets saved to Google Sheets!")

st.markdown("---")
st.markdown("💡 **Health & Wealth: Your complete life tracker** - Finances + Health + Nutrition (Data saved in Google Sheets ☁️)")
