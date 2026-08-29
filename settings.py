# Settings Module - Income, Fixed Expenses, Annual Costs

import streamlit as st
from datetime import datetime
from ..config import SETTINGS_HEADERS
from ..gsheet_client import get_gsheet_client, get_all_values_safe, clear_worksheet_safe, insert_row_safe
from ..utils import safe_float


def load_settings():
    """Load settings from Google Sheets - SIMPLIFIED"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            print("❌ No Google Sheets client")
            return {}
        
        # Get or create Settings worksheet
        try:
            ws = sheet.worksheet("Settings")
        except:
            print("⚠️ Settings worksheet doesn't exist yet")
            return {}
        
        # Get all values from worksheet
        all_values = get_all_values_safe(ws)
        
        # Check if we have data
        if len(all_values) < 2:
            print("📋 No settings data found (need headers + data row)")
            return {}
        
        # Get row 2 (data row)
        row_data = all_values[1]
        
        # Convert to dictionary
        settings = {}
        for i, header in enumerate(SETTINGS_HEADERS):
            if i < len(row_data):
                settings[header] = row_data[i]
            else:
                settings[header] = ''
        
        print(f"✅ Settings loaded")
        return settings
            
    except Exception as e:
        print(f"❌ Error loading settings: {str(e)}")
        return {}


def save_settings_to_gsheet(settings):
    """Save settings to Google Sheets - SIMPLIFIED"""
    try:
        sheet = get_gsheet_client()
        if not sheet:
            print("❌ No Google Sheets client")
            return False
        
        # Get or create Settings worksheet
        try:
            ws = sheet.worksheet("Settings")
            print("📝 Found existing Settings worksheet")
        except:
            print("📝 Creating new Settings worksheet...")
            ws = sheet.add_worksheet(title="Settings", rows=1000, cols=25)
        
        # Prepare data row
        data_row = [str(settings.get(k, '')) for k in SETTINGS_HEADERS]
        
        # Clear and rebuild
        try:
            clear_worksheet_safe(ws)
            insert_row_safe(ws, SETTINGS_HEADERS, 1)
            insert_row_safe(ws, data_row, 2)
            print(f"✅ Settings saved successfully")
            return True
        except Exception as e:
            print(f"❌ Error saving: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error in save_settings: {str(e)}")
        return False


def render_settings_tab():
    """Render Setup Tab - Income & Fixed Expenses"""
    st.markdown("### Monthly Income & Fixed Expenses Setup")
    
    # Add refresh button at top
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Data", key="refresh_settings_btn"):
            st.session_state.settings = load_settings()
            st.rerun()
    
    st.markdown("---")
    
    # Monthly Income
    st.markdown("#### 💵 Monthly Income")
    col1, col2 = st.columns(2)
    with col1:
        your_sal = st.number_input(
            "Your Salary (CAD)", 
            min_value=0.0, 
            value=safe_float(st.session_state.settings.get('your_salary', 0)), 
            step=100.0
        )
    with col2:
        wife_sal = st.number_input(
            "Wife's Salary (CAD)", 
            min_value=0.0, 
            value=safe_float(st.session_state.settings.get('wife_salary', 0)), 
            step=100.0
        )
    
    # Fixed Monthly Expenses
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
        fixed_values[key] = st.number_input(
            label, 
            min_value=0.0, 
            value=safe_float(st.session_state.settings.get(key, 0)), 
            step=50.0
        )
    
    # Retirement Savings Start Date
    st.markdown("#### 💾 Retirement Savings Start Date")
    st.info("📅 When did you start contributing to TFSA & RRSP? This helps us calculate your cumulative retirement savings correctly.")
    
    tfsa_rrsp_start_str = st.session_state.settings.get('tfsa_rrsp_start_date', '')
    if tfsa_rrsp_start_str:
        try:
            tfsa_rrsp_start = datetime.strptime(tfsa_rrsp_start_str, '%Y-%m-%d').date()
        except:
            tfsa_rrsp_start = datetime(2024, 9, 1).date()
    else:
        tfsa_rrsp_start = datetime(2024, 9, 1).date()
    
    tfsa_rrsp_start_date = st.date_input(
        "TFSA & RRSP Start Date", 
        value=tfsa_rrsp_start, 
        key="tfsa_rrsp_start_date_input"
    )
    
    # Annual Expenses
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
        annual_amount = st.number_input(
            f"{label} (yearly CAD)", 
            min_value=0.0, 
            value=safe_float(st.session_state.settings.get(key, 0)), 
            step=10.0
        )
        annual_values[key] = annual_amount
        monthly_equivalent += annual_amount / 12
    
    st.markdown(f"**Annual Total: ${sum(annual_values.values()):.2f}** → **Monthly Equivalent: ${monthly_equivalent:.2f}**")
    
    # Save button
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
                    st.info(f"📊 Your annual expenses (${sum(annual_values.values()):.2f}/year) add ${monthly_equivalent:.2f}/month to your budget")
                else:
                    st.error("❌ Error saving - Settings NOT updated to prevent data loss")
