"""
Smart Budget Tracker - Enhanced Version
========================================

Features:
1. Receipt upload + extraction
2. Budget management per category
3. Weekly trend comparison
4. Smart store recommendations
5. Item pattern learning
6. Category overspending alerts

Run: streamlit run streamlit_app.py
"""

import streamlit as st
import json
import os
import base64
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from PIL import Image
import anthropic
import pandas as pd

# File handling - MUST BE FIRST
EXPENSES_FILE = "expenses.json"
BUDGETS_FILE = "budgets.json"

def load_expenses():
    """Load expenses from file."""
    if os.path.exists(EXPENSES_FILE):
        try:
            with open(EXPENSES_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def load_budgets():
    """Load budget settings."""
    if os.path.exists(BUDGETS_FILE):
        try:
            with open(BUDGETS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# Page config
st.set_page_config(
    page_title="💰 Budget Tracker",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'expenses' not in st.session_state:
    st.session_state.expenses = load_expenses()

if 'budgets' not in st.session_state:
    st.session_state.budgets = load_budgets()

def save_expenses():
    """Save expenses to file."""
    with open(EXPENSES_FILE, 'w') as f:
        json.dump(st.session_state.expenses, f, indent=2)

def save_budgets():
    """Save budgets to file."""
    with open(BUDGETS_FILE, 'w') as f:
        json.dump(st.session_state.budgets, f, indent=2)

def extract_receipt(image_bytes):
    """Extract receipt details using Claude Vision."""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
        image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
        
        prompt = """Extract receipt information. Output ONLY valid JSON.

{
    "merchant": "Store name",
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "items": [
        {"name": "Item name", "quantity": 1, "price": 0.00}
    ],
    "subtotal": 0.00,
    "tax": 0.00,
    "total": 0.00,
    "payment_method": "Card/Cash"
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
        
        response_text = message.content[0].text
        return json.loads(response_text)
    except Exception as e:
        st.error(f"Error processing receipt: {str(e)}")
        return None

def categorize_expense(receipt):
    """Categorize expense."""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
        merchant = receipt.get('merchant', '').lower()
        items = [item.get('name', '').lower() for item in receipt.get('items', [])]
        items_text = ', '.join(items[:3])
        
        prompt = f"""Categorize into ONE category.

Merchant: {merchant}
Items: {items_text}

Choose from: Groceries, Dining, Transportation, Utilities, Entertainment, Shopping, Healthcare, Other

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

def get_recommendations(analysis):
    """Get AI recommendations."""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
        cats = '\n'.join([f"- {cat}: ${amt:.2f}" for cat, amt in analysis.get('categories', {}).items()])
        
        prompt = f"""Provide 3 specific recommendations based on spending:

Total: ${analysis.get('total_spent', 0):.2f}
Categories:
{cats}

Format as bullet points starting with '-'. Be practical and specific."""
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = message.content[0].text
        recs = [line.strip() for line in text.split('\n') if line.strip().startswith('-')]
        return [r.replace('-', '').strip() for r in recs[:3]]
    except:
        return ["Keep tracking expenses for insights"]

def analyze_expenses():
    """Analyze spending."""
    if not st.session_state.expenses:
        return {}
    
    total = sum(e.get('total', 0) for e in st.session_state.expenses)
    categories = defaultdict(float)
    
    for exp in st.session_state.expenses:
        cat = exp.get('category', 'Other')
        categories[cat] += exp.get('total', 0)
    
    daily_avg = total / max(len(st.session_state.expenses), 1)
    
    return {
        'total_spent': round(total, 2),
        'num_expenses': len(st.session_state.expenses),
        'avg_expense': round(total / len(st.session_state.expenses), 2) if st.session_state.expenses else 0,
        'daily_average': round(daily_avg, 2),
        'categories': {k: round(v, 2) for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)},
        'highest_category': max(categories, key=categories.get) if categories else 'N/A'
    }

def get_weekly_comparison():
    """Compare this week vs last week."""
    if not st.session_state.expenses:
        return None
    
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)
    
    this_week = defaultdict(float)
    last_week = defaultdict(float)
    
    for exp in st.session_state.expenses:
        try:
            exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
            cat = exp.get('category', 'Other')
            amt = exp.get('total', 0)
            
            if exp_date >= week_ago:
                this_week[cat] += amt
            elif exp_date >= two_weeks_ago:
                last_week[cat] += amt
        except:
            pass
    
    return {
        'this_week': dict(this_week),
        'last_week': dict(last_week)
    }

def get_store_recommendation():
    """Smart store recommendation based on buying patterns."""
    if not st.session_state.expenses:
        return None
    
    # Get this week's groceries
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    weekly_items = defaultdict(list)
    stores = defaultdict(float)
    
    for exp in st.session_state.expenses:
        try:
            if exp.get('category') != 'Groceries':
                continue
                
            exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
            if exp_date < week_ago:
                continue
            
            store = exp.get('merchant', 'Unknown')
            total = exp.get('total', 0)
            items = exp.get('items', [])
            
            # Track items by name
            for item in items:
                item_name = item.get('name', 'Item').lower()
                weekly_items[item_name].append({
                    'store': store,
                    'price': item.get('price', 0),
                    'quantity': item.get('quantity', 1)
                })
            
            stores[store] += total
        except:
            pass
    
    if not weekly_items or not stores:
        return None
    
    # Calculate average prices per item at each store
    store_prices = defaultdict(lambda: defaultdict(list))
    
    for item_name, prices in weekly_items.items():
        for price_info in prices:
            store = price_info['store']
            price = price_info['price']
            store_prices[store][item_name].append(price)
    
    # Estimate total cost at each store
    store_estimates = {}
    for store in stores.keys():
        estimated_total = 0
        for item_name, prices in weekly_items.items():
            if item_name in store_prices[store]:
                avg_price = sum(store_prices[store][item_name]) / len(store_prices[store][item_name])
                estimated_total += avg_price
        store_estimates[store] = round(estimated_total, 2)
    
    if not store_estimates:
        return None
    
    cheapest_store = min(store_estimates, key=store_estimates.get)
    current_avg = sum(stores.values()) / len(stores)
    potential_savings = current_avg - store_estimates[cheapest_store]
    
    return {
        'cheapest_store': cheapest_store,
        'estimated_cost': store_estimates[cheapest_store],
        'current_avg': round(current_avg, 2),
        'potential_savings': round(potential_savings, 2),
        'store_estimates': store_estimates,
        'item_count': len(weekly_items)
    }

def get_budget_alerts():
    """Get budget alerts for overspending."""
    if not st.session_state.budgets:
        return []
    
    analysis = analyze_expenses()
    alerts = []
    
    for category, budget in st.session_state.budgets.items():
        spent = analysis.get('categories', {}).get(category, 0)
        percentage = (spent / budget * 100) if budget > 0 else 0
        
        if percentage >= 100:
            alerts.append({
                'category': category,
                'spent': spent,
                'budget': budget,
                'percentage': round(percentage, 1),
                'status': '🔴 OVER BUDGET',
                'overage': round(spent - budget, 2)
            })
        elif percentage >= 80:
            alerts.append({
                'category': category,
                'spent': spent,
                'budget': budget,
                'percentage': round(percentage, 1),
                'status': '🟡 WARNING',
                'remaining': round(budget - spent, 2)
            })
    
    return alerts

# Main UI
st.title("💰 Smart Budget Tracker")
st.markdown("Upload receipt photos to track spending with AI insights")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📸 Upload", "📊 Dashboard", "⚙️ Budgets", "🏪 Store Tips"])

with tab1:
    st.markdown("### Upload Receipt Photo")
    
    uploaded_file = st.file_uploader(
        "Choose receipt image",
        type=["jpg", "jpeg", "png", "gif", "webp"],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
        
        if st.button("🤖 Process Receipt", use_container_width=True):
            with st.spinner("Processing receipt..."):
                image_bytes = uploaded_file.getvalue()
                receipt = extract_receipt(image_bytes)
                
                if receipt:
                    category = categorize_expense(receipt)
                    receipt['category'] = category
                    receipt['uploaded_at'] = datetime.now().isoformat()
                    
                    st.session_state.expenses.append(receipt)
                    save_expenses()
                    
                    st.success("✅ Receipt processed!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Merchant", receipt.get('merchant', 'N/A'))
                    with col2:
                        st.metric("Total", f"${receipt.get('total', 0):.2f}")
                    with col3:
                        st.metric("Category", receipt.get('category', 'N/A'))
                    
                    st.markdown("### Items")
                    for item in receipt.get('items', []):
                        st.write(f"• {item.get('name', 'Item')}: ${item.get('price', 0):.2f}")

with tab2:
    st.markdown("### Spending Dashboard")
    
    if st.session_state.expenses:
        analysis = analyze_expenses()
        
        # BUDGET ALERTS
        alerts = get_budget_alerts()
        if alerts:
            st.markdown("### 🚨 Budget Alerts")
            for alert in alerts:
                if alert['status'] == '🔴 OVER BUDGET':
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.error(f"{alert['category']}: {alert['status']}")
                    with col2:
                        st.metric("Spent", f"${alert['spent']:.2f}")
                    with col3:
                        st.metric("Over by", f"${alert['overage']:.2f}")
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.warning(f"{alert['category']}: {alert['status']}")
                    with col2:
                        st.metric("Spent", f"${alert['spent']:.2f}")
                    with col3:
                        st.metric("Remaining", f"${alert['remaining']:.2f}")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", f"${analysis['total_spent']:.2f}")
        with col2:
            st.metric("Avg Day", f"${analysis['daily_average']:.2f}")
        with col3:
            st.metric("Purchases", analysis['num_expenses'])
        with col4:
            st.metric("Avg Purchase", f"${analysis['avg_expense']:.2f}")
        
        # WEEKLY COMPARISON
        weekly = get_weekly_comparison()
        if weekly and (weekly['this_week'] or weekly['last_week']):
            st.markdown("### 📈 Weekly Comparison")
            
            for category in set(list(weekly['this_week'].keys()) + list(weekly['last_week'].keys())):
                this = weekly['this_week'].get(category, 0)
                last = weekly['last_week'].get(category, 0)
                
                if last > 0:
                    change = ((this - last) / last * 100)
                    if change > 0:
                        st.write(f"**{category}:** ${this:.2f} (↑ {change:.0f}% vs last week: ${last:.2f})")
                    elif change < 0:
                        st.write(f"**{category}:** ${this:.2f} (↓ {-change:.0f}% vs last week: ${last:.2f})")
                    else:
                        st.write(f"**{category}:** ${this:.2f} (same as last week)")
                else:
                    st.write(f"**{category}:** ${this:.2f} (new this week)")
        
        # Prediction
        predicted_month = analysis['daily_average'] * 30
        st.info(f"🔮 **Predicted Monthly Spending:** ${predicted_month:.2f}")
        
        # Category breakdown
        st.markdown("### Category Breakdown")
        if analysis['categories']:
            max_amt = max(analysis['categories'].values())
            for cat, amt in analysis['categories'].items():
                pct = (amt / analysis['total_spent'] * 100) if analysis['total_spent'] > 0 else 0
                st.write(f"{cat}: ${amt:.2f} ({pct:.1f}%)")
                st.progress(amt / max_amt)
        
        # Recommendations
        st.markdown("### AI Recommendations")
        recs = get_recommendations(analysis)
        for i, rec in enumerate(recs, 1):
            st.write(f"{i}. {rec}")
        
        # Recent expenses
        st.markdown("### Recent Expenses")
        for exp in reversed(st.session_state.expenses[-5:]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{exp.get('merchant', 'Unknown')}** ({exp.get('category', 'Other')})")
                st.caption(exp.get('date', 'N/A'))
            with col2:
                st.write(f"${exp.get('total', 0):.2f}")
        
        # Export
        if st.button("📥 Export Data as JSON"):
            data = {
                'expenses': st.session_state.expenses,
                'analysis': analysis,
                'exported_at': datetime.now().isoformat()
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(data, indent=2),
                file_name=f"budget_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    else:
        st.info("📸 No expenses yet. Upload a receipt to get started!")

with tab3:
    st.markdown("### Set Budget by Category")
    
    categories = ['Groceries', 'Dining', 'Transportation', 'Utilities', 'Entertainment', 'Shopping', 'Healthcare']
    
    col1, col2 = st.columns(2)
    with col1:
        selected_category = st.selectbox("Select Category", categories)
    
    with col2:
        current_budget = st.session_state.budgets.get(selected_category, 0)
        budget_amount = st.number_input(
            f"Monthly Budget for {selected_category}",
            min_value=0.0,
            value=float(current_budget),
            step=10.0
        )
    
    if st.button("💾 Save Budget"):
        st.session_state.budgets[selected_category] = budget_amount
        save_budgets()
        st.success(f"✅ Budget set: ${budget_amount:.2f}/month for {selected_category}")
    
    st.markdown("### Current Budgets")
    if st.session_state.budgets:
        for cat, budget in st.session_state.budgets.items():
            st.write(f"**{cat}:** ${budget:.2f}/month")
    else:
        st.info("No budgets set yet")

with tab4:
    st.markdown("### 🏪 Smart Store Recommendations")
    
    if st.session_state.expenses:
        rec = get_store_recommendation()
        
        if rec:
            st.success(f"💡 **SAVE ${rec['potential_savings']:.2f} THIS WEEK!**")
            
            st.markdown(f"### Go to **{rec['cheapest_store'].upper()}** 🎯")
            st.write(f"Estimated cost for your {rec['item_count']} regular items: **${rec['estimated_cost']:.2f}**")
            st.write(f"Your current average: ${rec['current_avg']:.2f}")
            st.write(f"**Potential savings: ${rec['potential_savings']:.2f}**")
            
            st.markdown("### Store Comparison")
            store_df = pd.DataFrame([
                {'Store': store, 'Estimated Cost': f"${cost:.2f}"}
                for store, cost in rec['store_estimates'].items()
            ])
            st.table(store_df)
            
            st.markdown("---")
            st.write("💡 **How this works:**")
            st.write("- Tracks items you regularly buy")
            st.write("- Compares prices across stores")
            st.write("- Recommends cheapest option for your weekly shop")
        else:
            st.info("📸 Upload more grocery receipts from different stores to see recommendations!")
    else:
        st.info("📸 Upload receipts to get smart store recommendations!")

st.markdown("---")
st.markdown("Built with Claude Vision API + Streamlit | Smart Budgeting with AI")
