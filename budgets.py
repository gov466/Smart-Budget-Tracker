# Budgets Module - Budget Planning & Tracking

import streamlit as st
from ..config import BUDGET_HEADERS
from ..gsheet_client import get_gsheet_client, get_all_values_safe, clear_worksheet_safe, insert_row_safe
from ..utils import safe_float


def load_budgets():
    """Load budgets from Google Sheets - SIMPLIFIED"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            print("❌ No Google Sheets client")
            return {}
        
        # Get or create Budget worksheet
        try:
            ws = sheet.worksheet("Budget")
        except:
            print("⚠️ Budget worksheet doesn't exist yet")
            return {}
        
        # Get all values from worksheet
        all_values = get_all_values_safe(ws)
        
        # Check if we have data
        if len(all_values) < 2:
            print("📋 No budget data found")
            return {}
        
        # Get row 2 (data row)
        row_data = all_values[1]
        
        # Convert to dictionary
        budgets = {}
        for i, header in enumerate(BUDGET_HEADERS):
            if i < len(row_data):
                budgets[header] = safe_float(row_data[i])
            else:
                budgets[header] = 0.0
        
        print(f"✅ Budgets loaded")
        return budgets
            
    except Exception as e:
        print(f"❌ Error loading budgets: {str(e)}")
        return {}


def save_budgets_to_gsheet(budgets):
    """Save budgets to Google Sheets - SIMPLIFIED"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            print("❌ No Google Sheets client")
            return False
        
        # Get or create Budget worksheet
        try:
            ws = sheet.worksheet("Budget")
            print("📝 Found existing Budget worksheet")
        except:
            print("📝 Creating new Budget worksheet...")
            ws = sheet.add_worksheet(title="Budget", rows=1000, cols=10)
        
        # Prepare data row
        data_row = [str(budgets.get(k, 0)) for k in BUDGET_HEADERS]
        
        # Clear and rebuild
        try:
            clear_worksheet_safe(ws)
            insert_row_safe(ws, BUDGET_HEADERS, 1)
            insert_row_safe(ws, data_row, 2)
            print(f"✅ Budgets saved successfully")
            return True
        except Exception as e:
            print(f"❌ Error saving: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error in save_budgets: {str(e)}")
        return False


def render_budgets_tab():
    """Render Budgets Tab"""
    st.markdown("### 🎯 Monthly Budgets by Category")
    st.info("💰 Set and track budgets for each spending category")
    # TODO: Implement budget UI with progress bars
    # TODO: Implement budget vs actual comparison
