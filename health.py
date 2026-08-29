# Health Module - Health Reports, Fitness Plans

import streamlit as st
from ..config import HEALTH_HEADERS
from ..gsheet_client import get_gsheet_client


def render_health_tab():
    """Render Health Tab"""
    st.markdown("### 🏥 Health Metrics & Reports")
    st.info("📋 Upload blood work reports and track health metrics")
    # TODO: Implement health tracking UI


def render_fitness_tab():
    """Render Fitness Plan Tab"""
    st.markdown("### 🏋️ Personalized Fitness Plan")
    st.info("💪 Get exercise recommendations based on your health metrics")
    # TODO: Implement fitness plan recommendations
