# Google Sheets Client - Authentication and Operations

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


@st.cache_resource
def get_gsheet_client():
    """Connect to Google Sheets with service account"""
    try:
        # Get credentials from Streamlit secrets
        creds_dict = st.secrets.get("gsheet", {})
        
        if not creds_dict:
            print("❌ No Google Sheets credentials in secrets")
            return None
        
        # Create credentials
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        
        # Authorize and return client
        client = gspread.authorize(creds)
        print("✅ Connected to Google Sheets")
        return client
        
    except Exception as e:
        print(f"❌ Error connecting to Google Sheets: {str(e)}")
        return None


def get_or_create_worksheet(sheet, worksheet_name, headers):
    """Get existing worksheet or create new one"""
    try:
        # Try to get existing worksheet
        try:
            ws = sheet.worksheet(worksheet_name)
            print(f"📝 Found existing '{worksheet_name}' worksheet")
            return ws
        except:
            # Create new worksheet if doesn't exist
            print(f"📝 Creating new '{worksheet_name}' worksheet...")
            ws = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=len(headers))
            
            # Add headers
            try:
                ws.insert_row(headers, 1)
                print(f"✅ Created '{worksheet_name}' with headers")
            except Exception as e:
                print(f"⚠️ Error adding headers: {str(e)}")
            
            return ws
            
    except Exception as e:
        print(f"❌ Error in get_or_create_worksheet: {str(e)}")
        return None


def get_all_values_safe(ws):
    """Get all values from worksheet safely"""
    try:
        return ws.get_all_values()
    except AttributeError as e:
        print(f"⚠️ AuthorizedSession error: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ Error getting values: {str(e)}")
        return []


def append_row_safe(ws, row):
    """Append row to worksheet safely"""
    try:
        ws.append_row(row)
        return True
    except Exception as e:
        print(f"❌ Error appending row: {str(e)}")
        return False


def insert_row_safe(ws, row, index):
    """Insert row at specific index safely"""
    try:
        ws.insert_row(row, index)
        return True
    except Exception as e:
        print(f"❌ Error inserting row: {str(e)}")
        return False


def update_cell_safe(ws, row, col, value):
    """Update single cell safely"""
    try:
        ws.update_cell(row, col, value)
        return True
    except Exception as e:
        print(f"❌ Error updating cell: {str(e)}")
        return False


def delete_rows_safe(ws, start_index, num_rows):
    """Delete rows safely"""
    try:
        ws.delete_rows(start_index, num_rows)
        return True
    except Exception as e:
        print(f"❌ Error deleting rows: {str(e)}")
        return False


def clear_worksheet_safe(ws):
    """Clear worksheet safely"""
    try:
        ws.clear()
        return True
    except Exception as e:
        print(f"❌ Error clearing worksheet: {str(e)}")
        return False
