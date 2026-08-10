#!/usr/bin/env python3
"""
Smart Budget Tracker Web Server
================================

Flask web app for:
- Receipt upload from phone
- Real-time processing
- Results display
- Historical spending dashboard

Run: python web_server.py
Access: http://localhost:5000 (computer) or http://192.168.x.x:5000 (phone on same WiFi)
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import anthropic

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Data storage file
EXPENSES_FILE = 'expenses.json'

# Initialize Claude client
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))


def load_expenses():
    """Load all expenses from file."""
    if os.path.exists(EXPENSES_FILE):
        try:
            with open(EXPENSES_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_expenses(expenses):
    """Save expenses to file."""
    with open(EXPENSES_FILE, 'w') as f:
        json.dump(expenses, f, indent=2)


def extract_receipt(image_path):
    """Extract receipt details from image using Claude Vision."""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
    suffix = Path(image_path).suffix.lower()
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(suffix, 'image/jpeg')
    
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
    
    try:
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
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt}
                ],
            }],
        )
        
        response_text = message.content[0].text
        return json.loads(response_text)
    except:
        return {
            "merchant": "Unknown",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "items": [],
            "total": 0.00
        }


def categorize_expense(receipt):
    """Categorize expense based on merchant and items."""
    merchant = receipt.get('merchant', '').lower()
    items = [item.get('name', '').lower() for item in receipt.get('items', [])]
    items_text = ', '.join(items[:3])
    
    prompt = f"""Categorize into ONE category.

Merchant: {merchant}
Items: {items_text}

Choose from: Groceries, Dining, Transportation, Utilities, Entertainment, Shopping, Healthcare, Other

Output ONLY category name."""
    
    try:
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


def analyze_expenses(expenses):
    """Analyze spending patterns."""
    if not expenses:
        return {}
    
    total = sum(e.get('total', 0) for e in expenses)
    categories = defaultdict(float)
    
    for exp in expenses:
        cat = exp.get('category', 'Other')
        categories[cat] += exp.get('total', 0)
    
    daily_avg = total / max(len(expenses), 1)
    
    return {
        'total_spent': round(total, 2),
        'num_expenses': len(expenses),
        'avg_expense': round(total / len(expenses), 2) if expenses else 0,
        'daily_average': round(daily_avg, 2),
        'categories': {k: round(v, 2) for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)},
        'highest_category': max(categories, key=categories.get) if categories else 'N/A'
    }


def get_recommendations(analysis, expenses):
    """Generate AI recommendations."""
    if not expenses:
        return []
    
    cats = '\n'.join([f"- {cat}: ${amt:.2f}" for cat, amt in analysis.get('categories', {}).items()])
    
    prompt = f"""Provide 3 specific recommendations based on spending:

Total: ${analysis.get('total_spent', 0):.2f}
Categories:
{cats}

Format as bullet points starting with '-'. Be practical."""
    
    try:
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


# Routes

@app.route('/')
def index():
    """Upload page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle receipt upload and processing."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().timestamp()}_{filename}")
        file.save(filepath)
        
        # Extract receipt
        receipt = extract_receipt(filepath)
        
        # Categorize
        category = categorize_expense(receipt)
        receipt['category'] = category
        receipt['uploaded_at'] = datetime.now().isoformat()
        
        # Save to expenses
        expenses = load_expenses()
        expenses.append(receipt)
        save_expenses(expenses)
        
        # Analyze
        analysis = analyze_expenses(expenses)
        
        return jsonify({
            'success': True,
            'receipt': receipt,
            'analysis': analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/results')
def results():
    """Display latest results."""
    expenses = load_expenses()
    if not expenses:
        return render_template('results.html', latest=None, analysis={}, recommendations=[])
    
    latest = expenses[-1]
    analysis = analyze_expenses(expenses)
    recommendations = get_recommendations(analysis, expenses)
    
    return render_template('results.html', latest=latest, analysis=analysis, recommendations=recommendations)


@app.route('/history')
def history():
    """Historical spending dashboard."""
    expenses = load_expenses()
    analysis = analyze_expenses(expenses)
    recommendations = get_recommendations(analysis, expenses)
    
    # Predict monthly
    if expenses:
        daily_avg = analysis['daily_average']
        predicted_month = daily_avg * 30
    else:
        predicted_month = 0
    
    return render_template('history.html', 
                         expenses=expenses, 
                         analysis=analysis,
                         recommendations=recommendations,
                         predicted_month=round(predicted_month, 2))


@app.route('/api/expenses')
def api_expenses():
    """API endpoint for historical expenses."""
    expenses = load_expenses()
    analysis = analyze_expenses(expenses)
    
    return jsonify({
        'expenses': expenses,
        'analysis': analysis,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/export')
def api_export():
    """Export all data as JSON."""
    expenses = load_expenses()
    analysis = analyze_expenses(expenses)
    
    data = {
        'expenses': expenses,
        'analysis': analysis,
        'exported_at': datetime.now().isoformat()
    }
    
    return jsonify(data)


@app.route('/health')
def health():
    """Health check."""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Smart Budget Tracker Web Server")
    print("="*70)
    print("\n🚀 Server starting...")
    print("\n📱 Access from phone:")
    print("   1. On same WiFi: http://192.168.1.X:5000")
    print("   2. Replace X with your computer's IP")
    print("   3. To find IP: ipconfig (Windows) or ifconfig (Mac/Linux)")
    print("\n💻 Access from computer: http://localhost:5000")
    print("\n" + "="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
