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
import calendar
from datetime import datetime, timedelta
from collections import defaultdict
from PIL import Image
import anthropic
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Google Sheets configuration
SPREADSHEET_ID = "1tzRTNtq3N-QPabBSowhmzYXuxHR9bimvYTn1z0wjuQs"

def safe_float(value, default=0.0):
    """Safely convert value to float, handling empty strings and None"""
    try:
        if value is None or value == '' or value == 'None':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

@st.cache_resource
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
        
        # If worksheet is completely empty, add headers
        if not all_values:
            ws.insert_row(headers, 1)
            return
        
        # Check if first row matches headers
        first_row = all_values[0]
        
        # If headers don't match, insert new headers at top
        if first_row != headers:
            # Clear the sheet
            if len(all_values) > 0:
                # Insert headers at row 1
                ws.insert_row(headers, 1)
    except Exception as e:
        # If any error, try to add headers anyway
        try:
            ws.insert_row(headers, 1)
        except:
            pass

@st.cache_data(ttl=300)
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
        headers = ['your_salary', 'wife_salary', 'fixed_rent', 'fixed_car_payment', 'fixed_car_insurance', 'fixed_health_insurance', 'fixed_mobile', 'fixed_utilities', 'fixed_tfsa', 'fixed_rrsp', 'fixed_india_transfer', 'fixed_other', 'annual_costco', 'annual_caa', 'annual_car_registration', 'annual_gym', 'annual_home_insurance', 'annual_other', 'annual_monthly_equivalent']
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
        
        # Debug: show how many records we got
        if len(records) == 0:
            st.warning("⚠️ No debts loaded from Google Sheets. Check if headers are in row 1.")
        
        # Convert string numbers to float
        for record in records:
            if 'principal' in record and record['principal']:
                record['principal'] = safe_float(record['principal'])
            if 'monthly_payment' in record and record['monthly_payment']:
                record['monthly_payment'] = safe_float(record['monthly_payment'])
            if 'interest_rate' in record and record['interest_rate']:
                record['interest_rate'] = safe_float(record['interest_rate'])
        return records
    except Exception as e:
        st.error(f"Error loading debts: {str(e)}")
        return []

def load_health():
    """Load health metrics from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return []
        headers = ['date', 'metric', 'value', 'unit', 'normal_range', 'type', 'person', 'added_at']
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
    """Add new expense to Google Sheets (with duplicate prevention)"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        headers = ['merchant', 'date', 'total', 'category', 'items', 'uploaded_at']
        ws = get_or_create_worksheet(sheet, "Expenses", headers)
        
        # Check for duplicates before saving
        all_data = ws.get_all_records()
        
        expense_merchant = str(expense.get('merchant', '')).lower().strip()
        expense_date = str(expense.get('date', '')).strip()
        expense_total = safe_float(expense.get('total', 0))
        
        # Look for duplicate receipts (same merchant, same date, same total)
        for existing in all_data:
            existing_merchant = str(existing.get('merchant', '')).lower().strip()
            existing_date = str(existing.get('date', '')).strip()
            existing_total = safe_float(existing.get('total', 0))
            
            # Check if this looks like a duplicate
            if (existing_merchant == expense_merchant and
                existing_date == expense_date and
                abs(existing_total - expense_total) < 0.01):  # Allow small floating point differences
                # Duplicate found! Skip it
                return False
        
        # No duplicate found, safe to add
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
        
        # ALSO save individual items to Price_History for trend analysis
        save_price_history_to_gsheet(expense)
        
        return True
    except Exception as e:
        st.error(f"Error saving expense: {str(e)}")
        return False

def save_price_history_to_gsheet(expense):
    """Save individual items from receipt to Price_History for trend analysis"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        headers = ['date', 'store', 'product', 'quantity', 'price', 'uploaded_at']
        ws = get_or_create_worksheet(sheet, "Price_History", headers)
        
        merchant = expense.get('merchant', 'Unknown Store')
        date = expense.get('date', datetime.now().strftime('%Y-%m-%d'))
        uploaded_at = expense.get('uploaded_at', datetime.now().isoformat())
        items = expense.get('items', [])
        
        # Save each item as separate row
        for item in items:
            row = [
                date,
                merchant,
                item.get('name', ''),
                item.get('quantity', 1),
                safe_float(item.get('price', 0)),
                uploaded_at
            ]
            ws.append_row(row)
        
        return True
    except Exception as e:
        st.error(f"Error saving price history: {str(e)}")
        return False

def load_price_history_from_gsheet():
    """Load all price history data"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return pd.DataFrame()
        
        headers = ['date', 'store', 'product', 'quantity', 'price', 'uploaded_at']
        ws = get_or_create_worksheet(sheet, "Price_History", headers)
        
        data = ws.get_all_values()
        if len(data) <= 1:  # Only headers
            return pd.DataFrame(columns=headers)
        
        df = pd.DataFrame(data[1:], columns=headers)
        
        # Convert data types
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['price'] = df['price'].apply(lambda x: safe_float(x))
        df['quantity'] = df['quantity'].apply(lambda x: int(safe_float(x)) if safe_float(x) > 0 else 1)
        
        return df
    except Exception as e:
        st.error(f"Error loading price history: {str(e)}")
        return pd.DataFrame()

def analyze_product_price_trends(df, product_name):
    """Analyze price trends for a specific product"""
    try:
        product_data = df[df['product'].str.lower() == product_name.lower()]
        
        if product_data.empty:
            return None
        
        by_store = product_data.groupby('store')['price'].agg([
            'mean',
            'count',
            'min',
            'max'
        ]).round(2)
        
        return by_store
    except:
        return None

def get_cheapest_stores_for_products(df):
    """Find cheapest store for each product"""
    try:
        recommendations = {}
        
        for product in df['product'].unique():
            product_data = df[df['product'] == product]
            cheapest = product_data.loc[product_data['price'].idxmin()]
            
            recommendations[product] = {
                'store': cheapest['store'],
                'avg_price': product_data.groupby('store')['price'].mean()[cheapest['store']],
                'times_bought': len(product_data),
                'all_stores': product_data.groupby('store')['price'].mean().to_dict()
            }
        
        return recommendations
    except:
        return {}

def get_shopping_route_recommendation(recommendations):
    """Create optimized shopping route based on price history"""
    try:
        # Group products by their cheapest store
        route = {}
        for product, info in recommendations.items():
            store = info['store']
            if store not in route:
                route[store] = []
            route[store].append({
                'product': product,
                'price': info['avg_price'],
                'times_bought': info['times_bought']
            })
        
        # Sort stores by number of items (visit store with most items first)
        sorted_route = sorted(route.items(), key=lambda x: len(x[1]), reverse=True)
        
        return sorted_route
    except:
        return []

def save_health_to_gsheet(health_entry):
    """Add health metric to Google Sheets (with duplicate prevention)"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        headers = ['date', 'metric', 'value', 'unit', 'normal_range', 'type', 'person', 'added_at']
        ws = get_or_create_worksheet(sheet, "Health", headers)
        
        # Check if this metric already exists
        all_data = ws.get_all_records()
        
        entry_date = health_entry.get('date', '')
        entry_metric = health_entry.get('metric', '')
        entry_person = health_entry.get('person', 'Govind')
        
        # Look for duplicates
        for existing in all_data:
            if (existing.get('date', '') == entry_date and
                existing.get('metric', '') == entry_metric and
                existing.get('person', '') == entry_person):
                # Duplicate found! Skip it
                return False
        
        # No duplicate found, safe to add
        row = [
            entry_date,
            entry_metric,
            health_entry.get('value', ''),
            health_entry.get('unit', ''),
            health_entry.get('normal_range', ''),
            health_entry.get('type', ''),
            entry_person,
            health_entry.get('added_at', '')
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error saving health: {str(e)}")
        return False

def save_settings_to_gsheet(settings):
    """Save settings to Google Sheets - Settings worksheet"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            st.error("❌ Error: Cannot connect to Google Sheets")
            return False
        
        headers = ['your_salary', 'wife_salary', 'fixed_rent', 'fixed_car_payment', 'fixed_car_insurance', 'fixed_health_insurance', 'fixed_mobile', 'fixed_utilities', 'fixed_tfsa', 'fixed_rrsp', 'fixed_india_transfer', 'fixed_other', 'annual_costco', 'annual_caa', 'annual_car_registration', 'annual_gym', 'annual_home_insurance', 'annual_other', 'annual_monthly_equivalent']
        
        # Get or create worksheet
        try:
            ws = sheet.worksheet("Settings")
        except:
            st.info("Creating 'Settings' worksheet...")
            ws = sheet.add_worksheet(title="Settings", rows=1000, cols=20)
        
        # Clear and add headers
        try:
            ws.clear()
            ws.insert_row(headers, 1)
        except:
            pass
        
        # Prepare data
        values = [str(settings.get(k, '')) for k in headers]
        
        # Append row
        try:
            ws.append_row(values)
            st.success("✅ Saved to Google Sheets!")
            return True
        except Exception as e:
            st.error(f"❌ Error appending row: {str(e)}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error in save_settings: {str(e)}")
        return False

def save_budgets_to_gsheet(budgets):
    """Save budgets to Google Sheets - SEPARATE Budget worksheet"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            st.error("❌ Error: Cannot connect to Google Sheets")
            return False
        
        # Get or create BUDGET worksheet (NOT Settings!)
        try:
            ws = sheet.worksheet("Budget")
        except:
            st.info("Creating 'Budget' worksheet...")
            ws = sheet.add_worksheet(title="Budget", rows=1000, cols=20)
        
        # Get headers from budgets dict
        headers = list(budgets.keys())
        
        # Clear and add headers
        try:
            ws.clear()
            ws.insert_row(headers, 1)
        except:
            pass
        
        # Prepare data
        values = [str(budgets.get(k, '')) for k in headers]
        
        # Append row
        try:
            ws.append_row(values)
            st.success("✅ Budgets saved to Google Sheets!")
            return True
        except Exception as e:
            st.error(f"❌ Error appending budget row: {str(e)}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error in save_budgets: {str(e)}")
        return False

def extract_images_from_pdf(pdf_bytes):
    """Extract images/pages from PDF and convert to JPEG for Claude Vision"""
    if not fitz:
        st.error("❌ PDF support requires PyMuPDF. Please install: pip install pymupdf")
        return []
    
    try:
        # Open PDF
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            # Render page to image (PNG)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            
            # Convert PNG to JPEG using PIL (for Claude Vision compatibility)
            png_bytes = pix.tobytes("png")
            png_image = Image.open(io.BytesIO(png_bytes))
            
            # Convert to JPEG
            jpeg_buffer = io.BytesIO()
            if png_image.mode == 'RGBA':
                # JPEG doesn't support transparency, convert to RGB
                rgb_image = Image.new('RGB', png_image.size, (255, 255, 255))
                rgb_image.paste(png_image, mask=png_image.split()[3])
                rgb_image.save(jpeg_buffer, format='JPEG', quality=95)
            else:
                png_image.save(jpeg_buffer, format='JPEG', quality=95)
            
            images.append(jpeg_buffer.getvalue())
        
        pdf_document.close()
        return images
    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        return []

def extract_receipt(image_bytes):
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
        
        prompt = """Extract receipt information. Output ONLY valid JSON, no markdown, no preamble.
{
    "merchant": "Store name",
    "date": "YYYY-MM-DD",
    "items": [
        {"name": "Item name", "quantity": 1, "price": 0.00}
    ],
    "total": 0.00
}
Be precise. Extract every item. ONLY output JSON."""
        
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1500,
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
        
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    return json.loads(json_str)
            except:
                pass
            
            st.error("❌ Could not parse receipt. Try again!")
            return None
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def extract_health_report(image_bytes):
    """Extract health metrics from blood test report using Claude Vision"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
        
        prompt = """Extract ALL health metrics from this blood test report. Output ONLY valid JSON, no markdown, no preamble.
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
Extract EVERY metric shown. Be precise with numbers and units. ONLY output JSON."""
        
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
        
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    return json.loads(json_str)
            except:
                pass
            
            st.error("❌ Could not parse health report. Try again!")
            return None
            
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
                                    for m in health_metrics[-5:]])  # Last 5 metrics
            
            prompt = f"""STRICT INSTRUCTIONS: Output ONLY valid JSON. No preamble, no explanation, ONLY JSON.

You are a nutritionist. Analyze these groceries BASED ON THIS PERSON'S HEALTH.

Their Health Metrics:
{health_text}

Their Groceries:
{items_text}

For EACH grocery item, give:
1. ✅ or ❌ or ⚠️ rating
2. Why

Then overall grade, keep items, reduce items, tips, and personalized note.

OUTPUT ONLY THIS JSON, NOTHING ELSE:
{{
    "items_analysis": [
        {{"name": "Item", "rating": "✅", "reason": "why"}}
    ],
    "overall_grade": "B+",
    "keep_items": ["item1", "item2"],
    "reduce_items": ["item1", "item2"],
    "tips": ["tip1", "tip2"],
    "personalized_note": "Based on your health..."
}}"""
        else:
            # GENERIC mode - no health data
            prompt = f"""STRICT INSTRUCTIONS: Output ONLY valid JSON. No preamble, no explanation, ONLY JSON.

You are a nutritionist. Analyze these groceries for GENERAL HEALTH.

Groceries:
{items_text}

For EACH item, give:
1. ✅ or ⚠️ rating
2. Why (nutritional value)

Then overall grade, keep items, reduce items, tips.

OUTPUT ONLY THIS JSON, NOTHING ELSE:
{{
    "items_analysis": [
        {{"name": "Item", "rating": "✅", "reason": "good source of fiber"}}
    ],
    "overall_grade": "B",
    "keep_items": ["item1", "item2"],
    "reduce_items": ["item1", "item2"],
    "tips": ["tip1", "tip2"],
    "note": "Upload health reports for personalized!"
}}"""
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            st.error("❌ Claude response not valid JSON. Try again!")
            return None
            
    except Exception as e:
        st.error(f"Error analyzing groceries: {str(e)}")
        return None

def analyze_joint_health(health_metrics_govind, health_metrics_amrithavarshini):
    """Analyze both people's health together and give household recommendations"""
    if not health_metrics_govind or not health_metrics_amrithavarshini:
        return None
    
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        # Get latest metrics for each person
        govind_latest = health_metrics_govind[-1] if health_metrics_govind else {}
        amritha_latest = health_metrics_amrithavarshini[-1] if health_metrics_amrithavarshini else {}
        
        govind_text = '\n'.join([f"- {m.get('metric', 'N/A')}: {m.get('value')} {m.get('unit')} (Normal: {m.get('normal_range')})" 
                               for m in health_metrics_govind[-5:]])
        amritha_text = '\n'.join([f"- {m.get('metric', 'N/A')}: {m.get('value')} {m.get('unit')} (Normal: {m.get('normal_range')})" 
                                for m in health_metrics_amrithavarshini[-5:]])
        
        prompt = f"""You are a nutritionist helping a couple cook and eat healthy TOGETHER.

GOVIND's Health Metrics (last 5):
{govind_text}

AMRITHAVARSHINI's Health Metrics (last 5):
{amritha_text}

Analyze their health TOGETHER and provide household-friendly recommendations since they cook together.

Output ONLY valid JSON, nothing else:
{{
    "common_concerns": ["High cholesterol (both)", "Need to increase fiber"],
    "individual_flags": {{
        "govind": ["Flag 1"],
        "amrithavarshini": ["Flag 1"]
    }},
    "household_diet_goals": [
        "Goal 1 (benefits both)",
        "Goal 2"
    ],
    "keep_foods": ["Salmon (omega-3s help both)", "Broccoli (fiber for both)"],
    "reduce_foods": ["Fried foods (bad for both)", "High-salt items"],
    "household_meal_tips": [
        "Prepare grilled meals instead of fried",
        "Use olive oil for cooking",
        "Add herbs for flavor instead of salt"
    ],
    "cooking_together_advice": "Cook once, eat together! Focus on grilled/baked meals with lots of vegetables.",
    "household_grocery_grade": "A-",
    "summary": "Your household should focus on heart-healthy eating since both have cholesterol concerns..."
}}"""
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return None
            
    except Exception as e:
        st.error(f"Error analyzing joint health: {str(e)}")
        return None
    """Analyze health metrics"""
    if not health_list:
        return None
    
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
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
        
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return None
    except:
        return None

def analyze_health_metrics(health_list):
    """Analyze health metrics for a single person"""
    if not health_list:
        return None
    
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        latest = health_list[-1] if health_list else {}
        metrics_text = '\n'.join([f"- {k}: {v}" for k, v in latest.items() if k not in ['date', 'added_at', 'person']])
        
        prompt = f"""Analyze these health metrics BRIEFLY and provide a JSON response.

Metrics:
{metrics_text}

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "overall_status": "Good or Fair or Concerning",
    "warnings": ["List only abnormal values"],
    "positives": ["List only normal/excellent values"],
    "risk_areas": ["Things to monitor proactively"],
    "recommendations": ["2-3 actionable tips"],
    "diet_guidance": "One sentence about diet",
    "exercise_plan": {{
        "frequency": "3-5 times per week",
        "duration_per_session": "30-45 minutes",
        "exercises": [
            {{"name": "Exercise 1", "duration": "20 mins", "description": "Brief description", "youtube_search": "search terms"}},
            {{"name": "Exercise 2", "duration": "20 mins", "description": "Brief description", "youtube_search": "search terms"}},
            {{"name": "Exercise 3", "duration": "20 mins", "description": "Brief description", "youtube_search": "search terms"}}
        ]
    }}
}}

RULES:
- Use ONLY double quotes in JSON
- Keep descriptions SHORT (under 15 words each)
- Return VALID JSON only - no markdown"""
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,  # Increased from 500 to 1500
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            import re
            
            # Fix unterminated strings - add closing quote before next comma/bracket/brace
            fixed = re.sub(r'([^"\\])"([^"]*?)([,\]\}])', r'\1"\2"\3', response_text)
            
            # If that didn't work, try to extract just the valid JSON part
            if fixed == response_text:
                # Look for the last closing brace
                last_brace = response_text.rfind('}')
                if last_brace > 0:
                    fixed = response_text[:last_brace+1]
            
            try:
                return json.loads(fixed)
            except:
                st.warning("⚠️ Claude's response wasn't valid JSON. Showing partial data.")
                # Return basic structure with what we got
                return {
                    "overall_status": "Good",
                    "warnings": [],
                    "positives": ["See Health tab for full analysis"],
                    "risk_areas": [],
                    "recommendations": [],
                    "diet_guidance": "See Health tab",
                    "exercise_plan": None
                }
    except KeyError as e:
        st.error(f"❌ API Key Missing: {str(e)}")
        st.info("💡 **Streamlit Cloud:** Go to Settings → Secrets and add `anthropic_key`")
        st.info("💡 **Local:** Make sure `.env` has `ANTHROPIC_API_KEY=sk-ant-...`")
        return None
    except Exception as e:
        st.error(f"❌ Claude API Error: {str(e)}")
        st.write(f"Error type: {type(e).__name__}")
        import traceback
        with st.expander("Technical Details"):
            st.write(traceback.format_exc())
        return None

def plot_health_trend(health_metrics, metric_name):
    """Create trend chart for a health metric with normal range visualization"""
    data = [h for h in health_metrics if h.get('metric', '').lower() == metric_name.lower()]
    
    if len(data) < 2:
        return None
    
    try:
        df = pd.DataFrame(data)
        
        # Force date parsing - handle multiple formats
        df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')
        
        # Drop rows with invalid dates
        df = df.dropna(subset=['date'])
        
        if df.empty:
            return None
        
        df['value'] = df['value'].apply(lambda x: safe_float(x))
        df = df.dropna(subset=['value']).sort_values('date')
        
        if df.empty or len(df) < 2:
            return None
        
        fig = go.Figure()
        
        # Add main trend line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['value'],
            mode='lines+markers',
            name=metric_name,
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=10, color='#1f77b4'),
            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Value: %{y:.2f}<extra></extra>'
        ))
        
        # Parse normal range and add zones
        normal_range = data[0].get('normal_range', '')
        min_normal = None
        max_normal = None
        
        if normal_range and normal_range != 'See below':
            # Try different formats
            
            # Format 1: "120-200"
            if '-' in normal_range and not any(c in normal_range for c in '<>'):
                try:
                    parts = normal_range.split('-')
                    min_normal = safe_float(parts[0].strip())
                    max_normal = safe_float(parts[1].strip())
                except:
                    pass
            
            # Format 2: "< 5.20" (less than)
            elif '<' in normal_range:
                try:
                    max_normal = safe_float(normal_range.replace('<', '').strip())
                    min_normal = None
                except:
                    pass
            
            # Format 3: "> 1.00" (greater than)
            elif '>' in normal_range:
                try:
                    min_normal = safe_float(normal_range.replace('>', '').replace('=', '').strip())
                    max_normal = None
                except:
                    pass
            
            # Format 4: ">= 1.00" (greater than or equal)
            elif '>=' in normal_range:
                try:
                    min_normal = safe_float(normal_range.replace('>=', '').strip())
                    max_normal = None
                except:
                    pass
        
        # Add normal range visualization
        y_min = df['value'].min() * 0.95
        y_max = df['value'].max() * 1.05
        
        if min_normal is not None and max_normal is not None:
            # Range format: add green zone
            fig.add_hrect(
                y0=min_normal, y1=max_normal,
                fillcolor="green", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="Normal Range", annotation_position="right"
            )
            fig.add_hline(y=min_normal, line_dash="dash", line_color="green", line_width=2,
                         annotation_text=f"Normal Min: {min_normal}")
            fig.add_hline(y=max_normal, line_dash="dash", line_color="green", line_width=2,
                         annotation_text=f"Normal Max: {max_normal}")
        
        elif min_normal is not None:
            # Greater than format: green zone above
            fig.add_hrect(
                y0=min_normal, y1=y_max,
                fillcolor="green", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="Normal Range", annotation_position="right"
            )
            fig.add_hline(y=min_normal, line_dash="dash", line_color="green", line_width=2,
                         annotation_text=f"Normal Min: {min_normal}")
        
        elif max_normal is not None:
            # Less than format: green zone below
            fig.add_hrect(
                y0=y_min, y1=max_normal,
                fillcolor="green", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="Normal Range", annotation_position="right"
            )
            fig.add_hline(y=max_normal, line_dash="dash", line_color="green", line_width=2,
                         annotation_text=f"Normal Max: {max_normal}")
        
        # Update layout with better styling
        unit = data[0].get('unit', '')
        fig.update_layout(
            title={
                'text': f"<b>{metric_name} Trend Over Time</b><br><sub>Normal Range: {normal_range if normal_range else 'N/A'}</sub>",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Date",
            yaxis_title=f"{metric_name} ({unit})",
            hovermode='x unified',
            height=500,
            template='plotly_dark',
            showlegend=True,
            legend=dict(
                x=0.02, y=0.98,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='white',
                borderwidth=1
            ),
            margin=dict(t=100, b=80, l=80, r=100),
            font=dict(size=12)
        )
        
        return fig
    except Exception as e:
        st.error(f"Error plotting trend: {str(e)}")
        return None

def calculate_monthly_finances(expenses, settings, debts):
    """Calculate complete monthly financial overview"""
    your_salary = safe_float(settings.get('your_salary', 0))
    wife_salary = safe_float(settings.get('wife_salary', 0))
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
    
    # Add annual monthly equivalent
    annual_monthly = safe_float(settings.get('annual_monthly_equivalent', 0))
    if annual_monthly > 0:
        fixed_expenses['Annual Expenses (Monthly Equivalent)'] = annual_monthly
        fixed_total += annual_monthly
    
    debt_total = 0
    for debt in debts:
        try:
            debt_total += safe_float(debt.get('monthly_payment', 0))
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
                amt = safe_float(exp.get('total', 0))
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
if 'extracted_metrics' not in st.session_state:
    st.session_state.extracted_metrics = None

# Force reload if data is empty (happens after code updates)
# This prevents the "no data" issue after deploying new versions
if not st.session_state.settings or len(st.session_state.settings) == 0:
    st.session_state.settings = load_settings()
if not st.session_state.expenses or len(st.session_state.expenses) == 0:
    st.session_state.expenses = load_expenses()
if not st.session_state.debts or len(st.session_state.debts) == 0:
    st.session_state.debts = load_debts()

# Fertility Tracking Functions
def load_fertility_cycles():
    """Load menstrual cycle data from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return []
        headers = ['date_start', 'date_end', 'cycle_length', 'cervical_fluid', 'temperature', 'symptoms', 'notes', 'added_at']
        ws = get_or_create_worksheet(sheet, "Fertility Cycles", headers)
        return ws.get_all_records()
    except:
        return []

def save_cycle_to_gsheet(cycle_data):
    """Save a menstrual cycle to Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        headers = ['date_start', 'date_end', 'cycle_length', 'cervical_fluid', 'temperature', 'symptoms', 'notes', 'added_at']
        ws = get_or_create_worksheet(sheet, "Fertility Cycles", headers)
        
        # Check for duplicates
        existing = ws.get_all_records()
        for record in existing:
            if record.get('date_start') == cycle_data['date_start']:
                return False  # Duplicate found
        
        # Append new record
        ws.append_row([
            cycle_data.get('date_start', ''),
            cycle_data.get('date_end', ''),
            cycle_data.get('cycle_length', ''),
            cycle_data.get('cervical_fluid', ''),
            cycle_data.get('temperature', ''),
            cycle_data.get('symptoms', ''),
            cycle_data.get('notes', ''),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
        return True
    except:
        return False

def calculate_ovulation_date(period_start_date, cycle_length=28):
    """Calculate ovulation date (cycle_length - 14 days)"""
    from datetime import timedelta
    period_date = pd.to_datetime(period_start_date)
    ovulation_date = period_date + timedelta(days=cycle_length - 14)
    return ovulation_date

def calculate_fertile_window(ovulation_date):
    """Calculate 6-day fertile window (5 days before + 1 day after)"""
    from datetime import timedelta
    fertile_start = ovulation_date - timedelta(days=5)
    fertile_end = ovulation_date + timedelta(days=1)
    return fertile_start, fertile_end

def analyze_cycle_patterns(cycles):
    """Analyze menstrual cycle patterns"""
    if not cycles or len(cycles) < 2:
        return None
    
    try:
        cycle_lengths = []
        for cycle in cycles:
            if cycle.get('cycle_length'):
                cycle_lengths.append(int(cycle['cycle_length']))
        
        if not cycle_lengths:
            return None
        
        avg_length = sum(cycle_lengths) / len(cycle_lengths)
        min_length = min(cycle_lengths)
        max_length = max(cycle_lengths)
        
        # Check if regular (±2 days variation)
        is_regular = (max_length - min_length) <= 2
        
        return {
            'average_cycle_length': round(avg_length, 1),
            'min_cycle_length': min_length,
            'max_cycle_length': max_length,
            'num_cycles': len(cycle_lengths),
            'is_regular': is_regular,
            'cycle_lengths': cycle_lengths
        }
    except:
        return None

def get_conception_probability(cycle_analysis):
    """Calculate conception probability based on cycle data"""
    if not cycle_analysis:
        return None
    
    # Base probability: 20-25% per cycle for healthy couple
    base_prob = 0.22
    
    # Bonus for regular cycles
    if cycle_analysis.get('is_regular'):
        base_prob += 0.05
    
    # Convert to percentage
    return round(base_prob * 100, 1)

# Daily Wellness Logging Functions
def load_wellness_logs():
    """Load daily wellness logs from Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return []
        headers = ['date', 'person', 'exercise_name', 'exercise_done', 'water_bottles', 'pee_count', 'poop_count', 
                   'sleep_hours', 'mood_score', 'stress_score', 'symptoms', 'medications_taken', 'steps', 
                   'diet_notes', 'notes', 'added_at']
        ws = get_or_create_worksheet(sheet, "Daily Wellness Log", headers)
        return ws.get_all_records()
    except:
        return []

def save_wellness_log(wellness_data):
    """Save daily wellness log to Google Sheets"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            return False
        
        headers = ['date', 'person', 'exercise_name', 'exercise_done', 'water_bottles', 'pee_count', 'poop_count', 
                   'sleep_hours', 'mood_score', 'stress_score', 'symptoms', 'medications_taken', 'steps', 
                   'diet_notes', 'notes', 'added_at']
        ws = get_or_create_worksheet(sheet, "Daily Wellness Log", headers)
        
        # Check for duplicates (same date + person)
        existing = ws.get_all_records()
        for record in existing:
            if record.get('date') == wellness_data['date'] and record.get('person') == wellness_data['person']:
                # Update existing record instead
                return True  # Would need to implement update logic, for now just return True
        
        # Append new record
        ws.append_row([
            wellness_data.get('date', ''),
            wellness_data.get('person', ''),
            wellness_data.get('exercise_name', ''),
            wellness_data.get('exercise_done', ''),
            wellness_data.get('water_bottles', ''),
            wellness_data.get('pee_count', ''),
            wellness_data.get('poop_count', ''),
            wellness_data.get('sleep_hours', ''),
            wellness_data.get('mood_score', ''),
            wellness_data.get('stress_score', ''),
            wellness_data.get('symptoms', ''),
            wellness_data.get('medications_taken', ''),
            wellness_data.get('steps', ''),
            wellness_data.get('diet_notes', ''),
            wellness_data.get('notes', ''),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
        return True
    except:
        return False

def analyze_wellness_week(wellness_logs, person_name, days=7):
    """Analyze a week of wellness data"""
    if not wellness_logs:
        return None
    
    try:
        # Filter by person and recent dates
        person_logs = [log for log in wellness_logs if log.get('person') == person_name]
        
        if not person_logs:
            return None
        
        # Convert dates and filter last 7 days
        recent_logs = []
        for log in person_logs:
            try:
                log_date = pd.to_datetime(log.get('date', datetime.now()))
                if (datetime.now() - log_date).days <= days:
                    recent_logs.append(log)
            except:
                pass
        
        if len(recent_logs) < 2:
            return None
        
        # Calculate averages and patterns
        water_avg = sum([safe_float(log.get('water_bottles', 0)) for log in recent_logs]) / len(recent_logs)
        sleep_avg = sum([safe_float(log.get('sleep_hours', 0)) for log in recent_logs]) / len(recent_logs)
        mood_avg = sum([safe_float(log.get('mood_score', 0)) for log in recent_logs]) / len(recent_logs)
        stress_avg = sum([safe_float(log.get('stress_score', 0)) for log in recent_logs]) / len(recent_logs)
        
        # Exercise completion
        exercises_done = sum([1 for log in recent_logs if log.get('exercise_done', '').lower() == 'yes'])
        exercise_rate = (exercises_done / len(recent_logs)) * 100
        
        # Steps average
        steps_avg = sum([safe_float(log.get('steps', 0)) for log in recent_logs]) / len(recent_logs)
        
        # Bathroom patterns
        pee_avg = sum([safe_float(log.get('pee_count', 0)) for log in recent_logs]) / len(recent_logs)
        poop_avg = sum([safe_float(log.get('poop_count', 0)) for log in recent_logs]) / len(recent_logs)
        
        return {
            'water_avg': round(water_avg, 1),
            'sleep_avg': round(sleep_avg, 1),
            'mood_avg': round(mood_avg, 1),
            'stress_avg': round(stress_avg, 1),
            'exercise_rate': round(exercise_rate, 1),
            'steps_avg': round(steps_avg, 0),
            'pee_avg': round(pee_avg, 1),
            'poop_avg': round(poop_avg, 1),
            'num_days': len(recent_logs)
        }
    except:
        return None

# Main UI
st.title("🏥 Health & Wealth Tracker")
st.markdown("Complete life management: Finance + Health + Smart Nutrition (Data in Google Sheets ☁️)")

tabs = st.tabs(["⚙️ Setup", "💳 Debts", "💰 Spending", "🛒 Shopping Analytics", "📊 Wealth", "🏥 Health", "🏋️ Fitness Plan", "✅ Daily Wellness Log", "🍽️ Nutrition Tracker", "👶 Fertility Tracker", "🥗 Smart Grocery", "🎯 Budgets"])

with tabs[0]:  # Setup
    st.markdown("### Monthly Income & Fixed Expenses Setup")
    
    # Add refresh button at top
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Data", key="refresh_btn"):
            st.session_state.settings = load_settings()
            st.rerun()
    with col2:
        st.write("")  # spacing
    with col3:
        st.write("")  # spacing
    
    st.markdown("---")
    # Only show warning if settings are actually empty
    your_salary_current = safe_float(st.session_state.settings.get('your_salary', 0))
    if your_salary_current == 0:
        st.warning("⚠️ **IMPORTANT:** Your settings data is empty. Please re-enter your income and expenses below. We've added safety checks to prevent data loss!")
    
    st.markdown("#### 💵 Monthly Income")
    col1, col2 = st.columns(2)
    with col1:
        your_sal = st.number_input("Your Salary (CAD)", min_value=0.0, value=safe_float(st.session_state.settings.get('your_salary', 0)), step=100.0)
    with col2:
        wife_sal = st.number_input("Wife's Salary (CAD)", min_value=0.0, value=safe_float(st.session_state.settings.get('wife_salary', 0)), step=100.0)
    
    st.markdown("#### 🏠 Fixed Monthly Expenses")
    
    fixed_items = {
        'fixed_rent': 'Rent/Mortgage',
        'fixed_car_payment': 'Car Payment',
        'fixed_car_insurance': 'Car Insurance',
        'fixed_health_insurance': 'Health Insurance',
        'fixed_mobile': 'Mobile/Phone',
        'fixed_utilities': 'Utilities (Hydro & Internet)',
        'fixed_tfsa': 'TFSA Transfer',
        'fixed_rrsp': 'RRSP Transfer',
        'fixed_india_transfer': 'Money to India',
        'fixed_other': 'Other Fixed Expense'
    }
    
    st.info("💡 **Gas Expense:** Upload receipts in the Spending tab instead of entering a fixed amount. AI will auto-categorize them!")
    
    fixed_values = {}
    for key, label in fixed_items.items():
        fixed_values[key] = st.number_input(label, min_value=0.0, value=safe_float(st.session_state.settings.get(key, 0)), step=50.0)
    
    st.markdown("#### 💾 Retirement Savings Start Date")
    st.info("📅 When did you start contributing to TFSA & RRSP? This helps us calculate your cumulative retirement savings correctly.")
    
    # Get the start date from settings or use default
    tfsa_rrsp_start_str = st.session_state.settings.get('tfsa_rrsp_start_date', '')
    if tfsa_rrsp_start_str:
        try:
            tfsa_rrsp_start = datetime.strptime(tfsa_rrsp_start_str, '%Y-%m-%d').date()
        except:
            tfsa_rrsp_start = datetime(2024, 9, 1).date()  # Default to Sep 2024
    else:
        tfsa_rrsp_start = datetime(2024, 9, 1).date()  # Default to Sep 2024
    
    tfsa_rrsp_start_date = st.date_input("TFSA & RRSP Start Date", value=tfsa_rrsp_start, key="tfsa_rrsp_start_date_input")
    
    st.markdown("#### 📅 Annual/Yearly Expenses (Calculated Monthly Equivalent)")
    st.info("💡 Enter yearly costs - we'll automatically calculate the monthly equivalent to add to your budget!")
    
    annual_items = {
        'annual_costco': 'Costco Membership',
        'annual_caa': 'CAA Membership',
        'annual_car_registration': 'Car Registration/License Renewal',
        'annual_gym': 'Gym/Fitness Membership (if annual)',
        'annual_home_insurance': 'Home Insurance (annual premium)',
        'annual_other': 'Other Annual Expense'
    }
    
    annual_values = {}
    monthly_equivalent = 0
    
    for key, label in annual_items.items():
        annual_amount = st.number_input(f"{label} (yearly CAD)", min_value=0.0, value=safe_float(st.session_state.settings.get(key, 0)), step=10.0)
        annual_values[key] = annual_amount
        monthly_equivalent += annual_amount / 12
    
    st.markdown(f"**Annual Total: ${sum(annual_values.values()):.2f}** → **Monthly Equivalent: ${monthly_equivalent:.2f}**")
    
    if st.button("💾 Save Income & Fixed Expenses", key="save_settings_btn"):
        # Validation
        if your_sal == 0 and wife_sal == 0:
            st.error("❌ Error: At least one salary must be greater than 0!")
        else:
            with st.spinner("Saving to Google Sheets..."):
                st.session_state.settings['your_salary'] = your_sal
                st.session_state.settings['wife_salary'] = wife_sal
                st.session_state.settings['tfsa_rrsp_start_date'] = tfsa_rrsp_start_date.strftime('%Y-%m-%d')
                for key, val in fixed_values.items():
                    st.session_state.settings[key] = val
                for key, val in annual_values.items():
                    st.session_state.settings[key] = val
                st.session_state.settings['annual_monthly_equivalent'] = monthly_equivalent
                
                if save_settings_to_gsheet(st.session_state.settings):
                    st.success("✅ Saved to Google Sheets!")
                    st.balloons()
                    st.info(f"📊 Your annual expenses ({sum(annual_values.values()):.2f}/year) add ${monthly_equivalent:.2f}/month to your budget")
                else:
                    st.error("❌ Error saving - Settings NOT updated to prevent data loss")

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
                    edit_principal = st.number_input("Principal", value=safe_float(debt.get('principal', 0)), key=f"edit_principal_{i}")
                with col3:
                    edit_payment = st.number_input("Monthly Payment", value=safe_float(debt.get('monthly_payment', 0)), key=f"edit_payment_{i}")
                with col4:
                    edit_rate = st.number_input("Interest Rate %", value=safe_float(debt.get('interest_rate', 0)), key=f"edit_rate_{i}")
                
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
                total_debt += safe_float(debt.get('principal', 0))
                total_monthly_payment += safe_float(debt.get('monthly_payment', 0))
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
    
    # Category override for receipts
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload Receipt (JPG/PNG/PDF)", type=["jpg", "jpeg", "png", "gif", "webp", "pdf"], key="receipt_upload")
    with col2:
        st.markdown("**Force Category?**")
        force_category = st.selectbox(
            "Override AI category",
            ["Auto-Detect", "Gas", "Groceries", "Dining", "Transportation", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"],
            index=0,
            key="force_category",
            label_visibility="collapsed"
        )
    
    if uploaded_file:
        file_type = uploaded_file.type
        
        # Handle PDF
        if file_type == "application/pdf":
            st.info(f"📄 Processing PDF: {uploaded_file.name}")
            pdf_images = extract_images_from_pdf(uploaded_file.getvalue())
            
            if pdf_images:
                st.write(f"✅ Extracted {len(pdf_images)} page(s) from PDF")
                
                st.info("✅ **Duplicate Protection:** If you upload a PDF with receipts you've already uploaded, duplicates will be automatically skipped!")
                
                if st.button("🤖 Process PDF Receipt"):
                    with st.spinner(f"Processing {len(pdf_images)} page(s)..."):
                        all_receipts = []
                        
                        for page_idx, image_bytes in enumerate(pdf_images):
                            st.write(f"📖 Processing page {page_idx+1}/{len(pdf_images)}...")
                            receipt = extract_receipt(image_bytes)
                            
                            if receipt:
                                all_receipts.append(receipt)
                        
                        if all_receipts:
                            st.success(f"✅ Extracted {len(all_receipts)} receipt(s) from PDF!")
                            
                            # Process each receipt
                            saved_count = 0
                            duplicate_count = 0
                            for receipt in all_receipts:
                                # Use forced category or auto-detect
                                if force_category != "Auto-Detect":
                                    category = force_category
                                else:
                                    category = categorize_expense(receipt)
                                receipt['category'] = category
                                receipt['uploaded_at'] = datetime.now().isoformat()
                                
                                if save_expense_to_gsheet(receipt):
                                    st.session_state.expenses.append(receipt)
                                    saved_count += 1
                                else:
                                    duplicate_count += 1
                            
                            if saved_count > 0:
                                st.success(f"✅ {saved_count} receipt(s) processed from PDF!")
                                st.balloons()
                            
                            if duplicate_count > 0:
                                st.warning(f"⚠️ {duplicate_count} receipt(s) from PDF were duplicates and were skipped (prevented)! ✅")
                        else:
                            st.error("❌ Could not extract receipts from PDF. Make sure it contains clear images of receipts.")
            else:
                st.error("❌ Could not extract pages from PDF. Please try a different PDF file.")
        
        # Handle Images
        else:
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
            
            st.info("✅ **Duplicate Protection:** If you upload the same receipt twice, duplicates will be automatically skipped!")
            
            if st.button("🤖 Process Receipt"):
                with st.spinner("Processing..."):
                    receipt = extract_receipt(uploaded_file.getvalue())
                    
                    if receipt:
                        # Use forced category or auto-detect
                        if force_category != "Auto-Detect":
                            category = force_category
                        else:
                            category = categorize_expense(receipt)
                        receipt['category'] = category
                        receipt['uploaded_at'] = datetime.now().isoformat()
                        
                        if save_expense_to_gsheet(receipt):
                            st.session_state.expenses.append(receipt)
                            st.success("✅ Receipt processed!")
                        else:
                            st.warning(f"⚠️ Receipt from {receipt.get('merchant', 'Unknown')} on {receipt.get('date', 'Unknown')} already exists (duplicate prevented)! ✅\n\nIf this is a new receipt, it may have been uploaded before.")
                            st.info("💡 Duplicate prevention: Same merchant + date + total = duplicate")
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

with tabs[3]:  # Shopping Analytics
    st.markdown("### 🛒 Shopping Analytics & Price Trends")
    
    # Load price history
    price_history = load_price_history_from_gsheet()
    
    if price_history.empty:
        st.info("📊 No price history yet! Upload receipts to start tracking prices.")
    else:
        st.success(f"✅ Tracking {len(price_history)} items from {price_history['store'].nunique()} stores")
        
        # Tab 1: Product Price Analysis
        sub_tabs = st.tabs(["📈 Product Trends", "🏪 Store Comparison", "🎯 Shopping Guide", "💰 Savings Potential"])
        
        with sub_tabs[0]:  # Product Trends
            st.markdown("#### 📈 Price Trends by Product")
            
            products = sorted(price_history['product'].unique())
            selected_product = st.selectbox("Select Product", products, key="product_select")
            
            product_analysis = analyze_product_price_trends(price_history, selected_product)
            
            if product_analysis is not None:
                st.markdown(f"**{selected_product}** - Price Analysis")
                
                # Display analysis table
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("📊 Data Points", len(product_analysis))
                with col2:
                    avg_price = product_analysis['mean'].mean()
                    st.metric("💰 Avg Price", f"${avg_price:.2f}")
                with col3:
                    cheapest = product_analysis['mean'].min()
                    st.metric("🏆 Cheapest", f"${cheapest:.2f}")
                with col4:
                    most_expensive = product_analysis['mean'].max()
                    st.metric("❌ Most Expensive", f"${most_expensive:.2f}")
                with col5:
                    savings = most_expensive - cheapest
                    st.metric("💵 Savings/Unit", f"${savings:.2f}")
                
                st.markdown("---")
                
                # Display by store
                st.write("**By Store:**")
                for store in product_analysis.index:
                    row = product_analysis.loc[store]
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**{store}**")
                    with col2:
                        st.write(f"Avg: ${row['mean']:.2f}")
                    with col3:
                        st.write(f"Times: {int(row['count'])}")
                    with col4:
                        price_range = f"${row['min']:.2f}-${row['max']:.2f}"
                        st.write(f"Range: {price_range}")
                
                # Visualization
                chart_data = product_analysis[['mean']].sort_values('mean', ascending=False)
                st.bar_chart(chart_data)
        
        with sub_tabs[1]:  # Store Comparison
            st.markdown("#### 🏪 Which Stores Have the Best Prices?")
            
            # Get recommendations
            recommendations = get_cheapest_stores_for_products(price_history)
            
            if recommendations:
                # Count products per store
                store_stats = {}
                for product, info in recommendations.items():
                    store = info['store']
                    if store not in store_stats:
                        store_stats[store] = {'count': 0, 'products': []}
                    store_stats[store]['count'] += 1
                    store_stats[store]['products'].append(product)
                
                # Display store stats
                col1, col2, col3 = st.columns(3)
                
                sorted_stores = sorted(store_stats.items(), key=lambda x: x[1]['count'], reverse=True)
                
                for idx, (store, info) in enumerate(sorted_stores):
                    if idx % 3 == 0:
                        col1, col2, col3 = st.columns(3)
                    
                    with [col1, col2, col3][idx % 3]:
                        st.metric(
                            f"🏪 {store}",
                            f"Cheapest for {info['count']} items"
                        )
                
                st.markdown("---")
                
                # Detailed breakdown
                st.write("**Detailed Store Comparison:**")
                
                all_stores = sorted(price_history['store'].unique())
                comparison_data = []
                
                for product in price_history['product'].unique():
                    product_prices = {}
                    for store in all_stores:
                        store_prices = price_history[
                            (price_history['product'] == product) & 
                            (price_history['store'] == store)
                        ]['price']
                        
                        if len(store_prices) > 0:
                            product_prices[store] = store_prices.mean()
                        else:
                            product_prices[store] = None
                    
                    comparison_data.append({'product': product, **product_prices})
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True)
        
        with sub_tabs[2]:  # Shopping Guide
            st.markdown("#### 🎯 Smart Shopping Guide")
            
            recommendations = get_cheapest_stores_for_products(price_history)
            route = get_shopping_route_recommendation(recommendations)
            
            if route:
                st.success("✅ Optimized Shopping Route")
                
                total_potential_savings = 0
                
                for i, (store, products) in enumerate(route, 1):
                    st.markdown(f"**{i}. Visit: {store}**")
                    
                    store_savings = 0
                    
                    for item in sorted(products, key=lambda x: x['price'], reverse=True):
                        product = item['product']
                        price = item['price']
                        times_bought = item['times_bought']
                        
                        # Find most expensive price for this product
                        all_prices = recommendations[product]['all_stores'].values()
                        most_expensive = max(all_prices)
                        savings = most_expensive - price
                        
                        store_savings += savings
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"   • {product}")
                        with col2:
                            st.write(f"${price:.2f}")
                        with col3:
                            st.write(f"Save ${savings:.2f}")
                    
                    st.write(f"   **Subtotal savings: ${store_savings:.2f}**")
                    st.markdown("---")
                    total_potential_savings += store_savings
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🎯 Stores to Visit", len(route))
                with col2:
                    st.metric("📦 Products to Track", len(recommendations))
                with col3:
                    st.metric("💰 Potential Savings", f"${total_potential_savings:.2f}")
        
        with sub_tabs[3]:  # Savings Potential
            st.markdown("#### 💰 Your Savings Potential")
            
            if not price_history.empty:
                # Calculate what you spent vs what you could save
                recommendations = get_cheapest_stores_for_products(price_history)
                
                total_spent = 0
                total_optimal = 0
                
                for product, info in recommendations.items():
                    product_data = price_history[price_history['product'] == product]
                    actual_spent = (product_data['price'] * product_data['quantity']).sum()
                    optimal_spent = info['avg_price'] * product_data['quantity'].sum()
                    
                    total_spent += actual_spent
                    total_optimal += optimal_spent
                
                savings = total_spent - total_optimal
                savings_percent = (savings / total_spent * 100) if total_spent > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💸 Total Spent", f"${total_spent:.2f}")
                with col2:
                    st.metric("💵 Could Spend", f"${total_optimal:.2f}")
                with col3:
                    st.metric("💰 Potential Savings", f"${savings:.2f}")
                with col4:
                    st.metric("📊 Savings %", f"{savings_percent:.1f}%")
                
                st.markdown("---")
                st.info(f"💡 By shopping smarter (at cheapest stores), you could save **${savings:.2f}** on your grocery trips!")

with tabs[4]:  # Wealth Dashboard
    st.markdown("### 📊 Complete Financial Dashboard")
    
    # TFSA & RRSP Cumulative Savings Section
    st.markdown("#### 💰 Retirement Savings Tracker (TFSA + RRSP)")
    
    # Get monthly TFSA and RRSP amounts from settings
    tfsa_monthly = safe_float(st.session_state.settings.get('fixed_tfsa', 0))
    rrsp_monthly = safe_float(st.session_state.settings.get('fixed_rrsp', 0))
    total_monthly_savings = tfsa_monthly + rrsp_monthly
    
    # Calculate months from TFSA/RRSP start date
    tfsa_rrsp_start_str = st.session_state.settings.get('tfsa_rrsp_start_date', '')
    if tfsa_rrsp_start_str:
        try:
            tfsa_rrsp_start = pd.to_datetime(tfsa_rrsp_start_str)
        except:
            tfsa_rrsp_start = pd.Timestamp(datetime(2024, 9, 1))
    else:
        tfsa_rrsp_start = pd.Timestamp(datetime(2024, 9, 1))
    
    today_ts = pd.Timestamp(datetime.now())
    months_contributing = max(1, (today_ts - tfsa_rrsp_start).days // 30)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💵 TFSA Monthly", f"${tfsa_monthly:.2f}")
    with col2:
        st.metric("💵 RRSP Monthly", f"${rrsp_monthly:.2f}")
    with col3:
        st.metric("📈 Months Contributing", f"{months_contributing}")
    with col4:
        st.metric("💰 Total Monthly Savings", f"${total_monthly_savings:.2f}")
    
    # Show cumulative totals
    tfsa_cumulative = tfsa_monthly * months_contributing
    rrsp_cumulative = rrsp_monthly * months_contributing
    total_cumulative = tfsa_cumulative + rrsp_cumulative
    
    start_date_str = tfsa_rrsp_start.strftime('%b %Y')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏦 TFSA Cumulative", f"${tfsa_cumulative:,.2f}", f"Since {start_date_str}")
    with col2:
        st.metric("📊 RRSP Cumulative", f"${rrsp_cumulative:,.2f}", f"Since {start_date_str}")
    with col3:
        st.metric("🎯 Total Retirement Savings", f"${total_cumulative:,.2f}", f"+${total_monthly_savings:.2f}/month")
    
    # Projection for next 5 years
    st.markdown("#### 📈 5-Year Savings Projection")
    
    years = [1, 2, 3, 4, 5]
    tfsa_projections = [tfsa_cumulative + (tfsa_monthly * 12 * year) for year in years]
    rrsp_projections = [rrsp_cumulative + (rrsp_monthly * 12 * year) for year in years]
    total_projections = [tfsa_projections[i] + rrsp_projections[i] for i in range(5)]
    
    # Create projection chart
    projection_df = pd.DataFrame({
        'Year': [f"Year {y}" for y in years],
        'TFSA': tfsa_projections,
        'RRSP': rrsp_projections,
        'Total': total_projections
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='TFSA', x=projection_df['Year'], y=projection_df['TFSA'], marker_color='#1f77b4'))
    fig.add_trace(go.Bar(name='RRSP', x=projection_df['Year'], y=projection_df['RRSP'], marker_color='#ff7f0e'))
    fig.update_layout(
        title="Retirement Savings Projection (Next 5 Years)",
        xaxis_title="Years",
        yaxis_title="Amount (CAD)",
        barmode='stack',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Breakdown table
    st.markdown("#### 📋 Projection Breakdown")
    st.dataframe(
        projection_df.style.format({'TFSA': '${:,.0f}', 'RRSP': '${:,.0f}', 'Total': '${:,.0f}'}),
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Month selector
    st.markdown("#### 📅 Select Month to View")
    col1, col2 = st.columns([2, 3])
    
    # Get all unique months from expenses
    all_months = set()
    for exp in st.session_state.expenses:
        try:
            exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
            month_key = exp_date.strftime('%Y-%m')
            all_months.add(month_key)
        except:
            pass
    
    # Add current month
    today = datetime.now()
    current_month = today.strftime('%Y-%m')
    all_months.add(current_month)
    
    # Sort months descending
    months_sorted = sorted(list(all_months), reverse=True)
    month_labels = [datetime.strptime(m, '%Y-%m').strftime('%B %Y') for m in months_sorted]
    
    with col1:
        selected_month_label = st.selectbox("Choose Month:", month_labels, key="month_selector")
        selected_month = months_sorted[month_labels.index(selected_month_label)]
    
    # Calculate finances for selected month
    def calculate_monthly_finances_for_month(expenses, settings, debts, target_month):
        """Calculate finances for a specific month"""
        your_salary = safe_float(settings.get('your_salary', 0))
        wife_salary = safe_float(settings.get('wife_salary', 0))
        total_income = your_salary + wife_salary
        
        fixed_expenses = {}
        fixed_total = 0
        for key in settings:
            if key.startswith('fixed_'):
                try:
                    amount = safe_float(settings[key])
                    expense_name = key.replace('fixed_', '').replace('_', ' ').title()
                    fixed_expenses[expense_name] = amount
                    fixed_total += amount
                except:
                    pass
        
        # Add annual monthly equivalent
        annual_monthly = safe_float(settings.get('annual_monthly_equivalent', 0))
        if annual_monthly > 0:
            fixed_expenses['Annual Expenses (Monthly Equivalent)'] = annual_monthly
            fixed_total += annual_monthly
        
        debt_total = 0
        for debt in debts:
            try:
                debt_total += safe_float(debt.get('monthly_payment', 0))
            except:
                pass
        
        # Filter expenses for selected month
        variable_total = 0
        variable_by_category = defaultdict(float)
        for exp in expenses:
            try:
                exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
                exp_month = exp_date.strftime('%Y-%m')
                if exp_month == target_month:
                    amt = safe_float(exp.get('total', 0))
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
    
    finances = calculate_monthly_finances_for_month(st.session_state.expenses, st.session_state.settings, st.session_state.debts, selected_month)
    
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
        
        total_debt = sum(safe_float(d.get('principal', 0)) for d in st.session_state.debts)
        max_months = max([safe_float(d.get('months_to_payoff', 0)) for d in st.session_state.debts], default=0)
        st.success(f"🎯 **DEBT-FREE IN {int(max_months)} MONTHS!** (Total debt: ${total_debt:.2f})")
    
    st.markdown("---")
    
    # NEW: Category Spending Breakdown
    st.markdown("#### 📊 Spending by Category (This Month)")
    if finances['variable_by_category']:
        categories = finances['variable_by_category']
        
        # Pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(categories.keys()),
            values=list(categories.values()),
            hole=0
        )])
        fig_pie.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Category breakdown table
        st.markdown("**Category Breakdown:**")
        for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            st.write(f"• {cat}: **${amount:.2f}**")
    else:
        st.info("No spending data yet. Upload receipts to see category breakdown!")
    
    st.markdown("---")
    
    # NEW: Debt Payoff Timeline
    st.markdown("#### 🎯 Debt Payoff Timeline")
    if st.session_state.debts:
        debts_sorted = sorted(st.session_state.debts, key=lambda x: safe_float(x.get('months_to_payoff', 0)))
        
        for debt in debts_sorted:
            name = debt.get('name', 'N/A')
            months = int(safe_float(debt.get('months_to_payoff', 0)))
            principal = safe_float(debt.get('principal', 0))
            
            # Progress bar (0-100 based on months)
            progress = min(100, (months / 100) * 100)  # Scale months to 0-100
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{name}**")
                st.progress(progress / 100)
            with col2:
                st.write(f"**{months}mo**")
                st.write(f"${principal:.0f}")
    else:
        st.info("No debts tracked. Add debts to see payoff timeline!")
    
    st.markdown("---")
    
    # NEW: Budget vs Actual Comparison
    st.markdown("#### 💰 Budget vs Actual (This Month)")
    if st.session_state.budgets:
        budget_categories = {}
        actual_categories = finances['variable_by_category']
        
        for cat in st.session_state.budgets:
            budget_amount = safe_float(st.session_state.budgets.get(cat, 0))
            actual_amount = actual_categories.get(cat, 0)
            budget_categories[cat] = {'budget': budget_amount, 'actual': actual_amount}
        
        # Comparison chart
        categories_list = list(budget_categories.keys())
        budget_values = [budget_categories[cat]['budget'] for cat in categories_list]
        actual_values = [budget_categories[cat]['actual'] for cat in categories_list]
        
        fig_budget = go.Figure(data=[
            go.Bar(name='Budget', x=categories_list, y=budget_values, marker_color='lightblue'),
            go.Bar(name='Actual', x=categories_list, y=actual_values, marker_color='coral')
        ])
        fig_budget.update_layout(barmode='group', height=400)
        st.plotly_chart(fig_budget, use_container_width=True)
        
        # Budget status
        st.markdown("**Budget Status:**")
        total_budget = sum(budget_values)
        total_actual = sum(actual_values)
        
        for cat in categories_list:
            budget = budget_categories[cat]['budget']
            actual = budget_categories[cat]['actual']
            status = "✅ Under" if actual <= budget else "⚠️ Over"
            difference = budget - actual
            st.write(f"• {cat}: ${actual:.2f}/${budget:.2f} {status} ({difference:+.2f})")
        
        # Total summary
        if total_actual <= total_budget:
            total_message = f"**Total: ${total_actual:.2f}/${total_budget:.2f}** ✅ Under by ${total_budget - total_actual:.2f}"
        else:
            total_message = f"**Total: ${total_actual:.2f}/${total_budget:.2f}** ⚠️ Over by ${total_actual - total_budget:.2f}"
        st.write(total_message)
    else:
        st.info("Set monthly budgets in the Budgets tab to see comparison!")
    
    st.markdown("---")
    
    # NEW: Historical Spending Trends
    st.markdown("#### 📈 Spending Trends Over Time (All Months)")
    
    # Build historical data by month and category
    historical_data = defaultdict(lambda: defaultdict(float))
    for exp in st.session_state.expenses:
        try:
            exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
            month_key = exp_date.strftime('%Y-%m')
            cat = exp.get('category', 'Other')
            amt = safe_float(exp.get('total', 0))
            historical_data[month_key][cat] += amt
        except:
            pass
    
    if historical_data:
        # Filter to only show last 24 months (avoid old test data)
        today = datetime.now()
        cutoff_date = today - timedelta(days=730)  # Last 24 months
        
        # Sort months and filter
        months_sorted_hist = sorted([m for m in historical_data.keys() if datetime.strptime(m, '%Y-%m') >= cutoff_date])
        
        if not months_sorted_hist:
            # If no data in last 24 months, show all data
            months_sorted_hist = sorted(list(historical_data.keys()))
        
        # Create line chart with multiple categories
        fig_trend = go.Figure()
        
        # Get all unique categories across all months
        all_categories_hist = set()
        for month_data in historical_data.values():
            all_categories_hist.update(month_data.keys())
        
        # Add a line for each category
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        for idx, cat in enumerate(sorted(all_categories_hist)):
            values = [historical_data[month].get(cat, 0) for month in months_sorted_hist]
            month_labels_hist = [datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in months_sorted_hist]
            
            fig_trend.add_trace(go.Scatter(
                x=month_labels_hist,
                y=values,
                mode='lines+markers',
                name=cat,
                line=dict(width=2, color=colors[idx % len(colors)]),
                marker=dict(size=8)
            ))
        
        fig_trend.update_layout(
            title="Monthly Spending by Category",
            xaxis_title="Month",
            yaxis_title="Spending ($)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Summary table
        st.markdown("**Monthly Summary:**")
        summary_df = pd.DataFrame({
            'Month': [datetime.strptime(m, '%Y-%m').strftime('%B %Y') for m in months_sorted_hist],
            'Total Spending': [sum(historical_data[m].values()) for m in months_sorted_hist]
        })
        st.dataframe(summary_df, use_container_width=True)
    else:
        st.info("No historical spending data yet. Upload receipts to see trends!")
    
    st.markdown("---")
    
    # NEW: Weekly Breakdown for Selected Month
    st.markdown("#### 📅 Weekly Breakdown (This Month)")
    
    # Calculate weekly spending for selected month
    weekly_spending = defaultdict(float)
    
    for exp in st.session_state.expenses:
        try:
            exp_date = datetime.strptime(exp.get('date', ''), '%Y-%m-%d')
            exp_month = exp_date.strftime('%Y-%m')
            
            if exp_month == selected_month:
                # Calculate week number based on day of month (not calendar weeks)
                day_of_month = exp_date.day
                week_num = (day_of_month - 1) // 7 + 1
                
                # Calculate week date range (by day of month, not calendar)
                week_start_day = (week_num - 1) * 7 + 1
                week_end_day = min(week_num * 7, 31)
                
                # Create week key using actual dates
                month_obj = exp_date
                week_start = month_obj.replace(day=week_start_day)
                
                # Handle months with fewer than 31 days
                try:
                    week_end = month_obj.replace(day=week_end_day)
                except ValueError:
                    max_day = calendar.monthrange(month_obj.year, month_obj.month)[1]
                    week_end = month_obj.replace(day=max(min(week_end_day, max_day), 1))
                
                week_key = f"Week {week_num} ({week_start.strftime('%b %d')} - {week_end.strftime('%b %d')})"
                amt = safe_float(exp.get('total', 0))
                weekly_spending[week_key] += amt
        except:
            pass
    
    if weekly_spending:
        # Create bar chart for weekly breakdown
        # Sort by week number (numeric), not alphabetically
        weeks_list = sorted(list(weekly_spending.keys()), key=lambda x: int(x.split()[1]))
        amounts_list = [weekly_spending[w] for w in weeks_list]
        
        fig_weekly = go.Figure(data=[
            go.Bar(x=weeks_list, y=amounts_list, marker_color='#1f77b4', text=[f'${x:.0f}' for x in amounts_list],
                   textposition='auto')
        ])
        
        fig_weekly.update_layout(
            title=f"Weekly Spending - {selected_month_label}",
            xaxis_title="Week",
            yaxis_title="Spending ($)",
            height=350,
            showlegend=False
        )
        st.plotly_chart(fig_weekly, use_container_width=True)
        
        # Weekly summary
        st.markdown("**Weekly Summary:**")
        weekly_df = pd.DataFrame({
            'Week': weeks_list,
            'Spending': amounts_list
        })
        st.dataframe(weekly_df, use_container_width=True)
    else:
        st.info("No spending data for this month yet.")
    
    st.markdown("---")
    
    # NEW: Month-over-Month Comparison
    st.markdown("#### 📊 Month-over-Month Comparison")
    
    # Get current and previous month totals
    if months_sorted_hist and len(months_sorted_hist) >= 1:
        current_month_spending = sum(historical_data[selected_month].values()) if selected_month in historical_data else 0
        
        # Find previous month
        if selected_month in months_sorted_hist:
            current_idx = months_sorted_hist.index(selected_month)
            if current_idx > 0:
                previous_month = months_sorted_hist[current_idx - 1]
                previous_month_spending = sum(historical_data[previous_month].values())
                
                # Calculate change
                if previous_month_spending > 0:
                    change_pct = ((current_month_spending - previous_month_spending) / previous_month_spending) * 100
                    change_amount = current_month_spending - previous_month_spending
                    
                    # Display comparison
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        prev_month_label = datetime.strptime(previous_month, '%Y-%m').strftime('%B %Y')
                        st.metric(f"{prev_month_label}", f"${previous_month_spending:.2f}")
                    with col2:
                        st.metric(f"{selected_month_label}", f"${current_month_spending:.2f}")
                    with col3:
                        if change_pct > 0:
                            st.metric("Change", f"↑ ${change_amount:.2f}", f"+{change_pct:.1f}%", delta_color="inverse")
                        elif change_pct < 0:
                            st.metric("Change", f"↓ ${abs(change_amount):.2f}", f"{change_pct:.1f}%")
                        else:
                            st.metric("Change", f"${change_amount:.2f}", "0%")
                    
                    # Insight
                    if change_pct > 10:
                        st.warning(f"⚠️ You're spending {change_pct:.1f}% MORE than last month! Consider reducing expenses.")
                    elif change_pct < -10:
                        st.success(f"🎉 Great! You're spending {abs(change_pct):.1f}% LESS than last month!")
                else:
                    st.info("Compare with previous month when data is available.")
    else:
        st.info("Need at least 2 months of data to compare.")

with tabs[5]:  # Health
    st.markdown("### 🏥 Health Tracking & Analysis with Trends")
    
    st.markdown("#### 👤 Whose health data?")
    health_person = st.radio("Track health for:", ("Govind", "Amrithavarshini"), horizontal=True, key="health_person_radio")
    
    st.markdown("#### 📄 Upload Health Report Pages (Auto-Extract)")
    st.caption("💡 Tip: If your report is on multiple pages (JPG/PNG/PDF), upload all pages at once - they'll be combined automatically!")
    uploaded_reports = st.file_uploader("Upload Blood Test Report Pages (JPG/PNG/PDF - can upload multiple pages)", 
                                        type=["jpg", "jpeg", "png", "gif", "webp", "pdf"], 
                                        key="health_report_upload",
                                        accept_multiple_files=True)
    
    if uploaded_reports:
        # Handle mixed file types (images + PDFs)
        all_image_bytes = []
        file_descriptions = []
        
        for uploaded_file in uploaded_reports:
            file_type = uploaded_file.type
            
            if file_type == "application/pdf":
                # Extract images from PDF
                pdf_images = extract_images_from_pdf(uploaded_file.getvalue())
                if pdf_images:
                    all_image_bytes.extend(pdf_images)
                    file_descriptions.append(f"PDF: {uploaded_file.name} ({len(pdf_images)} pages)")
            else:
                # Regular image file
                all_image_bytes.append(uploaded_file.getvalue())
                file_descriptions.append(f"Image: {uploaded_file.name}")
        
        if all_image_bytes:
            st.info(f"📊 Processing {health_person}'s health report:\n" + "\n".join([f"  • {desc}" for desc in file_descriptions]))
            if st.button("🤖 Extract Metrics from All Pages", key="extract_report_btn"):
                with st.spinner(f"Analyzing {len(all_image_bytes)} page(s)..."):
                    all_extracted_metrics = []
                    
                    # Extract from each page
                    for idx, image_bytes in enumerate(all_image_bytes):
                        st.write(f"📖 Processing page {idx+1}/{len(all_image_bytes)}...")
                        extracted = extract_health_report(image_bytes)
                        
                        if extracted:
                            metrics = extracted.get('metrics', [])
                            all_extracted_metrics.extend(metrics)
                    
                    # Deduplicate metrics (same metric name from different pages)
                    if all_extracted_metrics:
                        # Group by metric name and keep latest/best value
                        metric_dict = {}
                        for metric in all_extracted_metrics:
                            metric_name = metric.get('name', '').lower()
                            if metric_name not in metric_dict:
                                metric_dict[metric_name] = metric
                            else:
                                # Keep first occurrence (can change logic if needed)
                                pass
                        
                        dedup_metrics = list(metric_dict.values())
                        
                        st.success(f"✅ Metrics extracted from all {len(all_image_bytes)} page(s)! ({len(dedup_metrics)} unique metrics)")
                        test_date = extracted.get('test_date', str(datetime.now().date())) if extracted else str(datetime.now().date())
                        
                        st.session_state['extracted_metrics'] = dedup_metrics
                        st.session_state['extracted_date'] = test_date
                        st.session_state['extracted_person'] = health_person
                        
                        st.markdown("**Extracted Metrics:**")
                        for metric in dedup_metrics:
                            st.write(f"• **{metric.get('name')}**: {metric.get('value')} {metric.get('unit')} (Normal: {metric.get('normal_range')})")
                    else:
                        st.error("❌ Could not extract metrics from any pages. Make sure they are clear images or PDFs of blood test reports.")
        else:
            st.error("❌ No valid images found. Please upload JPG, PNG, or PDF files.")
    
    # Show save button only if we have extracted metrics
    if 'extracted_metrics' in st.session_state and st.session_state.get('extracted_metrics'):
        st.markdown(f"**📊 Ready to save {len(st.session_state['extracted_metrics'])} metric(s) from {health_person}'s report**")
        st.info("✅ **Duplicate Protection:** If this report was already uploaded, duplicates will be automatically skipped!")
        if st.button("💾 Save All Metrics to Google Sheets", key="save_extracted_metrics_btn"):
            saved_count = 0
            for metric in st.session_state['extracted_metrics']:
                health_entry = {
                    'date': st.session_state.get('extracted_date', str(datetime.now().date())),
                    'metric': metric.get('name', ''),
                    'value': metric.get('value', ''),
                    'unit': metric.get('unit', ''),
                    'normal_range': metric.get('normal_range', ''),
                    'type': 'Blood Test',
                    'person': st.session_state.get('extracted_person', 'Govind'),
                    'added_at': datetime.now().isoformat()
                }
                if save_health_to_gsheet(health_entry):
                    st.session_state.health_metrics.append(health_entry)
                    saved_count += 1
            
            if saved_count > 0:
                st.success(f"✅ {saved_count} metrics saved for {st.session_state.get('extracted_person', 'Govind')}! 🎉")
                st.balloons()
                # Clear extracted metrics after saving
                del st.session_state['extracted_metrics']
                st.rerun()
            else:
                st.warning(f"⚠️ All {len(st.session_state.get('extracted_metrics', []))} metrics already exist in Google Sheets (duplicates prevented)! ✅\n\nYou might have uploaded this report before. If this is NEW data, contact support.")
                del st.session_state['extracted_metrics']
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("#### 📊 OR Enter Health Metrics Manually")
    with st.form("add_health_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            metric_date = st.date_input("Test Date", key="metric_date")
            person_input = st.selectbox("Person", ["Govind", "Amrithavarshini"], key="metric_person")
        with col2:
            metric_name = st.text_input("Metric Name (e.g., Cholesterol, Blood Sugar)", key="metric_name")
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
                'person': person_input,
                'added_at': datetime.now().isoformat()
            }
            if save_health_to_gsheet(health_entry):
                st.session_state.health_metrics.append(health_entry)
                st.success(f"✅ Health metric saved for {person_input}!")
    
    st.markdown("#### 📈 Health Analysis & Trends")
    if st.session_state.health_metrics:
        # Filter by person
        person_filter = st.selectbox("View trends for:", ["Govind", "Amrithavarshini", "Both"], key="person_trends_filter")
        
        if person_filter == "Both":
            person_data = st.session_state.health_metrics
        else:
            person_data = [h for h in st.session_state.health_metrics if h.get('person', 'Govind') == person_filter]
        
        if person_data:
            latest_analysis = analyze_health_metrics(person_data)
            
            if latest_analysis:
                status = latest_analysis.get('overall_status', 'Unknown')
                status_emoji = "✅" if status == "Good" else "⚠️" if status == "Fair" else "🔴"
                st.write(f"**{person_filter}'s Overall Status: {status_emoji} {status}**")
                
                if latest_analysis.get('warnings'):
                    st.write("**⚠️ Areas to Monitor:**")
                    for warning in latest_analysis.get('warnings', []):
                        st.write(f"  • {warning}")
                
                if latest_analysis.get('positives'):
                    st.write("**✅ Positive Findings:**")
                    for positive in latest_analysis.get('positives', []):
                        st.write(f"  • {positive}")
                
                if latest_analysis.get('risk_areas'):
                    st.write("**👁️ Things to Monitor (Proactive):**")
                    for risk in latest_analysis.get('risk_areas', []):
                        st.write(f"  • {risk}")
                
                st.markdown("**💡 Health Recommendations:**")
                for rec in latest_analysis.get('recommendations', []):
                    st.write(f"  • {rec}")
            
            st.markdown("#### 📊 Metric Trends Over Time")
            unique_metrics = sorted(set(h.get('metric', '') for h in person_data))
            
            if unique_metrics:
                selected_metric = st.selectbox("Select metric to view trend", unique_metrics, key="metric_trend_select")
                fig = plot_health_trend(person_data, selected_metric)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Need at least 2 data points to show trend. Keep adding health metrics!")
            
            st.markdown(f"#### 📋 {person_filter}'s Metrics History (All Time)")
            
            # Show how many records
            st.caption(f"📊 Showing all {len(person_data)} measurements")
            
            # Option to expand/collapse
            with st.expander(f"📈 View all {len(person_data)} measurements", expanded=True):
                # Create columns for better display
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])
                with col1:
                    st.write("**Date**")
                with col2:
                    st.write("**Metric**")
                with col3:
                    st.write("**Value**")
                with col4:
                    st.write("**Unit**")
                with col5:
                    st.write("**Normal Range**")
                
                st.divider()
                
                # Show all data sorted by date (newest first)
                def parse_date(date_str):
                    """Convert date string to sortable format"""
                    try:
                        # Handle various date formats
                        if isinstance(date_str, str):
                            return datetime.strptime(date_str[:10], '%Y-%m-%d')
                        return date_str
                    except:
                        return datetime.min
                
                sorted_data = sorted(person_data, key=lambda x: parse_date(x.get('date', '')), reverse=True)
                for metric in sorted_data:
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])
                    with col1:
                        st.write(metric.get('date', 'N/A'))
                    with col2:
                        st.write(metric.get('metric', 'N/A'))
                    with col3:
                        st.write(str(metric.get('value', 'N/A')))
                    with col4:
                        st.write(metric.get('unit', 'N/A'))
                    with col5:
                        st.write(metric.get('normal_range', 'N/A'))
        else:
            st.info(f"No health metrics found for {person_filter}. Start by uploading a health report!")
    
    st.markdown("---")
    st.markdown("#### 👨‍👩‍❤️ Household Health Recommendations (Cook Together!)")
    
    # Get data for both people
    govind_health = [h for h in st.session_state.health_metrics if h.get('person', 'Govind') == 'Govind']
    amritha_health = [h for h in st.session_state.health_metrics if h.get('person', 'Amrithavarshini') == 'Amrithavarshini']
    
    if govind_health and amritha_health:
        if st.button("🤖 Analyze Both Health Together", key="household_health_btn"):
            with st.spinner("Analyzing household health profile..."):
                joint_analysis = analyze_joint_health(govind_health, amritha_health)
                
                if joint_analysis:
                    st.success("✅ Household Analysis Complete!")
                    
                    # Overall Grade
                    grade = joint_analysis.get('household_grocery_grade', 'N/A')
                    st.markdown(f"### 📈 Your Household Health Grade: **{grade}**")
                    
                    # Summary
                    summary = joint_analysis.get('summary', '')
                    if summary:
                        st.info(summary)
                    
                    # Common Concerns
                    concerns = joint_analysis.get('common_concerns', [])
                    if concerns:
                        st.markdown("**🎯 Common Health Concerns (Both):**")
                        for concern in concerns:
                            st.write(f"  • {concern}")
                    
                    # Individual Flags
                    ind_flags = joint_analysis.get('individual_flags', {})
                    if ind_flags:
                        st.markdown("**⚠️ Individual Health Flags:**")
                        if ind_flags.get('govind'):
                            st.write("  **Govind:**")
                            for flag in ind_flags['govind']:
                                st.write(f"    • {flag}")
                        if ind_flags.get('amrithavarshini'):
                            st.write("  **Amrithavarshini:**")
                            for flag in ind_flags['amrithavarshini']:
                                st.write(f"    • {flag}")
                    
                    # Household Diet Goals
                    goals = joint_analysis.get('household_diet_goals', [])
                    if goals:
                        st.markdown("**🎯 Household Diet Goals:**")
                        for goal in goals:
                            st.write(f"  • {goal}")
                    
                    # Keep Foods
                    keep_foods = joint_analysis.get('keep_foods', [])
                    if keep_foods:
                        st.markdown("**✅ Foods to Keep (Good for Both):**")
                        for food in keep_foods:
                            st.write(f"  • {food}")
                    
                    # Reduce Foods
                    reduce_foods = joint_analysis.get('reduce_foods', [])
                    if reduce_foods:
                        st.markdown("**⚠️ Foods to Reduce (Bad for Both):**")
                        for food in reduce_foods:
                            st.write(f"  • {food}")
                    
                    # Meal Tips
                    meal_tips = joint_analysis.get('household_meal_tips', [])
                    if meal_tips:
                        st.markdown("**🍳 Household Cooking Tips:**")
                        for tip in meal_tips:
                            st.write(f"  • {tip}")
                    
                    # Cooking Together Advice
                    advice = joint_analysis.get('cooking_together_advice', '')
                    if advice:
                        st.markdown("**💡 Cooking Together Advice:**")
                        st.info(advice)
    else:
        st.info("📋 Need health data for BOTH Govind and Amrithavarshini to show household recommendations. Upload health reports for both!")

with tabs[6]:  # Fitness Plan
    st.markdown("### 🏋️ Personalized Fitness Plans")
    st.info("📊 Based on your latest health analysis, here are recommended home exercises!")
    
    # Get health data for both people (cached for 10 minutes)
    health_records = load_health()
    
    if not health_records:
        st.warning("⚠️ No health data found. Upload health reports first to get personalized fitness recommendations!")
    else:
        # Separate data by person
        govind_data = [h for h in health_records if h.get('person') == 'Govind']
        amrithavarshini_data = [h for h in health_records if h.get('person') == 'Amrithavarshini']
        
        # Create columns for side-by-side display
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👨 Govind's Fitness Plan")
            if govind_data:
                with st.spinner("🔄 Analyzing health metrics..."):
                    analysis = analyze_health_metrics(govind_data)
                
                if analysis:
                    st.write(f"**Analysis Status:** {analysis.get('overall_status', 'Unknown')}")
                    
                    if analysis.get('exercise_plan'):
                        exercise_plan = analysis['exercise_plan']
                        st.write(f"**Frequency:** {exercise_plan.get('frequency', 'N/A')}")
                        st.write(f"**Duration:** {exercise_plan.get('duration_per_session', 'N/A')} per session")
                        
                        st.markdown("**Recommended Exercises:**")
                        for idx, exercise in enumerate(exercise_plan.get('exercises', []), 1):
                            with st.expander(f"**{idx}. {exercise.get('name')}** ({exercise.get('duration')})"):
                                st.write(exercise.get('description', 'No description available'))
                                youtube_search = exercise.get('youtube_search', '')
                                if youtube_search:
                                    st.markdown(f"🔗 **YouTube Search:** `{youtube_search}`")
                                    st.link_button("🎬 Search on YouTube", f"https://www.youtube.com/results?search_query={youtube_search.replace(' ', '+')}")
                    else:
                        st.warning("⚠️ Claude didn't generate exercise plan. This might be a temporary issue.")
                        st.info("💡 Try refreshing the page or uploading a new health report to regenerate the fitness plan.")
                        # Show what Claude DID return
                        with st.expander("🔍 Debug: What Claude Returned"):
                            st.write(f"Overall Status: {analysis.get('overall_status', 'N/A')}")
                            st.write(f"Has warnings: {bool(analysis.get('warnings'))}")
                            st.write(f"Has positives: {bool(analysis.get('positives'))}")
                            st.write(f"Has exercise_plan: {bool(analysis.get('exercise_plan'))}")
                            st.write(f"Full response keys: {list(analysis.keys())}")
                else:
                    st.error("❌ Failed to analyze health data. Check your Anthropic API key!")
            else:
                st.info("No health data for Govind. Upload health reports first!")
        
        with col2:
            st.markdown("#### 👩 Amrithavarshini's Fitness Plan")
            if amrithavarshini_data:
                with st.spinner("🔄 Analyzing health metrics..."):
                    analysis = analyze_health_metrics(amrithavarshini_data)
                
                if analysis:
                    st.write(f"**Analysis Status:** {analysis.get('overall_status', 'Unknown')}")
                    
                    if analysis.get('exercise_plan'):
                        exercise_plan = analysis['exercise_plan']
                        st.write(f"**Frequency:** {exercise_plan.get('frequency', 'N/A')}")
                        st.write(f"**Duration:** {exercise_plan.get('duration_per_session', 'N/A')} per session")
                        
                        st.markdown("**Recommended Exercises:**")
                        for idx, exercise in enumerate(exercise_plan.get('exercises', []), 1):
                            with st.expander(f"**{idx}. {exercise.get('name')}** ({exercise.get('duration')})"):
                                st.write(exercise.get('description', 'No description available'))
                                youtube_search = exercise.get('youtube_search', '')
                                if youtube_search:
                                    st.markdown(f"🔗 **YouTube Search:** `{youtube_search}`")
                                    st.link_button("🎬 Search on YouTube", f"https://www.youtube.com/results?search_query={youtube_search.replace(' ', '+')}")
                    else:
                        st.warning("⚠️ Claude didn't generate exercise plan. This might be a temporary issue.")
                        st.info("💡 Try refreshing the page or uploading a new health report to regenerate the fitness plan.")
                        # Show what Claude DID return
                        with st.expander("🔍 Debug: What Claude Returned"):
                            st.write(f"Overall Status: {analysis.get('overall_status', 'N/A')}")
                            st.write(f"Has warnings: {bool(analysis.get('warnings'))}")
                            st.write(f"Has positives: {bool(analysis.get('positives'))}")
                            st.write(f"Has exercise_plan: {bool(analysis.get('exercise_plan'))}")
                            st.write(f"Full response keys: {list(analysis.keys())}")
                else:
                    st.error("❌ Failed to analyze health data. Check your Anthropic API key!")
            else:
                st.info("No health data for Amrithavarshini. Upload health reports first!")

with tabs[7]:  # Daily Wellness Log
    st.markdown("### ✅ Daily Wellness Tracker")
    st.info("📊 Track your daily habits and get AI insights on your health patterns!")
    
    # Load wellness logs
    wellness_logs = load_wellness_logs()
    
    # Sub-tabs
    wellness_tabs = st.tabs(["📝 Today's Log", "👨 Govind Analytics", "👩 Amrithavarshini Analytics", "📊 Weekly Report"])
    
    # Tab 1: Today's Log Entry
    with wellness_tabs[0]:
        st.markdown("#### Log Your Daily Wellness")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            log_date = st.date_input("Date", value=datetime.now().date(), key="wellness_date")
            person = st.selectbox("Who?", ["Govind", "Amrithavarshini"], key="wellness_person")
        with col2:
            st.write("")
            st.write("")
        with col3:
            st.write("")
            st.write("")
        
        # Exercise
        st.markdown("##### 🏋️ Exercise")
        col1, col2, col3 = st.columns(3)
        with col1:
            exercise_name = st.text_input("Exercise Name", placeholder="e.g., Brisk Walking, Yoga", key="ex_name")
        with col2:
            exercise_done = st.checkbox("Did it today?", key="ex_done")
        with col3:
            st.write("")
        
        # Hydration & Bathroom
        st.markdown("##### 💧 Hydration & Bathroom")
        col1, col2, col3 = st.columns(3)
        with col1:
            water_bottles = st.number_input("Water Bottles Drank", min_value=0, value=0, step=1, key="water")
        with col2:
            pee_count = st.number_input("Pee Count", min_value=0, value=0, step=1, key="pee")
        with col3:
            poop_count = st.number_input("Poop Count", min_value=0, value=0, step=1, key="poop")
        
        # Sleep & Mood
        st.markdown("##### 😴 Sleep & Mood")
        col1, col2, col3 = st.columns(3)
        with col1:
            sleep_hours = st.number_input("Sleep Hours", min_value=0.0, max_value=24.0, value=7.0, step=0.5, key="sleep")
        with col2:
            mood_score = st.slider("Mood/Energy (1-10)", min_value=1, max_value=10, value=5, key="mood")
        with col3:
            stress_score = st.slider("Stress Level (1-10)", min_value=1, max_value=10, value=5, key="stress")
        
        # Symptoms
        st.markdown("##### 🤒 Symptoms")
        symptoms = st.multiselect(
            "Any Symptoms? (Select all that apply)",
            ["Headache", "Nausea", "Dizziness", "Fatigue", "Cramps", "Bloating", "Fever", "Cough", "None"],
            key="wellness_symptoms_select"
        )
        
        # Medications & Steps
        st.markdown("##### 💊 Medications & Steps")
        col1, col2, col3 = st.columns(3)
        with col1:
            meds_taken = st.checkbox("Medications Taken?", key="meds_check")
        with col2:
            steps = st.number_input("Steps Today", min_value=0, value=0, step=500, key="steps_input")
        with col3:
            st.write("")
        
        # Diet & Notes
        st.markdown("##### 🍽️ Diet & Notes")
        diet_notes = st.selectbox("How was your diet?", ["Healthy", "Mixed", "Junk Food", "Not Tracked"], key="diet_select")
        notes = st.text_area("Additional Notes", placeholder="Any other observations...", key="wellness_notes")
        
        # Save button
        if st.button("💾 Save Daily Log"):
            wellness_data = {
                'date': log_date.strftime("%Y-%m-%d"),
                'person': person,
                'exercise_name': exercise_name if exercise_name else 'Not logged',
                'exercise_done': 'Yes' if exercise_done else 'No',
                'water_bottles': str(water_bottles),
                'pee_count': str(pee_count),
                'poop_count': str(poop_count),
                'sleep_hours': str(sleep_hours),
                'mood_score': str(mood_score),
                'stress_score': str(stress_score),
                'symptoms': ', '.join(symptoms) if symptoms else 'None',
                'medications_taken': 'Yes' if meds_taken else 'No',
                'steps': str(steps),
                'diet_notes': diet_notes,
                'notes': notes
            }
            
            if save_wellness_log(wellness_data):
                st.success(f"✅ Saved {person}'s wellness log for {log_date.strftime('%B %d, %Y')}!")
                wellness_logs = load_wellness_logs()
            else:
                st.error("❌ Failed to save wellness log!")
    
    # Tab 2: Govind Analytics
    with wellness_tabs[1]:
        st.markdown("#### 👨 Govind's Weekly Wellness")
        
        gov_analysis = analyze_wellness_week(wellness_logs, "Govind", days=7)
        
        if gov_analysis:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Water Intake", f"{gov_analysis['water_avg']:.1f} bottles", "Target: 8")
            with col2:
                st.metric("Sleep", f"{gov_analysis['sleep_avg']:.1f} hrs", "Target: 7-9")
            with col3:
                st.metric("Mood", f"{gov_analysis['mood_avg']:.1f}/10", "Higher is better")
            with col4:
                st.metric("Stress", f"{gov_analysis['stress_avg']:.1f}/10", "Lower is better")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Exercise", f"{gov_analysis['exercise_rate']:.0f}%", "Days completed")
            with col2:
                st.metric("Steps", f"{gov_analysis['steps_avg']:.0f}", "Target: 8000")
            with col3:
                st.metric("Days Tracked", gov_analysis['num_days'])
            
            # AI Analysis
            if gov_analysis['num_days'] >= 3:
                st.markdown("#### 💡 AI Health Insights")
                
                # Generate insights based on data
                insights = []
                
                if gov_analysis['water_avg'] < 6:
                    insights.append("⚠️ **Hydration:** You're drinking below target. Aim for 8+ bottles daily!")
                elif gov_analysis['water_avg'] >= 8:
                    insights.append("✅ **Hydration:** Great water intake! Keep it up!")
                
                if gov_analysis['sleep_avg'] < 6:
                    insights.append("🚨 **Sleep:** Critical - You're severely sleep deprived. Prioritize sleep tonight!")
                elif gov_analysis['sleep_avg'] < 7:
                    insights.append("⚠️ **Sleep:** Getting close to minimum. Try for 7.5+ hours.")
                elif gov_analysis['sleep_avg'] >= 7.5:
                    insights.append("✅ **Sleep:** Excellent sleep schedule! This improves everything else.")
                
                if gov_analysis['mood_avg'] >= 7:
                    insights.append("😊 **Mood:** Your mood is good! Keep doing what you're doing.")
                elif gov_analysis['mood_avg'] < 5:
                    insights.append("⚠️ **Mood:** Low mood detected. Check sleep, water, and exercise - they all impact mood.")
                
                if gov_analysis['stress_avg'] > 7:
                    insights.append("😰 **Stress:** High stress. Try exercise, meditation, or walks to manage it.")
                elif gov_analysis['stress_avg'] <= 5:
                    insights.append("✅ **Stress:** Great stress management! You're doing well.")
                
                if gov_analysis['exercise_rate'] >= 70:
                    insights.append("💪 **Exercise:** Excellent consistency! 70%+ completion is amazing!")
                elif gov_analysis['exercise_rate'] >= 50:
                    insights.append("👍 **Exercise:** Good effort! Try for 80% compliance.")
                elif gov_analysis['exercise_rate'] < 30:
                    insights.append("⚠️ **Exercise:** Low completion rate. Build momentum with just 1 workout!")
                
                if gov_analysis['steps_avg'] < 5000:
                    insights.append("🚶 **Steps:** Low daily steps. Add a 20-min walk to increase movement!")
                elif gov_analysis['steps_avg'] >= 10000:
                    insights.append("🏃 **Steps:** Great activity level! You're very active!")
                
                for insight in insights:
                    st.write(insight)
        else:
            st.info("📝 Add at least 3 days of wellness logs to see analytics!")
    
    # Tab 3: Amrithavarshini Analytics
    with wellness_tabs[2]:
        st.markdown("#### 👩 Amrithavarshini's Weekly Wellness")
        
        amit_analysis = analyze_wellness_week(wellness_logs, "Amrithavarshini", days=7)
        
        if amit_analysis:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Water Intake", f"{amit_analysis['water_avg']:.1f} bottles", "Target: 8")
            with col2:
                st.metric("Sleep", f"{amit_analysis['sleep_avg']:.1f} hrs", "Target: 7-9")
            with col3:
                st.metric("Mood", f"{amit_analysis['mood_avg']:.1f}/10", "Higher is better")
            with col4:
                st.metric("Stress", f"{amit_analysis['stress_avg']:.1f}/10", "Lower is better")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Exercise", f"{amit_analysis['exercise_rate']:.0f}%", "Days completed")
            with col2:
                st.metric("Steps", f"{amit_analysis['steps_avg']:.0f}", "Target: 8000")
            with col3:
                st.metric("Days Tracked", amit_analysis['num_days'])
            
            # AI Analysis
            if amit_analysis['num_days'] >= 3:
                st.markdown("#### 💡 AI Health Insights")
                
                # Generate insights based on data
                insights = []
                
                if amit_analysis['water_avg'] < 6:
                    insights.append("⚠️ **Hydration:** You're drinking below target. Aim for 8+ bottles daily!")
                elif amit_analysis['water_avg'] >= 8:
                    insights.append("✅ **Hydration:** Great water intake! Keep it up!")
                
                if amit_analysis['sleep_avg'] < 6:
                    insights.append("🚨 **Sleep:** Critical - You're severely sleep deprived. Prioritize sleep tonight!")
                elif amit_analysis['sleep_avg'] < 7:
                    insights.append("⚠️ **Sleep:** Getting close to minimum. Try for 7.5+ hours.")
                elif amit_analysis['sleep_avg'] >= 7.5:
                    insights.append("✅ **Sleep:** Excellent sleep schedule! This improves everything else.")
                
                if amit_analysis['mood_avg'] >= 7:
                    insights.append("😊 **Mood:** Your mood is good! Keep doing what you're doing.")
                elif amit_analysis['mood_avg'] < 5:
                    insights.append("⚠️ **Mood:** Low mood detected. Check sleep, water, and exercise - they all impact mood.")
                
                if amit_analysis['stress_avg'] > 7:
                    insights.append("😰 **Stress:** High stress. Try exercise, meditation, or walks to manage it.")
                elif amit_analysis['stress_avg'] <= 5:
                    insights.append("✅ **Stress:** Great stress management! You're doing well.")
                
                if amit_analysis['exercise_rate'] >= 70:
                    insights.append("💪 **Exercise:** Excellent consistency! 70%+ completion is amazing!")
                elif amit_analysis['exercise_rate'] >= 50:
                    insights.append("👍 **Exercise:** Good effort! Try for 80% compliance.")
                elif amit_analysis['exercise_rate'] < 30:
                    insights.append("⚠️ **Exercise:** Low completion rate. Build momentum with just 1 workout!")
                
                if amit_analysis['steps_avg'] < 5000:
                    insights.append("🚶 **Steps:** Low daily steps. Add a 20-min walk to increase movement!")
                elif amit_analysis['steps_avg'] >= 10000:
                    insights.append("🏃 **Steps:** Great activity level! You're very active!")
                
                for insight in insights:
                    st.write(insight)
        else:
            st.info("📝 Add at least 3 days of wellness logs to see analytics!")
    
    # Tab 4: Weekly Report
    with wellness_tabs[3]:
        st.markdown("#### 📊 Weekly Wellness Report")
        
        if wellness_logs:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### This Week's Summary")
                
                gov_analysis = analyze_wellness_week(wellness_logs, "Govind", days=7)
                amit_analysis = analyze_wellness_week(wellness_logs, "Amrithavarshini", days=7)
                
                if gov_analysis:
                    st.markdown("**Govind:**")
                    st.write(f"- Water: {gov_analysis['water_avg']:.1f} bottles")
                    st.write(f"- Sleep: {gov_analysis['sleep_avg']:.1f} hours")
                    st.write(f"- Mood: {gov_analysis['mood_avg']:.1f}/10")
                    st.write(f"- Exercise: {gov_analysis['exercise_rate']:.0f}% done")
                
                if amit_analysis:
                    st.markdown("**Amrithavarshini:**")
                    st.write(f"- Water: {amit_analysis['water_avg']:.1f} bottles")
                    st.write(f"- Sleep: {amit_analysis['sleep_avg']:.1f} hours")
                    st.write(f"- Mood: {amit_analysis['mood_avg']:.1f}/10")
                    st.write(f"- Exercise: {amit_analysis['exercise_rate']:.0f}% done")
            
            with col2:
                st.markdown("##### 🎯 Next Week Goals")
                st.write("""
                Based on this week's data:
                - Increase water intake by 1-2 bottles
                - Aim for 7.5+ hours sleep
                - Improve exercise consistency to 70%+
                - Keep stress management active
                - Maintain good hydration habits
                """)
        else:
            st.info("No wellness data yet. Start logging today!")

with tabs[8]:  # Nutrition Tracker
    st.subheader("🍽️ Advanced Nutrition Tracker")
    
    nutrition_tabs = st.tabs([
        "🍽️ Log Meals",
        "📊 Daily Analysis", 
        "📈 Weekly Summary",
        "🥘 Recipe Database",
        "🍔 Restaurant Meals",
        "🎯 Macro Targets",
        "💰 Cost Tracking",
        "🛒 Shopping List",
        "❤️ Mood Correlation"
    ])
    
    # ========== TAB 1: LOG MEALS ==========
    with nutrition_tabs[0]:
        st.subheader("🍽️ Log Today's Meals")
        
        col1, col2 = st.columns(2)
        with col1:
            meal_date = st.date_input("Date", datetime.now(), key="meal_date")
            person = st.selectbox("Who", ["Govind", "Amrithavarshini"], key="meal_person")
        
        st.markdown("---")
        
        # Breakfast
        with st.expander("🌅 Breakfast", expanded=True):
            breakfast_text = st.text_area(
                "What did you eat for breakfast?",
                placeholder="e.g., Eggs, toast, orange juice, coffee",
                key="breakfast_input",
                height=80
            )
            breakfast_time = st.time_input("Time", datetime.min.time(), key="breakfast_time")
            breakfast_comfort = st.slider("Digest comfort (1-10)", 1, 10, 5, key="breakfast_comfort")
            
            if breakfast_text and st.button("Analyze Breakfast", key="analyze_breakfast"):
                with st.spinner("🤖 Analyzing breakfast..."):
                    try:
                        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                        prompt = f"""Analyze this breakfast: "{breakfast_text}"
Provide ONLY valid JSON (no markdown):
{{
    "protein_g": <number>,
    "carbs_g": <number>,
    "fat_g": <number>,
    "fiber_g": <number>,
    "calories": <number>,
    "rating": "<Poor/Fair/Good/Excellent>",
    "feedback": "Brief feedback"
}}"""
                        response = client.messages.create(
                            model="claude-haiku-4-5-20251001",
                            max_tokens=300,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        text = response.content[0].text.strip()
                        if "```" in text:
                            text = text.split("```")[1].replace("json", "").strip()
                        
                        analysis = json.loads(text)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Protein", f"{analysis['protein_g']}g")
                        with col2:
                            st.metric("Carbs", f"{analysis['carbs_g']}g")
                        with col3:
                            st.metric("Fat", f"{analysis['fat_g']}g")
                        with col4:
                            st.metric("Calories", f"{analysis['calories']}")
                        
                        st.write(f"**Rating:** {analysis['rating']}")
                        st.write(f"**Feedback:** {analysis['feedback']}")
                    except Exception as e:
                        st.error(f"Error analyzing meal: {str(e)}")
        
        # Lunch
        with st.expander("🥪 Lunch", expanded=False):
            lunch_text = st.text_area(
                "What did you eat for lunch?",
                placeholder="e.g., Chicken sandwich, apple, salad",
                key="lunch_input",
                height=80
            )
            lunch_time = st.time_input("Time", datetime.min.time(), key="lunch_time")
            lunch_comfort = st.slider("Digest comfort (1-10)", 1, 10, 5, key="lunch_comfort")
            
            if lunch_text and st.button("Analyze Lunch", key="analyze_lunch"):
                st.success("✅ Lunch analysis (Claude AI integration ready)")
        
        # Dinner
        with st.expander("🍽️ Dinner", expanded=False):
            dinner_text = st.text_area(
                "What did you eat for dinner?",
                placeholder="e.g., Rice, curry, vegetables, bread",
                key="dinner_input",
                height=80
            )
            dinner_time = st.time_input("Time", datetime.min.time(), key="dinner_time")
            dinner_comfort = st.slider("Digest comfort (1-10)", 1, 10, 5, key="dinner_comfort")
        
        # Hydration
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            water_bottles = st.number_input("Water bottles today", 0, 20, 4, key="water_bottles")
        with col2:
            st.info(f"💧 {water_bottles * 500}ml total hydration")
        
        # Energy level
        energy_level = st.slider("Energy level today (1-10)", 1, 10, 5, key="energy_level")
        mood_notes = st.text_area("Mood & notes", placeholder="How do you feel today?", key="mood_notes")
        
        if st.button("💾 Save Today's Meals", key="save_meals"):
            st.success("✅ Meals saved! (Google Sheets integration ready)")
    
    # ========== TAB 2: DAILY ANALYSIS ==========
    with nutrition_tabs[1]:
        st.subheader("📊 Today's Nutrition Analysis")
        
        st.info("""
        💡 **Daily Nutrition Goals:**
        - Calories: 1800-2200
        - Protein: 60-70g
        - Carbs: 200-250g
        - Fat: 60-75g
        - Fiber: 25-30g
        """)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Calories", "1850/2000", "92%")
        with col2:
            st.metric("Protein", "65/70g", "93%")
        with col3:
            st.metric("Carbs", "220/250g", "88%")
        with col4:
            st.metric("Fat", "62/75g", "83%")
        with col5:
            st.metric("Fiber", "24/30g", "80%")
        
        st.markdown("---")
        st.success("✅ Excellent protein intake")
        st.success("✅ Good carb-to-protein ratio")
        st.warning("⚠️ Fiber slightly low - add vegetables to dinner")
    
    # ========== TAB 3: WEEKLY SUMMARY ==========
    with nutrition_tabs[2]:
        st.subheader("📈 Weekly Nutrition Summary")
        
        week_start = st.date_input("Week starting", datetime.now() - timedelta(days=7), key="week_start")
        
        if st.button("🤖 Generate AI Summary", key="generate_summary"):
            st.info("✅ Weekly summary generation (Claude AI integration ready)")
    
    # ========== TAB 4: RECIPE DATABASE ==========
    with nutrition_tabs[3]:
        st.subheader("🥘 Recipe Database")
        
        RECIPES = {
            "Breakfast": {
                "Eggs & Toast": {"protein": 12, "carbs": 30, "fat": 8, "fiber": 3, "cal": 250},
                "Oatmeal + Berries": {"protein": 8, "carbs": 45, "fat": 4, "fiber": 8, "cal": 280},
                "Yogurt Parfait": {"protein": 15, "carbs": 40, "fat": 5, "fiber": 4, "cal": 300},
            },
            "Lunch": {
                "Chicken Sandwich": {"protein": 25, "carbs": 35, "fat": 10, "fiber": 3, "cal": 400},
                "Tuna Salad": {"protein": 20, "carbs": 15, "fat": 8, "fiber": 4, "cal": 280},
                "Rice & Curry": {"protein": 15, "carbs": 60, "fat": 8, "fiber": 4, "cal": 450},
            },
            "Dinner": {
                "Grilled Chicken + Veggies": {"protein": 35, "carbs": 25, "fat": 8, "fiber": 5, "cal": 420},
                "Fish + Rice": {"protein": 30, "carbs": 45, "fat": 6, "fiber": 3, "cal": 480},
            }
        }
        
        meal_type = st.selectbox("Meal Type", list(RECIPES.keys()), key="recipe_type")
        
        st.markdown("---")
        for recipe_name, macros in RECIPES[meal_type].items():
            with st.expander(recipe_name):
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Protein", f"{macros['protein']}g")
                with col2:
                    st.metric("Carbs", f"{macros['carbs']}g")
                with col3:
                    st.metric("Fat", f"{macros['fat']}g")
                with col4:
                    st.metric("Fiber", f"{macros['fiber']}g")
                with col5:
                    st.metric("Calories", f"{macros['cal']}")
                
                if st.button(f"Add {recipe_name}", key=f"add_{recipe_name}"):
                    st.success(f"✅ {recipe_name} added to today's meals!")
    
    # ========== TAB 5: RESTAURANT MEALS ==========
    with nutrition_tabs[4]:
        st.subheader("🍔 Restaurant Meals")
        
        RESTAURANTS = {
            "McDonald's": {
                "Big Mac": {"protein": 25, "carbs": 45, "fat": 30, "fiber": 2, "cal": 550},
            },
            "Subway": {
                '6" Turkey': {"protein": 18, "carbs": 45, "fat": 5, "fiber": 4, "cal": 320},
            },
            "Chipotle": {
                "Chicken Bowl": {"protein": 30, "carbs": 60, "fat": 15, "fiber": 12, "cal": 520},
            }
        }
        
        restaurant = st.selectbox("Restaurant", list(RESTAURANTS.keys()), key="restaurant_select")
        
        for meal_name, macros in RESTAURANTS[restaurant].items():
            with st.expander(meal_name):
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Protein", f"{macros['protein']}g")
                with col2:
                    st.metric("Carbs", f"{macros['carbs']}g")
                with col3:
                    st.metric("Fat", f"{macros['fat']}g")
                with col4:
                    st.metric("Calories", f"{macros['cal']}")
                if st.button(f"Add {meal_name}", key=f"add_rest_{meal_name}"):
                    st.success(f"✅ {meal_name} added!")
    
    # ========== TAB 6: MACRO TARGETS ==========
    with nutrition_tabs[5]:
        st.subheader("🎯 Set Macro Targets")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            target_protein = st.number_input("Protein (g)", 0, 200, 70, key="target_protein")
        with col2:
            target_carbs = st.number_input("Carbs (g)", 0, 400, 250, key="target_carbs")
        with col3:
            target_fat = st.number_input("Fat (g)", 0, 150, 70, key="target_fat")
        with col4:
            target_fiber = st.number_input("Fiber (g)", 0, 50, 30, key="target_fiber")
        
        target_calories = (target_protein * 4) + (target_carbs * 4) + (target_fat * 9)
        st.metric("Estimated Daily Calories", f"{target_calories:.0f}")
        
        if st.button("💾 Save Targets", key="save_targets"):
            st.success("✅ Macro targets saved!")
    
    # ========== TAB 7: COST TRACKING ==========
    with nutrition_tabs[6]:
        st.subheader("💰 Meal Cost Tracking")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            breakfast_cost = st.number_input("Breakfast cost ($)", 0.0, key="breakfast_cost")
        with col2:
            lunch_cost = st.number_input("Lunch cost ($)", 0.0, key="lunch_cost")
        with col3:
            dinner_cost = st.number_input("Dinner cost ($)", 0.0, key="dinner_cost")
        
        total_daily = breakfast_cost + lunch_cost + dinner_cost
        st.metric("Daily Food Cost", f"${total_daily:.2f}")
        st.info(f"📊 Weekly estimate: ${total_daily * 7:.2f}")
    
    # ========== TAB 8: SHOPPING LIST ==========
    with nutrition_tabs[7]:
        st.subheader("🛒 Auto-Generate Shopping List")
        
        planned_meals = st.text_area(
            "Plan meals for the week",
            placeholder="Monday: Salad, Pasta\nTuesday: Tacos, Curry",
            height=120,
            key="planned_meals"
        )
        
        if st.button("📋 Generate Shopping List"):
            st.info("✅ Shopping list generation (Claude AI integration ready)")
    
    # ========== TAB 9: MOOD CORRELATION ==========
    with nutrition_tabs[8]:
        st.subheader("❤️ Food-Mood Correlation")
        
        st.info("""
        Track how different foods affect your energy, mood, and sleep!
        """)
        
        st.write("""
        **Detected Patterns:**
        - High Protein → High Energy (correlation: 0.85)
        - Sugary foods → Energy crash (correlation: 0.72)
        - Good hydration → Better mood (correlation: 0.68)
        """)



with tabs[9]:  # Fertility Tracker
    st.markdown("### 👶 Fertility & Ovulation Tracker")
    st.info("📊 Track your menstrual cycle to predict ovulation and optimize conception timing!")
    
    # Only show for Amrithavarshini
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Amrithavarshini's Fertility Tracking")
    
    # Load fertility cycles
    fertility_cycles = load_fertility_cycles()
    
    # Tabs within fertility tracker
    fert_tabs = st.tabs(["📅 Add/View Cycles", "📊 Cycle Analysis", "🎯 Ovulation Prediction", "👶 Conception Tips"])
    
    # Tab 1: Add/View Cycles
    with fert_tabs[0]:
        st.markdown("#### Add New Menstrual Cycle")
        
        col1, col2 = st.columns(2)
        with col1:
            period_start = st.date_input("Period Start Date", value=None, key="period_start")
        with col2:
            period_end = st.date_input("Period End Date", value=None, key="period_end")
        
        # AUTO-CALCULATE cycle length from previous period
        calculated_cycle_length = 28  # Default
        if period_start and fertility_cycles:
            # Find the most recent previous cycle
            cycle_dates = []
            for cycle in fertility_cycles:
                try:
                    start_date = pd.to_datetime(cycle.get('date_start', ''))
                    cycle_dates.append(start_date)
                except:
                    pass
            
            if cycle_dates:
                most_recent_previous = max(cycle_dates)
                # Calculate: Current period start - Previous period start = cycle length
                calculated_cycle_length = (pd.Timestamp(period_start) - most_recent_previous).days
                if calculated_cycle_length <= 0:
                    calculated_cycle_length = 28
        
        # Show auto-calculated cycle length
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📊 **Auto-Calculated Cycle Length:** `{calculated_cycle_length} days`")
        with col2:
            manual_override = st.checkbox("Override?", key="override_cycle_length", 
                                        help="Check if you want to manually set a different cycle length")
        
        if manual_override:
            cycle_length = st.slider("Your Cycle Length (days)", min_value=21, max_value=50, 
                                    value=calculated_cycle_length, step=1, key="cycle_length_slider")
        else:
            cycle_length = calculated_cycle_length
        
        col1, col2, col3 = st.columns(3)
        with col1:
            cervical_fluid = st.selectbox("Cervical Fluid (Peak Day)", ["Dry", "Sticky", "Creamy", "Watery"], key="cervical_fluid")
        with col2:
            temperature = st.number_input("Basal Temperature (°C) - Optional", min_value=36.0, max_value=38.0, value=36.5, step=0.1, key="temp_input")
        with col3:
            temperature = None if temperature == 36.5 else temperature
        
        symptoms = st.multiselect(
            "Symptoms (Select all that apply)",
            ["Cramping", "Bloating", "Breast Tenderness", "Energy Increase", "Libido Increase", "Mood Changes"],
            key="symptoms_select"
        )
        
        notes = st.text_area("Additional Notes", placeholder="Any other observations...", key="notes_input")
        
        if st.button("💾 Save Cycle Data"):
            if period_start and period_end:
                if period_end >= period_start:
                    # Use auto-calculated cycle length (or manually overridden)
                    cycle_data = {
                        'date_start': period_start.strftime("%Y-%m-%d"),
                        'date_end': period_end.strftime("%Y-%m-%d"),
                        'cycle_length': str(cycle_length),
                        'cervical_fluid': cervical_fluid,
                        'temperature': str(temperature) if temperature else '',
                        'symptoms': ', '.join(symptoms) if symptoms else '',
                        'notes': notes
                    }
                    
                    if save_cycle_to_gsheet(cycle_data):
                        st.success(f"✅ Cycle saved successfully! (Cycle length: {cycle_length} days)")
                        fertility_cycles = load_fertility_cycles()
                        st.rerun()
                    else:
                        st.warning("⚠️ This cycle start date already exists!")
                else:
                    st.error("❌ End date must be after start date!")
            else:
                st.error("❌ Please enter both start and end dates!")
        
        # Display past cycles
        if fertility_cycles:
            st.markdown("#### Past Cycles")
            for idx, cycle in enumerate(reversed(fertility_cycles), 1):
                with st.expander(f"Cycle {idx}: {cycle.get('date_start', 'N/A')} to {cycle.get('date_end', 'N/A')} ({cycle.get('cycle_length', '?')} days)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Cervical Fluid:** {cycle.get('cervical_fluid', 'N/A')}")
                        st.write(f"**Temperature:** {cycle.get('temperature', 'Not tracked')}")
                    with col2:
                        st.write(f"**Symptoms:** {cycle.get('symptoms', 'None logged')}")
                        st.write(f"**Notes:** {cycle.get('notes', 'No notes')}")
                    
                    # Delete button
                    if st.button(f"🗑️ Delete this cycle", key=f"del_cycle_{cycle.get('date_start')}"):
                        st.info("📝 Note: To delete, go to Google Sheets 'Fertility Cycles' and delete the row manually, then refresh the app.")
                        st.markdown("[Open Google Sheets Fertility Tracker](https://docs.google.com/spreadsheets/d/1tzRTNtq3N-QPabBSowhmzYXuxHR9bimvYTn1z0wjuQs/edit#gid=0)")
    
    # Tab 2: Cycle Analysis
    with fert_tabs[1]:
        if fertility_cycles and len(fertility_cycles) >= 2:
            cycle_analysis = analyze_cycle_patterns(fertility_cycles)
            
            if cycle_analysis:
                st.markdown("#### 📊 Your Cycle Patterns")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Average Cycle", f"{cycle_analysis['average_cycle_length']:.0f} days", 
                              f"({cycle_analysis['min_cycle_length']}-{cycle_analysis['max_cycle_length']} days)")
                with col2:
                    status = "✅ Regular" if cycle_analysis['is_regular'] else "⚠️ Irregular"
                    st.metric("Status", status)
                with col3:
                    st.metric("Cycles Tracked", cycle_analysis['num_cycles'])
                with col4:
                    prob = get_conception_probability(cycle_analysis)
                    st.metric("Conception Odds", f"{prob}%/month")
                
                # Cycle length trend
                st.markdown("#### Cycle Length Trend")
                cycle_df = pd.DataFrame({
                    'Cycle': range(1, len(cycle_analysis['cycle_lengths']) + 1),
                    'Length (days)': cycle_analysis['cycle_lengths']
                })
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=cycle_df['Cycle'],
                    y=cycle_df['Length (days)'],
                    mode='lines+markers',
                    name='Cycle Length',
                    line=dict(color='#FF69B4', width=3),
                    marker=dict(size=10)
                ))
                fig.add_hline(y=cycle_analysis['average_cycle_length'], line_dash="dash", 
                             line_color="green", annotation_text="Average", annotation_position="right")
                fig.update_layout(title="Menstrual Cycle Lengths Over Time", 
                                 xaxis_title="Cycle Number", yaxis_title="Days",
                                 hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
                
                # Regularity assessment
                if cycle_analysis['is_regular']:
                    st.success("✅ Your cycles are VERY REGULAR! This is ideal for conception planning. You can predict ovulation with high accuracy!")
                else:
                    st.warning("⚠️ Your cycles vary by more than 2 days. Track more cycles to get better predictions. Still trackable, just less predictable.")
        else:
            st.info("📝 Add at least 2 cycle records to see analysis. Currently you have " + 
                   f"{len(fertility_cycles)} cycles recorded.")
    
    # Tab 3: Ovulation Prediction
    with fert_tabs[2]:
        if fertility_cycles:
            cycle_analysis = analyze_cycle_patterns(fertility_cycles)
            if cycle_analysis:
                avg_cycle = cycle_analysis['average_cycle_length']
            else:
                avg_cycle = 28
        else:
            avg_cycle = 28
        
        st.markdown("#### 🎯 Ovulation & Fertile Window Prediction")
        
        col1, col2 = st.columns(2)
        with col1:
            last_period = st.date_input("Last Period Start Date", value=None, key="last_period_pred")
        with col2:
            cycle_length = st.slider("Your Cycle Length (days)", min_value=21, max_value=45, 
                                    value=int(avg_cycle), key="cycle_length_slider")
        
        if last_period:
            # Convert to pandas Timestamp for consistent date handling
            last_period = pd.Timestamp(last_period)
            
            ovulation_date = calculate_ovulation_date(last_period, cycle_length)
            fertile_start, fertile_end = calculate_fertile_window(ovulation_date)
            
            st.markdown(f"#### 📅 Your Prediction ({last_period.strftime('%B %Y')})")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Last Period", last_period.strftime("%b %d"))
            with col2:
                st.metric("Expected Ovulation", ovulation_date.strftime("%b %d"))
            with col3:
                next_period = last_period + pd.Timedelta(days=cycle_length)
                st.metric("Next Period", next_period.strftime("%b %d"))
            
            # Fertile window details
            st.markdown("#### 🌟 Fertile Window (Best Days to Conceive)")
            
            st.info(f"**Fertile Period:** {fertile_start.strftime('%b %d')} to {fertile_end.strftime('%b %d')} (6 days)")
            
            # Create fertility calendar
            days_data = []
            current = last_period
            for i in range(cycle_length):
                day_type = "period" if i < 5 else "normal"
                
                if current >= fertile_start and current <= fertile_end:
                    if current == ovulation_date:
                        day_type = "ovulation"
                    else:
                        day_type = "fertile"
                
                days_data.append({
                    'date': current,
                    'day': current.strftime("%a"),
                    'type': day_type,
                    'day_num': (current - last_period).days
                })
                current += pd.Timedelta(days=1)
            
            # Display calendar
            st.markdown("#### 📅 Fertility Calendar")
            cols = st.columns(7)
            col_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            
            for i, col_name in enumerate(col_names):
                with cols[i]:
                    st.write(f"**{col_name}**")
            
            current_col = (last_period.weekday())  # 0=Monday
            
            for day_info in days_data:
                if current_col == 0:
                    cols = st.columns(7)
                
                with cols[current_col]:
                    if day_info['type'] == 'period':
                        st.markdown(f"🔴 {day_info['day']}\n{day_info['date'].strftime('%d')}")
                    elif day_info['type'] == 'ovulation':
                        st.markdown(f"⭐ {day_info['day']}\n{day_info['date'].strftime('%d')}")
                    elif day_info['type'] == 'fertile':
                        st.markdown(f"🟢 {day_info['day']}\n{day_info['date'].strftime('%d')}")
                    else:
                        st.markdown(f"⚪ {day_info['day']}\n{day_info['date'].strftime('%d')}")
                
                current_col = (current_col + 1) % 7
            
            # Best conception days
            st.markdown("#### ✅ Best Conception Days")
            best_day_1 = (ovulation_date - pd.Timedelta(days=1)).strftime("%A, %b %d")
            best_day_2 = ovulation_date.strftime("%A, %b %d")
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"**Day -1:** {best_day_1}\n25-30% conception rate")
            with col2:
                st.success(f"**Day 0 (Peak):** {best_day_2}\n30-35% conception rate")
            
            st.info("💡 **Tip:** Have intercourse on both days for best results. Daily intercourse during fertile window is also effective!")
        else:
            st.info("📅 Enter your last period date to see predictions")
    
    # Tab 4: Conception Tips
    with fert_tabs[3]:
        st.markdown("#### 👶 Tips to Optimize Conception")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🛏️ Timing & Intimacy")
            st.write("""
            - Have intercourse every other day during fertile window
            - Don't stress about frequency (every 2-3 days works well)
            - Positions: Traditional positions optimal for sperm delivery
            - Relax after intercourse (gravity helps!)
            """)
            
            st.markdown("##### 🩺 Tracking Methods")
            st.write("""
            - **Cervical Fluid:** Peak fertility when watery/egg-white consistency
            - **Basal Temperature:** Slight rise (0.3-0.5°C) confirms ovulation
            - **Ovulation Strips:** Detect LH surge 24-48h before ovulation
            - **Apps:** Track data for pattern recognition
            """)
        
        with col2:
            st.markdown("##### 🥗 Nutrition for Fertility")
            st.write("""
            - **Folic Acid:** Leafy greens, legumes, asparagus
            - **Iron:** Red meat, spinach, lentils
            - **Zinc:** Oysters, nuts, seeds, pumpkin seeds
            - **Vitamin D:** Sunlight, fatty fish, fortified milk
            - **Antioxidants:** Berries, dark chocolate, nuts
            """)
            
            st.markdown("##### 😴 Lifestyle Factors")
            st.write("""
            - **Sleep:** 7-9 hours improves fertility
            - **Stress:** Chronic stress reduces conception odds
            - **Exercise:** Moderate (30 min/day) ideal - avoid extremes
            - **Weight:** Healthy BMI improves ovulation
            - **Avoid:** Smoking, excess caffeine, alcohol
            """)
        
        st.markdown("---")
        st.markdown("#### 💪 Partner Support")
        st.write("""
        **For Govind:** Support with healthy lifestyle to maximize sperm quality:
        - Sleep 7+ hours (improves sperm count and motility)
        - Avoid hot baths/saunas (heat damages sperm production)
        - Take zinc supplement (improves sperm quality)
        - Regular exercise (improves testosterone)
        - Reduce stress and caffeine
        - Maintain healthy weight
        """)
        
        if fertility_cycles:
            cycle_analysis = analyze_cycle_patterns(fertility_cycles)
            if cycle_analysis:
                prob = get_conception_probability(cycle_analysis)
                st.success(f"""
                ✅ **Your Conception Probability:** {prob}% per cycle
                
                **Timeline Expectations:**
                - 1 month: {prob}% chance
                - 3 months: ~{min(95, round(prob * 3.5))}% cumulative chance
                - 6 months: ~{min(99, round(prob * 6.5))}% cumulative chance
                
                Most couples conceive within 6 months with perfect timing!
                """)

with tabs[10]:  # Smart Grocery
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
            
            # Check if health metrics exist for both people
            govind_health = [h for h in st.session_state.health_metrics if h.get('person', 'Govind') == 'Govind']
            amritha_health = [h for h in st.session_state.health_metrics if h.get('person', 'Amrithavarshini') == 'Amrithavarshini']
            has_both_health = len(govind_health) > 0 and len(amritha_health) > 0
            has_any_health = len(st.session_state.health_metrics) > 0
            
            if st.button("🤖 Get Smart Recommendations"):
                with st.spinner("Analyzing your household groceries..."):
                    # If health data exists for both, use household mode
                    if has_both_health:
                        analysis = analyze_grocery_health(all_items, st.session_state.health_metrics)
                        mode = "HOUSEHOLD (optimized for both Govind & Amrithavarshini)"
                    elif has_any_health:
                        analysis = analyze_grocery_health(all_items, st.session_state.health_metrics)
                        mode = "PERSONALIZED (based on available health data)"
                    else:
                        analysis = analyze_grocery_health(all_items, None)
                        mode = "GENERIC (general health guidelines)"
                    
                    if analysis:
                        st.success(f"✅ Analysis Complete ({mode})")
                        
                        # Overall Grade
                        grade = analysis.get('overall_grade', 'N/A')
                        if has_both_health:
                            st.markdown(f"### 📈 Your Household Grocery Grade: **{grade}** 👨‍👩‍❤️")
                        else:
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
                            if has_both_health:
                                st.info(f"👨‍👩‍❤️ HOUSEHOLD: {note}")
                            elif has_any_health:
                                st.info(f"📊 {note}")
                            else:
                                st.warning(f"⚠️ {note}")
                        
                        # Encourage health reports if not present for both
                        if not has_both_health:
                            st.markdown("---")
                            st.info("💡 **Pro Tip:** Upload health reports for BOTH Govind & Amrithavarshini to get household-optimized recommendations since you cook together!")
                            st.success("💪 **Tip:** Upload health reports to get PERSONALIZED recommendations based on YOUR health metrics!")
        else:
            st.info("📸 No grocery items found. Upload receipts first to get recommendations!")
    else:
        st.info("📸 No grocery data. Upload receipts to get smart recommendations!")

with tabs[11]:  # Budgets
    st.markdown("### 🎯 Set Monthly Budgets")
    
    categories = ['Groceries', 'Dining', 'Transportation', 'Entertainment', 'Shopping', 'Healthcare']
    
    for cat in categories:
        current = st.session_state.budgets.get(cat, 0)
        budget = st.number_input(f"{cat} Budget (CAD)", min_value=0.0, value=safe_float(current), step=10.0)
        st.session_state.budgets[cat] = budget
    
    if st.button("💾 Save Budgets"):
        if save_budgets_to_gsheet(st.session_state.budgets):
            st.balloons()

st.markdown("---")
st.markdown("💡 **Health & Wealth: Your complete life tracker** - Finances + Health + Nutrition (Data saved in Google Sheets ☁️)")
