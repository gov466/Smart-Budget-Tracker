"""
Smart Budget Tracker - Complete Household Finance Tracker
==========================================================

Features:
1. Monthly income tracking (both salaries)
2. Fixed expenses (auto-deducted monthly)
3. Debt management & payoff tracking
4. Variable spending (receipts)
5. Complete financial dashboard
6. Smart store recommendations

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

def load_expenses():
    if os.path.exists(EXPENSES_FILE):
        try:
            with open(EXPENSES_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def load_budgets():
    if os.path.exists(BUDGETS_FILE):
        try:
            with open(BUDGETS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_debts():
    if os.path.exists(DEBTS_FILE):
        try:
            with open(DEBTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_expenses():
    with open(EXPENSES_FILE, 'w') as f:
        json.dump(st.session_state.expenses, f, indent=2)

def save_budgets():
    with open(BUDGETS_FILE, 'w') as f:
        json.dump(st.session_state.budgets, f, indent=2)

def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(st.session_state.settings, f, indent=2)

def save_debts():
    with open(DEBTS_FILE, 'w') as f:
        json.dump(st.session_state.debts, f, indent=2)

# Page config
st.set_page_config(
    page_title="💰 Household Budget Tracker",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'expenses' not in st.session_state:
    st.session_state.expenses = load_expenses()
if 'budgets' not in st.session_state:
    st.session_state.budgets = load_budgets()
if 'settings' not in st.session_state:
    st.session_state.settings = load_settings()
if 'debts' not in st.session_state:
    st.session_state.debts = load_debts()

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

def calculate_monthly_finances():
    """Calculate complete monthly financial overview."""
    settings = st.session_state.settings
    
    # Income
    your_salary = float(settings.get('your_salary', 0))
    wife_salary = float(settings.get('wife_salary', 0))
    total_income = your_salary + wife_salary
    
    # Fixed expenses
    fixed_expenses = {}
    fixed_total = 0
    for key in settings:
        if key.startswith('fixed_'):
            amount = float(settings[key])
            expense_name = key.replace('fixed_', '').replace('_', ' ').title()
            fixed_expenses[expense_name] = amount
            fixed_total += amount
    
    # Debt payments
    debt_total = 0
    for debt in st.session_state.debts:
        debt_total += float(debt.get('monthly_payment', 0))
    
    # Variable expenses this month
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
st.title("💰 Household Budget Tracker")
st.markdown("Track income, expenses, debts & savings - your path to being debt-free")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚙️ Setup", "💳 Debts", "📸 Spending", "📊 Dashboard", "🎯 Budgets"])

with tab1:
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
        save_settings()
        st.success("✅ Saved!")

with tab2:
    st.markdown("### Debt Tracking & Management")
    
    st.markdown("#### ➕ Add New Debt")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        debt_name = st.text_input("Debt Name", placeholder="CC Debt / Car Loan / etc")
    with col2:
        principal = st.number_input("Principal Remaining (CAD)", min_value=0.0, step=100.0)
    with col3:
        monthly_payment = st.number_input("Monthly Payment (CAD)", min_value=0.0, step=50.0)
    with col4:
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, step=0.1)
    
    if st.button("➕ Add Debt"):
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
            save_debts()
            st.success(f"✅ {debt_name} added! Payoff timeline: {months_to_payoff} months")
    
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
                    save_debts()
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
    else:
        st.info("No debts tracked yet. Add one above!")

with tab3:
    st.markdown("### 📸 Track Variable Spending (Receipts)")
    
    uploaded_file = st.file_uploader("Upload Receipt", type=["jpg", "jpeg", "png", "gif", "webp"])
    
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
                    save_expenses()
                    
                    st.success("✅ Receipt processed!")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Store", receipt.get('merchant', 'N/A'))
                    with col2:
                        st.metric("Total", f"${receipt.get('total', 0):.2f}")
                    with col3:
                        st.metric("Category", category)

with tab4:
    st.markdown("### 📊 Complete Financial Dashboard")
    
    finances = calculate_monthly_finances()
    
    # Header
    st.markdown("#### 💰 Monthly Financial Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Income", f"${finances['total_income']:.2f}")
    with col2:
        st.metric("Fixed + Debt", f"${finances['fixed_total'] + finances['debt_payments']:.2f}")
    with col3:
        st.metric("Variable Spent", f"${finances['variable_total']:.2f}")
    with col4:
        st.metric("Remaining", f"${finances['remaining']:.2f}", delta=f"Surplus" if finances['remaining'] > 0 else "Deficit")
    
    # Income Breakdown
    st.markdown("#### 📥 Income")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"Your Salary: **${finances['your_salary']:.2f}**")
    with col2:
        st.write(f"Wife's Salary: **${finances['wife_salary']:.2f}**")
    with col3:
        st.write(f"**Total: ${finances['total_income']:.2f}**")
    
    # Fixed Expenses
    st.markdown("#### 🔧 Fixed Monthly Expenses (Auto-Deducted)")
    if finances['fixed_expenses']:
        for expense, amount in finances['fixed_expenses'].items():
            st.write(f"• {expense}: ${amount:.2f}")
        st.write(f"**Subtotal: ${finances['fixed_total']:.2f}**")
    
    # Debt Payments
    st.markdown("#### 💳 Monthly Debt Payments")
    if st.session_state.debts:
        for debt in st.session_state.debts:
            st.write(f"• {debt['name']}: ${debt['monthly_payment']:.2f}")
        st.write(f"**Subtotal: ${finances['debt_payments']:.2f}**")
    
    # Available for Variable
    st.markdown("#### 💵 Available for Variable Spending")
    available = finances['available_after_fixed_debt']
    spent = finances['variable_total']
    remaining = available - spent
    
    st.info(f"Budget: ${available:.2f} | Spent: ${spent:.2f} | Remaining: ${remaining:.2f}")
    
    # Variable by Category
    st.markdown("#### 📊 Variable Spending by Category (This Month)")
    if finances['variable_by_category']:
        for cat, amt in finances['variable_by_category'].items():
            st.write(f"• {cat}: ${amt:.2f}")
    
    # Debt Progress
    st.markdown("#### 🎯 Debt Payoff Progress")
    if st.session_state.debts:
        total_debt = sum(d['principal'] for d in st.session_state.debts)
        st.info(f"Total Remaining Debt: **${total_debt:.2f}**")
        st.write("Payoff Timeline:")
        for debt in st.session_state.debts:
            months = debt['months_to_payoff']
            years = months / 12
            st.write(f"• {debt['name']}: {months} months ({years:.1f} years)")

with tab5:
    st.markdown("### 🎯 Set Monthly Budgets for Variable Spending")
    
    categories = ['Groceries', 'Dining', 'Transportation', 'Entertainment', 'Shopping', 'Healthcare']
    
    for cat in categories:
        current = st.session_state.budgets.get(cat, 0)
        budget = st.number_input(f"{cat} Budget (CAD)", min_value=0.0, value=float(current), step=10.0)
        st.session_state.budgets[cat] = budget
    
    if st.button("💾 Save Budgets"):
        save_budgets()
        st.success("✅ Budgets saved!")

st.markdown("---")
st.markdown("💡 **This tracker helps you:** Track every penny | See debt payoff timeline | Plan for financial freedom")
