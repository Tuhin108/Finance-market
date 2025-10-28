import streamlit as st
from pycoingecko import CoinGeckoAPI
import pandas as pd
import numpy as np
import time
from datetime import datetime
from plotly.subplots import make_subplots
import plotly.graph_objs as go

st.set_page_config(page_title="Crypto INR Analyzer", layout="wide")
st.title("₿ Crypto (INR) Analyzer")

cg = CoinGeckoAPI()

# ----- Controls -----
top_n = st.sidebar.slider("Top N coins (to list)", 5, 50, 20)
days = st.sidebar.slider("History (days)", 1, 180, 30)
refresh = st.sidebar.slider("Auto-refresh (seconds)", 1, 60, 5)

# fetch top coins (INR)
@st.cache_data(ttl=60)
def fetch_top_coins(vs_currency="inr", per_page=50, page=1):
    try:
        coins = cg.get_coins_markets(vs_currency=vs_currency, order="market_cap_desc", per_page=per_page, page=page)
        return coins
    except Exception:
        return []

coins = fetch_top_coins(vs_currency="inr", per_page=top_n)
if not coins:
    st.error("CoinGecko fetch failed. Check connection.")
    st.stop()

coin_options = [c["id"] for c in coins]
coin = st.sidebar.selectbox("Select coin", coin_options, index=0)

# get price series from CoinGecko and convert to OHLC by resampling
@st.cache_data(ttl=30)
def cg_price_to_ohlc(coin_id, vs_currency="inr", days=30):
    chart = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs_currency, days=days)
    prices = pd.DataFrame(chart.get("prices", []), columns=["ts", "price"])
    if prices.empty:
        return pd.DataFrame()
    prices["ts"] = pd.to_datetime(prices["ts"], unit="ms")
    prices = prices.set_index("ts")
    # choose resample freq based on days
    if days <= 1:
        freq = "5min"
    elif days <= 7:
        freq = "15min"
    elif days <= 30:
        freq = "1h"
    elif days <= 90:
        freq = "4h"
    else:
        freq = "1d"
    ohlc = prices["price"].resample(freq).ohlc().ffill().dropna()
    return ohlc

def compute_indicators(df):
    res = df.copy()
    res["SMA50"] = res["close"].rolling(50, min_periods=1).mean()
    res["SMA200"] = res["close"].rolling(200, min_periods=1).mean()
    res["EMA20"] = res["close"].ewm(span=20, adjust=False).mean()
    delta = res["close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/14, min_periods=14).mean()
    ma_down = down.ewm(alpha=1/14, min_periods=14).mean()
    rs = ma_up / ma_down
    res["RSI"] = 100 - (100 / (1 + rs))
    res["BB_ma"] = res["close"].rolling(20).mean()
    res["BB_std"] = res["close"].rolling(20).std()
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

# ----- Fetch OHLC -----
with st.spinner("Fetching coin data from CoinGecko…"):
    ohlc = cg_price_to_ohlc(coin, vs_currency="inr", days=days)

if ohlc.empty:
    st.error("No OHLC data available for this coin/timeframe.")
else:
    df = compute_indicators(ohlc)

    # build plot
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05, row_heights=[0.7, 0.25],
                        specs=[[{"type": "candlestick"}], [{"type": "scatter"}]])
    fig.add_trace(go.Candlestick(x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"], name=coin.upper() if coin else "Unknown"), row=1, col=1)
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

    fig.update_layout(height=800, xaxis_rangeslider_visible=False, title_text=f"{coin.upper() if coin else 'Unknown'} (INR) with indicators")
    st.plotly_chart(fig, use_container_width=True)

    last = df.iloc[-1]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Price (INR)", f"{last['close']:.2f}")
    with col2:
        if "SMA50" in df.columns:
            st.metric("SMA50", f"{last['SMA50']:.2f}")
    with col3:
        if "RSI" in df.columns:
            st.metric("RSI(14)", f"{last['RSI']:.2f}")

    st.subheader("Automated analysis")
    st.info(analyze_basic(df))

st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
time.sleep(refresh)
st.rerun()
