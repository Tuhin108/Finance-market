import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from plotly.subplots import make_subplots
import plotly.graph_objs as go

st.set_page_config(page_title="Gold INR Analyzer", layout="wide")
st.title("🥇 Gold (INR) Analyzer")

# ----- Controls -----
period = st.sidebar.selectbox("History (period)", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)
# interval choices that typically work with yfinance periods
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=5)
refresh = st.sidebar.slider("Auto-refresh (seconds)", 1, 60, 5)

# ----- Helper funcs -----
@st.cache_data(ttl=20)
def fetch_yf(symbol, period, interval):
    t = yf.Ticker(symbol)
    try:
        df = t.history(period=period, interval=interval)
        df = df.dropna()
        return df
    except Exception:
        return pd.DataFrame()

def compute_indicators(df):
    res = df.copy()
    res["SMA50"] = res["Close"].rolling(window=50, min_periods=1).mean()
    res["SMA200"] = res["Close"].rolling(window=200, min_periods=1).mean()
    res["EMA20"] = res["Close"].ewm(span=20, adjust=False).mean()
    # RSI
    delta = res["Close"].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
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
    # SMA cross
    if "SMA50" in df.columns and "SMA200" in df.columns:
        if last["SMA50"] > last["SMA200"]:
            notes.append("Bullish trend — 50-SMA is above 200-SMA.")
        else:
            notes.append("Bearish trend — 50-SMA is below 200-SMA.")
    # RSI
    if "RSI" in df.columns and not np.isnan(last["RSI"]):
        r = last["RSI"]
        if r > 70:
            notes.append(f"RSI = {r:.1f} → Overbought (watch for pullback).")
        elif r < 30:
            notes.append(f"RSI = {r:.1f} → Oversold (possible bounce).")
        else:
            notes.append(f"RSI = {r:.1f} → Neutral momentum.")
    # Bollinger width
    if "BB_upper" in df.columns and "BB_lower" in df.columns:
        bbw = last["BB_upper"] - last["BB_lower"]
        if last["Close"] != 0:
            rel = bbw / last["Close"]
            if rel > 0.04:
                notes.append("Bollinger bands wide → High volatility.")
            else:
                notes.append("Bollinger bands narrow → Low volatility.")
    return " ".join(notes)

# ----- Fetch data -----
with st.spinner("Fetching gold & USD→INR data…"):
    gold_usd = fetch_yf("GC=F", period, interval)        # Gold (USD)
    usd_inr = fetch_yf("USDINR=X", period, interval)     # USD to INR

if gold_usd.empty or usd_inr.empty:
    st.error("Data fetch failed or returned no data. Try a different period/interval.")
else:
    # align USD→INR to gold timestamps
    usd_series = usd_inr["Close"].reindex(gold_usd.index, method="ffill")
    # build INR OHLC
    df = pd.DataFrame(index=gold_usd.index)
    df["Open"] = gold_usd["Open"] * usd_series
    df["High"] = gold_usd["High"] * usd_series
    df["Low"] = gold_usd["Low"] * usd_series
    df["Close"] = gold_usd["Close"] * usd_series
    df = df.dropna()

    # indicators
    df = compute_indicators(df)

    # Build combined chart (candlestick + SMA + Bollinger) and RSI subplot
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=[0.7, 0.25],
                        specs=[[{"type": "candlestick"}], [{"type": "scatter"}]])

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Gold INR"
    ), row=1, col=1)

    # SMA/EMA/Bollinger
    if "SMA50" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA50", line=dict(width=1.2)), row=1, col=1)
    if "SMA200" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="SMA200", line=dict(width=1.2)), row=1, col=1)
    if "BB_upper" in df.columns and "BB_lower" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], name="BB upper", line=dict(width=1), opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], name="BB lower", line=dict(width=1), opacity=0.6, fill='tonexty'), row=1, col=1)

    # RSI subplot
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI (14)"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", row=2, col=1)  # type: ignore
        fig.add_hline(y=30, line_dash="dash", row=2, col=1)  # type: ignore

    fig.update_layout(height=800, showlegend=True, xaxis_rangeslider_visible=False,
                      title_text="Gold price (converted to INR) with indicators")
    st.plotly_chart(fig, use_container_width=True)

    # Indicators quick metrics
    col1, col2, col3 = st.columns(3)
    last = df.iloc[-1]
    with col1:
        st.metric("Price (INR)", f"{last['Close']:.2f}")
    with col2:
        if "SMA50" in df.columns:
            st.metric("SMA50", f"{last['SMA50']:.2f}")
    with col3:
        if "SMA200" in df.columns:
            st.metric("SMA200", f"{last['SMA200']:.2f}")

    # Automated insight
    st.subheader("Automated analysis")
    insight = analyze_basic(df)
    st.info(insight)

# Auto-refresh
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
time.sleep(refresh)
st.rerun()
