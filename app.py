"""
app.py — Swing Scanner Pro v3
כולל ניתוח AI מעמיק למניה בודדת
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

st.set_page_config(page_title="Swing Scanner Pro", page_icon="📈", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');
body { background: #0a0e17; color: #c9d1d9; font-family: 'IBM Plex Mono', monospace; }
.main-title { color: #21ff87; font-size: 1.9rem; font-weight: 700; text-align: center; margin-bottom: 4px; }
.sub-title  { color: #8b949e; font-size: 0.82rem; text-align: center; margin-bottom: 16px; }
.stButton > button {
    background: linear-gradient(135deg, #21ff87, #00d4ff) !important;
    color: #0a0e17 !important; font-weight: 700 !important;
    font-size: 1.1rem !important; border: none !important;
    border-radius: 10px !important; padding: 14px !important;
    width: 100% !important; margin: 10px 0 !important;
}
.result-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 14px; margin: 8px 0;
}
.ai-card {
    background: #0d1117; border: 1px solid #21ff8740;
    border-right: 4px solid #21ff87;
    border-radius: 10px; padding: 20px; margin: 8px 0;
    font-size: 0.9rem; line-height: 1.9;
    color: #e6edf3 !important;
    direction: rtl; text-align: right;
}
.ai-card h2, .ai-card h3, .ai-card strong, .ai-card b {
    color: #21ff87 !important;
}
.ai-card ul, .ai-card ol {
    padding-right: 20px; padding-left: 0;
}
.ai-card li { margin: 6px 0; color: #e6edf3; }
.ticker   { color: #58a6ff; font-size: 1.2rem; font-weight: 700; }
.score-high { color: #21ff87; font-size: 1rem; font-weight: 700; }
.score-mid  { color: #f0b429; font-size: 1rem; font-weight: 700; }
.score-low  { color: #ff7b72; font-size: 1rem; font-weight: 700; }
.row-item { color: #8b949e; font-size: 0.78rem; margin: 3px 0; }
.row-val  { color: #c9d1d9; font-weight: 600; }
.positive { color: #21ff87; }
.negative { color: #ff7b72; }
.fail-card {
    background: #1a1014; border: 1px solid #ff7b7240;
    border-radius: 8px; padding: 10px 14px; margin: 6px 0;
    font-size: 0.78rem; color: #8b949e;
}
.disclaimer {
    background: #161b22; border-left: 3px solid #ff7b72;
    border-radius: 6px; padding: 12px; margin-top: 16px;
    font-size: 0.72rem; color: #8b949e;
}
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Universe ──────────────────────────────────────────────────
# ── QQQ Top 100 (Nasdaq-100) ──────────────────────────────────
QQQ100 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","COST",
    "NFLX","TMUS","CSCO","ADBE","AMD","PEP","INTU","QCOM","AMAT","TXN",
    "ISRG","BKNG","HON","AMGN","VRTX","PANW","ADP","SBUX","GILD","MDLZ",
    "ADI","REGN","LRCX","MU","KLAC","MELI","INTC","SNPS","CDNS","CEG",
    "FTNT","CTAS","MAR","ORLY","ABNB","PYPL","WDAY","MCHP","PCAR","ROST",
    "PAYX","MNST","DXCM","ODFL","IDXX","CPRT","FAST","KDP","DLTR","EXC",
    "VRSK","BIIB","NXPI","ON","FANG","XEL","GEHC","DDOG","CRWD","ZS",
    "TEAM","ANSS","SGEN","ILMN","ALGN","SWKS","MTCH","OKTA","LCID","RIVN",
    "TTWO","WBA","ENPH","MRNA","ZM","DOCU","PTON","SIRI","FOXA","FOX",
    "CSGP","CCEP","CMCSA","PDD","ASML","AZN","BIDU","JD","WBD","EBAY",
]

SP500_FULL = [
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","ABNB",
    "AKAM","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN",
    "AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN",
    "APH","ADI","ANSS","AON","APA","APO","AAPL","AMAT","APTV","ACGL","ARW",
    "ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON",
    "BKR","BALL","BAC","BAX","BDX","BBY","BIO","TECH","BIIB","BLK","BX",
    "BK","BA","BKNG","BWA","BSX","BMY","AVGO","BR","BRO","BF-B","BLDR",
    "BRK-B","CAH","KMX","CCL","CARR","CAT","CBOE","CBRE","CDW","CE","COR",
    "CNC","CNX","CDAY","CF","CRL","SCHW","CHTR","CVX","CMG","CB","CHD",
    "CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH",
    "CL","CMCSA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CTVA",
    "CSGP","COST","CPAY","CCI","CSX","CMI","CVS","DHR","DRI","DVA","DAY",
    "DE","DELL","DAL","DVN","DXCM","FANG","DLR","DFS","DG","DLTR","D",
    "DPZ","DOV","DOW","DHI","DTE","DUK","DD","EMN","ETN","EBAY","ECL",
    "EIX","EW","EA","ELV","LLY","EMR","ENPH","ETR","EOG","EPAM","EQT",
    "EFX","EQIX","EQR","ERIE","ESS","EL","EG","EVRG","ES","EXC","EXPE",
    "EXPD","EXR","XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB",
    "FSLR","FE","FI","FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX",
    "GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM","GPC",
    "GILD","GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE",
    "HLT","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUBB","HUM","HBAN",
    "HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE","IFF",
    "IP","IPG","INTU","ISRG","IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY",
    "J","JNJ","JCI","JPM","JNPR","K","KVUE","KDP","KEY","KEYS","KMB",
    "KIM","KMI","KKR","KLAC","KHC","KR","LHX","LH","LRCX","LW","LVS",
    "LDOS","LEN","LII","LIN","LYV","LKQ","LMT","L","LOW","LULU","LYB",
    "MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC",
    "MCD","MCK","MDT","MRK","META","MET","MTD","MGM","MCHP","MU","MSFT",
    "MAA","MRNA","MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS",
    "MSI","MSCI","NDAQ","NTAP","NFLX","NEM","NEE","NKE","NI","NDSN","NSC",
    "NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY",
    "ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PANW","PARA","PH",
    "PAYX","PAYC","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PNC",
    "POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG","PTC","PSA",
    "PHM","PWR","QCOM","DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG",
    "RMD","RVTY","ROK","ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB",
    "STX","SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO",
    "LUV","SWK","SBUX","STT","STLD","STE","SYK","SMCI","SYF","SNPS","SYY",
    "TMUS","TROW","TTWO","TPR","TRGP","TGT","TEL","TDY","TFX","TER","TSLA",
    "TXN","TXT","TMO","TJX","TSCO","TT","TDG","TRV","TRMB","TFC","TYL",
    "TSN","USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI","UNH","UHS",
    "VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VTRS","VICI","V","VST",
    "VMC","WRB","GWW","WAB","WBA","WMT","DIS","WBD","WM","WAT","WEC",
    "WFC","WELL","WST","WDC","WY","WMB","WTW","WYNN","XEL","XYL","YUM",
    "ZBRA","ZBH","ZTS",
]

SECTORS = {
    "AAPL":"Tech","MSFT":"Tech","NVDA":"Tech","AVGO":"Tech","ADBE":"Tech",
    "CRM":"Tech","ORCL":"Tech","AMD":"Tech","QCOM":"Tech","TXN":"Tech",
    "KLAC":"Tech","ADI":"Tech","LRCX":"Tech","MU":"Tech","SNPS":"Tech",
    "CDNS":"Tech","FTNT":"Tech","ANET":"Tech","PANW":"Tech","INTC":"Tech",
    "CSCO":"Tech","IBM":"Tech","HPE":"Tech","HPQ":"Tech","DELL":"Tech",
    "AMZN":"Cons.Disc","TSLA":"Cons.Disc","HD":"Cons.Disc","MCD":"Cons.Disc",
    "NKE":"Cons.Disc","LOW":"Cons.Disc","BKNG":"Cons.Disc","TJX":"Cons.Disc",
    "GOOGL":"Comm","META":"Comm","NFLX":"Comm","DIS":"Comm","CMCSA":"Comm",
    "JPM":"Finance","BAC":"Finance","WFC":"Finance","MS":"Finance",
    "GS":"Finance","AXP":"Finance","BLK":"Finance","SCHW":"Finance",
    "SPGI":"Finance","CME":"Finance","ICE":"Finance","MMC":"Finance",
    "PGR":"Finance","V":"Finance","MA":"Finance","BX":"Finance",
    "UNH":"Health","JNJ":"Health","LLY":"Health","MRK":"Health","ABBV":"Health",
    "TMO":"Health","ABT":"Health","AMGN":"Health","BMY":"Health","GILD":"Health",
    "VRTX":"Health","CI":"Health","SYK":"Health","ISRG":"Health","BDX":"Health",
    "REGN":"Health","DXCM":"Health","BIIB":"Health","IDXX":"Health","IQV":"Health",
    "XOM":"Energy","CVX":"Energy","EOG":"Energy","SLB":"Energy","COP":"Energy",
    "PSX":"Energy","MPC":"Energy","VLO":"Energy","OXY":"Energy",
    "PG":"Staples","KO":"Staples","PEP":"Staples","WMT":"Staples",
    "COST":"Staples","CL":"Staples","PM":"Staples","MO":"Staples",
    "LIN":"Materials","APD":"Materials","ECL":"Materials","SHW":"Materials",
    "NEM":"Materials","FCX":"Materials","NUE":"Materials","PPG":"Materials",
    "PLD":"Real Est","AMT":"Real Est","EQIX":"Real Est","CCI":"Real Est",
    "SO":"Utilities","DUK":"Utilities","NEE":"Utilities","AEP":"Utilities",
    "RTX":"Industrl","UPS":"Industrl","HON":"Industrl","CAT":"Industrl",
    "DE":"Industrl","GD":"Industrl","NSC":"Industrl","UNP":"Industrl",
    "LMT":"Industrl","GE":"Industrl","BA":"Industrl","MMM":"Industrl",
    "BRK-B":"Finance","TMUS":"Comm","T":"Comm","VZ":"Comm",
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

# ── Analyse ───────────────────────────────────────────────────
def analyse(ticker, spy_close, strict=True):
    try:
        raw=yf.download(ticker,period="1y",auto_adjust=True,progress=False,threads=False)
        if raw.empty or len(raw)<60: return None,"insufficient_data"
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        c=raw["Close"]; h=raw["High"]; l=raw["Low"]; v=raw["Volume"]
        price=float(c.iloc[-1]); avg_vol=float(v.rolling(20).mean().iloc[-1])
        vs=float(v.iloc[-1]/avg_vol) if avg_vol>0 else 0
        sma20=float(c.rolling(20).mean().iloc[-1])
        sma50=float(c.rolling(50).mean().iloc[-1])
        sma200=float(c.rolling(200).mean().iloc[-1])
        rsi_v=float(rsi(c).iloc[-1]); mh=macd_hist(c)
        mh_v=float(mh.iloc[-1]); mh_p=float(mh.iloc[-2])
        adx_v=float(adx(h,l,c).iloc[-1])
        obv=(np.sign(c.diff()).fillna(0)*v).cumsum(); obv_s=slope(obv.tail(20))
        mfi_v=float(mfi(h,l,c,v).iloc[-1]); atr_v=float(atr(h,l,c).iloc[-1])
        m1=float(c.pct_change(21).iloc[-1]); m3=float(c.pct_change(63).iloc[-1])
        high52=float(c.rolling(252).max().iloc[-1]); low52=float(c.rolling(252).min().iloc[-1])
        al=spy_close.reindex(c.index,method="ffill")
        rs=float(c.pct_change(20).iloc[-1])-float(al.pct_change(20).iloc[-1]) if al is not None and len(al)>=21 else 0.01

        if strict:
            if price<12:           return None,"מחיר נמוך מ-$12"
            if avg_vol<750000:     return None,"נפח יומי נמוך"
            if price<=sma50:       return None,"מחיר מתחת SMA50"
            if sma50<=sma200:      return None,"SMA50 מתחת SMA200"
            if not(45<=rsi_v<=68): return None,f"RSI מחוץ לטווח ({rsi_v:.1f})"
            if mh_v<=0:            return None,"MACD שלילי"
            if mh_v<=mh_p:         return None,"MACD לא עולה"
            if adx_v<23:           return None,f"ADX חלש ({adx_v:.1f})"
            if vs<1.6:             return None,f"Volume surge נמוך ({vs:.2f}x)"
            if obv_s<=0:           return None,"OBV יורד"
            if mfi_v<55:           return None,f"MFI נמוך ({mfi_v:.1f})"
            if rs<=0:              return None,"מפגר אחרי SPY"

        ms=0.35*sig(m1,.05,.10)+0.65*sig(m3,.12,.15)
        vs2=0.55*clamp((vs-1.6)/(3-1.6)*100)+0.45*sig(obv_s,0,1e6)
        ma=(sma50-sma200)/sma200 if sma200>0 else 0
        ts=0.60*clamp((adx_v-23)/(60-23)*100)+0.40*sig(ma,.02,.04)
        mfs=clamp((mfi_v-55)/(90-55)*100)
        ras=sig(m3/max(atr_v/price,0.005),2,3) if price>0 and atr_v>0 else 50
        rss=sig(rs,.02,.05)
        comp=clamp(0.30*ms+0.25*vs2+0.20*ts+0.15*mfs+0.10*ras+0.05*rss)

        notes=[]
        if m3>0.20:  notes.append("מומנטום חזק 3M")
        if vs>2.0:   notes.append("נפח גבוה")
        if adx_v>35: notes.append("טרנד חזק")
        if mfi_v>65: notes.append("קנייה מוסדית")
        if rsi_v<55: notes.append("מקום לעלייה")
        if rs>0.05:  notes.append("מכה את SPY")
        if not notes:notes=["סטאפ רב-גורמי"]

        stop=price-2.0*atr_v; rs_=price-stop
        shares=max(0,int(min(100000*(1.75/100)/rs_ if rs_>0 else 0,100000*0.10/price)))
        target=price+2.0*rs_
        target2=price+3.5*rs_

        flags=[]
        if price<12:           flags.append("⚠️ מחיר נמוך")
        if price<=sma50:       flags.append("⚠️ מתחת SMA50")
        if sma50<=sma200:      flags.append("⚠️ מתחת SMA200")
        if not(45<=rsi_v<=68): flags.append(f"⚠️ RSI={rsi_v:.0f}")
        if adx_v<23:           flags.append("⚠️ ADX חלש")
        if vs<1.6:             flags.append("⚠️ נפח נמוך")

        return {
            "ticker":ticker,"sector":SECTORS.get(ticker,"אחר"),
            "price":round(price,2),"score":round(comp,1),
            "sma20":round(sma20,2),"sma50":round(sma50,2),"sma200":round(sma200,2),
            "m1":round(m1*100,1),"m3":round(m3*100,1),
            "vs":round(vs,2),"rsi":round(rsi_v,1),
            "mfi":round(mfi_v,1),"adx":round(adx_v,1),
            "macd_hist":round(mh_v,4),
            "obv_up":obv_s>0,"rs":round(rs*100,1),
            "atr":round(atr_v,2),"atr_pct":round(atr_v/price*100,1),
            "high52":round(high52,2),"low52":round(low52,2),
            "avg_vol":int(avg_vol),"vol_today":int(v.iloc[-1]),
            "setup":"; ".join(notes[:2]),
            "stop":round(stop,2),"target":round(target,2),"target2":round(target2,2),
            "shares":shares,"risk":round(shares*rs_,0),
            "flags":flags,
        }, None
    except Exception as e:
        return None, str(e)[:40]

# ── AI Deep Analysis ──────────────────────────────────────────
def ai_deep_analysis(data, api_key):
    prompt = f"""You are an elite institutional-level market analyst and swing-trading strategist.

Analyze this stock for a 5-10 day swing trade. Respond in Hebrew. Be specific, analytical, and actionable.

STOCK DATA:
- Ticker: {data['ticker']}
- Sector: {data['sector']}
- Price: ${data['price']}
- Composite Score: {data['score']}/100

TECHNICAL INDICATORS:
- SMA20: ${data['sma20']} | SMA50: ${data['sma50']} | SMA200: ${data['sma200']}
- RSI(14): {data['rsi']} | MFI(14): {data['mfi']} | ADX: {data['adx']}
- MACD Histogram: {data['macd_hist']} ({"positive & rising" if data['macd_hist']>0 else "negative"})
- Volume Surge: {data['vs']}x 20-day average
- OBV Trend: {"Rising - accumulation" if data['obv_up'] else "Falling - distribution"}
- ATR: ${data['atr']} ({data['atr_pct']}% of price)
- Momentum 1M: {data['m1']}% | 3M: {data['m3']}%
- Relative Strength vs SPY: {data['rs']}%
- 52W High: ${data['high52']} | 52W Low: ${data['low52']}
- Price vs 52W High: {round((data['price']/data['high52']-1)*100,1)}%

RISK PARAMETERS:
- Entry: ${data['price']}
- Stop Loss: ${data['stop']}
- Target 1: ${data['target']}
- Target 2: ${data['target2']}
- Risk per share: ${round(data['price']-data['stop'],2)}

Provide a comprehensive analysis in the following structure:

## 🌍 מצב השוק הכללי
[Analyze current market regime - bullish/bearish/neutral - and how it affects this trade]

## 📊 ניתוח טכני מעמיק
[Detailed technical analysis - trend quality, support/resistance, breakout quality, volume confirmation, MA alignment]

## 🏦 Smart Money Analysis
[Signs of institutional accumulation or distribution, OBV analysis, volume patterns, potential traps]

## ⚠️ סיכונים עיקריים
[Key risks - earnings dates, sector risks, market conditions, technical risks]

## 🎯 תוכנית מסחר
**כניסה:** [Ideal entry zone and confirmation trigger]
**סטופ:** ${data['stop']} ([explain the stop placement])
**יעד 1:** ${data['target']} (R:R 2:1)
**יעד 2:** ${data['target2']} (R:R 3.5:1)
**ניהול עסקה:** [How to manage the trade after entry]

## ⭐ ציון איכות הסטאפ: X/10
[Overall setup quality score and brief justification]

## 📋 סיכום ומסקנה
[Final recommendation - strong buy / buy / neutral / avoid - with key reasons]"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json()["content"][0]["text"]
        else:
            return f"שגיאה: {resp.status_code} — {resp.text[:200]}"
    except Exception as e:
        return f"שגיאת חיבור: {str(e)[:100]}"

# ── Result card ───────────────────────────────────────────────
def show_card(i, row, show_flags=False):
    sc_cls = "score-high" if row["score"]>=70 else "score-mid" if row["score"]>=50 else "score-low"
    m3_cls = "positive" if row["m3"]>0 else "negative"
    arrow  = "▲" if row["m3"]>0 else "▼"
    obv    = "↑ עולה" if row["obv_up"] else "↓ יורד"
    flags  = " ".join(row.get("flags",[])) if show_flags and row.get("flags") else ""

    st.markdown(f"""
    <div class="result-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="ticker">#{i+1} {row['ticker']}</span>
        <span class="{sc_cls}">⭐ {row['score']}</span>
      </div>
      {'<div style="color:#f0b429;font-size:0.75rem;margin:4px 0">'+flags+'</div>' if flags else ''}
      <div class="row-item">💰 מחיר: <span class="row-val">${row['price']}</span> &nbsp;|&nbsp; 🏢 <span class="row-val">{row['sector']}</span></div>
      <div class="row-item">📈 מומנטום 3M: <span class="{m3_cls}">{arrow}{abs(row['m3'])}%</span> &nbsp;|&nbsp; Vol: <span class="row-val">{row['vs']}x</span></div>
      <div class="row-item">RSI: <span class="row-val">{row['rsi']}</span> &nbsp;|&nbsp; MFI: <span class="row-val">{row['mfi']}</span> &nbsp;|&nbsp; ADX: <span class="row-val">{row['adx']}</span></div>
      <div class="row-item">OBV: <span class="row-val">{obv}</span> &nbsp;|&nbsp; vs SPY: <span class="row-val">+{row['rs']}%</span></div>
      <div class="row-item">🛡️ כניסה: <span class="row-val">${row['price']}</span> | סטופ: <span class="negative">${row['stop']}</span> | יעד 1: <span class="positive">${row['target']}</span> | יעד 2: <span class="positive">${row['target2']}</span></div>
      <div class="row-item">📝 {row['setup']}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────
def main():
    st.markdown('<div class="main-title">📈 SWING SCANNER PRO</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">S&P 500 · {datetime.now().strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
    st.markdown("---")

    mode = st.radio("בחר מצב סריקה:", [
        "🔍 סריקה כללית — S&P 500",
        "🎯 ניתוח מניה בודדת + AI מעמיק",
        "📋 ניתוח מספר מניות ספציפיות",
    ])

    # ── Mode 1: General scan ──────────────────────────────────
    if mode == "🔍 סריקה כללית — S&P 500":
        universe_size = st.radio("בחר Universe:", ["🚀 QQQ — נאסד\"ק 100 (מהיר ~2 דק)", "⚡ S&P 500 — 150 מניות (מהיר ~3 דק)", "💎 S&P 500 — 500 מניות (מלא ~10 דק)"])
        top_n = st.slider("כמה מניות להציג?", 5, 20, 10)
        tickers = SP500_FULL if "500" in universe_size else SP500_FULL[:150]

        if st.button("🔍  RUN SCAN — סרוק עכשיו"):
            spy = yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
            if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
            spy_c = spy["Close"]

            prog = st.progress(0, text="מוריד נתונים...")
            results = []
            for i,t in enumerate(tickers):
                r,_ = analyse(t, spy_c, strict=True)
                if r: results.append(r)
                prog.progress((i+1)/len(tickers), text=f"סורק {t}... ({i+1}/{len(tickers)})")
            prog.empty()

            if not results:
                st.warning("לא נמצאו מניות שעוברות את הפילטרים היום.")
                return

            results.sort(key=lambda x: x["score"], reverse=True)
            sec_c={}; sel=[]
            for row in results:
                s=row["sector"]
                if sec_c.get(s,0)<3: sel.append(row); sec_c[s]=sec_c.get(s,0)+1
                if len(sel)>=top_n: break

            st.success(f"✅ נמצאו {len(sel)} מניות!")
            st.markdown("---")
            for i,row in enumerate(sel): show_card(i, row)

            csv = pd.DataFrame(sel).to_csv(index=False).encode()
            st.download_button("⬇️ הורד CSV", data=csv,
                file_name=f"scan_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    # ── Mode 2: Single stock + AI ─────────────────────────────
    elif mode == "🎯 ניתוח מניה בודדת + AI מעמיק":
        ticker_input = st.text_input("הכנס טיקר:", "").strip().upper()
        api_key = st.text_input("מפתח API (Anthropic):", type="password",
                                 help="נשמר רק לסשן זה, לא נשמר בשרת")

        if st.button("🔍  נתח עכשיו"):
            if not ticker_input:
                st.warning("הכנס טיקר")
                return

            spy = yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
            if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)

            with st.spinner(f"מנתח {ticker_input}..."):
                r, err = analyse(ticker_input, spy["Close"], strict=False)

            if not r:
                st.error(f"לא ניתן לנתח את {ticker_input}: {err}")
                return

            show_card(0, r, show_flags=True)

            if api_key:
                st.markdown("---")
                st.markdown("### 🤖 ניתוח AI מעמיק")
                with st.spinner("Claude מנתח את המניה... (~30 שניות)"):
                    analysis = ai_deep_analysis(r, api_key)
                st.markdown(f'<div class="ai-card">{analysis}</div>', unsafe_allow_html=True)
            else:
                st.info("💡 הוסף מפתח API לקבלת ניתוח AI מעמיק")

    # ── Mode 3: Multiple specific tickers ────────────────────
    else:
        custom = st.text_input("הכנס טיקרים (מופרדים בפסיק):", "")
        top_n = 50
        tickers = [t.strip().upper() for t in custom.split(",") if t.strip()] if custom else []

        if tickers:
            st.info(f"מנתח {len(tickers)} מניות: {', '.join(tickers)}")
        else:
            st.warning("הכנס לפחות טיקר אחד")
            return

        if st.button("🔍  נתח עכשיו"):
            spy = yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
            if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
            spy_c = spy["Close"]

            prog = st.progress(0, text="מוריד נתונים...")
            results=[]; failures=[]
            for i,t in enumerate(tickers):
                r,err = analyse(t, spy_c, strict=False)
                if r: results.append(r)
                elif err: failures.append((t,err))
                prog.progress((i+1)/len(tickers), text=f"סורק {t}...")
            prog.empty()

            if not results:
                st.warning("לא ניתן לנתח את המניות שהוזנו.")
                return

            results.sort(key=lambda x: x["score"], reverse=True)
            st.success(f"✅ נותחו {len(results)} מניות!")
            st.markdown("---")
            for i,row in enumerate(results): show_card(i, row, show_flags=True)

            if failures:
                st.markdown("---")
                for t,err in failures:
                    st.markdown(f'<div class="fail-card">❌ <b>{t}</b> — {err}</div>', unsafe_allow_html=True)

            csv = pd.DataFrame(results).to_csv(index=False).encode()
            st.download_button("⬇️ הורד CSV", data=csv,
                file_name=f"scan_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    st.markdown("""
    <div class="disclaimer">
    ⚠️ <b>אזהרת סיכון</b> — למטרות לימוד בלבד. אין המלצת השקעה.
    לעולם אל תסכן יותר מ-1.5-2% מההון שלך בעסקה אחת.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
