"""
Health & Wealth Tracker
=======================

Complete life management app combining:
1. Financial tracking (income, expenses, debts)
2. Health tracking (blood tests, medical reports, trends)
3. Smart nutrition (personalized grocery recommendations)

Run: streamlit run streamlit_app.py
"""

import streamlit as st
import json
import os
import base64
from datetime import datetime, timedelta
from collections import defaultdict
from PIL import Image
import anthropic
import pandas as pd

# File handling
EXPENSES_FILE = "expenses.json"
BUDGETS_FILE = "budgets.json"
SETTINGS_FILE = "settings.json"
DEBTS_FILE = "debts.json"
HEALTH_FILE = "health.json"
HEALTH_REPORTS_FILE = "health_reports.json"

def load_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {} if 'json' in filename else []
    return {} if 'json' in filename else []

def save_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# Page config
st.set_page_config(
    page_title="🏥 Health & Wealth Tracker",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'expenses' not in st.session_state:
    st.session_state.expenses = load_file(EXPENSES_FILE)
if 'budgets' not in st.session_state:
    st.session_state.budgets = load_file(BUDGETS_FILE)
if 'settings' not in st.session_state:
    st.session_state.settings = load_file(SETTINGS_FILE)
if 'debts' not in st.session_state:
    st.session_state.debts = load_file(DEBTS_FILE)
if 'health_metrics' not in st.session_state:
    st.session_state.health_metrics = load_file(HEALTH_FILE)
if 'health_reports' not in st.session_state:
    st.session_state.health_reports = load_file(HEALTH_REPORTS_FILE)

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

def analyze_health_metrics():
    """Analyze current health based on metrics."""
    if not st.session_state.health_metrics:
        return None
    
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
        latest = st.session_state.health_metrics[-1] if st.session_state.health_metrics else {}
        metrics_text = '\n'.join([f"- {k}: {v}" for k, v in latest.items() if k not in ['date', 'report_file', 'added_at']])
        
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

def get_grocery_recommendations():
    """Give personalized grocery recommendations based on health metrics and purchase history."""
    if not st.session_state.health_metrics or not st.session_state.expenses:
        return None
    
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
        # Get recent grocery items
        recent_items = defaultdict(int)
        today = datetime.now()
        month_ago = today - timedelta(days=30)
        
        for exp in st.session_state.expenses:
            if exp.get('category') != 'Groceries':
                continue
            try:
                exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
                if exp_date >= month_ago:
                    for item in exp.get('items', []):
                        item_name = item.get('name', '')
                        recent_items[item_name] += 1
            except:
                pass
        
        if not recent_items:
            return None
        
        latest_health = st.session_state.health_metrics[-1]
        health_text = '\n'.join([f"- {k}: {v}" for k, v in latest_health.items() if k not in ['date', 'report_file', 'added_at']])
        items_text = '\n'.join([f"- {item} (bought {count} times)" for item, count in list(recent_items.items())[:10]])
        
        prompt = f"""Based on their health metrics and grocery purchases, give recommendations.

Health Status:
{health_text}

Items They Usually Buy:
{items_text}

For EACH item they buy, suggest:
- Keep buying: for positive nutrients
- Reduce: if bad for their health condition
- Replace with: better alternative

Output ONLY JSON:
{{
    "recommendations": [
        {{"item": "Chicken", "status": "Keep", "reason": "Good protein"}},
        {{"item": "Bacon", "status": "Reduce", "reason": "High sodium - you have high BP"}},
        {{"item": "Spinach", "status": "Keep", "reason": "Lowers cholesterol"}},
        {{"item": "Replace with", "recommendation": "Use olive oil instead of butter"}}
    ],
    "overall_grade": "8/10",
    "summary": "Your grocery choices are generally healthy. Focus on reducing salt."
}}"""
        
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(message.content[0].text)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def calculate_monthly_finances():
    """Calculate complete monthly financial overview."""
    settings = st.session_state.settings
    
    your_salary = float(settings.get('your_salary', 0))
    wife_salary = float(settings.get('wife_salary', 0))
    total_income = your_salary + wife_salary
    
    fixed_expenses = {}
    fixed_total = 0
    for key in settings:
        if key.startswith('fixed_'):
            amount = float(settings[key])
            expense_name = key.replace('fixed_', '').replace('_', ' ').title()
            fixed_expenses[expense_name] = amount
            fixed_total += amount
    
    debt_total = 0
    for debt in st.session_state.debts:
        debt_total += float(debt.get('monthly_payment', 0))
    
    today = datetime.now()
    month_start = today.replace(day=1)
    
    variable_total = 0
    variable_by_category = defaultdict(float)
    for exp in st.session_state.expenses:
        try:
            exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
            if exp_date >= month_start:
                amt = exp.get('total', 0)
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

# Main UI
st.title("🏥 Health & Wealth Tracker")
st.markdown("Complete life management: Finance + Health + Smart Nutrition")

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
        save_file(SETTINGS_FILE, st.session_state.settings)
        st.success("✅ Saved!")

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
                    'created_date': datetime.now().isoformat(),
                    'months_to_payoff': months_to_payoff
                }
                st.session_state.debts.append(new_debt)
                save_file(DEBTS_FILE, st.session_state.debts)
                st.success(f"✅ {debt_name} added! Payoff timeline: {months_to_payoff} months")
            else:
                st.warning("Please fill in all fields (name, principal > 0, monthly payment > 0)")
    
    st.markdown("#### 📋 Your Debts")
    if st.session_state.debts:
        total_debt = 0
        total_monthly_payment = 0
        
        for i, debt in enumerate(st.session_state.debts):
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 0.5])
            
            with col1:
                st.write(f"**{debt['name']}**")
            with col2:
                st.write(f"${debt['principal']:.2f}")
            with col3:
                st.write(f"${debt['monthly_payment']:.2f}/mo")
            with col4:
                st.write(f"{debt['months_to_payoff']} months")
            with col5:
                if st.button("❌", key=f"del_debt_{i}"):
                    st.session_state.debts.pop(i)
                    save_file(DEBTS_FILE, st.session_state.debts)
                    st.rerun()
            
            total_debt += debt['principal']
            total_monthly_payment += debt['monthly_payment']
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Debt", f"${total_debt:.2f}")
        with col2:
            st.metric("Total Monthly Payment", f"${total_monthly_payment:.2f}")
        with col3:
            max_months = max([d['months_to_payoff'] for d in st.session_state.debts], default=0)
            st.metric("Debt-Free Timeline", f"{max_months} months")

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
                    
                    st.session_state.expenses.append(receipt)
                    save_file(EXPENSES_FILE, st.session_state.expenses)
                    
                    st.success("✅ Receipt processed!")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Store", receipt.get('merchant', 'N/A'))
                    with col2:
                        st.metric("Total", f"${receipt.get('total', 0):.2f}")
                    with col3:
                        st.metric("Category", category)

with tabs[3]:  # Wealth Dashboard
    st.markdown("### 📊 Complete Financial Dashboard")
    
    finances = calculate_monthly_finances()
    
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
            st.write(f"• {debt['name']}: ${debt['monthly_payment']:.2f}")
        st.write(f"**Subtotal: ${finances['debt_payments']:.2f}**")
        
        total_debt = sum(d['principal'] for d in st.session_state.debts)
        max_months = max([d['months_to_payoff'] for d in st.session_state.debts], default=0)
        st.success(f"🎯 **DEBT-FREE IN {max_months} MONTHS!** (Total debt: ${total_debt:.2f})")

with tabs[4]:  # Health
    st.markdown("### 🏥 Health Tracking & Analysis")
    
    st.markdown("#### 📤 Upload Medical Reports")
    col1, col2 = st.columns(2)
    with col1:
        report_type = st.selectbox("Report Type", ["Blood Test", "Physical Exam", "Other Medical Report"])
    with col2:
        report_date = st.date_input("Report Date")
    
    uploaded_report = st.file_uploader("Upload PDF or Image", type=["pdf", "jpg", "jpeg", "png"], key="health_upload")
    
    if uploaded_report and st.button("📎 Save Report"):
        report_data = {
            'type': report_type,
            'date': str(report_date),
            'filename': uploaded_report.name,
            'uploaded_at': datetime.now().isoformat()
        }
        st.session_state.health_reports.append(report_data)
        save_file(HEALTH_REPORTS_FILE, st.session_state.health_reports)
        st.success("✅ Report saved!")
    
    st.markdown("#### 📊 Enter Health Metrics Manually")
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_date = st.date_input("Test Date", key="metric_date")
    with col2:
        metric_type = st.selectbox("Metric Type", ["Blood Test Results", "Blood Pressure", "Weight/BMI", "Other"], key="metric_type")
    with col3:
        metric_name = st.text_input("Metric Name (e.g., Cholesterol, Blood Sugar)", key="metric_name")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_value = st.number_input("Value", step=0.1, key="metric_value")
    with col2:
        metric_unit = st.text_input("Unit (mg/dL, mmol/L, etc)", key="metric_unit")
    with col3:
        metric_normal = st.text_input("Normal Range (e.g., 120-200)", key="metric_normal")
    
    if st.button("✅ Add Health Metric"):
        health_entry = {
            'date': str(metric_date),
            'type': metric_type,
            'metric': metric_name,
            'value': metric_value,
            'unit': metric_unit,
            'normal_range': metric_normal,
            'added_at': datetime.now().isoformat()
        }
        st.session_state.health_metrics.append(health_entry)
        save_file(HEALTH_FILE, st.session_state.health_metrics)
        st.success("✅ Metric saved!")
    
    st.markdown("#### 📈 Health Trends & Analysis")
    if st.session_state.health_metrics:
        latest_analysis = analyze_health_metrics()
        
        if latest_analysis:
            col1, col2 = st.columns(2)
            with col1:
                status = latest_analysis.get('overall_status', 'Unknown')
                status_emoji = "✅" if status == "Good" else "⚠️" if status == "Fair" else "🔴"
                st.write(f"**Overall Status: {status_emoji} {status}**")
            
            with col2:
                if latest_analysis.get('flags'):
                    st.write("**⚠️ Flags:**")
                    for flag in latest_analysis.get('flags', []):
                        st.write(f"  • {flag}")
            
            st.markdown("**💡 Health Recommendations:**")
            for rec in latest_analysis.get('recommendations', []):
                st.write(f"  • {rec}")
            
            st.markdown("**🥗 Diet Guidance:**")
            st.write(latest_analysis.get('diet_guidance', 'No guidance available'))
        
        st.markdown("#### 📋 Your Metrics History")
        for metric in reversed(st.session_state.health_metrics[-10:]):
            st.write(f"**{metric['date']}** - {metric['metric']}: {metric['value']} {metric['unit']} (Normal: {metric['normal_range']})")

with tabs[5]:  # Smart Grocery
    st.markdown("### 🥗 Smart Grocery Recommendations")
    
    if st.session_state.health_metrics and st.session_state.expenses:
        recommendations = get_grocery_recommendations()
        
        if recommendations:
            st.success(f"**Overall Grade: {recommendations.get('overall_grade', 'N/A')}**")
            st.write(recommendations.get('summary', ''))
            
            st.markdown("#### 🛒 Your Usual Items - Health Assessment:")
            for rec in recommendations.get('recommendations', []):
                item = rec.get('item')
                status = rec.get('status')
                reason = rec.get('reason')
                
                if status == "Keep":
                    st.write(f"✅ **{item}** - {reason}")
                elif status == "Reduce":
                    st.write(f"⚠️ **{item}** - {reason}")
                else:
                    st.write(f"💡 {reason}")
        else:
            st.info("📸 Upload more grocery receipts to get personalized recommendations!")
    else:
        st.info("📊 Add health metrics and upload grocery receipts to get smart recommendations!")

with tabs[6]:  # Budgets
    st.markdown("### 🎯 Set Monthly Budgets")
    
    categories = ['Groceries', 'Dining', 'Transportation', 'Entertainment', 'Shopping', 'Healthcare']
    
    for cat in categories:
        current = st.session_state.budgets.get(cat, 0)
        budget = st.number_input(f"{cat} Budget (CAD)", min_value=0.0, value=float(current), step=10.0)
        st.session_state.budgets[cat] = budget
    
    if st.button("💾 Save Budgets"):
        save_file(BUDGETS_FILE, st.session_state.budgets)
        st.success("✅ Budgets saved!")

st.markdown("---")
st.markdown("💡 **Health & Wealth: Your complete life tracker** - Finances + Health + Smart Nutrition")
