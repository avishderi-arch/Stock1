"""
Swing Scanner Pro v6 — Top-Down Architecture
שלב 1: Market Regime (SPY + VIX)
שלב 2: Top Sectors (ETF strength)
שלב 3: Best stocks within top sectors
שלב 4: VWAP + scoring
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import re
from datetime import datetime

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
.regime-bull  { background:#0d1a0d; border:2px solid #21ff87; border-radius:10px; padding:14px; margin:8px 0; text-align:center; }
.regime-bear  { background:#1a0d0d; border:2px solid #ff7b72; border-radius:10px; padding:14px; margin:8px 0; text-align:center; }
.regime-neut  { background:#161b22; border:2px solid #f0b429; border-radius:10px; padding:14px; margin:8px 0; text-align:center; }
.sector-card  { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:10px 14px; margin:4px 0; color:#e6edf3; font-size:0.85rem; }
.result-card  { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:14px; margin:8px 0; color:#e6edf3; }
.hc-card      { background:#0d1117; border:2px solid #21ff87; border-radius:12px; padding:16px; margin:10px 0; }
.ss-card      { background:#1a0d1a; border:2px solid #ff7b72; border-radius:12px; padding:16px; margin:10px 0; }
.gap-card     { background:#0d1a1a; border:2px solid #00d4ff; border-radius:12px; padding:16px; margin:10px 0; }
.vwap-above   { color:#21ff87; font-weight:700; }
.vwap-below   { color:#ff7b72; font-weight:700; }
.ai-card {
    background:#0d1117; border:1px solid #21ff8740;
    border-right:4px solid #21ff87; border-radius:10px;
    padding:20px; margin:8px 0; font-size:0.9rem;
    line-height:1.9; color:#e6edf3 !important;
    direction:rtl; text-align:right;
}
.ai-card h2 { color:#21ff87 !important; font-size:1rem; margin:12px 0 4px; }
.ai-card h3 { color:#00d4ff !important; font-size:0.9rem; margin:8px 0 4px; }
.earnings-warn { background:#1a1500; border:1px solid #f0b429; border-radius:8px; padding:8px 12px; margin:4px 0; font-size:0.78rem; color:#f0b429; }
.ticker  { color:#58a6ff; font-size:1.2rem; font-weight:700; }
.score-high { color:#21ff87; font-size:1rem; font-weight:700; }
.score-mid  { color:#f0b429; font-size:1rem; font-weight:700; }
.score-low  { color:#ff7b72; font-size:1rem; font-weight:700; }
.row-item { color:#d0d8e0; font-size:0.82rem; margin:5px 0; }
.row-val  { color:#ffffff; font-weight:700; font-size:0.85rem; }
.result-card *, .hc-card *, .ss-card *, .gap-card * { color: inherit; }
.positive { color:#21ff87; }
.negative { color:#ff7b72; }
.disclaimer { background:#161b22; border-left:3px solid #ff7b72; border-radius:6px; padding:12px; margin-top:16px; font-size:0.72rem; color:#8b949e; }
.tracker-row { background:#161b22; border-radius:8px; padding:10px; margin:4px 0; font-size:0.8rem; }
#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sector ETF Map ────────────────────────────────────────────
SECTOR_ETFS = {
    "Tech":       ("XLK",  ["AAPL","MSFT","NVDA","AVGO","ADBE","AMD","QCOM","TXN","KLAC","ADI","LRCX","MU","SNPS","CDNS","FTNT","ANET","PANW","INTC","CSCO","DELL","DDOG","CRWD","NOW","INTU","FICO","AMAT","WDAY","ZS"]),
    "Finance":    ("XLF",  ["JPM","BAC","WFC","MS","GS","AXP","BLK","SCHW","SPGI","CME","ICE","MMC","PGR","V","MA","BX","KKR","USB","TROW","BRK-B"]),
    "Health":     ("XLV",  ["UNH","JNJ","LLY","MRK","ABBV","TMO","ABT","AMGN","BMY","GILD","VRTX","CI","SYK","ISRG","BDX","REGN","DXCM","BIIB","IDXX","IQV","MRNA","HCA","HUM","MDT","EW"]),
    "Cons.Disc":  ("XLY",  ["AMZN","TSLA","HD","MCD","NKE","LOW","BKNG","TJX","LULU","MAR","SBUX","ORLY"]),
    "Comm":       ("XLC",  ["GOOGL","META","NFLX","DIS","CMCSA","T","VZ","TMUS"]),
    "Industrl":   ("XLI",  ["RTX","UPS","HON","CAT","DE","GD","NSC","UNP","LMT","GE","BA","MMM"]),
    "Energy":     ("XLE",  ["XOM","CVX","EOG","SLB","COP","PSX","MPC","VLO","OXY","DVN"]),
    "Staples":    ("XLP",  ["PG","KO","PEP","WMT","COST","CL","PM","MO"]),
    "Materials":  ("XLB",  ["LIN","APD","ECL","SHW","NEM","FCX","NUE","PPG"]),
    "Real Est":   ("XLRE", ["PLD","AMT","EQIX","CCI"]),
    "Utilities":  ("XLU",  ["SO","DUK","NEE","AEP"]),
}

# ── MidCap / Growth Universe (מניות צמיחה שאינן ב-S&P 500) ──
MIDCAP_GROWTH = [
    # SaaS / Tech Growth
    "SNOW","DDOG","CRWD","ZS","OKTA","NET","BILL","GTLB","ESTC","MDB",
    "CFLT","AFRM","UPST","SOFI","HOOD","COIN","MSTR","SMAR","DUOL","ASAN",
    "PLTR","PATH","AI","BBAI","SOUN","IONQ","RGTI","QUBT","QBTS","ARQQ",
    # Biotech / Health Growth
    "RXRX","BEAM","EDIT","NTLA","CRSP","FATE","ACAD","AXSM","INVA","PRCT",
    "IRTC","GKOS","TMDX","BLFS","NVCR","IDYA","VERA","ARWR","MDGL","VKTX",
    # Clean Energy / EV
    "ENPH","FSLR","RUN","NOVA","ARRY","STEM","CHPT","BLNK","EVGO","LCID",
    "RIVN","FSR","GOEV","WKHS","NKLA","HYZN","PLUG","FCEL","BLDP","BE",
    # Fintech / Consumer
    "SQ","PYPL","AFRM","OPEN","OPENDOOR","LMND","ROOT","HI","UWMC","RKT",
    # Semiconductors Small/Mid
    "WOLF","AMBA","AEIS","ACLS","MTSI","SITM","POWI","DIOD","IMOS","CEVA",
    # Retail / Consumer Growth
    "BIRD","XPOF","BROS","CAVA","SHAK","WINGSTOP","PTLO","FAT","CZNC","JACK",
]

# Remove duplicates and clean
MIDCAP_GROWTH = list(dict.fromkeys([t for t in MIDCAP_GROWTH if len(t)<=5]))

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

def calc_atr(h,l,c,p=14):
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

def calc_vwap(h,l,c,v,period=20):
    tp=(h+l+c)/3
    return (tp*v).rolling(period).sum()/v.rolling(period).sum()

# ── PHASE 1: Market Regime ────────────────────────────────────
@st.cache_data(ttl=1800)
def get_market_regime():
    try:
        spy=yf.download("SPY",period="3mo",auto_adjust=True,progress=False,threads=False)
        if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
        spy_c=spy["Close"]
        price=float(spy_c.iloc[-1])
        sma50=float(spy_c.rolling(50).mean().iloc[-1])
        sma200=float(spy_c.rolling(200).mean().iloc[-1])
        rsi_v=float(rsi(spy_c).iloc[-1])
        ret_1m=float(spy_c.pct_change(21).iloc[-1])
        ret_5d=float(spy_c.pct_change(5).iloc[-1])
        above_50=price>sma50
        above_200=price>sma200
        golden=sma50>sma200

        # VIX
        try:
            vix=yf.download("^VIX",period="5d",auto_adjust=True,progress=False,threads=False)
            if isinstance(vix.columns,pd.MultiIndex): vix.columns=vix.columns.get_level_values(0)
            vix_val=float(vix["Close"].iloc[-1])
        except: vix_val=20.0

        # Regime determination
        bull_signals=sum([above_50,above_200,golden,rsi_v>50,ret_1m>0,ret_5d>0,vix_val<20])
        if bull_signals>=5:   regime="bullish"
        elif bull_signals<=2: regime="bearish"
        else:                 regime="neutral"

        return {
            "regime":regime,"spy_price":round(price,2),
            "sma50":round(sma50,2),"sma200":round(sma200,2),
            "above_50":above_50,"above_200":above_200,"golden":golden,
            "rsi":round(rsi_v,1),"ret_1m":round(ret_1m*100,1),
            "ret_5d":round(ret_5d*100,1),"vix":round(vix_val,1),
            "bull_signals":bull_signals,
        }
    except Exception as e:
        return {"regime":"unknown","error":str(e)}

# ── PHASE 2: Sector Strength ──────────────────────────────────
@st.cache_data(ttl=1800)
def get_sector_ranking():
    try:
        spy=yf.download("SPY",period="2mo",auto_adjust=True,progress=False,threads=False)
        if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
        spy_ret_1m=float(spy["Close"].pct_change(21).iloc[-1])
        spy_ret_5d=float(spy["Close"].pct_change(5).iloc[-1])

        sectors=[]
        for sector,(etf,stocks) in SECTOR_ETFS.items():
            try:
                df=yf.download(etf,period="2mo",auto_adjust=True,progress=False,threads=False)
                if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                if len(df)<22: continue
                ret_1m=float(df["Close"].pct_change(21).iloc[-1])
                ret_5d=float(df["Close"].pct_change(5).iloc[-1])
                rs_1m=ret_1m-spy_ret_1m
                rs_5d=ret_5d-spy_ret_5d
                # Combined score: 60% 1M + 40% 5D relative strength
                score=0.60*rs_1m+0.40*rs_5d
                sectors.append({
                    "sector":sector,"etf":etf,
                    "ret_1m":round(ret_1m*100,1),
                    "ret_5d":round(ret_5d*100,1),
                    "rs_1m":round(rs_1m*100,1),
                    "rs_5d":round(rs_5d*100,1),
                    "score":round(score*100,2),
                    "stocks":stocks,
                })
            except: pass
        sectors.sort(key=lambda x:x["score"],reverse=True)
        return sectors
    except: return []

# ── PHASE 3+4: Stock Analysis with VWAP ──────────────────────
def analyse_stock(ticker, spy_close, strict=True, sector_score=0):
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
        atr_v=float(calc_atr(h,l,c).iloc[-1])
        m1=float(c.pct_change(21).iloc[-1])
        m3=float(c.pct_change(63).iloc[-1])
        high52_series=c.rolling(252).max()
        high52=float(high52_series.iloc[-1]) if not pd.isna(high52_series.iloc[-1]) else float(c.max())
        low52_series=c.rolling(252).min()
        low52=float(low52_series.iloc[-1]) if not pd.isna(low52_series.iloc[-1]) else float(c.min())
        atr_pct=atr_v/price*100

        # VWAP (20-day)
        vwap_val=float(calc_vwap(h,l,c,v,20).iloc[-1])
        above_vwap=price>vwap_val
        vwap_dist=round((price-vwap_val)/vwap_val*100,1)

        al=spy_close.reindex(c.index,method="ffill")
        rs_spy=float(c.pct_change(20).iloc[-1])-float(al.pct_change(20).iloc[-1]) if len(al)>=21 else 0.01

        # Trend age
        above_sma50=c>c.rolling(50).mean()
        trend_age=int(above_sma50[::-1].cumprod().sum()) if above_sma50.iloc[-1] else 0

        # Distance from 52W high
        dist_52h=(high52-price)/high52*100

        if strict:
            if price<10:           return None,"מחיר נמוך"
            if avg_vol<400000:     return None,"נפח נמוך"
            if price<=sma50:       return None,"מתחת SMA50"
            if sma50<=sma200:      return None,"SMA50 מתחת SMA200"
            if not(38<=rsi_v<=74): return None,f"RSI {rsi_v:.0f}"
            if mh_v<=0:            return None,"MACD שלילי"
            if adx_v<18:           return None,f"ADX חלש {adx_v:.0f}"
            if vs<1.2:             return None,f"נפח נמוך {vs:.1f}x"
            if obv_s<=0:           return None,"OBV יורד"
            if mfi_v<48:           return None,f"MFI נמוך {mfi_v:.0f}"
            if rs_spy<=0:          return None,"מפגר SPY"
            if atr_pct>10:         return None,f"תנודתיות קיצונית"

        # ── Scoring ──────────────────────────────────────────
        ms=0.35*sig(m1,.05,.10)+0.65*sig(m3,.12,.15)
        vs2=0.55*clamp((vs-1.2)/(3-1.2)*100)+0.45*sig(obv_s,0,1e6)
        ma=(sma50-sma200)/sma200 if sma200>0 else 0
        ts=0.60*clamp((adx_v-18)/(60-18)*100)+0.40*sig(ma,.02,.04)
        mfs=clamp((mfi_v-48)/(90-48)*100)
        ras=sig(m3/max(atr_pct/100,0.005),2,3)
        rss=sig(rs_spy,.02,.05)

        # VWAP bonus — above VWAP = institutional support
        vwap_bonus=8 if above_vwap and vwap_dist<3 else 4 if above_vwap else -5

        # Sector strength bonus (passed in)
        sec_bonus=min(sector_score*1.5,12) if sector_score>0 else 0

        # 52W High proximity bonus
        h52_bonus=10 if dist_52h<2 else 5 if dist_52h<6 else 0

        # Trend age bonus
        trend_bonus=min(trend_age/30*6,8)

        base=0.28*ms+0.23*vs2+0.20*ts+0.14*mfs+0.10*ras+0.05*rss
        comp=clamp(base*100+vwap_bonus+sec_bonus+h52_bonus/10+trend_bonus/10)

        notes=[]
        if above_vwap:    notes.append(f"מעל VWAP (+{vwap_dist}%)")
        if m3>0.15:       notes.append("מומנטום חזק 3M")
        if vs>2.0:        notes.append("נפח גבוה")
        if adx_v>35:      notes.append("טרנד חזק")
        if mfi_v>65:      notes.append("קנייה מוסדית")
        if dist_52h<3:    notes.append("קרוב לשיא 52W")
        if sec_bonus>8:   notes.append("סקטור מוביל")
        if not notes:     notes=["סטאפ רב-גורמי"]

        stop=price-2.0*atr_v; rsk=price-stop
        shares=max(0,int(min(100000*(1.75/100)/rsk if rsk>0 else 0,100000*0.10/price)))
        target=price+2.0*rsk; target2=price+3.5*rsk

        flags=[]
        if not above_vwap:  flags.append("⚠️ מתחת VWAP")
        if rsi_v>70:        flags.append(f"⚠️ RSI קנוי ({rsi_v:.0f})")
        if vs<1.2:          flags.append("⚠️ נפח נמוך")
        if atr_pct>6:       flags.append(f"⚠️ תנודתי {atr_pct:.1f}%")

        return {
            "ticker":ticker,
            "price":round(price,2),"score":round(comp,1),
            "sma20":round(sma20,2),"sma50":round(sma50,2),"sma200":round(sma200,2),
            "vwap":round(vwap_val,2),"above_vwap":above_vwap,"vwap_dist":vwap_dist,
            "m1":round(m1*100,1),"m3":round(m3*100,1),
            "vs":round(vs,2),"rsi":round(rsi_v,1),
            "mfi":round(mfi_v,1),"adx":round(adx_v,1),
            "macd_hist":round(mh_v,4),"obv_up":obv_s>0,"rs":round(rs_spy*100,1),
            "atr":round(atr_v,2),"atr_pct":round(atr_pct,1),
            "high52":round(high52,2),"low52":round(low52,2),
            "dist_52h":round(dist_52h,1),"trend_age":trend_age,
            "avg_vol":int(avg_vol),"setup":"; ".join(notes[:2]),
            "stop":round(stop,2),"target":round(target,2),"target2":round(target2,2),
            "shares":shares,"flags":flags,
        }, None
    except Exception as e:
        return None,str(e)[:40]

# ── Earnings Guard ────────────────────────────────────────────
def get_earnings_info(ticker):
    try:
        t=yf.Ticker(ticker); cal=t.calendar
        if cal is None or (hasattr(cal,'empty') and cal.empty): return None,"unknown"
        if isinstance(cal,dict):
            dates=cal.get("Earnings Date",[])
            if not dates: return None,"unknown"
            next_e=pd.Timestamp(dates[0])
        else:
            if "Earnings Date" not in cal.columns: return None,"unknown"
            next_e=pd.Timestamp(cal["Earnings Date"].iloc[0])
        days=(next_e.tz_localize(None)-pd.Timestamp.now()).days
        if days<0:  return None,"passed"
        if days<=3: return days,"danger"
        if days<=7: return days,"warning"
        if days<=14:return days,"caution"
        return days,"safe"
    except: return None,"unknown"

# ── Short Squeeze ─────────────────────────────────────────────
def analyse_squeeze(ticker):
    try:
        raw=yf.download(ticker,period="6mo",auto_adjust=True,progress=False,threads=False)
        if raw.empty or len(raw)<30: return None
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        c=raw["Close"]; h=raw["High"]; l=raw["Low"]; v=raw["Volume"]
        price=float(c.iloc[-1]); avg_vol=float(v.rolling(20).mean().iloc[-1])
        vs=float(v.iloc[-1]/avg_vol) if avg_vol>0 else 0
        rsi_v=float(rsi(c).iloc[-1]); atr_v=float(calc_atr(h,l,c).iloc[-1])
        sma20=c.rolling(20).mean(); std20=c.rolling(20).std()
        bb_upper=float((sma20+2*std20).iloc[-1]); bb_lower=float((sma20-2*std20).iloc[-1])
        bb_width=round((bb_upper-bb_lower)/float(sma20.iloc[-1])*100,1) if float(sma20.iloc[-1])>0 else 0
        price_vs_bb=round((price-bb_lower)/(bb_upper-bb_lower)*100,1) if (bb_upper-bb_lower)>0 else 50
        rsi_trend=slope(rsi(c).tail(5))
        m5=float(c.pct_change(5).iloc[-1]); m10=float(c.pct_change(10).iloc[-1])
        score=0; reasons=[]
        if vs>2.0:         score+=30; reasons.append(f"נפח {vs:.1f}x")
        elif vs>1.5:       score+=15; reasons.append(f"נפח {vs:.1f}x")
        if rsi_v>60:       score+=20; reasons.append(f"RSI {rsi_v:.0f}")
        if rsi_trend>0:    score+=10; reasons.append("RSI עולה")
        if m5>0.03:        score+=15; reasons.append(f"5D +{m5*100:.1f}%")
        if m10>0.05:       score+=10; reasons.append(f"10D +{m10*100:.1f}%")
        if price_vs_bb>75: score+=15; reasons.append("שובר BB")
        if bb_width<10:    score+=15; reasons.append("BB Squeeze")
        if score<40 or price<5 or avg_vol<200000: return None
        return {
            "ticker":ticker,"price":round(price,2),"squeeze_score":min(score,100),
            "vs":round(vs,2),"rsi":round(rsi_v,1),
            "bb_width":bb_width,"price_vs_bb":price_vs_bb,
            "m5":round(m5*100,1),"m10":round(m10*100,1),
            "reasons":"; ".join(reasons[:3]),
            "stop":round(price-2.0*atr_v,2),"target":round(price*1.10,2),
        }
    except: return None

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
        vol_ratio=float(df["Volume"].iloc[-1])/avg_vol if avg_vol>0 else 0
        if abs(gap_pct)<1.5 or vol_ratio<1.5: return None
        return {
            "ticker":ticker,"gap_pct":round(gap_pct,2),
            "direction":"UP" if gap_pct>0 else "DOWN",
            "vol_ratio":round(vol_ratio,2),
            "prev_close":round(prev_close,2),
            "open":round(today_open,2),"close":round(today_close,2),
            "holding":today_close>today_open if gap_pct>0 else today_close<today_open,
        }
    except: return None

# ── AI Analysis ───────────────────────────────────────────────
def ai_deep_analysis(data, api_key, regime=None, sector_rank=None):
    regime_ctx=""
    if regime:
        regime_ctx=f"מצב שוק: {regime['regime']} | SPY: ${regime['spy_price']} | VIX: {regime['vix']} | RSI SPY: {regime['rsi']} | חודש: {regime['ret_1m']}%"
    sector_ctx=""
    if sector_rank:
        top3=", ".join([f"{s['sector']} ({s['rs_1m']:+.1f}%)" for s in sector_rank[:3]])
        sector_ctx=f"סקטורים מובילים: {top3}"

    prompt=f"""אתה אנליסט מוסדי מקצועי. נתח מניה לסווינג 5-10 ימים. ענה בעברית. היה ספציפי ומעשי.

{regime_ctx}
{sector_ctx}

טיקר: {data['ticker']} | מחיר: ${data['price']} | ניקוד: {data['score']}/100
SMA20: ${data['sma20']} | SMA50: ${data['sma50']} | SMA200: ${data['sma200']}
VWAP (20D): ${data['vwap']} | {"מעל VWAP ✅" if data['above_vwap'] else "מתחת VWAP ⚠️"} ({data['vwap_dist']:+.1f}%)
RSI: {data['rsi']} | MFI: {data['mfi']} | ADX: {data['adx']} | MACD Hist: {data['macd_hist']}
Vol Surge: {data['vs']}x | OBV: {"עולה" if data['obv_up'] else "יורד"}
מומנטום 1M: {data['m1']}% | 3M: {data['m3']}% | vs SPY: {data['rs']}%
ATR: ${data['atr']} ({data['atr_pct']}%) | שיא 52W: ${data['high52']} | מרחק: {data['dist_52h']}%
גיל טרנד: {data['trend_age']} ימים
כניסה: ${data['price']} | סטופ: ${data['stop']} | יעד 1: ${data['target']} | יעד 2: ${data['target2']}

## 🌍 מצב שוק ומגזר
## 📊 ניתוח טכני (כולל VWAP)
## 🏦 Smart Money
## ⚠️ סיכונים
## 🎯 תוכנית מסחר
## ⭐ ציון: X/10
## 📋 המלצה"""

    try:
        resp=requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key":api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-5","max_tokens":3000,"messages":[{"role":"user","content":prompt}]},
            timeout=120,
        )
        if resp.status_code==200: return resp.json()["content"][0]["text"]
        return f"שגיאה: {resp.status_code}"
    except Exception as e: return f"שגיאת חיבור: {str(e)[:80]}"

# ── UI Helpers ────────────────────────────────────────────────
def show_regime(r):
    if not r or r.get("regime")=="unknown": return
    regime=r["regime"]
    cls={"bullish":"regime-bull","bearish":"regime-bear","neutral":"regime-neut"}[regime]
    icon={"bullish":"🟢","bearish":"🔴","neutral":"🟡"}[regime]
    label={"bullish":"שורי — מתאים ללונגים","bearish":"דובי — זהירות עם לונגים","neutral":"ניטרלי — מסחר סלקטיבי"}[regime]
    checks=f"SPY {'✅' if r['above_50'] else '❌'} SMA50 | {'✅' if r['above_200'] else '❌'} SMA200 | {'✅' if r['golden'] else '❌'} Golden Cross | VIX {r['vix']} | RSI {r['rsi']}"
    st.markdown(f'<div class="{cls}"><b>{icon} שוק {label}</b><br><small>{checks}</small><br><small>SPY חודש: {r["ret_1m"]:+.1f}% | שבוע: {r["ret_5d"]:+.1f}%</small></div>',unsafe_allow_html=True)

def show_sector_ranking(sectors):
    st.markdown("**📊 דירוג מגזרים (Relative Strength vs SPY):**")
    for i,s in enumerate(sectors[:5]):
        bar_color="#21ff87" if s["rs_1m"]>0 else "#ff7b72"
        medal=["🥇","🥈","🥉","4️⃣","5️⃣"][i]
        st.markdown(f'<div class="sector-card">{medal} <b>{s["sector"]}</b> ({s["etf"]}) | 1M: <span style="color:{bar_color}">{s["rs_1m"]:+.1f}%</span> vs SPY | 5D: <span style="color:{bar_color}">{s["rs_5d"]:+.1f}%</span></div>',unsafe_allow_html=True)

def show_card(i, row, style="normal", show_earnings=False):
    sc_cls="score-high" if row["score"]>=70 else "score-mid" if row["score"]>=50 else "score-low"
    m3_cls="positive" if row["m3"]>0 else "negative"
    arrow="▲" if row["m3"]>0 else "▼"
    obv="↑" if row["obv_up"] else "↓"
    flags=" ".join(row.get("flags",[])) if row.get("flags") else ""
    card_cls="hc-card" if style=="hc" else "result-card"
    vwap_cls="vwap-above" if row.get("above_vwap") else "vwap-below"
    vwap_icon="✅" if row.get("above_vwap") else "⚠️"

    st.markdown(f"""
    <div class="{card_cls}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="ticker">#{i+1} {row['ticker']} {'🔥' if style=='hc' else ''}</span>
        <span class="{sc_cls}">⭐ {row['score']}</span>
      </div>
      {'<div style="font-size:0.75rem;margin:4px 0">'+flags+'</div>' if flags else ''}
      <div class="row-item">💰 <span class="row-val">${row['price']}</span> | VWAP: <span class="{vwap_cls}">{vwap_icon} ${row.get('vwap','-')} ({row.get('vwap_dist',0):+.1f}%)</span></div>
      <div class="row-item">📈 3M: <span class="{m3_cls}">{arrow}{abs(row['m3'])}%</span> | Vol: <span class="row-val">{row['vs']}x</span> | ADX: <span class="row-val">{row['adx']}</span> | טרנד: <span class="row-val">{row.get('trend_age',0)}d</span></div>
      <div class="row-item">RSI: <span class="row-val">{row['rsi']}</span> | MFI: <span class="row-val">{row['mfi']}</span> | OBV: <span class="row-val">{obv}</span> | SPY: <span class="row-val">{row['rs']:+.1f}%</span></div>
      <div class="row-item">📏 שיא 52W: <span class="row-val">${row['high52'] if row['high52'] and str(row['high52']) != 'nan' else 'N/A'}</span> (מרחק: {row.get('dist_52h','-')}%)</div>
      <div class="row-item">🛡️ כניסה: <span class="row-val">${row['price']}</span> | סטופ: <span class="negative">${row['stop']}</span> | יעד 1: <span class="positive">${row['target']}</span> | יעד 2: <span class="positive">${row['target2']}</span></div>
      <div class="row-item">📝 {row['setup']}</div>
    </div>""", unsafe_allow_html=True)

    if show_earnings and row.get("earnings_days") is not None:
        days=row["earnings_days"]; status=row.get("earnings_status","")
        color={"danger":"#ff7b72","warning":"#f0b429","caution":"#58a6ff"}.get(status,"#8b949e")
        icon={"danger":"🚨","warning":"⚠️","caution":"📅"}.get(status,"📅")
        st.markdown(f'<div class="earnings-warn" style="border-color:{color};color:{color}">{icon} דוח רווחים בעוד {days} ימים</div>',unsafe_allow_html=True)

def show_squeeze_card(i, row):
    st.markdown(f"""
    <div class="ss-card">
      <div style="display:flex;justify-content:space-between">
        <span class="ticker">#{i+1} {row['ticker']} 💥</span>
        <span style="color:#ff7b72;font-weight:700">Squeeze: {row['squeeze_score']}</span>
      </div>
      <div class="row-item">💰 ${row['price']} | Vol: <span class="row-val">{row['vs']}x</span> | RSI: <span class="row-val">{row['rsi']}</span></div>
      <div class="row-item">BB Width: {row['bb_width']}% | מיקום: {row['price_vs_bb']}% | 5D: <span class="positive">{row['m5']:+.1f}%</span></div>
      <div class="row-item">🛡️ סטופ: <span class="negative">${row['stop']}</span> | יעד: <span class="positive">${row['target']}</span></div>
      <div class="row-item">🔥 {row['reasons']}</div>
    </div>""", unsafe_allow_html=True)

def show_gap_card(i, row):
    cls="positive" if row["direction"]=="UP" else "negative"
    arrow="▲" if row["direction"]=="UP" else "▼"
    hold="✅ מחזיק" if row["holding"] else "⚠️ נחלש"
    st.markdown(f"""
    <div class="gap-card">
      <div style="display:flex;justify-content:space-between">
        <span class="ticker">#{i+1} {row['ticker']}</span>
        <span class="{cls}">{arrow} {abs(row['gap_pct'])}% גאפ</span>
      </div>
      <div class="row-item">אמש: ${row['prev_close']} → פתיחה: ${row['open']} → עכשיו: ${row['close']}</div>
      <div class="row-item">נפח: <span class="row-val">{row['vol_ratio']}x</span> | {hold}</div>
    </div>""", unsafe_allow_html=True)

def save_to_tracker(results, scan_date):
    if "tracker" not in st.session_state: st.session_state["tracker"]=[]
    for r in results[:5]:
        st.session_state["tracker"].append({
            "date":scan_date,"ticker":r["ticker"],
            "entry":r["price"],"target":r["target"],
            "stop":r["stop"],"score":r["score"],
        })

def show_tracker():
    if "tracker" not in st.session_state or not st.session_state["tracker"]:
        st.info("אין עסקאות במעקב. הרץ סריקה כדי להוסיף."); return
    for i,t in enumerate(st.session_state["tracker"]):
        try:
            cur=yf.download(t["ticker"],period="2d",auto_adjust=True,progress=False,threads=False)
            if isinstance(cur.columns,pd.MultiIndex): cur.columns=cur.columns.get_level_values(0)
            cur_price=float(cur["Close"].iloc[-1]) if not cur.empty else t["entry"]
        except: cur_price=t["entry"]
        pnl=round((cur_price-t["entry"])/t["entry"]*100,2)
        cls="positive" if pnl>0 else "negative"
        status="🎯 יעד" if cur_price>=t["target"] else "🛑 סטופ" if cur_price<=t["stop"] else "⏳ פתוח"
        st.markdown(f'<div class="tracker-row"><span class="ticker">{t["ticker"]}</span> | כניסה: ${t["entry"]} | עכשיו: ${cur_price:.2f} | <span class="{cls}">{"▲" if pnl>0 else "▼"}{abs(pnl)}%</span> | {status} | {t["date"]}</div>',unsafe_allow_html=True)
    if st.button("🗑️ נקה"): st.session_state["tracker"]=[]; st.rerun()

# ── MAIN ──────────────────────────────────────────────────────
def main():
    st.markdown('<div class="main-title">📈 SWING SCANNER PRO</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">Top-Down Analysis · {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)
    st.markdown("---")

    mode=st.radio("בחר מצב:", [
        "🔍 סריקה Top-Down (מומלץ)",
        "🔥 High Conviction",
        "💥 Short Squeeze",
        "📊 Gap & Go",
        "🎯 מניה בודדת + AI",
        "📋 מניות ספציפיות",
        "📈 Performance Tracker",
    ])

    # ── TOP-DOWN SCAN (Main mode) ─────────────────────────────
    if mode=="🔍 סריקה Top-Down (מומלץ)":
        top_n=st.slider("כמה מניות?",5,15,10)
        show_earn=st.checkbox("הצג אזהרות דוחות",value=True)
        n_sectors=st.slider("כמה מגזרים לסרוק?",1,5,3)

        if st.button("🔍 סרוק Top-Down"):
            # Phase 1: Market Regime
            with st.spinner("שלב 1/3 — בודק מצב שוק..."):
                regime=get_market_regime()
            show_regime(regime)

            if regime.get("regime")=="bearish":
                st.error("⛔ שוק דובי — לא מומלץ לפתוח לונגים. המשך בזהירות רבה.")

            # Phase 2: Sector Ranking
            with st.spinner("שלב 2/3 — מדרג מגזרים..."):
                sectors=get_sector_ranking()
            if sectors:
                st.markdown("---")
                show_sector_ranking(sectors)

            # Phase 3+4: Stock scan within top sectors
            st.markdown("---")
            top_sectors=sectors[:n_sectors]
            all_tickers=[]
            for s in top_sectors:
                for t in s["stocks"]:
                    if t not in all_tickers: all_tickers.append(t)

            include_midcap = st.checkbox("הוסף מניות צמיחה (MidCap) — מניות שאינן ב-S&P 500", value=False)
        if include_midcap:
            all_tickers = all_tickers + [t for t in MIDCAP_GROWTH if t not in all_tickers]
            st.info(f"שלב 3/3 — סורק {len(all_tickers)} מניות (כולל {len(MIDCAP_GROWTH)} מניות צמיחה)...")
        else:
            st.info(f"שלב 3/3 — סורק {len(all_tickers)} מניות מ-{n_sectors} מגזרים מובילים...")

            spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
            if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
            spy_c=spy["Close"]

            # sector score map
            sec_score_map={s["sector"]:s["score"] for s in sectors}

            prog=st.progress(0); results_s=[]; results_r=[]
            for i,t in enumerate(all_tickers):
                # find sector for this ticker
                t_sector=next((s["sector"] for s in top_sectors if t in s["stocks"]),"")
                sec_sc=sec_score_map.get(t_sector,0)
                r,_=analyse_stock(t,spy_c,strict=True,sector_score=sec_sc)
                if r:
                    r["sector"]=t_sector
                    results_s.append(r)
                else:
                    r2,_=analyse_stock(t,spy_c,strict=False,sector_score=sec_sc)
                    if r2 and r2["score"]>=55:
                        r2["sector"]=t_sector
                        results_r.append(r2)
                prog.progress((i+1)/len(all_tickers),text=f"סורק {t}...")
            prog.empty()

            results=results_s if results_s else results_r
            if not results: st.warning("לא נמצאו מניות."); return
            if not results_s: st.warning("תנאי שוק מאתגרים — מציג מועמדים עם פילטרים מקולים.")
            else: st.success(f"✅ {len(results_s)} מניות עברו את כל הפילטרים!")

            results.sort(key=lambda x:x["score"],reverse=True)
            sel=results[:top_n]

            if show_earn:
                for row in sel:
                    days,status=get_earnings_info(row["ticker"])
                    row["earnings_days"]=days; row["earnings_status"]=status

            for i,row in enumerate(sel): show_card(i,row,show_earnings=show_earn)
            save_to_tracker(sel,datetime.now().strftime("%d/%m"))
            csv=pd.DataFrame(sel).to_csv(index=False).encode()
            st.download_button("⬇️ CSV",data=csv,file_name=f"topdown_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")

    # ── HIGH CONVICTION ───────────────────────────────────────
    elif mode=="🔥 High Conviction":
        opt=st.radio("Universe:",["🚀 QQQ 100","⚡ S&P 500 — 150","🔍 Top-Down (מגזרים חזקים)"])
        st.info("ניקוד 68+ | ADX 25+ | Volume 1.5x+ | מומנטום 10%+ | מעל VWAP")

        if st.button("🔥 מצא High Conviction"):
            spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
            if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
            spy_c=spy["Close"]

            if "Top-Down" in opt:
                with st.spinner("טוען מגזרים..."):
                    sectors=get_sector_ranking()
                tickers=[t for s in sectors[:3] for t in s["stocks"]]
                sec_map={s["sector"]:s["score"] for s in sectors}
            elif "QQQ" in opt:
                tickers=[t for s in SECTOR_ETFS.values() for t in s[1]][:100]
                sec_map={}
            else:
                tickers=[t for s in SECTOR_ETFS.values() for t in s[1]][:150]
                sec_map={}

            prog=st.progress(0); hc=[]; all_r=[]
            for i,t in enumerate(tickers):
                sec_sc=sec_map.get(next((s for s,(_,stocks) in SECTOR_ETFS.items() if t in stocks),""),0)
                r,_=analyse_stock(t,spy_c,strict=True,sector_score=sec_sc)
                if r:
                    all_r.append(r)
                    if r["score"]>=68 and r["adx"]>=25 and r["vs"]>=1.5 and r["m3"]>=10:
                        days,status=get_earnings_info(t)
                        r["earnings_days"]=days; r["earnings_status"]=status
                        hc.append(r)
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()

            hc.sort(key=lambda x:x["score"],reverse=True); hc=hc[:3]
            if hc:
                st.success(f"🔥 {len(hc)} High Conviction!")
                for i,row in enumerate(hc): show_card(i,row,style="hc",show_earnings=True)
            elif all_r:
                all_r.sort(key=lambda x:x["score"],reverse=True)
                st.warning("לא נמצאו High Conviction מלאים — הטובות שנמצאו:")
                for i,row in enumerate(all_r[:3]): show_card(i,row,style="hc")
            else:
                st.warning("לא נמצאו מניות כלל.")

    # ── SHORT SQUEEZE ─────────────────────────────────────────
    elif mode=="💥 Short Squeeze":
        opt=st.radio("Universe:",["🚀 QQQ","⚡ S&P 500"])
        tickers=[t for s in SECTOR_ETFS.values() for t in s[1]]
        tickers=list(dict.fromkeys(tickers))[:100] if "QQQ" in opt else tickers[:150]
        st.info("BB Squeeze + נפח פתאומי + RSI עולה | סיכון גבוה")

        if st.button("💥 סרוק"):
            prog=st.progress(0); sq=[]
            for i,t in enumerate(tickers):
                r=analyse_squeeze(t)
                if r: sq.append(r)
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()
            sq.sort(key=lambda x:x["squeeze_score"],reverse=True); sq=sq[:5]
            if sq:
                st.success(f"💥 {len(sq)} מועמדות!")
                st.warning("⚠️ פוזיציה קטנה — סיכון גבוה!")
                for i,row in enumerate(sq): show_squeeze_card(i,row)
            else: st.warning("לא נמצאו. נסה בשעות מסחר.")

    # ── GAP & GO ──────────────────────────────────────────────
    elif mode=="📊 Gap & Go":
        opt=st.radio("Universe:",["🚀 QQQ","⚡ S&P 500"])
        tickers=list(dict.fromkeys([t for s in SECTOR_ETFS.values() for t in s[1]]))
        tickers=tickers[:100] if "QQQ" in opt else tickers[:150]
        st.info("מחפש גאפי פתיחה >1.5% על נפח גבוה — הרץ אחרי 16:30 ישראל")

        if st.button("📊 סרוק Gap & Go"):
            prog=st.progress(0); gaps=[]
            for i,t in enumerate(tickers):
                r=detect_gap(t)
                if r: gaps.append(r)
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()
            ups=[g for g in gaps if g["direction"]=="UP"]
            dns=[g for g in gaps if g["direction"]=="DOWN"]
            ups.sort(key=lambda x:x["gap_pct"],reverse=True)
            if ups:
                st.success(f"📊 {len(ups)} גאפי עלייה!")
                for i,r in enumerate(ups[:5]): show_gap_card(i,r)
            if dns:
                st.markdown("**גאפי ירידה:**")
                for i,r in enumerate(dns[:3]): show_gap_card(i,r)
            if not gaps: st.warning("לא נמצאו גאפים. נסה אחרי פתיחת שוק.")

    # ── SINGLE + AI ───────────────────────────────────────────
    elif mode=="🎯 מניה בודדת + AI":
        ticker_input=st.text_input("הכנס טיקר:","").strip().upper()
        api_key=st.text_input("מפתח API:",type="password")
        show_earn=st.checkbox("בדוק דוח רווחים",value=True)

        if st.button("🎯 נתח"):
            if not ticker_input: st.warning("הכנס טיקר"); return
            with st.spinner("טוען נתוני שוק..."):
                regime=get_market_regime()
                sectors=get_sector_ranking()
            show_regime(regime)

            spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
            if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
            with st.spinner(f"מנתח {ticker_input}..."):
                r,err=analyse_stock(ticker_input,spy["Close"],strict=False)
            if not r: st.error(f"שגיאה: {err}"); return

            if show_earn:
                days,status=get_earnings_info(ticker_input)
                r["earnings_days"]=days; r["earnings_status"]=status
            r["sector"]=next((s for s,(_,stocks) in SECTOR_ETFS.items() if ticker_input in stocks),"אחר")
            show_card(0,r,show_earnings=show_earn)

            if api_key:
                st.markdown("---")
                st.markdown("### 🤖 ניתוח AI מעמיק")
                with st.spinner("Claude מנתח... (עד 2 דקות)"):
                    analysis=ai_deep_analysis(r,api_key,regime=regime,sector_rank=sectors)
                    if "שגיאת חיבור" in analysis or "timed out" in analysis.lower():
                        st.info("מנסה שוב..."); analysis=ai_deep_analysis(r,api_key,regime=regime,sector_rank=sectors)
                html=re.sub(r'^## (.+)$',r'<h2>\1</h2>',analysis,flags=re.MULTILINE)
                html=re.sub(r'^### (.+)$',r'<h3>\1</h3>',html,flags=re.MULTILINE)
                html=html.replace("\n","<br>")
                st.markdown(f'<div class="ai-card">{html}</div>',unsafe_allow_html=True)
            else:
                st.info("💡 הוסף מפתח API לניתוח AI")

    # ── MULTIPLE ──────────────────────────────────────────────
    elif mode=="📋 מניות ספציפיות":
        custom=st.text_input("הכנס טיקרים (מופרדים בפסיק):","")
        show_earn=st.checkbox("בדוק דוחות",value=True)
        tickers=[t.strip().upper() for t in custom.split(",") if t.strip()] if custom else []

        if tickers:
            st.info(f"מנתח: {', '.join(tickers)}")
            st.caption("💡 טיפ: ניתן להכניס כל טיקר — כולל מניות צמיחה כמו SNOW, DDOG, PLTR, CRWD")
            if st.button("📋 נתח עכשיו"):
                spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
                if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
                spy_c=spy["Close"]
                prog=st.progress(0); results=[]; failures=[]
                for i,t in enumerate(tickers):
                    r,err=analyse_stock(t,spy_c,strict=False)
                    if r:
                        r["sector"]=next((s for s,(_,stocks) in SECTOR_ETFS.items() if t in stocks),"אחר")
                        if show_earn:
                            days,status=get_earnings_info(t)
                            r["earnings_days"]=days; r["earnings_status"]=status
                        results.append(r)
                    elif err: failures.append((t,err))
                    prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
                prog.empty()
                if not results: st.warning("לא ניתן לנתח."); return
                results.sort(key=lambda x:x["score"],reverse=True)
                st.success(f"✅ {len(results)} מניות")
                for i,row in enumerate(results): show_card(i,row,show_earnings=show_earn)
                for t,err in failures:
                    st.markdown(f'<div style="color:#8b949e;font-size:0.78rem">❌ {t} — {err}</div>',unsafe_allow_html=True)
                csv=pd.DataFrame(results).to_csv(index=False).encode()
                st.download_button("⬇️ CSV",data=csv,file_name=f"specific_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")
        else:
            st.warning("הכנס לפחות טיקר אחד")

    # ── TRACKER ───────────────────────────────────────────────
    elif mode=="📈 Performance Tracker":
        show_tracker()

    st.markdown('<div class="disclaimer">⚠️ <b>אזהרת סיכון</b> — למטרות לימוד בלבד. אין המלצת השקעה. לעולם אל תסכן יותר מ-1.5-2% מההון שלך בעסקה אחת.</div>',unsafe_allow_html=True)

if __name__=="__main__":
    main()
