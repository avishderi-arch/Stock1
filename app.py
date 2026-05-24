"""
app.py — Swing Trading Scanner · Mobile-Friendly Version
כפתור RUN SCAN נמצא במסך הראשי — עובד מהטלפון!
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime

st.set_page_config(
    page_title="Swing Scanner Pro",
    page_icon="📈",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');
body { background: #0a0e17; color: #c9d1d9; font-family: 'IBM Plex Mono', monospace; }
.main-title { color: #21ff87; font-size: 2rem; font-weight: 700; text-align: center; margin-bottom: 4px; }
.sub-title  { color: #8b949e; font-size: 0.85rem; text-align: center; margin-bottom: 20px; }
.stButton > button {
    background: linear-gradient(135deg, #21ff87, #00d4ff) !important;
    color: #0a0e17 !important; font-weight: 700 !important;
    font-size: 1.2rem !important; border: none !important;
    border-radius: 10px !important; padding: 16px !important;
    width: 100% !important; margin: 12px 0 !important;
}
.result-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 16px; margin: 10px 0;
}
.ticker { color: #58a6ff; font-size: 1.3rem; font-weight: 700; }
.score-high { color: #21ff87; font-size: 1.1rem; font-weight: 700; }
.score-mid  { color: #f0b429; font-size: 1.1rem; font-weight: 700; }
.row-item { color: #8b949e; font-size: 0.8rem; margin: 4px 0; }
.row-val  { color: #c9d1d9; font-weight: 600; }
.positive { color: #21ff87; }
.negative { color: #ff7b72; }
.disclaimer {
    background: #161b22; border-left: 3px solid #ff7b72;
    border-radius: 6px; padding: 12px; margin-top: 20px;
    font-size: 0.75rem; color: #8b949e;
}
hr { border-color: #21272e !important; }
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Universe ──────────────────────────────────────────────────
SP500 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","JPM","UNH","XOM",
    "V","LLY","AVGO","JNJ","MA","PG","HD","MRK","CVX","ABBV","COST","PEP",
    "KO","WMT","BAC","ADBE","CRM","ACN","MCD","TMO","CSCO","ABT","NKE",
    "WFC","TXN","LIN","ORCL","DHR","NFLX","AMD","QCOM","HON","AMGN","UPS",
    "MS","BMY","SCHW","RTX","LOW","SPGI","CAT","GS","BLK","DE","SYK","ISRG",
    "AXP","BKNG","GILD","VRTX","CI","ANET","TJX","PLD","PANW","BDX","ZTS",
    "CME","ITW","EOG","MCO","CL","APD","GD","USB","MMC","PGR","SLB","ADP",
    "REGN","ICE","NSC","CTAS","KLAC","ADI","LRCX","MU","SNPS","CDNS","FTNT",
]

SECTORS = {
    "AAPL":"Tech","MSFT":"Tech","NVDA":"Tech","AVGO":"Tech","ADBE":"Tech",
    "CRM":"Tech","ORCL":"Tech","AMD":"Tech","QCOM":"Tech","TXN":"Tech",
    "KLAC":"Tech","ADI":"Tech","LRCX":"Tech","MU":"Tech","SNPS":"Tech",
    "CDNS":"Tech","FTNT":"Tech","ANET":"Tech","PANW":"Tech",
    "AMZN":"Cons.Disc","TSLA":"Cons.Disc","HD":"Cons.Disc","MCD":"Cons.Disc",
    "NKE":"Cons.Disc","LOW":"Cons.Disc","BKNG":"Cons.Disc","TJX":"Cons.Disc",
    "GOOGL":"Comm","META":"Comm","NFLX":"Comm","CSCO":"Comm",
    "JPM":"Finance","BAC":"Finance","WFC":"Finance","MS":"Finance",
    "GS":"Finance","AXP":"Finance","BLK":"Finance","SCHW":"Finance",
    "SPGI":"Finance","CME":"Finance","ICE":"Finance","MMC":"Finance","PGR":"Finance",
    "UNH":"Health","JNJ":"Health","LLY":"Health","MRK":"Health","ABBV":"Health",
    "TMO":"Health","ABT":"Health","AMGN":"Health","BMY":"Health","GILD":"Health",
    "VRTX":"Health","CI":"Health","SYK":"Health","ISRG":"Health","BDX":"Health","REGN":"Health",
    "XOM":"Energy","CVX":"Energy","EOG":"Energy","SLB":"Energy",
    "V":"Finance","MA":"Finance","USB":"Finance","MCO":"Finance","AON":"Finance",
    "PG":"Staples","KO":"Staples","PEP":"Staples","WMT":"Staples","COST":"Staples","CL":"Staples",
    "LIN":"Materials","APD":"Materials",
    "PLD":"Real Est",
    "RTX":"Industrl","UPS":"Industrl","HON":"Industrl","CAT":"Industrl",
    "DE":"Industrl","GD":"Industrl","NSC":"Industrl","CTAS":"Industrl",
    "ITW":"Industrl","ACN":"Industrl",
}

# ── Indicators ────────────────────────────────────────────────
def rsi(c,p=14):
    d=c.diff(); g=d.clip(lower=0).ewm(com=p-1,min_periods=p).mean()
    l=(-d).clip(lower=0).ewm(com=p-1,min_periods=p).mean()
    return 100-(100/(1+g/l.replace(0,np.nan)))

def macd_hist(c):
    ml=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean()
    return ml-ml.ewm(span=9,adjust=False).mean()

def adx(h,l,c,p=14):
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    dp=((h-h.shift())>(l.shift()-l)).astype(float)*(h-h.shift()).clip(lower=0)
    dm=((l.shift()-l)>(h-h.shift())).astype(float)*(l.shift()-l).clip(lower=0)
    a=tr.ewm(com=p-1,min_periods=p).mean()
    dip=dp.ewm(com=p-1,min_periods=p).mean()/a*100
    dim=dm.ewm(com=p-1,min_periods=p).mean()/a*100
    dx=((dip-dim).abs()/(dip+dim).replace(0,np.nan))*100
    return dx.ewm(com=p-1,min_periods=p).mean()

def mfi(h,l,c,v,p=14):
    tp=(h+l+c)/3; rmf=tp*v
    pos=rmf.where(tp>tp.shift(),0).rolling(p).sum()
    neg=rmf.where(tp<tp.shift(),0).rolling(p).sum()
    return 100-(100/(1+pos/neg.replace(0,np.nan)))

def atr(h,l,c,p=14):
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(com=p-1,min_periods=p).mean()

def slope(s):
    y=s.dropna().values
    if len(y)<2: return 0.0
    return float(np.polyfit(np.arange(len(y),dtype=float),y,1)[0])

def sig(x,c=0,s=1):
    if s==0: return 50.0
    return float(1/(1+np.exp(-(x-c)/s))*100)

def clamp(v,lo=0,hi=100): return float(max(lo,min(hi,v)))

# ── Analyse one ticker ────────────────────────────────────────
def analyse(ticker, spy_close):
    try:
        raw=yf.download(ticker,period="1y",auto_adjust=True,progress=False,threads=False)
        if raw.empty or len(raw)<60: return None
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        c=raw["Close"]; h=raw["High"]; l=raw["Low"]; v=raw["Volume"]
        price=float(c.iloc[-1]); avg_vol=float(v.rolling(20).mean().iloc[-1])
        vs=float(v.iloc[-1]/avg_vol) if avg_vol>0 else 0
        sma50=float(c.rolling(50).mean().iloc[-1]); sma200=float(c.rolling(200).mean().iloc[-1])
        rsi_v=float(rsi(c).iloc[-1]); mh=macd_hist(c)
        mh_v=float(mh.iloc[-1]); mh_p=float(mh.iloc[-2])
        adx_v=float(adx(h,l,c).iloc[-1])
        obv=(np.sign(c.diff()).fillna(0)*v).cumsum(); obv_s=slope(obv.tail(20))
        mfi_v=float(mfi(h,l,c,v).iloc[-1]); atr_v=float(atr(h,l,c).iloc[-1])
        m1=float(c.pct_change(21).iloc[-1]); m3=float(c.pct_change(63).iloc[-1])
        al=spy_close.reindex(c.index,method="ffill")
        rs=float(c.pct_change(20).iloc[-1])-float(al.pct_change(20).iloc[-1]) if al is not None and len(al)>=21 else 0.01

        if price<12: return None
        if avg_vol<750000: return None
        if price<=sma50: return None
        if sma50<=sma200: return None
        if not(45<=rsi_v<=68): return None
        if mh_v<=0 or mh_v<=mh_p: return None
        if adx_v<23: return None
        if vs<1.6: return None
        if obv_s<=0: return None
        if mfi_v<55: return None
        if rs<=0: return None

        ms=0.35*sig(m1,.05,.10)+0.65*sig(m3,.12,.15)
        vs2=0.55*clamp((vs-1.6)/(3-1.6)*100)+0.45*sig(obv_s,0,1e6)
        ma=(sma50-sma200)/sma200 if sma200>0 else 0
        ts=0.60*clamp((adx_v-23)/(60-23)*100)+0.40*sig(ma,.02,.04)
        mfs=clamp((mfi_v-55)/(90-55)*100)
        ras=sig(m3/max(atr_v/price,0.005),2,3) if price>0 and atr_v>0 else 50
        rss=sig(rs,.02,.05)
        comp=clamp(0.30*ms+0.25*vs2+0.20*ts+0.15*mfs+0.10*ras+0.05*rss)

        notes=[]
        if m3>0.20: notes.append("Strong 3M momentum")
        if vs>2.0:  notes.append("Heavy vol surge")
        if adx_v>35:notes.append("Powerful trend")
        if mfi_v>65:notes.append("Institutional buying")
        if rsi_v<55:notes.append("Room to run")
        if rs>0.05: notes.append("Outperforming SPY")
        if not notes: notes=["Multi-factor setup"]

        stop=price-2.0*atr_v; rs_=price-stop
        shares=max(0,int(min(100000*(1.75/100)/rs_ if rs_>0 else 0,100000*0.10/price)))
        target=price+2.0*rs_

        return {
            "ticker":ticker,"sector":SECTORS.get(ticker,"Other"),
            "price":round(price,2),"score":round(comp,1),
            "m1":round(m1*100,1),"m3":round(m3*100,1),
            "vs":round(vs,2),"rsi":round(rsi_v,1),
            "mfi":round(mfi_v,1),"adx":round(adx_v,1),
            "obv_up":obv_s>0,"rs":round(rs*100,1),
            "setup":"; ".join(notes[:2]),
            "stop":round(stop,2),"target":round(target,2),
            "shares":shares,"risk":round(shares*rs_,0),
        }
    except: return None

# ── Scan ──────────────────────────────────────────────────────
def run_scan(tickers, top_n):
    spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
    if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
    spy_c=spy["Close"]

    prog=st.progress(0,text="מוריד נתונים...")
    results=[]
    for i,t in enumerate(tickers):
        r=analyse(t,spy_c)
        if r: results.append(r)
        prog.progress((i+1)/len(tickers),text=f"סורק {t}... ({i+1}/{len(tickers)})")

    prog.empty()
    if not results: return pd.DataFrame()

    df=pd.DataFrame(results).sort_values("score",ascending=False)
    sec_c={}; sel=[]
    for _,row in df.iterrows():
        s=row["sector"]
        if sec_c.get(s,0)<3:
            sel.append(row); sec_c[s]=sec_c.get(s,0)+1
        if len(sel)>=top_n: break
    return pd.DataFrame(sel).reset_index(drop=True)

# ── UI ────────────────────────────────────────────────────────
def main():
    st.markdown(f'<div class="main-title">📈 SWING SCANNER PRO</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">S&P 500 · {datetime.now().strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
    st.markdown("---")

    top_n = st.slider("כמה מניות להציג?", 5, 20, 10)

    if st.button("🔍  RUN SCAN — סרוק עכשיו"):
        df = run_scan(SP500, top_n)

        if df.empty:
            st.warning("לא נמצאו מניות שעוברות את כל הפילטרים היום.")
            return

        st.success(f"✅ נמצאו {len(df)} מניות מובילות!")
        st.markdown("---")

        for i, row in df.iterrows():
            sc_cls = "score-high" if row["score"]>=70 else "score-mid"
            m3_cls = "positive" if row["m3"]>0 else "negative"
            m3_arrow = "▲" if row["m3"]>0 else "▼"
            obv_txt = "↑ עולה" if row["obv_up"] else "↓ יורד"

            st.markdown(f"""
            <div class="result-card">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span class="ticker">#{i+1} {row['ticker']}</span>
                <span class="{sc_cls}">⭐ {row['score']}</span>
              </div>
              <div class="row-item">💰 מחיר: <span class="row-val">${row['price']}</span> &nbsp;|&nbsp; 🏢 <span class="row-val">{row['sector']}</span></div>
              <div class="row-item">📈 מומנטום 3M: <span class="{m3_cls}">{m3_arrow}{abs(row['m3'])}%</span> &nbsp;|&nbsp; Vol: <span class="row-val">{row['vs']}x</span></div>
              <div class="row-item">RSI: <span class="row-val">{row['rsi']}</span> &nbsp;|&nbsp; MFI: <span class="row-val">{row['mfi']}</span> &nbsp;|&nbsp; ADX: <span class="row-val">{row['adx']}</span></div>
              <div class="row-item">OBV: <span class="row-val">{obv_txt}</span> &nbsp;|&nbsp; vs SPY: <span class="row-val">+{row['rs']}%</span></div>
              <div class="row-item">🛡️ כניסה: <span class="row-val">${row['price']}</span> | סטופ: <span class="negative">${row['stop']}</span> | יעד: <span class="positive">${row['target']}</span></div>
              <div class="row-item">📝 {row['setup']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ הורד תוצאות CSV", data=csv,
            file_name=f"scan_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

        st.markdown("""
        <div class="disclaimer">
        ⚠️ <strong>אזהרת סיכון</strong> — למטרות לימוד בלבד. אין המלצת השקעה.
        לעולם אל תסכן יותר מ-1.5-2% מההון שלך בעסקה אחת.
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
