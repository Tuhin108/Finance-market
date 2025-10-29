import streamlit as st

st.set_page_config(page_title="Finance Market (INR)", layout="wide")
st.title("📊 Finance Market (INR)")
st.markdown(
    """
    This app alone can help you to decide your Trade. Use the Customization options, decide wisely and make your see your money grow 💹
    Welcome — this app has three pages:
    - 🥇 **Gold (INR)** — Gold price converted to INR (USD→INR * Gold USD)
    - 💱 **Forex (INR)** — Major forex vs INR (USDINR, EURINR, GBPINR, JPYINR, AUDINR)
    - ₿ **Crypto (INR)** — Top cryptocurrencies priced in INR from CoinGecko

    Each page shows interactive charts (candlestick or line), technical indicators (SMA/EMA/RSI/Bollinger) and a short automated analysis.
    Use the left sidebar to navigate pages and set intervals/refresh.
    """
)
st.markdown("---")
st.markdown("Try out the Customisation Options that are available in the Sidebar.")
st.markdown("Run `streamlit run Home.py` to open the app. Adjust refresh intervals on each page (default 5s).")
st.markdown("Made by Tuhin with ❤️.")

