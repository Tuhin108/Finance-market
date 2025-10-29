import streamlit as st

st.set_page_config(page_title="Finance Analyzer (INR)", layout="wide")
st.title("📊 Finance Analyzer (INR)")
st.markdown(
    """
    Welcome — this app has three pages:
    - 🥇 **Gold (INR)** — Gold price converted to INR (USD→INR * Gold USD)
    - 💱 **Forex (INR)** — Major forex vs INR (USDINR, EURINR, GBPINR, JPYINR, AUDINR)
    - ₿ **Crypto (INR)** — Top cryptocurrencies priced in INR from CoinGecko

    Each page shows interactive charts (candlestick or line), technical indicators (SMA/EMA/RSI/Bollinger) and a short automated analysis.
    Use the left sidebar to navigate pages and set intervals/refresh.
    """
)
st.markdown("---")
st.markdown("Run `streamlit run Home.py` to open the app. Adjust refresh intervals on each page (default 5s).")
