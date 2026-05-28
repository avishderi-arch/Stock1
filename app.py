"""
Swing Scanner Pro v5 — Full Featured
שכבות: פילטרים | ניקוד | AI | Earnings Guard | Sector Strength | Gap | Volatility | Tracker
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import re
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Swing Scanner Pro", page_icon="📈", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');
body { background:#0a0e17; color:#c9d1d9; font-family:'IBM Plex Mono',monospace; }
.main-title { color:#21ff87; font-size:1.9rem; font-weight:700; text-align:center; margin-bottom:4px; }
.sub-title  { color:#8b949e; font-size:0.82rem; text-align:center; margin-bottom:16px; }
.stButton > button {
    background:linear-gradient(135deg,#21ff87,#00d4ff) !important;
    color:#0a0e17 !important; font-weight:700 !important; font-size:1.1rem !important;
    border:none !important; border-radius:10px !important; padding:14px !important;
    width:100% !important; margin:10px 0 !important;
}
.result-card { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:14px; margin:8px 0; }
.hc-card     { background:#0d1117; border:2px solid #21ff87; border-radius:12px; padding:16px; margin:10px 0; }
.ss-card     { background:#1a0d1a; border:2px solid #ff7b72; border-radius:12px; padding:16px; margin:10px 0; }
.gap-card    { background:#0d1a0d; border:2px solid #00d4ff; border-radius:12px; padding:16px; margin:10px 0; }
.ai-card {
    background:#0d1117; border:1px solid #21ff8740; border-right:4px solid #21ff87;
    border-radius:10px; padding:20px; margin:8px 0; font-size:0.9rem;
    line-height:1.9; color:#e6edf3 !important; direction:rtl; text-align:right;
}
.ai-card h2 { color:#21ff87 !important; font-size:1rem; margin:12px 0 4px; }
.ai-card h3 { color:#00d4ff !important; font-size:0.9rem; margin:8px 0 4px; }
.earnings-warn { background:#1a1500; border:1px solid #f0b429; border-radius:8px; padding:10px 14px; margin:6px 0; font-size:0.8rem; color:#f0b429; }
.sector-badge { background:#21ff8720; color:#21ff87; border-radius:4px; padding:2px 8px; font-size:0.75rem; }
.ticker  { color:#58a6ff; font-size:1.2rem; font-weight:700; }
.score-high { color:#21ff87; font-size:1rem; font-weight:700; }
.score-mid  { color:#f0b429; font-size:1rem; font-weight:700; }
.score-low  { color:#ff7b72; font-size:1rem; font-weight:700; }
.row-item { color:#8b949e; font-size:0.78rem; margin:3px 0; }
.row-val  { color:#c9d1d9; font-weight:600; }
.positive { color:#21ff87; }
.negative { color:#ff7b72; }
.disclaimer { background:#161b22; border-left:3px solid #ff7b72; border-radius:6px; padding:12px; margin-top:16px; font-size:0.72rem; color:#8b949e; }
.tracker-row { background:#161b22; border-radius:8px; padding:10px; margin:4px 0; font-size:0.8rem; }
#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Universes ─────────────────────────────────────────────────
QQQ100 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","COST",
    "NFLX","TMUS","CSCO","ADBE","AMD","PEP","INTU","QCOM","AMAT","TXN",
    "ISRG","BKNG","HON","AMGN","VRTX","PANW","ADP","SBUX","GILD","MDLZ",
    "ADI","REGN","LRCX","MU","KLAC","MELI","INTC","SNPS","CDNS","CEG",
    "FTNT","CTAS","MAR","ORLY","ABNB","PYPL","WDAY","MCHP","PCAR","ROST",
    "PAYX","MNST","DXCM","ODFL","IDXX","CPRT","FAST","KDP","DLTR","EXC",
    "VRSK","BIIB","NXPI","ON","FANG","XEL","GEHC","DDOG","CRWD","ZS",
    "TEAM","ANSS","ILMN","ALGN","SWKS","OKTA","TTWO","WBA","ENPH","MRNA",
    "DOCU","CMCSA","PDD","ASML","AZN","BIDU","JD","WBD","EBAY","CSGP",
    "CCEP","FOXA","FOX","ZM","PTON","SIRI","MTCH","RIVN","LCID","SGEN",
]

SP500_150 = [
    "MMM","ABT","ABBV","ACN","ADBE","AMD","AFL","AMZN","AXP","AIG","AMT",
    "AMGN","APH","ADI","AAPL","AMAT","ANET","T","ADP","AZO","BAC","BAX",
    "BDX","BLK","BX","BA","BKNG","BSX","BMY","AVGO","CAT","CBOE","CVX",
    "CMG","CB","CI","CTAS","CSCO","C","CME","KO","CL","CMCSA","COP","STZ",
    "COST","CCI","CSX","CVS","DHR","DE","DELL","DVN","DXCM","DLR","DG",
    "DUK","ECL","EW","EA","ELV","LLY","EMR","ENPH","EOG","EQIX","XOM",
    "FDS","FICO","FAST","FDX","FIS","FITB","FSLR","FTNT","FCX","GE","GD",
    "GIS","GILD","GS","HCA","HSY","HPE","HLT","HD","HON","HUM","IBM",
    "IDXX","ITW","INTU","ISRG","ICE","JPM","JNJ","KMB","KLAC","KR","LHX",
    "LRCX","LIN","LMT","LOW","LULU","MA","MAR","MCD","MCK","MDT","MRK",
    "META","MET","MCHP","MU","MSFT","MCO","MS","MSI","NFLX","NEM","NEE",
    "NKE","NSC","NOC","NVDA","NXPI","ORLY","OXY","ON","ORCL","PCAR","PANW",
    "PH","PAYX","PEP","PFE","PM","PSX","PNC","PG","PGR","PLD","PRU","QCOM",
    "RTX","REGN","RSG","RMD","ROST","SPGI","CRM","SLB","SRE","NOW","SHW",
    "SYK","SNPS","TROW","TGT","TEL","TSLA","TXN","TMO","TJX","TT","TRV",
    "USB","UPS","URI","UNH","VLO","VZ","VRTX","V","WMT","DIS","WM","WFC",
    "WMB","XEL","YUM","ZBH","ZTS","BRK-B","GOOGL","GOOG",
]

SP500_FULL = SP500_150 + [
    "AOS","AES","A","APD","ABNB","AKAM","ALB","ARE","ALGN","ALLE","LNT",
    "ALL","MO","AMCR","AEE","AAL","AEP","AWK","AMP","AME","AON","APA",
    "APO","APTV","ACGL","ARW","AJG","AIZ","ATO","ADSK","AVB","AVY","AXON",
    "BKR","BALL","BBY","BIIB","BK","BWA","BR","BRO","CAH","KMX","CCL",
    "CARR","CBRE","CDW","CE","COR","CNC","CDAY","CF","CRL","SCHW","CHTR",
    "CHD","CINF","CFG","CLX","CMS","CTSH","CAG","ED","CEG","COO","CPRT",
    "GLW","CTVA","CSGP","CPAY","CMI","DHI","DRI","DVA","DAL","DLR","DFS",
    "DLTR","D","DPZ","DOV","DOW","DTE","DD","EMN","ETN","EBAY","EIX",
    "EFX","EQR","ERIE","ESS","EL","EG","EVRG","ES","EXC","EXPE","EXPD",
    "EXR","FFIV","FRT","FI","FMC","F","FTV","FOXA","FOX","BEN","GRMN",
    "IT","GEHC","GEN","GNRC","GM","GPC","HAL","HIG","HAS","DOC","HSIC",
    "HES","HRL","HST","HWM","HPQ","HUBB","HBAN","HII","IEX","INCY","IR",
    "PODD","INTC","IFF","IP","IPG","IVZ","INVH","IQV","IRM","JBHT","JBL",
    "JKHY","J","JCI","JNPR","K","KVUE","KDP","KEY","KEYS","KIM","KMI",
    "KKR","KHC","LH","LW","LVS","LDOS","LEN","LII","LYV","LKQ","L","LYB",
    "MTB","MRO","MPC","MKTX","MMC","MLM","MAS","MTCH","MKC","MGM","MAA",
    "MHK","MOH","TAP","MDLZ","MPWR","MNST","MOS","NDAQ","NTAP","NI","NDSN",
    "NTRS","NCLH","NRG","NUE","NVR","ODFL","OMC","OKE","OTIS","PKG","PARA",
    "PAYC","PYPL","PNR","PFG","PEG","PTC","PSA","PHM","PWR","DGX","RL",
    "RJF","O","REG","RF","RVTY","ROK","ROL","ROP","RCL","SBAC","STX",
    "SPG","SWKS","SJM","SW","SNA","SOLV","SO","LUV","SWK","SBUX","STT",
    "STLD","STE","SYF","SYY","TMUS","TTWO","TPR","TRGP","TDY","TFX","TER",
    "TXT","TSCO","TDG","TRMB","TFC","TYL","TSN","UBER","UDR","ULTA","UNP",
    "UAL","UHS","VTR","VLTO","VRSN","VRSK","VTRS","VICI","VST","VMC","WRB",
    "GWW","WAB","WBA","WAT","WEC","WELL","WST","WDC","WY","WTW","WYNN",
    "XYL","ZBRA","SMCI","GEHC","CEG","VST",
]

SECTORS = {
    "AAPL":"Tech","MSFT":"Tech","NVDA":"Tech","AVGO":"Tech","ADBE":"Tech",
    "CRM":"Tech","ORCL":"Tech","AMD":"Tech","QCOM":"Tech","TXN":"Tech",
    "KLAC":"Tech","ADI":"Tech","LRCX":"Tech","MU":"Tech","SNPS":"Tech",
    "CDNS":"Tech","FTNT":"Tech","ANET":"Tech","PANW":"Tech","INTC":"Tech",
    "CSCO":"Tech","IBM":"Tech","HPE":"Tech","HPQ":"Tech","DELL":"Tech",
    "DDOG":"Tech","CRWD":"Tech","ZS":"Tech","OKTA":"Tech","WDAY":"Tech",
    "TEAM":"Tech","ANSS":"Tech","KEYS":"Tech","MPWR":"Tech","AXON":"Tech",
    "AMAT":"Tech","FICO":"Tech","INTU":"Tech","NOW":"Tech","ADSK":"Tech",
    "AMZN":"Cons.Disc","TSLA":"Cons.Disc","HD":"Cons.Disc","MCD":"Cons.Disc",
    "NKE":"Cons.Disc","LOW":"Cons.Disc","BKNG":"Cons.Disc","TJX":"Cons.Disc",
    "LULU":"Cons.Disc","MAR":"Cons.Disc","SBUX":"Cons.Disc","ORLY":"Cons.Disc",
    "GOOGL":"Comm","META":"Comm","NFLX":"Comm","DIS":"Comm","CMCSA":"Comm",
    "T":"Comm","VZ":"Comm","TMUS":"Comm","WBD":"Comm","FOXA":"Comm",
    "JPM":"Finance","BAC":"Finance","WFC":"Finance","MS":"Finance",
    "GS":"Finance","AXP":"Finance","BLK":"Finance","SCHW":"Finance",
    "SPGI":"Finance","CME":"Finance","ICE":"Finance","MMC":"Finance",
    "PGR":"Finance","V":"Finance","MA":"Finance","BX":"Finance","KKR":"Finance",
    "UNH":"Health","JNJ":"Health","LLY":"Health","MRK":"Health","ABBV":"Health",
    "TMO":"Health","ABT":"Health","AMGN":"Health","BMY":"Health","GILD":"Health",
    "VRTX":"Health","CI":"Health","SYK":"Health","ISRG":"Health","BDX":"Health",
    "REGN":"Health","DXCM":"Health","BIIB":"Health","IDXX":"Health","IQV":"Health",
    "MRNA":"Health","HCA":"Health","HUM":"Health","MDT":"Health","EW":"Health",
    "XOM":"Energy","CVX":"Energy","EOG":"Energy","SLB":"Energy","COP":"Energy",
    "PSX":"Energy","MPC":"Energy","VLO":"Energy","OXY":"Energy","DVN":"Energy",
    "PG":"Staples","KO":"Staples","PEP":"Staples","WMT":"Staples",
    "COST":"Staples","CL":"Staples","PM":"Staples","MO":"Staples",
    "LIN":"Materials","APD":"Materials","ECL":"Materials","SHW":"Materials",
    "NEM":"Materials","FCX":"Materials","NUE":"Materials","PPG":"Materials",
    "PLD":"Real Est","AMT":"Real Est","EQIX":"Real Est","CCI":"Real Est",
    "SO":"Utilities","DUK":"Utilities","NEE":"Utilities","AEP":"Utilities",
    "RTX":"Industrl","UPS":"Industrl","HON":"Industrl","CAT":"Industrl",
    "DE":"Industrl","GD":"Industrl","NSC":"Industrl","UNP":"Industrl",
    "LMT":"Industrl","GE":"Industrl","BA":"Industrl","MMM":"Industrl",
    "BRK-B":"Finance","TROW":"Finance","USB":"Finance",
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

# ── Earnings Guard ────────────────────────────────────────────
def get_earnings_info(ticker):
    """Returns days until next earnings and warning level"""
    try:
        t=yf.Ticker(ticker)
        cal=t.calendar
        if cal is None or cal.empty: return None, "unknown"
        if isinstance(cal, dict):
            dates=cal.get("Earnings Date",[])
            if not dates: return None,"unknown"
            next_e=pd.Timestamp(dates[0]) if not isinstance(dates[0],pd.Timestamp) else dates[0]
        else:
            if "Earnings Date" not in cal.columns: return None,"unknown"
            next_e=pd.Timestamp(cal["Earnings Date"].iloc[0])
        days=(next_e.tz_localize(None)-pd.Timestamp.now()).days
        if days<0: return None,"passed"
        if days<=3:  return days,"danger"   # בסכנה — דוח תוך 3 ימים
        if days<=7:  return days,"warning"  # אזהרה — דוח תוך שבוע
        if days<=14: return days,"caution"  # זהירות — דוח תוך 2 שבועות
        return days,"safe"
    except:
        return None,"unknown"

# ── Sector Strength ───────────────────────────────────────────
SECTOR_ETFS = {
    "Tech":"XLK","Finance":"XLF","Health":"XLV","Energy":"XLE",
    "Cons.Disc":"XLY","Staples":"XLP","Industrl":"XLI",
    "Materials":"XLB","Real Est":"XLRE","Utilities":"XLU","Comm":"XLC",
}

@st.cache_data(ttl=3600)
def get_sector_strengths():
    strengths={}
    spy=yf.download("SPY",period="1mo",auto_adjust=True,progress=False,threads=False)
    if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
    spy_ret=float(spy["Close"].pct_change(20).iloc[-1]) if len(spy)>=21 else 0
    for sector,etf in SECTOR_ETFS.items():
        try:
            df=yf.download(etf,period="1mo",auto_adjust=True,progress=False,threads=False)
            if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
            if len(df)>=21:
                ret=float(df["Close"].pct_change(20).iloc[-1])
                strengths[sector]=round((ret-spy_ret)*100,1)
        except: pass
    return strengths

# ── Gap Detection ─────────────────────────────────────────────
def detect_gap(ticker):
    try:
        df=yf.download(ticker,period="5d",auto_adjust=True,progress=False,threads=False)
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        if len(df)<2: return None
        prev_close=float(df["Close"].iloc[-2])
        today_open=float(df["Open"].iloc[-1])
        today_close=float(df["Close"].iloc[-1])
        gap_pct=(today_open-prev_close)/prev_close*100
        avg_vol=float(df["Volume"].rolling(5).mean().iloc[-1])
        vol_today=float(df["Volume"].iloc[-1])
        vol_ratio=vol_today/avg_vol if avg_vol>0 else 0
        if abs(gap_pct)<1.5 or vol_ratio<1.5: return None
        return {
            "ticker":ticker,"gap_pct":round(gap_pct,2),
            "direction":"UP" if gap_pct>0 else "DOWN",
            "vol_ratio":round(vol_ratio,2),
            "prev_close":round(prev_close,2),
            "open":round(today_open,2),
            "close":round(today_close,2),
            "holding":today_close>today_open if gap_pct>0 else today_close<today_open,
        }
    except: return None

# ── Core analysis ─────────────────────────────────────────────
def analyse(ticker, spy_close, strict=True, sector_strengths=None):
    try:
        raw=yf.download(ticker,period="1y",auto_adjust=True,progress=False,threads=False)
        if raw.empty or len(raw)<60: return None,"insufficient_data"
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        c=raw["Close"]; h=raw["High"]; l=raw["Low"]; v=raw["Volume"]

        price=float(c.iloc[-1])
        avg_vol=float(v.rolling(20).mean().iloc[-1])
        vs=float(v.iloc[-1]/avg_vol) if avg_vol>0 else 0
        sma20=float(c.rolling(20).mean().iloc[-1])
        sma50=float(c.rolling(50).mean().iloc[-1])
        sma200=float(c.rolling(200).mean().iloc[-1])
        rsi_v=float(rsi(c).iloc[-1])
        mh=macd_hist(c); mh_v=float(mh.iloc[-1]); mh_p=float(mh.iloc[-2])
        adx_v=float(adx(h,l,c).iloc[-1])
        obv=(np.sign(c.diff()).fillna(0)*v).cumsum(); obv_s=slope(obv.tail(20))
        mfi_v=float(mfi(h,l,c,v).iloc[-1])
        atr_v=float(atr(h,l,c).iloc[-1])
        m1=float(c.pct_change(21).iloc[-1])
        m3=float(c.pct_change(63).iloc[-1])
        high52=float(c.rolling(252).max().iloc[-1])
        low52=float(c.rolling(252).min().iloc[-1])
        atr_pct=atr_v/price*100

        al=spy_close.reindex(c.index,method="ffill")
        rs=float(c.pct_change(20).iloc[-1])-float(al.pct_change(20).iloc[-1]) if len(al)>=21 else 0.01

        # Trend Age — how many days above SMA50
        above_sma50=c>c.rolling(50).mean()
        trend_age=int(above_sma50[::-1].cumprod().sum()) if above_sma50.iloc[-1] else 0

        # Volatility check — too high ATR = risky
        if atr_pct>8 and strict:
            return None,f"תנודתיות קיצונית (ATR {atr_pct:.1f}%)"

        if strict:
            if price<10:           return None,"מחיר נמוך"
            if avg_vol<500000:     return None,"נפח נמוך"
            if price<=sma50:       return None,"מתחת SMA50"
            if sma50<=sma200:      return None,"SMA50 מתחת SMA200"
            if not(40<=rsi_v<=72): return None,f"RSI {rsi_v:.0f} מחוץ לטווח"
            if mh_v<=0:            return None,"MACD שלילי"
            if adx_v<20:           return None,f"ADX חלש {adx_v:.0f}"
            if vs<1.3:             return None,f"נפח נמוך {vs:.1f}x"
            if obv_s<=0:           return None,"OBV יורד"
            if mfi_v<50:           return None,f"MFI נמוך {mfi_v:.0f}"
            if rs<=0:              return None,"מפגר אחרי SPY"

        # Scoring
        ms=0.35*sig(m1,.05,.10)+0.65*sig(m3,.12,.15)
        vs2=0.55*clamp((vs-1.3)/(3-1.3)*100)+0.45*sig(obv_s,0,1e6)
        ma=(sma50-sma200)/sma200 if sma200>0 else 0
        ts=0.60*clamp((adx_v-20)/(60-20)*100)+0.40*sig(ma,.02,.04)
        mfs=clamp((mfi_v-50)/(90-50)*100)
        ras=sig(m3/max(atr_pct/100,0.005),2,3)
        rss=sig(rs,.02,.05)

        # Sector Strength Bonus
        sector=SECTORS.get(ticker,"אחר")
        sector_bonus=0
        if sector_strengths and sector in sector_strengths:
            ss=sector_strengths[sector]
            sector_bonus=min(ss*2,10) if ss>0 else 0

        # Distance from 52W High bonus
        dist_52h=(high52-price)/high52*100
        h52_bonus=10 if dist_52h<3 else 5 if dist_52h<8 else 0

        # Trend Age bonus
        trend_bonus=min(trend_age/30*5,8)

        comp=clamp(0.30*ms+0.25*vs2+0.20*ts+0.15*mfs+0.10*ras+0.05*rss+sector_bonus+h52_bonus/10+trend_bonus/10)

        notes=[]
        if m3>0.20:        notes.append("מומנטום חזק 3M")
        if vs>2.0:         notes.append("נפח גבוה")
        if adx_v>35:       notes.append("טרנד חזק")
        if mfi_v>65:       notes.append("קנייה מוסדית")
        if rsi_v<55:       notes.append("מקום לעלייה")
        if rs>0.05:        notes.append("מכה את SPY")
        if dist_52h<3:     notes.append("קרוב לשיא 52 שבועות")
        if trend_age>60:   notes.append(f"טרנד {trend_age} ימים")
        if sector_bonus>5: notes.append(f"סקטור חזק ({sector})")
        if not notes:      notes=["סטאפ רב-גורמי"]

        stop=price-2.0*atr_v; rsk=price-stop
        shares=max(0,int(min(100000*(1.75/100)/rsk if rsk>0 else 0,100000*0.10/price)))
        target=price+2.0*rsk; target2=price+3.5*rsk

        flags=[]
        if price<=sma50:   flags.append("⚠️ מתחת SMA50")
        if sma50<=sma200:  flags.append("⚠️ מתחת SMA200")
        if rsi_v>70:       flags.append(f"⚠️ RSI קנוי ({rsi_v:.0f})")
        if vs<1.3:         flags.append("⚠️ נפח נמוך")
        if atr_pct>6:      flags.append(f"⚠️ תנודתיות גבוהה {atr_pct:.1f}%")

        return {
            "ticker":ticker,"sector":sector,
            "price":round(price,2),"score":round(comp,1),
            "sma20":round(sma20,2),"sma50":round(sma50,2),"sma200":round(sma200,2),
            "m1":round(m1*100,1),"m3":round(m3*100,1),
            "vs":round(vs,2),"rsi":round(rsi_v,1),
            "mfi":round(mfi_v,1),"adx":round(adx_v,1),
            "macd_hist":round(mh_v,4),"obv_up":obv_s>0,"rs":round(rs*100,1),
            "atr":round(atr_v,2),"atr_pct":round(atr_pct,1),
            "high52":round(high52,2),"low52":round(low52,2),
            "dist_52h":round(dist_52h,1),"trend_age":trend_age,
            "avg_vol":int(avg_vol),"vol_today":int(v.iloc[-1]),
            "setup":"; ".join(notes[:2]),
            "stop":round(stop,2),"target":round(target,2),"target2":round(target2,2),
            "shares":shares,"risk":round(shares*rsk,0),"flags":flags,
        }, None
    except Exception as e:
        return None,str(e)[:40]

# ── Short Squeeze ─────────────────────────────────────────────
def analyse_squeeze(ticker, spy_close):
    try:
        raw=yf.download(ticker,period="6mo",auto_adjust=True,progress=False,threads=False)
        if raw.empty or len(raw)<30: return None
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        c=raw["Close"]; h=raw["High"]; l=raw["Low"]; v=raw["Volume"]
        price=float(c.iloc[-1]); avg_vol=float(v.rolling(20).mean().iloc[-1])
        vs=float(v.iloc[-1]/avg_vol) if avg_vol>0 else 0
        rsi_v=float(rsi(c).iloc[-1]); atr_v=float(atr(h,l,c).iloc[-1])
        sma20=c.rolling(20).mean(); std20=c.rolling(20).std()
        bb_upper=float((sma20+2*std20).iloc[-1]); bb_lower=float((sma20-2*std20).iloc[-1])
        bb_width=round((bb_upper-bb_lower)/float(sma20.iloc[-1])*100,1)
        price_vs_bb=round((price-bb_lower)/(bb_upper-bb_lower)*100,1) if (bb_upper-bb_lower)>0 else 50
        vol_trend=slope(v.tail(10)); rsi_trend=slope(rsi(c).tail(5))
        m5=float(c.pct_change(5).iloc[-1]); m10=float(c.pct_change(10).iloc[-1])
        score=0; reasons=[]
        if vs>2.0:         score+=30; reasons.append(f"נפח פתאומי {vs:.1f}x")
        elif vs>1.5:       score+=15; reasons.append(f"נפח גבוה {vs:.1f}x")
        if rsi_v>60:       score+=20; reasons.append(f"RSI עולה ({rsi_v:.0f})")
        if rsi_trend>0:    score+=10; reasons.append("מומנטום RSI")
        if m5>0.03:        score+=15; reasons.append(f"5 ימים +{m5*100:.1f}%")
        if m10>0.05:       score+=10; reasons.append(f"10 ימים +{m10*100:.1f}%")
        if price_vs_bb>75: score+=15; reasons.append("שובר BB עליון")
        if vol_trend>0:    score+=10; reasons.append("נפח גובר")
        if bb_width<10:    score+=15; reasons.append("BB Squeeze")
        if score<40 or price<5 or avg_vol<200000: return None
        return {
            "ticker":ticker,"sector":SECTORS.get(ticker,"אחר"),
            "price":round(price,2),"squeeze_score":min(score,100),
            "vs":round(vs,2),"rsi":round(rsi_v,1),
            "bb_width":bb_width,"price_vs_bb":price_vs_bb,
            "m5":round(m5*100,1),"m10":round(m10*100,1),
            "reasons":"; ".join(reasons[:3]),
            "stop":round(price-2.0*atr_v,2),"target":round(price*1.10,2),
        }
    except: return None

# ── AI Analysis ───────────────────────────────────────────────
def ai_deep_analysis(data, api_key):
    earnings_info=f"ימים לדוח: {data.get('earnings_days','לא ידוע')} | סטטוס: {data.get('earnings_status','לא ידוע')}"
    prompt=f"""אתה אנליסט מוסדי מקצועי. נתח מניה לסווינג 5-10 ימים. ענה בעברית. היה ספציפי ומעשי.

טיקר: {data['ticker']} | סקטור: {data['sector']} | מחיר: ${data['price']} | ניקוד: {data['score']}/100
SMA20: ${data['sma20']} | SMA50: ${data['sma50']} | SMA200: ${data['sma200']}
RSI: {data['rsi']} | MFI: {data['mfi']} | ADX: {data['adx']} | MACD Hist: {data['macd_hist']}
Vol Surge: {data['vs']}x | OBV: {"עולה" if data['obv_up'] else "יורד"}
מומנטום 1M: {data['m1']}% | 3M: {data['m3']}% | vs SPY: {data['rs']}%
ATR: ${data['atr']} ({data['atr_pct']}%) | שיא 52W: ${data['high52']} | מרחק משיא: {data['dist_52h']}%
גיל הטרנד: {data['trend_age']} ימים | {earnings_info}
כניסה: ${data['price']} | סטופ: ${data['stop']} | יעד 1: ${data['target']} | יעד 2: ${data['target2']}

## 🌍 מצב השוק והמניה
## 📊 ניתוח טכני מעמיק
## 🏦 Smart Money Analysis
## ⚠️ סיכונים (כולל דוחות אם רלוונטי)
## 🎯 תוכנית מסחר מדויקת
## ⭐ ציון: X/10
## 📋 המלצה סופית"""
    try:
        resp=requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key":api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-5","max_tokens":3000,"messages":[{"role":"user","content":prompt}]},
            timeout=120,
        )
        if resp.status_code==200: return resp.json()["content"][0]["text"]
        return f"שגיאה: {resp.status_code}"
    except Exception as e:
        return f"שגיאת חיבור: {str(e)[:80]}"

# ── Cards ─────────────────────────────────────────────────────
def show_card(i, row, style="normal", show_earnings=False):
    sc_cls="score-high" if row["score"]>=70 else "score-mid" if row["score"]>=50 else "score-low"
    m3_cls="positive" if row["m3"]>0 else "negative"
    arrow="▲" if row["m3"]>0 else "▼"
    obv="↑ עולה" if row["obv_up"] else "↓ יורד"
    flags=" ".join(row.get("flags",[])) if row.get("flags") else ""
    card_cls={"hc":"hc-card","gap":"gap-card"}.get(style,"result-card")
    icon="🔥" if style=="hc" else "📊"

    st.markdown(f"""
    <div class="{card_cls}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="ticker">#{i+1} {row['ticker']} {icon}</span>
        <span class="{sc_cls}">⭐ {row['score']}</span>
      </div>
      {'<div style="color:#f0b429;font-size:0.75rem;margin:4px 0">'+flags+'</div>' if flags else ''}
      <div class="row-item">💰 <span class="row-val">${row['price']}</span> | 🏢 <span class="row-val">{row['sector']}</span> | טרנד: <span class="row-val">{row.get('trend_age',0)} ימים</span></div>
      <div class="row-item">📈 3M: <span class="{m3_cls}">{arrow}{abs(row['m3'])}%</span> | Vol: <span class="row-val">{row['vs']}x</span> | ADX: <span class="row-val">{row['adx']}</span></div>
      <div class="row-item">RSI: <span class="row-val">{row['rsi']}</span> | MFI: <span class="row-val">{row['mfi']}</span> | OBV: <span class="row-val">{obv}</span> | SPY: <span class="row-val">+{row['rs']}%</span></div>
      <div class="row-item">📏 שיא 52W: <span class="row-val">${row['high52']}</span> (מרחק: <span class="row-val">{row.get('dist_52h','-')}%</span>)</div>
      <div class="row-item">🛡️ כניסה: <span class="row-val">${row['price']}</span> | סטופ: <span class="negative">${row['stop']}</span> | יעד 1: <span class="positive">${row['target']}</span> | יעד 2: <span class="positive">${row['target2']}</span></div>
      <div class="row-item">📝 {row['setup']}</div>
    </div>""", unsafe_allow_html=True)

    if show_earnings and row.get("earnings_days") is not None:
        days=row["earnings_days"]; status=row.get("earnings_status","")
        color={"danger":"#ff7b72","warning":"#f0b429","caution":"#58a6ff"}.get(status,"#8b949e")
        icon={"danger":"🚨","warning":"⚠️","caution":"📅"}.get(status,"📅")
        st.markdown(f'<div class="earnings-warn" style="border-color:{color};color:{color}">{icon} דוח רווחים בעוד {days} ימים — {"סיכון גבוה! שקול לדלג" if status=="danger" else "הזהר בגודל הפוזיציה" if status=="warning" else "שים לב"}</div>',unsafe_allow_html=True)

def show_squeeze_card(i, row):
    st.markdown(f"""
    <div class="ss-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="ticker">#{i+1} {row['ticker']} 💥</span>
        <span style="color:#ff7b72;font-weight:700">Squeeze: {row['squeeze_score']}</span>
      </div>
      <div class="row-item">💰 <span class="row-val">${row['price']}</span> | 🏢 <span class="row-val">{row['sector']}</span></div>
      <div class="row-item">📈 5D: <span class="positive">▲{row['m5']}%</span> | 10D: <span class="positive">▲{row['m10']}%</span> | Vol: <span class="row-val">{row['vs']}x</span></div>
      <div class="row-item">RSI: <span class="row-val">{row['rsi']}</span> | BB Width: <span class="row-val">{row['bb_width']}%</span> | מיקום: <span class="row-val">{row['price_vs_bb']}%</span></div>
      <div class="row-item">🛡️ סטופ: <span class="negative">${row['stop']}</span> | יעד: <span class="positive">${row['target']}</span></div>
      <div class="row-item">🔥 {row['reasons']}</div>
    </div>""", unsafe_allow_html=True)

def show_gap_card(i, row):
    dir_color="positive" if row["direction"]=="UP" else "negative"
    dir_arrow="▲" if row["direction"]=="UP" else "▼"
    holding_txt="✅ מחזיק" if row["holding"] else "⚠️ לא מחזיק"
    st.markdown(f"""
    <div class="gap-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="ticker">#{i+1} {row['ticker']} 📊</span>
        <span class="{dir_color}">{dir_arrow} גאפ {abs(row['gap_pct'])}%</span>
      </div>
      <div class="row-item">סגירה אמש: <span class="row-val">${row['prev_close']}</span> | פתיחה היום: <span class="row-val">${row['open']}</span> | עכשיו: <span class="row-val">${row['close']}</span></div>
      <div class="row-item">נפח: <span class="row-val">{row['vol_ratio']}x</span> | {holding_txt}</div>
    </div>""", unsafe_allow_html=True)

# ── Performance Tracker ───────────────────────────────────────
def save_to_tracker(results, scan_date):
    if "tracker" not in st.session_state:
        st.session_state["tracker"]=[]
    for r in results[:5]:
        st.session_state["tracker"].append({
            "date":scan_date,"ticker":r["ticker"],
            "entry":r["price"],"target":r["target"],
            "stop":r["stop"],"score":r["score"],
            "status":"פתוח",
        })

def show_tracker():
    if "tracker" not in st.session_state or not st.session_state["tracker"]:
        st.info("אין עסקאות במעקב עדיין. הרץ סריקה כדי להוסיף.")
        return
    st.markdown("### 📊 עסקאות במעקב")
    for i,t in enumerate(st.session_state["tracker"]):
        try:
            cur=yf.download(t["ticker"],period="2d",auto_adjust=True,progress=False,threads=False)
            if isinstance(cur.columns,pd.MultiIndex): cur.columns=cur.columns.get_level_values(0)
            cur_price=float(cur["Close"].iloc[-1]) if not cur.empty else t["entry"]
        except: cur_price=t["entry"]
        pnl=round((cur_price-t["entry"])/t["entry"]*100,2)
        pnl_cls="positive" if pnl>0 else "negative"
        status="🎯 יעד הושג" if cur_price>=t["target"] else "🛑 סטופ" if cur_price<=t["stop"] else "⏳ פתוח"
        st.markdown(f"""
        <div class="tracker-row">
          <span class="ticker">{t['ticker']}</span> |
          כניסה: ${t['entry']} | עכשיו: ${cur_price:.2f} |
          <span class="{pnl_cls}">{'▲' if pnl>0 else '▼'}{abs(pnl)}%</span> |
          {status} | {t['date']}
        </div>""", unsafe_allow_html=True)
    if st.button("🗑️ נקה מעקב"):
        st.session_state["tracker"]=[]
        st.rerun()

# ── Main ──────────────────────────────────────────────────────
def main():
    st.markdown('<div class="main-title">📈 SWING SCANNER PRO</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">S&P 500 + QQQ · {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)
    st.markdown("---")

    mode=st.radio("בחר מצב:", [
        "🔍 סריקה כללית",
        "🔥 High Conviction",
        "💥 Short Squeeze",
        "📊 Gap & Go",
        "🎯 מניה בודדת + AI",
        "📋 מניות ספציפיות",
        "📈 Performance Tracker",
    ])

    def get_universe(label=""):
        opt=st.radio("Universe:", ["🚀 QQQ 100","⚡ S&P 500 — 150","💎 S&P 500 מלא"],key=label)
        if "QQQ" in opt: return QQQ100
        if "מלא" in opt: return SP500_FULL
        return SP500_150

    def get_spy():
        spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
        if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
        return spy["Close"]

    # ── General ───────────────────────────────────────────────
    if mode=="🔍 סריקה כללית":
        tickers=get_universe("gen")
        top_n=st.slider("כמה מניות?",5,20,10)
        show_earnings=st.checkbox("הצג אזהרות דוחות רווחים",value=True)
        sector_info=st.checkbox("טען עוצמת סקטורים (איטי יותר)",value=False)

        if st.button("🔍 סרוק עכשיו"):
            spy_c=get_spy()
            ss=get_sector_strengths() if sector_info else {}
            prog=st.progress(0); rs=[]; rr=[]
            for i,t in enumerate(tickers):
                r,_=analyse(t,spy_c,strict=True,sector_strengths=ss)
                if r: rs.append(r)
                else:
                    r2,_=analyse(t,spy_c,strict=False,sector_strengths=ss)
                    if r2 and r2["score"]>=58: rr.append(r2)
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()

            results=rs if rs else rr
            if not results: st.error("לא נמצאו מניות."); return
            if not rs: st.warning(f"⚠️ תנאי שוק מאתגרים. מציג {len(rr)} עם ניקוד גבוה.")
            else: st.success(f"✅ {len(rs)} מניות עברו את כל הפילטרים!")

            results.sort(key=lambda x:x["score"],reverse=True)
            sec_c={}; sel=[]
            for row in results:
                s=row["sector"]
                if sec_c.get(s,0)<3: sel.append(row); sec_c[s]=sec_c.get(s,0)+1
                if len(sel)>=top_n: break

            # Add earnings info
            if show_earnings:
                st.info("בודק תאריכי דוחות...")
                for row in sel:
                    days,status=get_earnings_info(row["ticker"])
                    row["earnings_days"]=days; row["earnings_status"]=status

            for i,row in enumerate(sel): show_card(i,row,show_earnings=show_earnings)
            save_to_tracker(sel,datetime.now().strftime("%d/%m"))
            csv=pd.DataFrame(sel).to_csv(index=False).encode()
            st.download_button("⬇️ הורד CSV",data=csv,file_name=f"scan_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")

    # ── High Conviction ───────────────────────────────────────
    elif mode=="🔥 High Conviction":
        tickers=get_universe("hc")
        st.info("ניקוד 68+ | ADX 25+ | Volume 1.5x+ | מומנטום 10%+")
        if st.button("🔥 מצא High Conviction"):
            spy_c=get_spy(); prog=st.progress(0); hc=[]
            all_results=[]
            for i,t in enumerate(tickers):
                r,_=analyse(t,spy_c,strict=True)
                if r:
                    all_results.append(r)
                    if r["score"]>=68 and r["adx"]>=25 and r["vs"]>=1.5 and r["m3"]>=10:
                        days,status=get_earnings_info(t)
                        r["earnings_days"]=days; r["earnings_status"]=status
                        hc.append(r)
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()
            hc.sort(key=lambda x:x["score"],reverse=True); hc=hc[:3]
            if hc:
                st.success(f"🔥 {len(hc)} High Conviction setups!")
                for i,row in enumerate(hc): show_card(i,row,style="hc",show_earnings=True)
            elif all_results:
                all_results.sort(key=lambda x:x["score"],reverse=True)
                st.warning("לא נמצאו High Conviction מלאים — מציג את 3 הטובות שנמצאו:")
                for i,row in enumerate(all_results[:3]): show_card(i,row,style="hc")
            else:
                st.warning("לא נמצאו מניות כלל. ייתכן שהשוק סגור.")

    # ── Short Squeeze ─────────────────────────────────────────
    elif mode=="💥 Short Squeeze":
        tickers=get_universe("ss")
        st.info("BB Squeeze + נפח פתאומי + RSI עולה")
        if st.button("💥 סרוק Short Squeeze"):
            spy_c=get_spy(); prog=st.progress(0); sq=[]
            for i,t in enumerate(tickers):
                r=analyse_squeeze(t,spy_c)
                if r: sq.append(r)
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()
            sq.sort(key=lambda x:x["squeeze_score"],reverse=True); sq=sq[:5]
            if sq:
                st.success(f"💥 {len(sq)} מועמדות!")
                st.warning("⚠️ סיכון גבוה — פוזיציה קטנה יותר!")
                for i,row in enumerate(sq): show_squeeze_card(i,row)
            else: st.warning("לא נמצאו Short Squeeze setups.")

    # ── Gap & Go ──────────────────────────────────────────────
    elif mode=="📊 Gap & Go":
        tickers=get_universe("gap")
        st.info("מחפש גאפי פתיחה >1.5% על נפח גבוה — רץ בבוקר אחרי פתיחת שוק (16:30 ישראל)")
        if st.button("📊 סרוק Gap & Go"):
            prog=st.progress(0); gaps=[]
            for i,t in enumerate(tickers):
                r=detect_gap(t)
                if r: gaps.append(r)
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()
            gaps_up=[g for g in gaps if g["direction"]=="UP"]
            gaps_dn=[g for g in gaps if g["direction"]=="DOWN"]
            gaps_up.sort(key=lambda x:x["gap_pct"],reverse=True)
            if gaps_up:
                st.success(f"📊 {len(gaps_up)} גאפי עלייה!")
                for i,row in enumerate(gaps_up[:5]): show_gap_card(i,row)
            if gaps_dn:
                st.markdown("**גאפי ירידה (פוטנציאל שורט):**")
                for i,row in enumerate(gaps_dn[:3]): show_gap_card(i,row)
            if not gaps: st.warning("לא נמצאו גאפים משמעותיים. נסה מוקדם יותר ביום.")

    # ── Single + AI ───────────────────────────────────────────
    elif mode=="🎯 מניה בודדת + AI":
        ticker_input=st.text_input("הכנס טיקר:","").strip().upper()
        api_key=st.text_input("מפתח API:",type="password")
        show_earn=st.checkbox("בדוק תאריך דוח רווחים",value=True)

        if st.button("🎯 נתח עכשיו"):
            if not ticker_input: st.warning("הכנס טיקר"); return
            spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
            if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
            with st.spinner(f"מנתח {ticker_input}..."):
                r,err=analyse(ticker_input,spy["Close"],strict=False)
            if not r: st.error(f"שגיאה: {err}"); return
            if show_earn:
                days,status=get_earnings_info(ticker_input)
                r["earnings_days"]=days; r["earnings_status"]=status
            show_card(0,r,show_earnings=show_earn)

            if api_key:
                st.markdown("---")
                st.markdown("### 🤖 ניתוח AI מעמיק")
                with st.spinner("Claude מנתח... (עד 2 דקות)"):
                    analysis=ai_deep_analysis(r,api_key)
                    if "שגיאת חיבור" in analysis or "timed out" in analysis.lower():
                        st.info("מנסה שוב..."); analysis=ai_deep_analysis(r,api_key)
                html=re.sub(r'^## (.+)$',r'<h2>\1</h2>',analysis,flags=re.MULTILINE)
                html=re.sub(r'^### (.+)$',r'<h3>\1</h3>',html,flags=re.MULTILINE)
                html=html.replace("\n","<br>")
                st.markdown(f'<div class="ai-card">{html}</div>',unsafe_allow_html=True)
            else:
                st.info("💡 הוסף מפתח API לניתוח AI")

    # ── Multiple ──────────────────────────────────────────────
    elif mode=="📋 מניות ספציפיות":
        custom=st.text_input("הכנס טיקרים (מופרדים בפסיק):","")
        tickers=[t.strip().upper() for t in custom.split(",") if t.strip()] if custom else []
        show_earn=st.checkbox("בדוק תאריכי דוחות",value=True)
        if not tickers:
            st.warning("הכנס טיקרים")
        else:
            st.info(f"מנתח: {', '.join(tickers)}")

        if tickers and st.button("📋 נתח עכשיו"):
            spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
            if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
            spy_c=spy["Close"]
            prog=st.progress(0); results=[]; failures=[]
            for i,t in enumerate(tickers):
                r,err=analyse(t,spy_c,strict=False)
                if r:
                    if show_earn:
                        days,status=get_earnings_info(t)
                        r["earnings_days"]=days; r["earnings_status"]=status
                    results.append(r)
                elif err: failures.append((t,err))
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()
            if not results: st.warning("לא ניתן לנתח."); return
            results.sort(key=lambda x:x["score"],reverse=True)
            st.success(f"✅ {len(results)} מניות נותחו")
            for i,row in enumerate(results): show_card(i,row,show_earnings=show_earn)
            if failures:
                for t,err in failures:
                    st.markdown(f'<div style="color:#8b949e;font-size:0.78rem">❌ {t} — {err}</div>',unsafe_allow_html=True)
            csv=pd.DataFrame(results).to_csv(index=False).encode()
            st.download_button("⬇️ הורד CSV",data=csv,file_name=f"scan_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")

    # ── Tracker ───────────────────────────────────────────────
    elif mode=="📈 Performance Tracker":
        show_tracker()

    st.markdown("""
    <div class="disclaimer">
    ⚠️ <b>אזהרת סיכון</b> — למטרות לימוד בלבד. אין המלצת השקעה.
    לעולם אל תסכן יותר מ-1.5-2% מההון שלך בעסקה אחת.
    </div>""", unsafe_allow_html=True)

if __name__=="__main__":
    main()
