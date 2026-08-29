# Financial Module - Debts, Spending, Wealth Management

import streamlit as st
from datetime import datetime
from ..config import DEBT_HEADERS, EXPENSE_HEADERS
from ..gsheet_client import get_gsheet_client
from ..utils import safe_float


def render_debts_tab():
    """Render Debts Tab"""
    st.markdown("### Debt Tracking & Management")
    st.info("💳 Track and manage your debts - Calculate payoff timeline and interest")
    # TODO: Implement debt tracking UI
    

def render_spending_tab():
    """Render Spending Tab"""
    st.markdown("### Expense Tracking & Analytics")
    st.info("💰 Track spending by category and analyze patterns")
    # TODO: Implement spending UI
    

def render_wealth_tab():
    """Render Wealth Tab"""
    st.markdown("### Wealth Dashboard & Financial Summary")
    st.info("📊 View your financial overview and retirement savings")
    # TODO: Implement wealth dashboard
