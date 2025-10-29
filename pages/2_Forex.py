import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from plotly.subplots import make_subplots
import plotly.graph_objs as go

st.set_page_config(page_title="Forex INR Analyzer", layout="wide")
st.title("💱 Forex (INR) Analyzer")

# ----- Controls -----
pairs = ["USDINR=X", "EURINR=X", "GBPINR=X", "JPYINR=X", "AUDINR=X"]
pair = st.sidebar.selectbox("Select pair", pairs, index=0)
period = st.sidebar.selectbox("History (period)", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=5)
refresh = st.sidebar.slider("Auto-refresh (seconds)", 1, 60, 5)

@st.cache_data(ttl=20)
def fetch_yf(symbol, period, interval):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period=period, interval=interval)
        df = df.dropna()
        return df
    except Exception:
        return pd.DataFrame()

def compute_indicators(df):
    res = df.copy()
    res["SMA50"] = res["Close"].rolling(50, min_periods=1).mean()
    res["SMA200"] = res["Close"].rolling(200, min_periods=1).mean()
    res["EMA20"] = res["Close"].ewm(span=20, adjust=False).mean()
    # RSI
    delta = res["Close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/14, min_periods=14).mean()
    ma_down = down.ewm(alpha=1/14, min_periods=14).mean()
    rs = ma_up / ma_down
    res["RSI"] = 100 - (100 / (1 + rs))
    # Bollinger
    res["BB_ma"] = res["Close"].rolling(20).mean()
    res["BB_std"] = res["Close"].rolling(20).std()
    res["BB_upper"] = res["BB_ma"] + 2 * res["BB_std"]
    res["BB_lower"] = res["BB_ma"] - 2 * res["BB_std"]
    return res

def analyze_basic(df):
    if df is None or df.empty:
        return "No data to analyze."
    last = df.iloc[-1]
    notes = []
    if "SMA50" in df.columns and "SMA200" in df.columns:
        notes.append("Bullish" if last["SMA50"] > last["SMA200"] else "Bearish")
    if "RSI" in df.columns and not np.isnan(last["RSI"]):
        r = last["RSI"]
        if r > 70:
            notes.append(f"RSI {r:.1f} Overbought")
        elif r < 30:
            notes.append(f"RSI {r:.1f} Oversold")
        else:
            notes.append(f"RSI {r:.1f} Neutral")
    return " | ".join(notes)

# ----- Fetch & show -----
with st.spinner("Fetching forex data…"):
    df = fetch_yf(pair, period, interval)

if df.empty:
    st.error("No data received. Try a different interval or period.")
else:
    df = compute_indicators(df)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05, row_heights=[0.7, 0.25],
                        specs=[[{"type": "candlestick"}], [{"type": "scatter"}]])
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=pair), row=1, col=1)
    if "SMA50" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA50"), row=1, col=1)
    if "SMA200" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="SMA200"), row=1, col=1)
    if "BB_upper" in df.columns and "BB_lower" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], name="BB upper", opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], name="BB lower", opacity=0.6, fill='tonexty'), row=1, col=1)

    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI (14)"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", row=2, col=1)  # type: ignore
        fig.add_hline(y=30, line_dash="dash", row=2, col=1)  # type: ignore

    fig.update_layout(height=800, xaxis_rangeslider_visible=False, title_text=f"{pair} (INR) with indicators")
    st.plotly_chart(fig, use_container_width=True)

    # quick metrics and analysis
    last = df.iloc[-1]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Latest", f"{last['Close']:.4f}")
    with col2:
        if "SMA50" in df.columns:
            st.metric("SMA50", f"{last['SMA50']:.4f}")
    with col3:
        if "SMA200" in df.columns:
            st.metric("SMA200", f"{last['SMA200']:.4f}")

    st.subheader("Automated analysis")
    st.info(analyze_basic(df))

st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
time.sleep(refresh)
st.rerun()
