"""
Swing Scanner Pro v8.5 — Full Enhanced Edition with Backtesting & Alerts
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Swing Scanner Pro v8.5", page_icon="📈", layout="wide")

# CSS
st.markdown("""
<style>
.main-title { color:#21ff87; font-size:2.3rem; font-weight:700; text-align:center; margin-bottom:5px; }
.sub-title { color:#8b949e; text-align:center; font-size:0.95rem; }
.stButton button { background:linear-gradient(135deg,#21ff87,#00d4ff); color:#0a0e17; font-weight:700; border-radius:10px; padding:12px; }
.result-card { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:18px; margin:10px 0; }
.strong { border-left:6px solid #21ff87; }
.good { border-left:6px solid #f0b429; }
.ai-card { background:#0d1117; border-right:5px solid #21ff87; padding:20px; border-radius:10px; direction:rtl; text-align:right; line-height:1.7; }
</style>
""", unsafe_allow_html=True)

# ==================== HELPERS ====================
def safe_float(val, default=0.0):
    try:
        f = float(val)
        return f if not np.isnan(f) else default
    except: 
        return default

def rsi(c, p=14):
    d = c.diff()
    g = d.clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    l = (-d).clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    rs = g / l.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def adx(h, l, c, p=14):
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    dp = ((h - h.shift()) > (l.shift() - l)).astype(float) * (h - h.shift()).clip(lower=0)
    dm = ((l.shift() - l) > (h - h.shift())).astype(float) * (l.shift() - l).clip(lower=0)
    a = tr.ewm(com=p-1, min_periods=p).mean()
    dip = dp.ewm(com=p-1, min_periods=p).mean() / a * 100
    dim = dm.ewm(com=p-1, min_periods=p).mean() / a * 100
    dx = ((dip - dim).abs() / (dip + dim).replace(0, np.nan)) * 100
    return dx.ewm(com=p-1, min_periods=p).mean()

# ==================== CORE ANALYSIS ====================
@st.cache_data(ttl=1800)
def analyse_stock(ticker, spy_close, strict=True, sector_score=0):
    try:
        raw = yf.download(ticker, period="1y", auto_adjust=True, progress=False, threads=False)
        if raw.empty or len(raw) < 100:
            return None, "נתונים לא מספיקים"

        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        c = raw["Close"]
        h = raw["High"]
        l = raw["Low"]
        v = raw["Volume"]
        price = safe_float(c.iloc[-1])
        if price < 5: return None, "מחיר נמוך"

        ema8 = c.ewm(span=8).mean().iloc[-1]
        ema21 = c.ewm(span=21).mean().iloc[-1]
        ema50 = c.ewm(span=50).mean().iloc[-1]
        rsi_v = safe_float(rsi(c).iloc[-1])
        adx_v = safe_float(adx(h, l, c).iloc[-1])

        avg_vol = safe_float(v.rolling(20).mean().iloc[-1])
        vs = safe_float(v.iloc[-1] / avg_vol) if avg_vol > 0 else 0

        # Stochastic
        k_line = 100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
        stoch_k = safe_float(k_line.iloc[-1])

        high52 = safe_float(c.rolling(252).max().iloc[-1])
        dist_52h = (high52 - price) / high52 * 100 if high52 > 0 else 999

        # VWAP & RS
        tp = (h + l + c) / 3
        vwap_val = safe_float(((tp * v).rolling(20).sum() / v.rolling(20).sum()).iloc[-1])
        al = spy_close.reindex(c.index, method="ffill")
        rs_spy = safe_float(c.pct_change(20).iloc[-1] - al.pct_change(20).iloc[-1])

        # Weekly
        weekly = c.resample('W').last()
        above_weekly = price > weekly.rolling(20).mean().iloc[-1] if len(weekly) > 20 else True

        # Fundamentals
        try:
            info = yf.Ticker(ticker).info
            inst_own = safe_float(info.get("heldPercentInstitutions", 0)) * 100
            rec_mean = safe_float(info.get("recommendationMean", 3))
        except:
            inst_own = rec_mean = 0

        # Enhanced Scoring
        score = 0
        score += 25 if (price > ema21 > ema50 and above_weekly) else 8
        score += 22 if safe_float(c.pct_change(63).iloc[-1]) > 0.15 else 0
        score += 18 * min(max((vs - 1.7)/4, 0), 1)
        score += 15 * min(max((adx_v - 24)/45, 0), 1)
        score += 10 if (48 <= rsi_v <= 73 and stoch_k < 82) else 3
        score += 10 * min(max((rs_spy + 0.04)/0.14, 0), 1)
        score += 12 if (price > vwap_val and dist_52h < 8) else 4
        score += 8 if (inst_own > 68 and rec_mean <= 2.2) else 0
        score += sector_score * 1.4

        score = min(98, score)
        quality = "Strong" if score >= 78 else "Good" if score >= 65 else "Fair"

        if strict and quality == "Fair":
            return None, f"Quality: {quality}"

        atr = safe_float((h - l).rolling(14).mean().iloc[-1])  # simple ATR approx
        stop = round(price - 2.1 * atr, 2)
        rsk = max(price - stop, 0.01)
        target = round(price + 2.9 * rsk, 2)
        target2 = round(price + 4.7 * rsk, 2)

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "score": round(score, 1),
            "quality": quality,
            "rsi": round(rsi_v, 1),
            "adx": round(adx_v, 1),
            "vs": round(vs, 2),
            "rs": round(rs_spy * 100, 1),
            "inst_own": round(inst_own, 1),
            "dist_52h": round(dist_52h, 1),
            "stop": stop,
            "target": target,
            "target2": target2,
            "setup": "EMA + Volume + RS + Smart Money"
        }, None
    except Exception as e:
        return None, str(e)[:80]

# ==================== AI ANALYSIS ====================
def ai_deep_analysis(data, api_key):
    if not api_key:
        return "הזן מפתח API של Claude"
    prompt = f"""אתה אנליסט סווינג מקצועי. נתח את הסטאפ:

טיקר: {data['ticker']} | מחיר: ${data['price']} | ציון: {data['score']} | איכות: {data['quality']}
RSI: {data['rsi']} | ADX: {data['adx']} | Volume: {data['vs']}x | vs SPY: {data['rs']}% | מוסדיים: {data['inst_own']}% 

ענה בעברית בפורמט ברור:
## 🎯 הערכה כללית
## 📍 כניסה
## 🛑 Stop Loss + יעדים
## 🔥 קטליזטור
## ⚠️ סיכונים
## ⭐ ביטחון"""
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-3-5-sonnet-20240620", "max_tokens": 1800, "messages": [{"role": "user", "content": prompt}]},
            timeout=80
        )
        if resp.status_code == 200:
            return resp.json()["content"][0]["text"]
        return f"שגיאה {resp.status_code}"
    except Exception as e:
        return f"שגיאת חיבור: {str(e)[:100]}"

# ==================== BACKTESTING SIMPLE ====================
def simple_backtest(ticker, days_back=60):
    try:
        end = datetime.now()
        start = end - timedelta(days=days_back + 100)
        df = yf.download(ticker, start=start, end=end, progress=False)
        if len(df) < 50: return None
        entry_price = df['Close'].iloc[-days_back-1]
        current_price = df['Close'].iloc[-1]
        pnl = (current_price - entry_price) / entry_price * 100
        return {"ticker": ticker, "entry": round(entry_price,2), "current": round(current_price,2), "pnl": round(pnl,2)}
    except:
        return None

# ==================== DISPLAY ====================
def show_card(i, row):
    color = "#21ff87" if row["quality"] == "Strong" else "#f0b429"
    st.markdown(f"""
    <div class="result-card {'strong' if row['quality']=='Strong' else 'good'}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:1.3rem; font-weight:700;">#{i+1} {row['ticker']}</span>
            <span style="color:{color}; font-size:1.2rem;">⭐ {row['score']} — {row['quality']}</span>
        </div>
        <div>💰 ${row['price']} | Vol {row['vs']}x | ADX {row['adx']}</div>
        <div>RSI {row['rsi']} | vs SPY {row['rs']:+.1f}% | Inst {row.get('inst_own',0)}%</div>
        <div style="margin-top:8px;">🛡️ ${row['stop']} → 🎯 ${row['target']} | ${row['target2']}</div>
        <div style="color:#c9d6df; font-size:0.9rem; margin-top:6px;">{row['setup']}</div>
    </div>
    """, unsafe_allow_html=True)

# ==================== MAIN ====================
def main():
    st.markdown('<div class="main-title">📈 SWING SCANNER PRO v8.5</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Confluence Engine + Backtesting + Alerts</div>', unsafe_allow_html=True)
    st.markdown("---")

    mode = st.radio("בחר מצב:", ["🔍 Top-Down Scan", "🔥 High Conviction", "🎯 Single + AI", "📊 Backtesting", "🛎️ Alerts"], horizontal=True)

    spy_close = yf.download("SPY", period="1y", auto_adjust=True, progress=False, threads=False)["Close"]

    if mode == "🎯 Single + AI":
        ticker = st.text_input("טיקר", "NVDA").strip().upper()
        api_key = st.text_input("Claude API Key", type="password")
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("🚀 נתח מניה"):
                r, err = analyse_stock(ticker, spy_close, strict=False)
                if r:
                    show_card(0, r)
                    if api_key:
                        with st.spinner("Claude מנתח..."):
                            analysis = ai_deep_analysis(r, api_key)
                            st.markdown("### 🤖 ניתוח AI")
                            st.markdown(f'<div class="ai-card">{analysis.replace("\n","<br>")}</div>', unsafe_allow_html=True)
                else:
                    st.error(err)

    elif mode == "📊 Backtesting":
        st.subheader("בדיקת ביצועים היסטורית")
        tickers_input = st.text_input("טיקרים לבדיקה (מופרדים בפסיק)", "NVDA,TSLA,PLTR")
        days = st.slider("כמה ימים אחורה?", 30, 180, 60)
        if st.button("הרץ Backtest"):
            tickers = [t.strip().upper() for t in tickers_input.split(",")]
            results = []
            for t in tickers:
                bt = simple_backtest(t, days)
                if bt:
                    results.append(bt)
            if results:
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
                st.success(f"ממוצע PnL: {df['pnl'].mean():.2f}%")
            else:
                st.warning("לא נמצאו נתונים")

    elif mode == "🛎️ Alerts":
        st.subheader("הגדרת Alerts")
        st.info("בגרסה זו: שמירת setups + סימולציית Telegram")
        if "alerts" not in st.session_state:
            st.session_state.alerts = []
        
        ticker_alert = st.text_input("טיקר להתראה", "")
        if st.button("הוסף להתראות"):
            if ticker_alert:
                st.session_state.alerts.append({"ticker": ticker_alert.upper(), "date": datetime.now().strftime("%d/%m %H:%M")})
                st.success(f"{ticker_alert} נוסף להתראות")
        
        if st.session_state.alerts:
            st.write("התראות פעילות:")
            for a in st.session_state.alerts:
                st.write(f"• {a['ticker']} — {a['date']}")

    st.markdown("---")
    st.markdown("**⚠️ אזהרה:** כלי לימודי בלבד. ניהול סיכונים חשוב.")

if __name__ == "__main__":
    main()
