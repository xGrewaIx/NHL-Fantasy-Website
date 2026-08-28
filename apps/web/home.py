"""
home.py: This is the homepage of the application.
"""

# https://docs.streamlit.io/get-started
import streamlit as st

# set_page_config: Configure default settings of the page
st.set_page_config(
    page_title="NHL Fantasy Platform",
    page_icon="🏒",
    layout="wide",
)


st.title("NHL Fantasy Platform")

st.write("End-to-end NHL analytics and fantasy hockey platform.")

st.info("Development environment is running")
