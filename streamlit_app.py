"""
Smart Budget Tracker - Streamlit Version
=========================================

Mobile-friendly budget tracking with receipt OCR
Deploy to Streamlit Cloud (free, no laptop needed)

Run: streamlit run streamlit_app.py
"""

import streamlit as st
import json
import os
import base64
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from PIL import Image
import anthropic

# Page config
st.set_page_config(
    page_title="💰 Budget Tracker",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
    load_expenses()

# CSS styling
st.markdown("""
    <style>
    .main {
        max-width: 600px;
        margin: 0 auto;
    }
    .metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9em;
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

# File handling
EXPENSES_FILE = "expenses.json"

def load_expenses():
    """Load expenses from file."""
    if os.path.exists(EXPENSES_FILE):
        try:
            with open(EXPENSES_FILE, 'r') as f:
                st.session_state.expenses = json.load(f)
        except:
            st.session_state.expenses = []

def save_expenses():
    """Save expenses to file."""
    with open(EXPENSES_FILE, 'w') as f:
        json.dump(st.session_state.expenses, f, indent=2)

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
            model="claude-opus-4-1",
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

# Main UI
st.title("💰 Smart Budget Tracker")
st.markdown("Upload receipt photos to track spending")

# Tabs
tab1, tab2 = st.tabs(["📸 Upload Receipt", "📊 History"])

with tab1:
    st.markdown("### Upload Receipt Photo")
    
    uploaded_file = st.file_uploader(
        "Choose receipt image",
        type=["jpg", "jpeg", "png", "gif", "webp"],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        # Show image
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
        
        # Process
        if st.button("🤖 Process Receipt", use_container_width=True):
            with st.spinner("Processing receipt..."):
                image_bytes = uploaded_file.getvalue()
                receipt = extract_receipt(image_bytes)
                
                if receipt:
                    # Categorize
                    category = categorize_expense(receipt)
                    receipt['category'] = category
                    receipt['uploaded_at'] = datetime.now().isoformat()
                    
                    # Save
                    st.session_state.expenses.append(receipt)
                    save_expenses()
                    
                    # Show results
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

st.markdown("---")
st.markdown("Built with Claude Vision API + Streamlit")
