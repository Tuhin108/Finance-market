import streamlit as st

st.set_page_config(page_title="Finance market (INR)", layout="wide")
st.title("📊 Finance market")
st.markdown(
    """
    Welcome:
    - ₿ **Crypto (INR)** — Top cryptocurrencies priced in INR from CoinGecko

    This page shows interactive charts (candlestick or line), technical indicators and a short automated analysis.
    Use the left sidebar to navigate pages and set intervals/refresh.
    """
)
st.markdown("---")
st.markdown("Run `streamlit run Home.py` to open the app. Adjust refresh intervals on each page (default 5s).")
