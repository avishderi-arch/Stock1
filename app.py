"""
app.py — Swing Trading Scanner · Streamlit Web App
Run locally:   streamlit run app.py
Deploy free:   https://streamlit.io/cloud  (connect GitHub repo)
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
import json
import io
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from joblib import Parallel, delayed

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Swing Scanner Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS — dark terminal-finance aesthetic
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0a0e17;
    color: #c9d1d9;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21ff8733;
    border-radius: 12px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #21ff87, #00d4ff, transparent);
}
.main-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.1rem;
    font-weight: 700;
    color: #21ff87;
    letter-spacing: -1px;
    margin: 0;
}
.main-subtitle {
    color: #8b949e;
    font-size: 0.9rem;
    margin-top: 4px;
    font-family: 'IBM Plex Mono', monospace;
}

/* Metric cards */
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px 20px;
    text-align: center;
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: #21ff87;
}
.metric-label {
    font-size: 0.75rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
}

/* Table styling */
.stock-table { width: 100%; border-collapse: collapse; }
.stock-table th {
    background: #161b22;
    color: #8b949e;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 10px 14px;
    border-bottom: 1px solid #21ff8740;
    text-align: left;
}
.stock-table td {
    padding: 12px 14px;
    border-bottom: 1px solid #21272e;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}
.stock-table tr:hover td { background: #161b2280; }
.rank-badge {
    background: #21ff8720;
    color: #21ff87;
    border-radius: 4px;
    padding: 2px 8px;
    font-weight: 700;
    font-size: 0.8rem;
}
.ticker-text { color: #58a6ff; font-weight: 700; font-size: 1rem; }
.score-high  { color: #21ff87; font-weight: 700; }
.score-mid   { color: #f0b429; font-weight: 700; }
.score-low   { color: #ff7b72; font-weight: 700; }
.positive    { color: #21ff87; }
.negative    { color: #ff7b72; }
.neutral     { color: #8b949e; }
.pill {
    display: inline-block;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 600;
}
.pill-green { background: #21ff8720; color: #21ff87; }
.pill-red   { background: #ff7b7220; color: #ff7b72; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21272e;
}
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #21ff87, #00d4ff) !important;
    color: #0a0e17 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 28px !important;
    font-size: 1rem !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Progress / status */
.status-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #21ff87;
    border-radius: 6px;
    padding: 12px 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    margin: 8px 0;
}

/* Risk table */
.risk-table { width:100%; border-collapse:collapse; margin-top:8px; }
.risk-table th {
    background:#161b22; color:#8b949e;
    font-family:'IBM Plex Mono',monospace; font-size:0.68rem;
    text-transform:uppercase; letter-spacing:1px;
    padding:8px 12px; border-bottom:1px solid #30363d;
}
.risk-table td {
    padding:10px 12px; border-bottom:1px solid #21272e;
    font-family:'IBM Plex Mono',monospace; font-size:0.82rem;
}

/* Divider */
hr { border-color: #21272e !important; margin: 24px 0 !important; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# S&P 500 TICKER LIST  (representative 150-stock subset for speed)
# ─────────────────────────────────────────────────────────────
SP500_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","BRK-B","JPM","UNH",
    "XOM","V","LLY","AVGO","JNJ","MA","PG","HD","MRK","CVX","ABBV","COST",
    "PEP","KO","WMT","BAC","ADBE","CRM","ACN","MCD","TMO","CSCO","ABT","NKE",
    "WFC","TXN","LIN","ORCL","DHR","PM","NFLX","AMD","QCOM","MDT","HON",
    "AMGN","UPS","MS","BMY","SCHW","RTX","LOW","SPGI","CAT","GS","BLK","DE",
    "ELV","SYK","ISRG","AXP","BKNG","GILD","VRTX","CI","MO","ANET","TJX",
    "PLD","PANW","SO","DUK","AON","BDX","ZTS","CME","ITW","EOG","HUM","MCO",
    "PSX","CL","APD","GD","USB","MMC","PGR","SLB","ADP","REGN","ICE","NSC",
    "CTAS","KLAC","ADI","LRCX","MU","SNPS","CDNS","FTNT","MCHP","ON","NXPI",
    "TEL","APH","GLW","KEYS","ANSS","IDXX","ILMN","MTD","WAT","A","RMD",
    "STE","BAX","EW","HOLX","PODD","DXCM","VEEV","ALGN","FICO","PAYC","EPAM",
    "MPWR","ENPH","FSLR","CEG","VST","ETR","AEE","CMS","NI","OGE","PNW",
    "EVRG","LNT","WTRG","AWK","ECL","PPG","SHW","RPM","EMN","CF","MOS",
    "NUE","STLD","RS","CMC","ATI","HWM","TKR","CRS","ARNC",
]

SECTOR_MAP = {
    "AAPL":"Technology","MSFT":"Technology","NVDA":"Technology","AVGO":"Technology",
    "ADBE":"Technology","CRM":"Technology","ORCL":"Technology","AMD":"Technology",
    "QCOM":"Technology","TXN":"Technology","KLAC":"Technology","ADI":"Technology",
    "LRCX":"Technology","MU":"Technology","SNPS":"Technology","CDNS":"Technology",
    "FTNT":"Technology","MCHP":"Technology","ON":"Technology","NXPI":"Technology",
    "ANET":"Technology","PANW":"Technology","KEYS":"Technology","ANSS":"Technology",
    "MPWR":"Technology","EPAM":"Technology","FICO":"Technology","PAYC":"Technology",
    "AMZN":"Consumer Discretionary","TSLA":"Consumer Discretionary","HD":"Consumer Discretionary",
    "MCD":"Consumer Discretionary","NKE":"Consumer Discretionary","LOW":"Consumer Discretionary",
    "BKNG":"Consumer Discretionary","TJX":"Consumer Discretionary","ALGN":"Consumer Discretionary",
    "GOOGL":"Communication","META":"Communication","NFLX":"Communication","CSCO":"Communication",
    "JPM":"Financials","BAC":"Financials","WFC":"Financials","MS":"Financials","GS":"Financials",
    "AXP":"Financials","BLK":"Financials","SCHW":"Financials","SPGI":"Financials","CME":"Financials",
    "ICE":"Financials","AON":"Financials","MMC":"Financials","PGR":"Financials","USB":"Financials",
    "UNH":"Healthcare","JNJ":"Healthcare","LLY":"Healthcare","MRK":"Healthcare","ABBV":"Healthcare",
    "TMO":"Healthcare","ABT":"Healthcare","MDT":"Healthcare","AMGN":"Healthcare","BMY":"Healthcare",
    "GILD":"Healthcare","VRTX":"Healthcare","CI":"Healthcare","SYK":"Healthcare","ISRG":"Healthcare",
    "BDX":"Healthcare","ZTS":"Healthcare","ELV":"Healthcare","HUM":"Healthcare","REGN":"Healthcare",
    "IDXX":"Healthcare","ILMN":"Healthcare","MTD":"Healthcare","WAT":"Healthcare","A":"Healthcare",
    "RMD":"Healthcare","STE":"Healthcare","BAX":"Healthcare","EW":"Healthcare","HOLX":"Healthcare",
    "PODD":"Healthcare","DXCM":"Healthcare","VEEV":"Healthcare",
    "XOM":"Energy","CVX":"Energy","PSX":"Energy","SLB":"Energy","EOG":"Energy",
    "V":"Financials","MA":"Financials",
    "PG":"Consumer Staples","KO":"Consumer Staples","PEP":"Consumer Staples","WMT":"Consumer Staples",
    "COST":"Consumer Staples","MO":"Consumer Staples","CL":"Consumer Staples",
    "BRK-B":"Financials",
    "LIN":"Materials","APD":"Materials","ECL":"Materials","PPG":"Materials","SHW":"Materials",
    "RPM":"Materials","EMN":"Materials","CF":"Materials","MOS":"Materials","NUE":"Materials",
    "STLD":"Materials","RS":"Materials",
    "PLD":"Real Estate",
    "SO":"Utilities","DUK":"Utilities","AEE":"Utilities","CMS":"Utilities","ETR":"Utilities",
    "CEG":"Utilities","VST":"Utilities",
    "RTX":"Industrials","UPS":"Industrials","HON":"Industrials","CAT":"Industrials","DE":"Industrials",
    "GD":"Industrials","NSC":"Industrials","CTAS":"Industrials","ITW":"Industrials","ACN":"Industrials",
    "TEL":"Industrials","APH":"Industrials","GLW":"Industrials","HWM":"Industrials",
    "ENPH":"Technology","FSLR":"Technology",
}


# ─────────────────────────────────────────────────────────────
# INDICATOR FUNCTIONS
# ─────────────────────────────────────────────────────────────

def _rsi(close, period=14):
    delta = close.diff()
    gain  = delta.clip(lower=0).ewm(com=period-1, min_periods=period).mean()
    loss  = (-delta).clip(lower=0).ewm(com=period-1, min_periods=period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def _macd_hist(close, fast=12, slow=26, signal=9):
    ml = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    return ml - ml.ewm(span=signal, adjust=False).mean()

def _adx(high, low, close, period=14):
    tr   = pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    dmp  = ((high-high.shift())>(low.shift()-low)).astype(float)*(high-high.shift()).clip(lower=0)
    dmm  = ((low.shift()-low)>(high-high.shift())).astype(float)*(low.shift()-low).clip(lower=0)
    atr  = tr.ewm(com=period-1,min_periods=period).mean()
    di_p = dmp.ewm(com=period-1,min_periods=period).mean()/atr*100
    di_m = dmm.ewm(com=period-1,min_periods=period).mean()/atr*100
    dx   = ((di_p-di_m).abs()/(di_p+di_m).replace(0,np.nan))*100
    return dx.ewm(com=period-1,min_periods=period).mean()

def _obv(close, volume):
    return (np.sign(close.diff()).fillna(0)*volume).cumsum()

def _mfi(high, low, close, volume, period=14):
    tp  = (high+low+close)/3
    rmf = tp*volume
    pos = rmf.where(tp>tp.shift(),0).rolling(period).sum()
    neg = rmf.where(tp<tp.shift(),0).rolling(period).sum()
    return 100-(100/(1+pos/neg.replace(0,np.nan)))

def _atr(high, low, close, period=14):
    tr = pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(com=period-1,min_periods=period).mean()

def _slope(series):
    y = series.dropna().values
    if len(y)<2: return 0.0
    return float(np.polyfit(np.arange(len(y),dtype=float),y,1)[0])

def _sigmoid(x, centre=0, scale=1):
    if scale==0: return 50.0
    return float(1/(1+np.exp(-(x-centre)/scale))*100)

def _clamp(v,lo=0,hi=100): return float(max(lo,min(hi,v)))


# ─────────────────────────────────────────────────────────────
# SCANNER CORE
# ─────────────────────────────────────────────────────────────

def analyse_ticker(ticker, spy_close, cfg):
    try:
        raw = yf.download(ticker, period="1y", auto_adjust=True, progress=False, threads=False)
        if raw.empty or len(raw) < 60: return None
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        df = raw[["Open","High","Low","Close","Volume"]].copy()

        close  = df["Close"]; high = df["High"]; low = df["Low"]; vol = df["Volume"]
        price  = float(close.iloc[-1])
        sma50  = float(close.rolling(50).mean().iloc[-1])
        sma200 = float(close.rolling(200).mean().iloc[-1])
        avg_vol= float(vol.rolling(20).mean().iloc[-1])
        v_surge= float(vol.iloc[-1]/avg_vol) if avg_vol>0 else 0
        rsi_v  = float(_rsi(close).iloc[-1])
        mh     = _macd_hist(close); mh_val=float(mh.iloc[-1]); mh_prev=float(mh.iloc[-2])
        adx_v  = float(_adx(high,low,close).iloc[-1])
        obv_s  = _slope(_obv(close,vol).tail(20))
        mfi_v  = float(_mfi(high,low,close,vol).iloc[-1])
        atr_v  = float(_atr(high,low,close).iloc[-1])
        mom1m  = float(close.pct_change(21).iloc[-1])
        mom3m  = float(close.pct_change(63).iloc[-1])

        # Relative strength vs SPY
        aligned = spy_close.reindex(close.index, method="ffill")
        if aligned is not None and len(aligned)>=21:
            rs = float(close.pct_change(20).iloc[-1]) - float(aligned.pct_change(20).iloc[-1])
        else:
            rs = 0.01

        # ── Hard filters ─────────────────────────────────────
        if price < cfg["min_price"]:          return None
        if avg_vol < cfg["min_vol"]:          return None
        if price <= sma50:                    return None
        if sma50 <= sma200:                   return None
        if not (cfg["rsi_low"]<=rsi_v<=cfg["rsi_high"]): return None
        if mh_val <= 0:                       return None
        if mh_val <= mh_prev:                 return None
        if adx_v < cfg["min_adx"]:           return None
        if v_surge < cfg["vol_surge"]:        return None
        if obv_s <= 0:                        return None
        if mfi_v < cfg["min_mfi"]:           return None
        if rs <= 0:                           return None

        # ── Scoring ──────────────────────────────────────────
        mom_score = 0.35*_sigmoid(mom1m,.05,.10)+0.65*_sigmoid(mom3m,.12,.15)
        vol_score = 0.55*_clamp((v_surge-1.6)/(3-1.6)*100)+0.45*_sigmoid(obv_s,0,1e6)
        ma_spread = (sma50-sma200)/sma200 if sma200>0 else 0
        tr_score  = 0.60*_clamp((adx_v-23)/(60-23)*100)+0.40*_sigmoid(ma_spread,.02,.04)
        mf_score  = _clamp((mfi_v-55)/(90-55)*100)
        ra_score  = _sigmoid(mom3m/max(atr_v/price,0.005),2,3) if price>0 and atr_v>0 else 50
        rs_score  = _sigmoid(rs,.02,.05)

        composite = (
            0.30*mom_score + 0.25*vol_score + 0.20*tr_score +
            0.15*mf_score  + 0.10*ra_score  + 0.05*rs_score
        )

        # ── Setup notes ───────────────────────────────────────
        notes = []
        if mom3m>0.20:    notes.append("Strong 3M momentum")
        if v_surge>2.0:   notes.append("Heavy vol surge")
        if adx_v>35:      notes.append("Powerful trend")
        if mfi_v>65:      notes.append("Institutional accumulation")
        if rsi_v<55:      notes.append("Room to run")
        if rs>0.05:       notes.append("Outperforming SPY")
        if not notes:     notes = ["Multi-factor setup"]

        # ── Risk / position ───────────────────────────────────
        stop   = price - 2.0*atr_v
        risk_s = price - stop
        port   = cfg["portfolio"]
        max_r  = port * (cfg["risk_pct"]/100)
        shares = max(0, int(min(max_r/risk_s if risk_s>0 else 0, port*0.10/price)))
        target = price + 2.0*risk_s

        return {
            "ticker":    ticker,
            "sector":    SECTOR_MAP.get(ticker, "Other"),
            "price":     round(price,2),
            "score":     round(_clamp(composite),1),
            "mom_1m":    round(mom1m*100,1),
            "mom_3m":    round(mom3m*100,1),
            "vol_surge": round(v_surge,2),
            "rsi":       round(rsi_v,1),
            "mfi":       round(mfi_v,1),
            "adx":       round(adx_v,1),
            "obv_up":    obv_s > 0,
            "rs_spy":    round(rs*100,1),
            "setup":     "; ".join(notes[:2]),
            "stop":      round(stop,2),
            "target":    round(target,2),
            "shares":    shares,
            "risk_amt":  round(shares*risk_s,0),
            "risk_pct":  round(shares*risk_s/port*100,2) if port>0 else 0,
        }
    except Exception:
        return None


def run_scan(tickers, cfg, progress_cb=None):
    spy = yf.download("SPY", period="1y", auto_adjust=True, progress=False, threads=False)
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
    spy_close = spy["Close"]

    results = []
    total = len(tickers)
    for i, t in enumerate(tickers):
        r = analyse_ticker(t, spy_close, cfg)
        if r: results.append(r)
        if progress_cb: progress_cb((i+1)/total)

    if not results: return pd.DataFrame()

    df = pd.DataFrame(results).sort_values("score", ascending=False)

    # Sector cap
    sector_counts = {}
    selected = []
    for _, row in df.iterrows():
        sec = row["sector"]
        if sector_counts.get(sec,0) < cfg["max_per_sector"]:
            selected.append(row)
            sector_counts[sec] = sector_counts.get(sec,0)+1
        if len(selected)>=cfg["top_n"]: break

    return pd.DataFrame(selected).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────

def score_color_class(s):
    if s>=70: return "score-high"
    if s>=55: return "score-mid"
    return "score-low"

def pct_html(v):
    cls = "positive" if v>0 else "negative"
    arrow = "▲" if v>0 else "▼"
    return f'<span class="{cls}">{arrow}{abs(v):.1f}%</span>'

def render_main_table(df):
    rows_html = ""
    for i, row in df.iterrows():
        rank    = i+1
        sc_cls  = score_color_class(row["score"])
        obv_pill= '<span class="pill pill-green">↑ Rising</span>' if row["obv_up"] else '<span class="pill pill-red">↓ Falling</span>'
        rows_html += f"""
        <tr>
          <td><span class="rank-badge">#{rank}</span></td>
          <td><span class="ticker-text">{row['ticker']}</span></td>
          <td>${row['price']:.2f}</td>
          <td><span class="{sc_cls}">{row['score']}</span></td>
          <td>{pct_html(row['mom_3m'])}</td>
          <td>{row['vol_surge']:.2f}×</td>
          <td>{row['rsi']:.1f}</td>
          <td>{row['mfi']:.1f}</td>
          <td>{row['adx']:.1f}</td>
          <td>{obv_pill}</td>
          <td><span class="neutral">{row['sector'][:16]}</span></td>
          <td><span class="neutral" style="font-size:0.78rem">{row['setup'][:32]}</span></td>
        </tr>"""

    st.markdown(f"""
    <table class="stock-table">
      <thead><tr>
        <th>Rank</th><th>Ticker</th><th>Price</th><th>Score</th>
        <th>Mom 3M</th><th>Vol Surge</th><th>RSI</th><th>MFI</th>
        <th>ADX</th><th>OBV</th><th>Sector</th><th>Setup</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


def render_risk_table(df, portfolio):
    rows_html = ""
    for _, row in df.iterrows():
        rp_cls = "positive" if row["risk_pct"]<=2.0 else "negative"
        rows_html += f"""
        <tr>
          <td><span class="ticker-text">{row['ticker']}</span></td>
          <td>${row['price']:.2f}</td>
          <td><span class="negative">${row['stop']:.2f}</span></td>
          <td><span class="positive">${row['target']:.2f}</span></td>
          <td>{row['shares']:,}</td>
          <td>${row['shares']*row['price']:,.0f}</td>
          <td><span class="negative">${row['risk_amt']:,.0f}</span></td>
          <td><span class="{rp_cls}">{row['risk_pct']:.2f}%</span></td>
          <td>2.0:1</td>
        </tr>"""

    st.markdown(f"""
    <table class="risk-table">
      <thead><tr>
        <th>Ticker</th><th>Entry</th><th>Stop</th><th>Target</th>
        <th>Shares</th><th>Pos Value</th><th>$ Risk</th><th>% Risk</th><th>R:R</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    <p style="color:#8b949e;font-size:0.75rem;margin-top:8px;font-family:'IBM Plex Mono',monospace;">
    Stop = Entry − 2×ATR(14) &nbsp;|&nbsp; Target = Entry + 2×Risk &nbsp;|&nbsp; Portfolio: ${portfolio:,.0f}
    </p>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# MAIN UI
# ─────────────────────────────────────────────────────────────

def main():
    # ── Header ───────────────────────────────────────────────
    st.markdown(f"""
    <div class="main-header">
      <div class="main-title">📈 SWING SCANNER PRO</div>
      <div class="main-subtitle">
        S&P 500 · Daily Swing Trading Signals · {datetime.now().strftime('%A, %B %d %Y')}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Scanner Settings")
        st.markdown("---")

        portfolio   = st.number_input("Portfolio Size ($)", 10_000, 10_000_000, 100_000, step=10_000)
        risk_pct    = st.slider("Max Risk per Trade (%)", 0.5, 3.0, 1.75, 0.25)
        top_n       = st.slider("Top N picks", 5, 20, 10)
        max_sector  = st.slider("Max per sector", 1, 5, 3)

        st.markdown("---")
        st.markdown("**Filter Thresholds**")
        min_price   = st.number_input("Min Price ($)", 1.0, 100.0, 12.0, 1.0)
        min_vol     = st.number_input("Min Avg Volume (K)", 100, 5000, 750, 50) * 1000
        rsi_low     = st.slider("RSI min", 30, 60, 45)
        rsi_high    = st.slider("RSI max", 55, 80, 68)
        min_adx     = st.slider("Min ADX", 15, 40, 23)
        vol_surge   = st.slider("Vol Surge min (×)", 1.0, 3.0, 1.6, 0.1)
        min_mfi     = st.slider("Min MFI", 40, 75, 55)

        st.markdown("---")
        st.markdown("**Universe**")
        use_full    = st.checkbox("Full 150-stock universe", value=True)
        custom_raw  = st.text_input("Or enter tickers (comma-separated)", "")

        st.markdown("---")
        run_btn     = st.button("🔍  RUN SCAN")

    cfg = dict(
        min_price=min_price, min_vol=min_vol,
        rsi_low=rsi_low,     rsi_high=rsi_high,
        min_adx=min_adx,     vol_surge=vol_surge,
        min_mfi=min_mfi,     portfolio=portfolio,
        risk_pct=risk_pct,   top_n=top_n,
        max_per_sector=max_sector,
    )

    # ── Determine universe ────────────────────────────────────
    if custom_raw.strip():
        tickers = [t.strip().upper() for t in custom_raw.split(",") if t.strip()]
    elif use_full:
        tickers = SP500_TICKERS
    else:
        tickers = SP500_TICKERS[:50]

    # ── Initial state ─────────────────────────────────────────
    if "results" not in st.session_state:
        st.markdown("""
        <div class="status-box">
          ► Configure filters in the sidebar, then click <strong>RUN SCAN</strong> to find today's top swing trade setups.
        </div>
        """, unsafe_allow_html=True)

        c1,c2,c3,c4 = st.columns(4)
        for col,label,val in zip(
            [c1,c2,c3,c4],
            ["Universe","Filters Active","Strategy","Hold Period"],
            [f"{len(tickers)} stocks","11 gates","Momentum + Flow","5–20 days"],
        ):
            col.markdown(f"""
            <div class="metric-card">
              <div class="metric-value" style="font-size:1.4rem">{val}</div>
              <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)
        return

    # ── Run scan ──────────────────────────────────────────────
    if run_btn:
        st.markdown("---")
        prog_bar = st.progress(0, text="Fetching data from Yahoo Finance...")
        status   = st.empty()
        t0       = time.perf_counter()

        def update(p):
            prog_bar.progress(p, text=f"Analysing stocks... {int(p*100)}%")

        with st.spinner(""):
            df = run_scan(tickers, cfg, progress_cb=update)

        elapsed = time.perf_counter()-t0
        prog_bar.empty(); status.empty()

        st.session_state["results"] = df
        st.session_state["elapsed"] = elapsed
        st.session_state["scanned"] = len(tickers)
        st.session_state["cfg"]     = cfg

    # ── Display results ───────────────────────────────────────
    if "results" in st.session_state:
        df      = st.session_state["results"]
        elapsed = st.session_state.get("elapsed", 0)
        scanned = st.session_state.get("scanned", len(tickers))

        if df.empty:
            st.warning("⚠️ No stocks passed all filters today. Try relaxing thresholds in the sidebar.")
            return

        # Metric bar
        m1,m2,m3,m4,m5 = st.columns(5)
        for col,label,val,color in zip(
            [m1,m2,m3,m4,m5],
            ["Scanned","Passed","Top Picks","Avg Score","Run Time"],
            [scanned, len(df)+max(0,scanned-len(df)-scanned+len(df)),
             len(df), f"{df['score'].mean():.1f}", f"{elapsed:.0f}s"],
            ["#21ff87","#00d4ff","#f0b429","#21ff87","#8b949e"],
        ):
            col.markdown(f"""
            <div class="metric-card">
              <div class="metric-value" style="color:{color}">{val}</div>
              <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Main table
        st.markdown("#### 🏆 Top Swing Trade Candidates")
        render_main_table(df)

        st.markdown("<br>", unsafe_allow_html=True)

        # Risk table
        st.markdown("#### 🛡️ Risk Management & Position Sizing")
        render_risk_table(df, portfolio)

        # Sector breakdown
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns([1,1])

        with col_a:
            st.markdown("#### 📊 Sector Distribution")
            sec_counts = df["sector"].value_counts()
            st.bar_chart(sec_counts, color="#21ff87")

        with col_b:
            st.markdown("#### 📈 Score Distribution")
            st.bar_chart(df.set_index("ticker")["score"], color="#00d4ff")

        # Export
        st.markdown("---")
        col_dl1, col_dl2, _ = st.columns([1,1,2])

        csv_bytes = df.to_csv(index=False).encode()
        col_dl1.download_button(
            "⬇ Download CSV",
            data=csv_bytes,
            file_name=f"swing_scan_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        json_str = df.to_json(orient="records", indent=2)
        col_dl2.download_button(
            "⬇ Download JSON",
            data=json_str.encode(),
            file_name=f"swing_scan_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
        )

        # Disclaimer
        st.markdown("""
        <div style="background:#161b22;border:1px solid #ff7b7230;border-left:3px solid #ff7b72;
                    border-radius:6px;padding:14px 18px;margin-top:16px;
                    font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#8b949e;">
        ⚠️ <strong style="color:#ff7b72">RISK DISCLAIMER</strong> — For educational and research purposes only.
        Not financial advice. Never risk more than 1.5–2% of portfolio capital per trade.
        Past signals do not guarantee future results. Always use stop-losses.
        </div>
        """, unsafe_allow_html=True)

    # Run scan if button pressed
    if run_btn:
        st.rerun()


if __name__ == "__main__":
    main()
