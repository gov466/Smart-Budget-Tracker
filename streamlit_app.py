"""
Health & Wealth Tracker with Google Sheets Integration
======================================================

Features:
1. Monthly income tracking (both salaries)
2. Fixed expenses (auto-deducted monthly)
3. Debt management & payoff tracking
4. Variable spending (receipts)
5. Health tracking (blood tests, metrics) with TREND CHARTS
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
import plotly.graph_objects as go
import plotly.express as px

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

def ensure_headers(ws, headers):
    """Ensure worksheet has proper headers - insert if needed"""
    try:
        all_values = ws.get_all_values()
        
        # If worksheet is empty, add headers
        if not all_values:
            ws.insert_row(headers, 1)
            return
        
        # If first row doesn't match headers, insert headers at top
        first_row = all_values[0]
        if first_row != headers:
            ws.insert_row(headers, 1)
    except:
        pass

def get_or_create_worksheet(sheet, name, headers):
    """Get worksheet by name or create if it doesn't exist"""
    try:
        ws = sheet.worksheet(name)
        ensure_headers(ws, headers)
        return ws
    except:
        ws = sheet.add_worksheet(title=name, rows=1000, cols=20)
        ws.append_row(headers)
        return ws

def load_settings():
    """Load settings from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return {}
        headers = ['your_salary', 'wife_salary', 'fixed_rent', 'fixed_car_payment', 'fixed_car_insurance', 'fixed_mobile', 'fixed_utilities', 'fixed_groceries_budget', 'fixed_tfsa', 'fixed_rrsp', 'fixed_india_transfer', 'fixed_other']
        ws = get_or_create_worksheet(sheet, "Settings", headers)
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
        headers = ['merchant', 'date', 'total', 'category', 'items', 'uploaded_at']
        ws = get_or_create_worksheet(sheet, "Expenses", headers)
        records = ws.get_all_records()
        # Parse items JSON if present
        for record in records:
            if 'items' in record and record['items']:
                try:
                    record['items'] = json.loads(record['items'])
                except:
                    record['items'] = []
        return records
    except:
        return []

def load_debts():
    """Load debts from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return []
        headers = ['name', 'principal', 'monthly_payment', 'interest_rate', 'months_to_payoff', 'created_date']
        ws = get_or_create_worksheet(sheet, "Debts", headers)
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
        headers = ['date', 'metric', 'value', 'unit', 'normal_range', 'type', 'added_at']
        ws = get_or_create_worksheet(sheet, "Health", headers)
        return ws.get_all_records()
    except:
        return []

def load_budgets():
    """Load budgets from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return {}
        headers = ['Groceries', 'Dining', 'Transportation', 'Entertainment', 'Shopping', 'Healthcare']
        ws = get_or_create_worksheet(sheet, "Budget", headers)
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
        
        headers = ['name', 'principal', 'monthly_payment', 'interest_rate', 'months_to_payoff', 'created_date']
        ws = get_or_create_worksheet(sheet, "Debts", headers)
        
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

def delete_debt_from_gsheet(debt_name):
    """Delete debt row from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        headers = ['name', 'principal', 'monthly_payment', 'interest_rate', 'months_to_payoff', 'created_date']
        ws = get_or_create_worksheet(sheet, "Debts", headers)
        records = ws.get_all_records()
        
        for idx, record in enumerate(records, start=2):
            if record.get('name') == debt_name:
                ws.delete_rows(idx)
                return True
        return False
    except Exception as e:
        st.error(f"Error deleting debt: {str(e)}")
        return False

def update_debt_in_gsheet(old_name, new_debt):
    """Update debt in Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        headers = ['name', 'principal', 'monthly_payment', 'interest_rate', 'months_to_payoff', 'created_date']
        ws = get_or_create_worksheet(sheet, "Debts", headers)
        records = ws.get_all_records()
        
        for idx, record in enumerate(records, start=2):
            if record.get('name') == old_name:
                ws.update([[
                    new_debt.get('name', ''),
                    new_debt.get('principal', ''),
                    new_debt.get('monthly_payment', ''),
                    new_debt.get('interest_rate', ''),
                    new_debt.get('months_to_payoff', ''),
                    new_debt.get('created_date', '')
                ]], f'A{idx}:F{idx}')
                return True
        return False
    except Exception as e:
        st.error(f"Error updating debt: {str(e)}")
        return False

def save_expense_to_gsheet(expense):
    """Add new expense to Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        headers = ['merchant', 'date', 'total', 'category', 'items', 'uploaded_at']
        ws = get_or_create_worksheet(sheet, "Expenses", headers)
        
        # Convert items list to JSON string
        items_json = json.dumps(expense.get('items', []))
        
        row = [
            expense.get('merchant', ''),
            expense.get('date', ''),
            expense.get('total', ''),
            expense.get('category', ''),
            items_json,
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
        
        headers = ['date', 'metric', 'value', 'unit', 'normal_range', 'type', 'added_at']
        ws = get_or_create_worksheet(sheet, "Health", headers)
        
        row = [
            health_entry.get('date', ''),
            health_entry.get('metric', ''),
            health_entry.get('value', ''),
            health_entry.get('unit', ''),
            health_entry.get('normal_range', ''),
            health_entry.get('type', ''),
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
        
        headers = ['your_salary', 'wife_salary', 'fixed_rent', 'fixed_car_payment', 'fixed_car_insurance', 'fixed_mobile', 'fixed_utilities', 'fixed_groceries_budget', 'fixed_tfsa', 'fixed_rrsp', 'fixed_india_transfer', 'fixed_other']
        ws = get_or_create_worksheet(sheet, "Settings", headers)
        
        all_rows = ws.get_all_values()
        if len(all_rows) > 1:
            ws.delete_rows(2, len(all_rows))
        
        values = [str(settings.get(k, '')) for k in headers]
        ws.append_row(values)
        return True
    except Exception as e:
        st.error(f"Error saving settings: {str(e)}")
        return False

def extract_receipt(image_bytes):
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
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

def extract_health_report(image_bytes):
    """Extract health metrics from blood test report using Claude Vision"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
        
        prompt = """Extract ALL health metrics from this blood test report. Output ONLY valid JSON.
{
    "test_date": "YYYY-MM-DD",
    "metrics": [
        {
            "name": "Cholesterol",
            "value": 200,
            "unit": "mg/dL",
            "normal_range": "120-200"
        }
    ]
}
Extract EVERY metric shown. Be precise with numbers and units."""
        
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=2000,
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
        st.error(f"Error extracting report: {str(e)}")
        return None

def categorize_expense(receipt):
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
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

def analyze_grocery_health(items, health_metrics=None):
    """Analyze groceries and give recommendations (generic or personalized)"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Build item list
        items_text = "\n".join([f"- {item.get('name', 'N/A')}" for item in items])
        
        if health_metrics:
            # PERSONALIZED mode - with health data
            health_text = "\n".join([f"- {m.get('metric', 'N/A')}: {m.get('value')} {m.get('unit')} (Normal: {m.get('normal_range')})" 
                                    for m in health_metrics[-5:]], f'A{idx}:F{idx}')  # Last 5 metrics
            
            prompt = f"""You are a nutritionist. Analyze these groceries BASED ON THIS PERSON'S HEALTH.

Their Health Metrics:
{health_text}

Their Groceries:
{items_text}

For EACH grocery item, give:
1. ✅ or ❌ or ⚠️ rating (based on their health)
2. Why (how it affects their health)

Then:
3. Overall grocery grade (A to F)
4. Top 3 items to KEEP
5. Top 3 items to REDUCE or REPLACE
6. Health-specific tips

Output ONLY valid JSON:
{{
    "items_analysis": [
        {{"name": "Item", "rating": "✅", "reason": "why"}},
    ],
    "overall_grade": "B+",
    "keep_items": ["item1", "item2"],
    "reduce_items": ["item1", "item2"],
    "tips": ["tip1", "tip2"],
    "personalized_note": "Based on your high cholesterol..."
}}"""
        else:
            # GENERIC mode - no health data
            prompt = f"""You are a nutritionist. Analyze these groceries for GENERAL HEALTH.

Groceries:
{items_text}

For EACH item, give:
1. ✅ or ⚠️ rating (general health)
2. Why (nutritional value)

Then:
3. Overall grocery grade (A to F)
4. Top healthy items
5. Items to moderate
6. General healthy eating tips

Output ONLY valid JSON:
{{
    "items_analysis": [
        {{"name": "Item", "rating": "✅", "reason": "good source of fiber"}},
    ],
    "overall_grade": "B",
    "keep_items": ["item1", "item2"],
    "reduce_items": ["item1", "item2"],
    "tips": ["tip1", "tip2"],
    "note": "⚠️ Upload health reports for personalized recommendations!"
}}"""
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(message.content[0].text)
    except Exception as e:
        st.error(f"Error analyzing groceries: {str(e)}")
        return None
    """Analyze health metrics"""
    if not health_list:
        return None
    
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        latest = health_list[-1] if health_list else {}
        metrics_text = '\n'.join([f"- {k}: {v}" for k, v in latest.items() if k not in ['date', 'added_at']], f'A{idx}:F{idx}')
        
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

def plot_health_trend(health_metrics, metric_name):
    """Create trend chart for a health metric"""
    data = [h for h in health_metrics if h.get('metric', '').lower() == metric_name.lower()]
    
    if len(data) < 2:
        return None
    
    try:
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.dropna(subset=['value']).sort_values('date')
        
        if df.empty:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['value'],
            mode='lines+markers',
            name=metric_name,
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=8)
        ))
        
        normal_range = data[0].get('normal_range', '')
        if normal_range and '-' in normal_range:
            try:
                min_val, max_val = normal_range.split('-')
                min_val = float(min_val.strip())
                max_val = float(max_val.strip())
                
                fig.add_hline(y=min_val, line_dash="dash", line_color="green", annotation_text="Normal Range")
                fig.add_hline(y=max_val, line_dash="dash", line_color="green")
            except:
                pass
        
        fig.update_layout(
            title=f"{metric_name} Trend Over Time",
            xaxis_title="Date",
            yaxis_title=f"{metric_name} ({data[0].get('unit', '')})",
            hovermode='x unified',
            height=400
        )
        
        return fig
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
        
        for i, debt in enumerate(st.session_state.debts):
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 0.7, 0.7])
            
            with col1:
                st.write(f"**{debt.get('name', 'N/A')}**")
            with col2:
                st.write(f"${debt.get('principal', 0):.2f}")
            with col3:
                st.write(f"${debt.get('monthly_payment', 0):.2f}/mo")
            with col4:
                st.write(f"{debt.get('months_to_payoff', 0)} months")
            with col5:
                if st.button("✏️", key=f"edit_debt_{i}", help="Edit"):
                    st.session_state[f"editing_debt_{i}"] = not st.session_state.get(f"editing_debt_{i}", False)
            with col6:
                if st.button("🗑️", key=f"del_debt_{i}", help="Delete"):
                    if delete_debt_from_gsheet(debt.get('name', '')):
                        st.session_state.debts.pop(i)
                        st.success(f"✅ {debt.get('name', '')} deleted!")
                        st.rerun()
            
            # Edit form
            if st.session_state.get(f"editing_debt_{i}", False):
                st.write("**Edit Debt:**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    edit_name = st.text_input("Debt Name", value=debt.get('name', ''), key=f"edit_name_{i}")
                with col2:
                    edit_principal = st.number_input("Principal", value=float(debt.get('principal', 0)), key=f"edit_principal_{i}")
                with col3:
                    edit_payment = st.number_input("Monthly Payment", value=float(debt.get('monthly_payment', 0)), key=f"edit_payment_{i}")
                with col4:
                    edit_rate = st.number_input("Interest Rate %", value=float(debt.get('interest_rate', 0)), key=f"edit_rate_{i}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save", key=f"save_edit_{i}"):
                        new_months = int(edit_principal / edit_payment) if edit_payment > 0 else 0
                        updated_debt = {
                            'name': edit_name,
                            'principal': edit_principal,
                            'monthly_payment': edit_payment,
                            'interest_rate': edit_rate,
                            'months_to_payoff': new_months,
                            'created_date': debt.get('created_date', '')
                        }
                        if update_debt_in_gsheet(debt.get('name', ''), updated_debt):
                            st.session_state.debts[i] = updated_debt
                            st.session_state[f"editing_debt_{i}"] = False
                            st.success("✅ Debt updated!")
                            st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_edit_{i}"):
                        st.session_state[f"editing_debt_{i}"] = False
                        st.rerun()
            
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
                        
                        st.markdown("#### 📋 Items Extracted:")
                        items = receipt.get('items', [])
                        if items:
                            for item in items:
                                st.write(f"• {item.get('name', 'N/A')} - Qty: {item.get('quantity', 1)}, Price: ${item.get('price', 0):.2f}")
                        else:
                            st.info("No items found in receipt")
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
    st.markdown("### 🏥 Health Tracking & Analysis with Trends")
    
    st.markdown("#### 📄 Upload Health Report (Auto-Extract)")
    uploaded_report = st.file_uploader("Upload Blood Test Report", type=["jpg", "jpeg", "png", "gif", "webp", "pdf"], key="health_report_upload")
    
    if uploaded_report:
        st.info("📊 Processing your health report...")
        if st.button("🤖 Extract Metrics from Report"):
            with st.spinner("Analyzing report..."):
                extracted = extract_health_report(uploaded_report.getvalue())
                
                if extracted:
                    st.success("✅ Metrics extracted!")
                    test_date = extracted.get('test_date', str(datetime.now().date()))
                    metrics = extracted.get('metrics', [])
                    
                    st.markdown("**Extracted Metrics:**")
                    for metric in metrics:
                        st.write(f"• **{metric.get('name')}**: {metric.get('value')} {metric.get('unit')} (Normal: {metric.get('normal_range')})")
                    
                    if st.button("💾 Save All Metrics to Google Sheets"):
                        saved_count = 0
                        for metric in metrics:
                            health_entry = {
                                'date': test_date,
                                'metric': metric.get('name', ''),
                                'value': metric.get('value', ''),
                                'unit': metric.get('unit', ''),
                                'normal_range': metric.get('normal_range', ''),
                                'type': 'Blood Test',
                                'added_at': datetime.now().isoformat()
                            }
                            if save_health_to_gsheet(health_entry):
                                st.session_state.health_metrics.append(health_entry)
                                saved_count += 1
                        
                        st.success(f"✅ {saved_count} metrics saved to Google Sheets!")
                        st.balloons()
    
    st.markdown("---")
    
    st.markdown("#### 📊 OR Enter Health Metrics Manually")
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
    
    st.markdown("#### 📈 Health Analysis & Trends")
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
        
        st.markdown("#### 📊 Metric Trends Over Time")
        unique_metrics = sorted(set(h.get('metric', '') for h in st.session_state.health_metrics))
        
        if unique_metrics:
            selected_metric = st.selectbox("Select metric to view trend", unique_metrics)
            fig = plot_health_trend(st.session_state.health_metrics, selected_metric)
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Need at least 2 data points to show trend. Keep adding health metrics!")
        
        st.markdown("#### 📋 Your Metrics History")
        for metric in reversed(st.session_state.health_metrics[-10:]):
            st.write(f"**{metric.get('date')}** - {metric.get('metric')}: {metric.get('value')} {metric.get('unit')} (Normal: {metric.get('normal_range')})")

with tabs[5]:  # Smart Grocery
    st.markdown("### 🥗 Smart Grocery Recommendations")
    
    if st.session_state.expenses:
        # Collect all grocery items
        all_items = []
        for expense in st.session_state.expenses:
            items = expense.get('items', [])
            if items:
                all_items.extend(items)
        
        if all_items:
            st.markdown("#### 📊 Analyzing Your Groceries...")
            
            # Check if health metrics exist
            has_health_data = len(st.session_state.health_metrics) > 0
            
            if st.button("🤖 Get Smart Recommendations"):
                with st.spinner("Analyzing your groceries..."):
                    # If health data exists, use personalized mode
                    if has_health_data:
                        analysis = analyze_grocery_health(all_items, st.session_state.health_metrics)
                        mode = "PERSONALIZED (based on your health)"
                    else:
                        analysis = analyze_grocery_health(all_items, None)
                        mode = "GENERIC (general health guidelines)"
                    
                    if analysis:
                        st.success(f"✅ Analysis Complete ({mode})")
                        
                        # Overall Grade
                        grade = analysis.get('overall_grade', 'N/A')
                        st.markdown(f"### 📈 Your Grocery Grade: **{grade}**")
                        
                        # Items Analysis
                        st.markdown("#### 📋 Item Analysis:")
                        for item_analysis in analysis.get('items_analysis', []):
                            rating = item_analysis.get('rating', '?')
                            name = item_analysis.get('name', 'Unknown')
                            reason = item_analysis.get('reason', '')
                            st.write(f"{rating} **{name}** - {reason}")
                        
                        # Keep Items
                        st.markdown("#### ✅ Items to KEEP:")
                        for item in analysis.get('keep_items', []):
                            st.write(f"• {item}")
                        
                        # Reduce Items
                        st.markdown("#### ⚠️ Items to REDUCE or REPLACE:")
                        for item in analysis.get('reduce_items', []):
                            st.write(f"• {item}")
                        
                        # Tips
                        st.markdown("#### 💡 Tips:")
                        for tip in analysis.get('tips', []):
                            st.write(f"• {tip}")
                        
                        # Note
                        note = analysis.get('personalized_note') or analysis.get('note', '')
                        if note:
                            if has_health_data:
                                st.info(f"📊 {note}")
                            else:
                                st.warning(f"⚠️ {note}")
                        
                        # Encourage health reports if not present
                        if not has_health_data:
                            st.markdown("---")
                            st.success("💪 **Tip:** Upload health reports to get PERSONALIZED recommendations based on YOUR health metrics!")
        else:
            st.info("📸 No grocery items found. Upload receipts first to get recommendations!")
    else:
        st.info("📸 No grocery data. Upload receipts to get smart recommendations!")

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
