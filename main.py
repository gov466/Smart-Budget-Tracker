# Health & Wealth Tracker - Main App Entry Point
# Modular structure for better maintainability

import streamlit as st
from config import APP_TITLE, APP_ICON, LAYOUT, MAIN_TABS
from modules import (
    render_settings_tab,
    render_debts_tab,
    render_spending_tab,
    render_wealth_tab,
    render_health_tab,
    render_fitness_tab,
    render_wellness_tab,
    render_nutrition_tracker_tab,
    render_fertility_tab,
    render_shopping_tab,
    render_budgets_tab
)
from modules.budgets import load_budgets
from modules.settings import load_settings


def initialize_session_state():
    """Initialize all session state variables"""
    if 'settings' not in st.session_state:
        st.session_state.settings = load_settings()
    
    if 'budgets' not in st.session_state:
        st.session_state.budgets = load_budgets()


def main():
    """Main app function"""
    # Page config
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout=LAYOUT,
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # App title
    st.markdown(f"# {APP_TITLE}")
    st.markdown("---")
    
    # Create tabs
    tabs = st.tabs(MAIN_TABS)
    
    # Tab mapping to functions
    tab_functions = [
        render_settings_tab,           # Tab 0: ⚙️ Setup
        render_debts_tab,              # Tab 1: 💳 Debts
        render_spending_tab,           # Tab 2: 💰 Spending
        None,                          # Tab 3: 🛒 Shopping Analytics (placeholder)
        render_wealth_tab,             # Tab 4: 📊 Wealth
        render_health_tab,             # Tab 5: 🏥 Health
        render_fitness_tab,            # Tab 6: 🏋️ Fitness Plan
        render_wellness_tab,           # Tab 7: ✅ Daily Wellness Log
        render_nutrition_tracker_tab,  # Tab 8: 🍽️ Nutrition Tracker
        render_fertility_tab,          # Tab 9: 👶 Fertility Tracker
        render_shopping_tab,           # Tab 10: 🥗 Smart Grocery
        render_budgets_tab,            # Tab 11: 🎯 Budgets
    ]
    
    # Render active tabs
    for tab, tab_func in zip(tabs, tab_functions):
        with tab:
            if tab_func:
                try:
                    tab_func()
                except Exception as e:
                    st.error(f"❌ Error loading tab: {str(e)}")
            else:
                st.info("🔨 This tab is under development")
    
    # Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Session Info")
    st.sidebar.info(f"✅ Settings loaded: {bool(st.session_state.settings)}")
    st.sidebar.info(f"✅ Budgets loaded: {bool(st.session_state.budgets)}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Utilities")
    if st.sidebar.button("🔄 Refresh All Data"):
        st.session_state.settings = load_settings()
        st.session_state.budgets = load_budgets()
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 About")
    st.sidebar.info(
        "**Health & Wealth Tracker v2.0** (Modular)\n\n"
        "- 💰 Budget & expense tracking\n"
        "- 📊 Wealth dashboard\n"
        "- 🏥 Health metrics\n"
        "- 🍽️ Nutrition tracking\n"
        "- 👶 Fertility tracking\n"
        "- 🛒 Smart shopping\n"
        "\n**Built with:** Streamlit + Google Sheets + Claude AI"
    )


if __name__ == "__main__":
    main()
