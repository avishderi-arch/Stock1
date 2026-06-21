"""
Swing Scanner Pro v7 — Full Edition
מצבים: Top-Down Swing | High Conviction | Short Squeeze | Gap & Go
        מניה בודדת + AI | מניות ספציפיות | השקעה לטווח בינוני | Performance Tracker
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import re
from datetime import datetime

st.set_page_config(page_title="Swing Scanner Pro", page_icon="📈", layout="centered")

# ── Dynamic S&P 500 loader ────────────────────────────────────
@st.cache_data(ttl=86400)  # cache 24 hours
def load_sp500_full():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df = tables[0]
        col = next((c for c in df.columns if "symbol" in c.lower() or "ticker" in c.lower()), df.columns[0])
        tickers = df[col].str.replace(".", "-", regex=False).str.strip().tolist()
        return [t for t in tickers if t and len(t) <= 5]
    except:
        return []

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { background:#0a0e17 !important; color:#e6edf3 !important; font-family:'IBM Plex Mono',monospace; }
.main-title { color:#21ff87; font-size:1.9rem; font-weight:700; text-align:center; margin-bottom:4px; }
.sub-title  { color:#8b949e; font-size:0.82rem; text-align:center; margin-bottom:16px; }
.stButton > button {
    background:linear-gradient(135deg,#21ff87,#00d4ff) !important;
    color:#0a0e17 !important; font-weight:700 !important; font-size:1.1rem !important;
    border:none !important; border-radius:10px !important; padding:14px !important;
    width:100% !important; margin:10px 0 !important;
}
.regime-bull { background:#0d1a0d; border:2px solid #21ff87; border-radius:10px; padding:14px; margin:8px 0; color:#e6edf3; }
.regime-bear { background:#1a0d0d; border:2px solid #ff7b72; border-radius:10px; padding:14px; margin:8px 0; color:#e6edf3; }
.regime-neut { background:#1a1a0d; border:2px solid #f0b429; border-radius:10px; padding:14px; margin:8px 0; color:#e6edf3; }
.sector-card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:10px 14px; margin:4px 0; color:#e6edf3; font-size:0.85rem; }
.result-card { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:16px; margin:8px 0; color:#e6edf3; }
.hc-card     { background:#0d1117; border:2px solid #21ff87; border-radius:12px; padding:16px; margin:10px 0; color:#e6edf3; }
.ss-card     { background:#1a0d1a; border:2px solid #ff7b72; border-radius:12px; padding:16px; margin:10px 0; color:#e6edf3; }
.gap-card    { background:#0d1a1a; border:2px solid #00d4ff; border-radius:12px; padding:16px; margin:10px 0; color:#e6edf3; }
.value-card  { background:#0d1117; border:2px solid #f0b429; border-radius:12px; padding:16px; margin:10px 0; color:#e6edf3; }
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
.ticker   { color:#58a6ff; font-size:1.2rem; font-weight:700; }
.score-high { color:#21ff87; font-size:1rem; font-weight:700; }
.score-mid  { color:#f0b429; font-size:1rem; font-weight:700; }
.score-low  { color:#ff7b72; font-size:1rem; font-weight:700; }
.row-item { color:#c9d6df; font-size:0.82rem; margin:5px 0; }
.row-val  { color:#ffffff; font-weight:700; }
.positive { color:#21ff87; font-weight:600; }
.negative { color:#ff7b72; font-weight:600; }
.vwap-above { color:#21ff87; font-weight:700; }
.vwap-below { color:#ff7b72; font-weight:700; }
.disclaimer { background:#161b22; border-left:3px solid #ff7b72; border-radius:6px; padding:12px; margin-top:16px; font-size:0.72rem; color:#8b949e; }
.tracker-row { background:#161b22; border-radius:8px; padding:10px; margin:4px 0; font-size:0.8rem; color:#e6edf3; }
#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sector ETF Map ────────────────────────────────────────────
SECTOR_ETFS = {
    "Tech":      ("XLK",  ["AAPL","MSFT","NVDA","AVGO","ADBE","AMD","QCOM","TXN","KLAC","ADI","LRCX","MU","SNPS","CDNS","FTNT","ANET","PANW","INTC","CSCO","DELL","DDOG","CRWD","NOW","INTU","FICO","AMAT","WDAY","ZS","OKTA","NET"]),
    "Finance":   ("XLF",  ["JPM","BAC","WFC","MS","GS","AXP","BLK","SCHW","SPGI","CME","ICE","AJG","PGR","V","MA","BX","KKR","USB","TROW","BRK-B"]),
    "Health":    ("XLV",  ["UNH","JNJ","LLY","MRK","ABBV","TMO","ABT","AMGN","BMY","GILD","VRTX","CI","SYK","ISRG","BDX","REGN","DXCM","BIIB","IDXX","IQV","MRNA","HCA","HUM","MDT","EW","AXSM","RXRX"]),
    "Cons.Disc": ("XLY",  ["AMZN","TSLA","HD","MCD","NKE","LOW","BKNG","TJX","LULU","MAR","SBUX","ORLY","ROST","EBAY"]),
    "Comm":      ("XLC",  ["GOOGL","META","NFLX","DIS","CMCSA","T","VZ","TMUS","WBD"]),
    "Industrl":  ("XLI",  ["RTX","UPS","HON","CAT","DE","GD","NSC","UNP","LMT","GE","BA","MMM","CTAS","ITW"]),
    "Energy":    ("XLE",  ["XOM","CVX","EOG","SLB","COP","PSX","MPC","VLO","OXY","DVN","FANG"]),
    "Staples":   ("XLP",  ["PG","KO","PEP","WMT","COST","CL","PM","MO","KMB","GIS"]),
    "Materials": ("XLB",  ["LIN","APD","ECL","SHW","NEM","FCX","NUE","PPG","ALB"]),
    "Real Est":  ("XLRE", ["PLD","AMT","EQIX","CCI","SPG","DLR"]),
    "Utilities": ("XLU",  ["SO","DUK","NEE","AEP","EXC","XEL"]),
}

# ── MidCap / Growth Universe ──────────────────────────────────
MIDCAP_GROWTH = [
    "SNOW","PLTR","NET","BILL","GTLB","MDB","DDOG","TEAM","DUOL","ASAN",
    "PATH","AI","BBAI","SOUN","IONQ","COIN","HOOD","SOFI","UPST","AFRM",
    "RXRX","BEAM","CRSP","NTLA","EDIT","ACAD","AXSM","NVCR","MDGL","VKTX",
    "ENPH","FSLR","RUN","PLUG","BE","CHPT","EVGO","RIVN","LCID","WOLF",
    "AMBA","SITM","POWI","MTSI","ACLS","SQ","OPEN","LMND","CAVA","BROS",
    "WINGSTOP","SHAK","PTLO","XPOF","DKNG","PENN","LNW","GENI","ACMR",
]
MIDCAP_GROWTH = list(dict.fromkeys([t for t in MIDCAP_GROWTH if t and len(t)<=5]))

# ── Value / Dividend / ETF Universe (Long-Term) ───────────────
LONGTERM_ETFS = [
    # Core Market ETFs
    ("SPY",  "S&P 500 ETF",           "ETF"),
    ("QQQ",  "Nasdaq-100 ETF",        "ETF"),
    ("VTI",  "Total Market ETF",      "ETF"),
    ("IWM",  "Small Cap ETF",         "ETF"),
    ("DIA",  "Dow Jones ETF",         "ETF"),
    ("VEA",  "Developed Markets ETF", "ETF"),
    ("VWO",  "Emerging Markets ETF",  "ETF"),
    # Dividend / Value
    ("SCHD", "Dividend ETF",          "Dividend"),
    ("VYM",  "High Yield Dividend",   "Dividend"),
    ("DVY",  "Select Dividend",       "Dividend"),
    ("DGRO", "Dividend Growth",       "Dividend"),
    # Sector ETFs
    ("XLK",  "Tech Sector",           "Sector"),
    ("XLV",  "Health Sector",         "Sector"),
    ("XLF",  "Finance Sector",        "Sector"),
    ("XLE",  "Energy Sector",         "Sector"),
    ("XLY",  "Consumer Disc",         "Sector"),
    # Value Stocks
    ("BRK-B","Berkshire Hathaway",    "Value"),
    ("JNJ",  "Johnson & Johnson",     "Value"),
    ("PG",   "Procter & Gamble",      "Value"),
    ("KO",   "Coca-Cola",             "Value"),
    ("MCD",  "McDonald's",            "Value"),
    ("JPM",  "JPMorgan Chase",        "Value"),
    ("V",    "Visa",                  "Value"),
    ("MSFT", "Microsoft",             "Value"),
    ("AAPL", "Apple",                 "Value"),
    ("GOOGL","Alphabet",              "Value"),
]

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

def safe_float(val, default=0.0):
    try:
        f = float(val)
        return f if not np.isnan(f) else default
    except: return default

# ── Market Regime ─────────────────────────────────────────────
@st.cache_data(ttl=900)
def get_market_regime():
    try:
        spy=yf.download("SPY",period="6mo",auto_adjust=True,progress=False,threads=False)
        if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
        c=spy["Close"]
        price=safe_float(c.iloc[-1])
        sma50=safe_float(c.rolling(50).mean().iloc[-1])
        sma200=safe_float(c.rolling(200).mean().iloc[-1])
        rsi_v=safe_float(rsi(c).iloc[-1])
        ret_1m=safe_float(c.pct_change(21).iloc[-1])
        ret_5d=safe_float(c.pct_change(5).iloc[-1])
        above_50=price>sma50; above_200=price>sma200; golden=sma50>sma200
        try:
            vix=yf.download("^VIX",period="5d",auto_adjust=True,progress=False,threads=False)
            if isinstance(vix.columns,pd.MultiIndex): vix.columns=vix.columns.get_level_values(0)
            vix_val=safe_float(vix["Close"].iloc[-1],20.0)
        except: vix_val=20.0
        bull=sum([above_50,above_200,golden,rsi_v>50,ret_1m>0,ret_5d>0,vix_val<20])
        regime="bullish" if bull>=5 else "bearish" if bull<=2 else "neutral"
        return {"regime":regime,"spy_price":round(price,2),"sma50":round(sma50,2),
                "sma200":round(sma200,2),"above_50":above_50,"above_200":above_200,
                "golden":golden,"rsi":round(rsi_v,1),"ret_1m":round(ret_1m*100,1),
                "ret_5d":round(ret_5d*100,1),"vix":round(vix_val,1),"bull_signals":bull}
    except Exception as e: return {"regime":"unknown","error":str(e)}

# ── Sector Ranking ────────────────────────────────────────────
@st.cache_data(ttl=900)
def get_sector_ranking():
    try:
        # Download SPY
        import time; time.sleep(0.2)
        spy=yf.download("SPY",period="6mo",auto_adjust=True,progress=False,threads=False)
        if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
        if spy.empty or len(spy)<22:
            # Fallback: return sectors with stocks only, no relative strength
            return [{"sector":s,"etf":e,"ret_1m":0,"ret_5d":0,"rs_1m":0,"rs_5d":0,"score":0,"stocks":stks}
                    for s,(e,stks) in SECTOR_ETFS.items()]
        spy_ret_1m=safe_float(spy["Close"].pct_change(21).iloc[-1])
        spy_ret_5d=safe_float(spy["Close"].pct_change(5).iloc[-1])
        sectors=[]
        for sector,(etf,stocks) in SECTOR_ETFS.items():
            try:
                import time; time.sleep(0.3)
                df=yf.download(etf,period="3mo",auto_adjust=True,progress=False,threads=False)
                if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                if df.empty or len(df)<5:
                    sectors.append({"sector":sector,"etf":etf,"ret_1m":0,"ret_5d":0,
                        "rs_1m":0,"rs_5d":0,"score":0,"stocks":stocks})
                    continue
                r1m=safe_float(df["Close"].pct_change(min(21,len(df)-1)).iloc[-1])
                r5d=safe_float(df["Close"].pct_change(min(5,len(df)-1)).iloc[-1])
                rs1=r1m-spy_ret_1m; rs5=r5d-spy_ret_5d
                sectors.append({"sector":sector,"etf":etf,"ret_1m":round(r1m*100,1),
                    "ret_5d":round(r5d*100,1),"rs_1m":round(rs1*100,1),
                    "rs_5d":round(rs5*100,1),"score":round((0.6*rs1+0.4*rs5)*100,2),"stocks":stocks})
            except:
                sectors.append({"sector":sector,"etf":etf,"ret_1m":0,"ret_5d":0,
                    "rs_1m":0,"rs_5d":0,"score":0,"stocks":stocks})
        sectors.sort(key=lambda x:x["score"],reverse=True)
        return sectors
    except:
        # Full fallback - return all sectors with their stocks
        return [{"sector":s,"etf":e,"ret_1m":0,"ret_5d":0,"rs_1m":0,"rs_5d":0,"score":0,"stocks":stks}
                for s,(e,stks) in SECTOR_ETFS.items()]

# ── Market Sentiment Panel ───────────────────────────────────
@st.cache_data(ttl=1800)
def get_fear_greed():
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        if resp.status_code == 200:
            data = resp.json()["data"][0]
            return {"value": int(data["value"]), "label": data["value_classification"]}
    except: pass
    return None

@st.cache_data(ttl=1800)
def get_put_call():
    try:
        vix = yf.download("^VIX", period="5d", auto_adjust=True, progress=False, threads=False)
        vix3m = yf.download("^VIX3M", period="5d", auto_adjust=True, progress=False, threads=False)
        if isinstance(vix.columns, pd.MultiIndex): vix.columns = vix.columns.get_level_values(0)
        if isinstance(vix3m.columns, pd.MultiIndex): vix3m.columns = vix3m.columns.get_level_values(0)
        vix_val = float(vix["Close"].iloc[-1])
        vix3m_val = float(vix3m["Close"].iloc[-1]) if not vix3m.empty else vix_val * 1.1
        ratio = round(vix_val / vix3m_val, 3)
        sentiment = "פחד" if ratio > 1 else "ניטרלי" if ratio > 0.85 else "חמדנות"
        return {"vix": round(vix_val,1), "vix3m": round(vix3m_val,1), "ratio": ratio, "sentiment": sentiment}
    except: return None

@st.cache_data(ttl=3600)
def get_market_breadth():
    try:
        sample = ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","JPM","UNH","XOM",
                  "V","LLY","AVGO","JNJ","MA","PG","HD","MRK","CVX","ABBV","COST","PEP",
                  "KO","WMT","BAC","ADBE","ACN","MCD","TMO","CSCO","ABT","NKE","WFC","TXN"]
        up=0; down=0; above_50=0; above_200=0
        for t in sample:
            try:
                df=yf.download(t,period="3mo",auto_adjust=True,progress=False,threads=False)
                if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                if len(df)<5: continue
                c=df["Close"]
                if float(c.pct_change(1).iloc[-1])>0: up+=1
                else: down+=1
                if len(c)>=50 and float(c.iloc[-1])>float(c.rolling(50).mean().iloc[-1]): above_50+=1
                if len(c)>=200 and float(c.iloc[-1])>float(c.rolling(200).mean().iloc[-1]): above_200+=1
            except: pass
        total=up+down
        return {"up":up,"down":down,"total":total,
            "adv_pct":round(up/total*100) if total>0 else 50,
            "above_50_pct":round(above_50/total*100) if total>0 else 50,
            "above_200_pct":round(above_200/total*100) if total>0 else 50}
    except: return None

def show_sentiment_panel(fg=None, pc=None, breadth=None):
    st.markdown("### 🧭 מנטליות השוק")
    cols=st.columns(3)
    with cols[0]:
        if fg:
            v=fg["value"]
            c="#ff7b72" if v<30 else "#21ff87" if v>70 else "#f0b429"
            lbl={"Extreme Fear":"פחד קיצוני","Fear":"פחד","Neutral":"ניטרלי","Greed":"חמדנות","Extreme Greed":"חמדנות קיצונית"}.get(fg["label"],fg["label"])
            st.markdown(f'''<div style="background:#161b22;border:1px solid {c};border-radius:8px;padding:12px;text-align:center"><div style="color:{c};font-size:1.5rem;font-weight:700">{v}</div><div style="color:{c};font-size:0.75rem">{lbl}</div><div style="color:#8b949e;font-size:0.7rem">Fear & Greed</div></div>''',unsafe_allow_html=True)
        else:
            st.markdown('''<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center;color:#8b949e">F&G N/A</div>''',unsafe_allow_html=True)
    with cols[1]:
        if pc:
            c="#ff7b72" if pc["ratio"]>1 else "#21ff87" if pc["ratio"]<0.85 else "#f0b429"
            st.markdown(f'''<div style="background:#161b22;border:1px solid {c};border-radius:8px;padding:12px;text-align:center"><div style="color:{c};font-size:1.5rem;font-weight:700">{pc["ratio"]}</div><div style="color:{c};font-size:0.75rem">{pc["sentiment"]}</div><div style="color:#8b949e;font-size:0.7rem">VIX/VIX3M</div></div>''',unsafe_allow_html=True)
        else:
            st.markdown('''<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center;color:#8b949e">VIX N/A</div>''',unsafe_allow_html=True)
    with cols[2]:
        if breadth:
            c="#21ff87" if breadth["adv_pct"]>60 else "#ff7b72" if breadth["adv_pct"]<40 else "#f0b429"
            st.markdown(f'''<div style="background:#161b22;border:1px solid {c};border-radius:8px;padding:12px;text-align:center"><div style="color:{c};font-size:1.5rem;font-weight:700">{breadth["adv_pct"]}%</div><div style="color:#8b949e;font-size:0.75rem">\u2191{breadth["up"]} \u2193{breadth["down"]}</div><div style="color:#8b949e;font-size:0.7rem">רוחב שוק</div></div>''',unsafe_allow_html=True)
        else:
            st.markdown('''<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;text-align:center;color:#8b949e">Breadth N/A</div>''',unsafe_allow_html=True)
    if fg and pc:
        bull=sum([fg["value"]>50, pc["ratio"]<1, breadth["adv_pct"]>50 if breadth else False])
        c="#21ff87" if bull>=2 else "#ff7b72"
        txt="✅ מנטליות חיובית — תומכת בלונגים" if bull>=2 else "⚠️ מנטליות שלילית — זהירות"
        st.markdown(f'''<div style="color:{c};font-size:0.85rem;margin-top:8px;text-align:center">{txt}</div>''',unsafe_allow_html=True)
    if breadth:
        st.markdown(f'''<div style="color:#8b949e;font-size:0.72rem;text-align:center">מעל SMA50: {breadth["above_50_pct"]}% | מעל SMA200: {breadth["above_200_pct"]}%</div>''',unsafe_allow_html=True)
    st.markdown("---")

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
        if days<0:   return None,"passed"
        if days<=3:  return days,"danger"
        if days<=7:  return days,"warning"
        if days<=14: return days,"caution"
        return days,"safe"
    except: return None,"unknown"


# ── News & Catalyst Detection ─────────────────────────────────
def get_stock_news(ticker, max_items=5):
    try:
        t = yf.Ticker(ticker)
        news = t.news
        if not news: return []
        items = []
        for n in news[:max_items]:
            title = n.get("title", "")
            publisher = n.get("publisher", "")
            ts = n.get("providerPublishTime", 0)
            age_hours = round((datetime.now().timestamp() - ts) / 3600) if ts else 0
            items.append({
                "title": title, "publisher": publisher,
                "age_hours": age_hours,
                "age_str": f"{age_hours}h" if age_hours < 48 else f"{age_hours//24}d"
            })
        return items
    except: return []

def detect_catalyst(news_items):
    if not news_items: return "neutral", []
    positive_kw = ["contract","deal","partnership","upgrade","beat","raises guidance",
        "acquisition","fda approval","approved","wins","awarded","record",
        "buyback","dividend","collaboration","agreement","milestone"]
    negative_kw = ["downgrade","misses","cuts guidance","lawsuit","investigation",
        "recall","warning","layoffs","delay","rejected","probe","loss"]
    pos=0; neg=0; catalysts=[]
    for n in news_items:
        tl = n["title"].lower()
        for kw in positive_kw:
            if kw in tl:
                pos+=1; catalysts.append(("🟢", n["title"][:65], n["age_str"])); break
        for kw in negative_kw:
            if kw in tl:
                neg+=1; catalysts.append(("🔴", n["title"][:65], n["age_str"])); break
    sentiment = "positive" if pos>neg else "negative" if neg>pos else "neutral"
    return sentiment, catalysts[:3]

def show_news_card(ticker, news_items, sentiment, catalysts):
    if not news_items: return
    bc = "#21ff87" if sentiment=="positive" else "#ff7b72" if sentiment=="negative" else "#30363d"
    sl = {"positive":"🟢 קטליזטור חיובי","negative":"🔴 סיכון בחדשות","neutral":"⚪ ניטרלי"}.get(sentiment,"")
    html = f'''<div style="background:#0d1117;border:1px solid {bc};border-radius:8px;padding:12px;margin:6px 0">'''
    html += f'''<div style="color:#e6edf3;font-weight:700;margin-bottom:8px">📰 חדשות — {ticker} <span style="color:{bc};font-size:0.8rem">{sl}</span></div>'''
    for n in news_items[:4]:
        ac = "#21ff87" if n["age_hours"]<24 else "#8b949e"
        html += f'''<div style="margin:3px 0;font-size:0.78rem"><span style="color:{ac}">[{n["age_str"]}]</span> <span style="color:#c9d6df">{n["title"][:72]}</span></div>'''
    if catalysts:
        html += '''<div style="margin-top:8px;padding-top:8px;border-top:1px solid #30363d">'''
        for icon,title,age in catalysts:
            html += f'''<div style="font-size:0.78rem;margin:2px 0">{icon} <span style="color:#e6edf3">{title}</span> <span style="color:#8b949e">({age})</span></div>'''
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Conviction Score (Layer 2) ───────────────────────────────
def get_conviction_data(ticker):
    """Fetch analyst data and institutional ownership via yfinance"""
    result = {
        "analyst_rating": 0,      # 1-5 (1=Strong Buy, 5=Strong Sell)
        "analyst_count": 0,
        "price_target": 0,
        "price_target_upside": 0,
        "inst_ownership_pct": 0,
        "recommendation": "N/A",
        "conviction_score": 0,
        "conviction_notes": [],
    }
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # Analyst recommendation
        rec = info.get("recommendationMean", 0)
        rec_key = info.get("recommendationKey", "none")
        num_analysts = info.get("numberOfAnalystOpinions", 0)
        result["analyst_rating"] = round(rec, 2) if rec else 0
        result["analyst_count"] = num_analysts
        result["recommendation"] = rec_key

        # Price target
        target = info.get("targetMeanPrice", 0)
        current = info.get("currentPrice", 0) or info.get("regularMarketPrice", 0)
        if target and current and current > 0:
            upside = round((target - current) / current * 100, 1)
            result["price_target"] = round(target, 2)
            result["price_target_upside"] = upside

        # Institutional ownership
        inst_pct = info.get("institutionOwnershipPercent", 0) or info.get("institutionsPercentHeld", 0)
        if inst_pct:
            result["inst_ownership_pct"] = round(inst_pct * 100, 1)

        # Calculate conviction score
        score = 0
        notes = []

        # Analyst score (1=Strong Buy gets 25pts, 3=Hold gets 5pts, 5=Sell gets 0)
        if rec > 0:
            analyst_pts = max(0, round((3.5 - rec) * 12))
            score += analyst_pts
            if rec <= 1.5:
                notes.append(f"💎 Strong Buy ({num_analysts} אנליסטים)")
            elif rec <= 2.5:
                notes.append(f"✅ Buy ({num_analysts} אנליסטים)")
            elif rec <= 3.0:
                notes.append(f"⚪ Hold ({num_analysts} אנליסטים)")

        # Price target upside
        upside = result["price_target_upside"]
        if upside > 25:
            score += 25; notes.append(f"🎯 יעד אנליסטים +{upside}%")
        elif upside > 15:
            score += 15; notes.append(f"🎯 יעד +{upside}%")
        elif upside > 5:
            score += 8

        # Institutional ownership
        inst = result["inst_ownership_pct"]
        if inst > 70:
            score += 15; notes.append(f"🏦 בעלות מוסדית {inst}%")
        elif inst > 50:
            score += 10; notes.append(f"🏦 מוסדיים {inst}%")
        elif inst > 30:
            score += 5

        result["conviction_score"] = min(score, 65)
        result["conviction_notes"] = notes[:3]
    except: pass
    return result

def show_conviction_badge(cv_data):
    """Show conviction score badge"""
    score = cv_data.get("conviction_score", 0)
    if score == 0: return
    color = "#21ff87" if score >= 40 else "#f0b429" if score >= 20 else "#8b949e"
    label = "HIGH CONVICTION" if score >= 40 else "MODERATE" if score >= 20 else "LOW"
    rec = cv_data.get("recommendation", "").replace("strongBuy","Strong Buy").replace("buy","Buy").replace("hold","Hold").replace("sell","Sell")
    upside = cv_data.get("price_target_upside", 0)
    inst = cv_data.get("inst_ownership_pct", 0)
    notes = " | ".join(cv_data.get("conviction_notes", []))

    html = (
        f'<div style="background:#0d1117;border:2px solid {color};border-radius:8px;'
        f'padding:10px 14px;margin:6px 0">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span style="color:{color};font-weight:700;font-size:0.9rem">🎯 {label}</span>'
        f'<span style="color:{color};font-size:1.1rem;font-weight:700">{score}/65</span>'
        f'</div>'
        f'<div style="color:#c9d6df;font-size:0.78rem;margin-top:4px">'
        f'{"📊 " + rec if rec and rec != "none" else ""}'
        f'{" | 🎯 יעד +" + str(upside) + "%" if upside > 0 else ""}'
        f'{" | 🏦 " + str(inst) + "%" if inst > 0 else ""}'
        f'</div>'
        f'{"<div style=\"color:#8b949e;font-size:0.75rem;margin-top:3px\">" + notes + "</div>" if notes else ""}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

# ── Analyst Upgrade Detector ──────────────────────────────────
UPGRADE_SCORE_BONUS = 8     # בונוס לציון בעת שדרוג אנליסט אחרון (10 ימים)
DOWNGRADE_SCORE_PENALTY = -5  # קנס בעת הורדת דירוג אחרונה

@st.cache_data(ttl=21600, show_spinner=False)
def get_recent_upgrades(ticker, days_back=10):
    """שדרוגי/הורדות דירוג אנליסטים מהימים האחרונים (yfinance upgrades_downgrades)"""
    try:
        t = yf.Ticker(ticker)
        df = t.upgrades_downgrades
        if df is None or (hasattr(df, "empty") and df.empty): return []
        df = df.reset_index()
        df["GradeDate"] = pd.to_datetime(df["GradeDate"])
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days_back)
        recent = df[df["GradeDate"] >= cutoff].sort_values("GradeDate", ascending=False)

        upgrade_kw = ["buy", "outperform", "overweight", "strong buy", "accumulate"]
        downgrade_kw = ["sell", "underperform", "underweight", "reduce"]
        out = []
        for _, row in recent.iterrows():
            action = str(row.get("Action", "")).lower()
            to_g = str(row.get("ToGrade", "")); to_l = to_g.lower()
            from_g = str(row.get("FromGrade", ""))
            if action == "up" or (any(k in to_l for k in upgrade_kw) and not any(k in to_l for k in downgrade_kw)):
                direction = "up"
            elif action == "down" or any(k in to_l for k in downgrade_kw):
                direction = "down"
            else:
                direction = "other"
            out.append({
                "date": row["GradeDate"].strftime("%d/%m"),
                "firm": str(row.get("Firm", "")),
                "from": "" if from_g.lower() in ("nan", "none", "") else from_g,
                "to": to_g,
                "direction": direction,
            })
        return out
    except Exception:
        return []

def show_upgrade_badge(upgrades, bonus=0):
    """מציג badge לשדרוג/הורדת דירוג אנליסט אחרון, אם קיים בחלון הזמן"""
    if not upgrades: return
    ups = [u for u in upgrades if u["direction"] == "up"]
    downs = [u for u in upgrades if u["direction"] == "down"]
    if not ups and not downs: return

    if ups:
        u = ups[0]
        frm = f"{u['from']} → " if u["from"] else ""
        extra = f" | +{len(ups)-1} שדרוגים נוספים" if len(ups) > 1 else ""
        bonus_txt = f' | <span style="color:#21ff87">⭐ +{bonus} לניקוד</span>' if bonus > 0 else ""
        st.markdown(
            f'<div style="background:#0d1a0d;border:2px solid #21ff87;border-radius:8px;'
            f'padding:8px 12px;margin:4px 0;font-size:0.8rem;color:#e6edf3">'
            f'🆙 <b style="color:#21ff87">שדרוג אנליסט</b> ({u["date"]}): {u["firm"]} '
            f'{frm}<b>{u["to"]}</b>{extra}{bonus_txt}</div>',
            unsafe_allow_html=True,
        )
    if downs:
        d = downs[0]
        frm = f"{d['from']} → " if d["from"] else ""
        bonus_txt = f' | <span style="color:#ff7b72">⬇️ {bonus} לניקוד</span>' if bonus < 0 else ""
        st.markdown(
            f'<div style="background:#1a0d0d;border:2px solid #ff7b72;border-radius:8px;'
            f'padding:8px 12px;margin:4px 0;font-size:0.8rem;color:#e6edf3">'
            f'⚠️ <b style="color:#ff7b72">הורדת דירוג</b> ({d["date"]}): {d["firm"]} '
            f'{frm}<b>{d["to"]}</b>{bonus_txt}</div>',
            unsafe_allow_html=True,
        )

# ── Core Stock Analysis ───────────────────────────────────────
def analyse_stock(ticker, spy_close, strict=True, sector_score=0):
    try:
        import time
        time.sleep(0.1)  # Rate limit protection
        raw=yf.download(ticker,period="1y",auto_adjust=True,progress=False,threads=False)
        if raw.empty or len(raw)<60: return None,"insufficient_data"
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        c=raw["Close"]; h=raw["High"]; l=raw["Low"]; v=raw["Volume"]
        price=safe_float(c.iloc[-1])
        if price<=0: return None,"invalid_price"
        avg_vol=safe_float(v.rolling(20).mean().iloc[-1])
        vs=safe_float(v.iloc[-1]/avg_vol) if avg_vol>0 else 0
        sma20=safe_float(c.rolling(20).mean().iloc[-1])
        sma50=safe_float(c.rolling(50).mean().iloc[-1])
        sma200=safe_float(c.rolling(200).mean().iloc[-1])
        rsi_v=safe_float(rsi(c).iloc[-1])
        mh=macd_hist(c); mh_v=safe_float(mh.iloc[-1]); mh_p=safe_float(mh.iloc[-2])
        adx_v=safe_float(adx(h,l,c).iloc[-1])
        obv=(np.sign(c.diff()).fillna(0)*v).cumsum(); obv_s=slope(obv.tail(20))
        mfi_v=safe_float(mfi(h,l,c,v).iloc[-1])
        atr_v=safe_float(calc_atr(h,l,c).iloc[-1])
        m1=safe_float(c.pct_change(21).iloc[-1])
        m3=safe_float(c.pct_change(63).iloc[-1])
        atr_pct=atr_v/price*100 if price>0 else 0
        # 52W High/Low
        h52s=c.rolling(min(252,len(c))).max(); l52s=c.rolling(min(252,len(c))).min()
        high52=safe_float(h52s.iloc[-1], price)
        low52=safe_float(l52s.iloc[-1], price)
        dist_52h=(high52-price)/high52*100 if high52>0 else 0
        # VWAP (20-day rolling)
        tp=(h+l+c)/3
        vwap_num=(tp*v).rolling(20).sum()
        vwap_den=v.rolling(20).sum().replace(0,np.nan)
        vwap_series=vwap_num/vwap_den
        vwap_val=safe_float(vwap_series.iloc[-1])
        if vwap_val<=0 or np.isnan(vwap_val): vwap_val=sma20
        above_vwap=price>vwap_val
        vwap_dist=round((price-vwap_val)/vwap_val*100,1) if vwap_val>0 else 0
        # RS vs SPY
        al=spy_close.reindex(c.index,method="ffill")
        rs_spy=safe_float(c.pct_change(20).iloc[-1])-safe_float(al.pct_change(20).iloc[-1]) if len(al)>=21 else 0.01
        # Trend age
        above_s50=c>c.rolling(50).mean()
        trend_age=int(above_s50[::-1].cumprod().sum()) if above_s50.iloc[-1] else 0

        if strict:
            if price<10:            return None,"מחיר נמוך"
            if avg_vol<400000:      return None,"נפח נמוך"
            if price<=sma50:        return None,"מתחת SMA50"
            if sma50<=sma200:       return None,"SMA50 מתחת SMA200"
            if not(38<=rsi_v<=74):  return None,f"RSI {rsi_v:.0f}"
            if mh_v<=0:             return None,"MACD שלילי"
            if adx_v<18:            return None,f"ADX {adx_v:.0f}"
            if vs<1.2:              return None,f"נפח {vs:.1f}x"
            if obv_s<=0:            return None,"OBV יורד"
            if mfi_v<48:            return None,f"MFI {mfi_v:.0f}"
            if rs_spy<=0:           return None,"מפגר SPY"
            if atr_pct>10:          return None,"תנודתיות קיצונית"

        # Scoring
        ms=0.35*sig(m1,.05,.10)+0.65*sig(m3,.12,.15)
        vs2=0.55*clamp((vs-1.2)/(3-1.2)*100)+0.45*sig(obv_s,0,1e6)
        ma=(sma50-sma200)/sma200 if sma200>0 else 0
        ts=0.60*clamp((adx_v-18)/(60-18)*100)+0.40*sig(ma,.02,.04)
        mfs=clamp((mfi_v-48)/(90-48)*100)
        ras=sig(m3/max(atr_pct/100,0.005),2,3)
        rss=sig(rs_spy,.02,.05)
        vwap_bonus=8 if above_vwap and vwap_dist<3 else 4 if above_vwap else -5
        sec_bonus=min(sector_score*1.5,12) if sector_score>0 else 0
        h52_bonus=10 if dist_52h<2 else 5 if dist_52h<6 else 0
        trend_bonus=min(trend_age/30*6,8)
        base=0.28*ms+0.23*vs2+0.20*ts+0.14*mfs+0.10*ras+0.05*rss
        # Volume trend over 5 days (rel vol trend)
        vol_trend_5d = slope(v.tail(5)/avg_vol if avg_vol>0 else v.tail(5))
        vol_trend_bonus = 5 if vol_trend_5d > 0.1 else 0
        # Pullback quality: price between SMA20 and SMA50 = healthy pullback
        pullback_bonus = 6 if sma50 < price < sma20*1.05 and price > sma50 else 0
        comp=clamp(base+vwap_bonus+sec_bonus+h52_bonus/10+trend_bonus/10+vol_trend_bonus+pullback_bonus)

        notes=[]
        if above_vwap:   notes.append(f"מעל VWAP (+{vwap_dist}%)")
        if m3>0.15:      notes.append("מומנטום חזק 3M")
        if vs>2.0:       notes.append("נפח גבוה")
        if adx_v>35:     notes.append("טרנד חזק")
        if mfi_v>65:     notes.append("קנייה מוסדית")
        if dist_52h<3:   notes.append("קרוב לשיא 52W")
        if sec_bonus>8:  notes.append("סקטור מוביל")
        if not notes:    notes=["סטאפ רב-גורמי"]

        stop=price-2.0*atr_v; rsk=max(price-stop,0.01)
        shares=max(0,int(min(100000*(1.75/100)/rsk,100000*0.10/price)))
        target=price+2.0*rsk; target2=price+3.5*rsk

        flags=[]
        if not above_vwap: flags.append("⚠️ מתחת VWAP")
        if rsi_v>70:       flags.append(f"⚠️ RSI קנוי ({rsi_v:.0f})")
        if vs<1.2:         flags.append("⚠️ נפח נמוך")
        if atr_pct>6:      flags.append(f"⚠️ תנודתי {atr_pct:.1f}%")

        return {"ticker":ticker,"price":round(price,2),"score":round(comp,1),
            "sma20":round(sma20,2),"sma50":round(sma50,2),"sma200":round(sma200,2),
            "vwap":round(vwap_val,2),"above_vwap":above_vwap,"vwap_dist":vwap_dist,
            "m1":round(m1*100,1),"m3":round(m3*100,1),"vs":round(vs,2),
            "rsi":round(rsi_v,1),"mfi":round(mfi_v,1),"adx":round(adx_v,1),
            "macd_hist":round(mh_v,4),"obv_up":obv_s>0,"rs":round(rs_spy*100,1),
            "atr":round(atr_v,2),"atr_pct":round(atr_pct,1),
            "high52":round(high52,2),"low52":round(low52,2),"dist_52h":round(dist_52h,1),
            "trend_age":trend_age,"avg_vol":int(avg_vol),
            "setup":"; ".join(notes[:2]),"stop":round(stop,2),
            "target":round(target,2),"target2":round(target2,2),
            "shares":shares,"flags":flags}, None
    except Exception as e: return None,str(e)[:40]

# ── Long-Term Analysis ────────────────────────────────────────
def analyse_longterm(ticker, name, category):
    try:
        raw=yf.download(ticker,period="3y",auto_adjust=True,progress=False,threads=False)
        if raw.empty or len(raw)<60: return None
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        c=raw["Close"]; v=raw["Volume"]
        price=safe_float(c.iloc[-1])
        if price<=0: return None
        sma50=safe_float(c.rolling(50).mean().iloc[-1])
        sma200=safe_float(c.rolling(200).mean().iloc[-1])
        rsi_v=safe_float(rsi(c).iloc[-1])
        ret_1y=safe_float(c.pct_change(252).iloc[-1]) if len(c)>=252 else 0
        ret_6m=safe_float(c.pct_change(126).iloc[-1]) if len(c)>=126 else 0
        ret_3m=safe_float(c.pct_change(63).iloc[-1]) if len(c)>=63 else 0
        # Trend quality
        above_200=price>sma200
        golden=sma50>sma200
        # Volatility (annual)
        vol_annual=safe_float(c.pct_change().std()*np.sqrt(252)*100)
        # Drawdown from high
        rolling_max=c.rolling(252).max()
        drawdown=safe_float((c-rolling_max)/rolling_max*100).iloc[-1] if len(c)>=252 else 0
        # Score for long-term
        score=0
        if above_200: score+=25
        if golden:    score+=20
        if ret_1y>0:  score+=min(ret_1y*100,20)
        if ret_3m>0:  score+=min(ret_3m*100,15)
        if rsi_v<70:  score+=10
        if vol_annual<20: score+=10
        score=clamp(score)

        # Dividend info
        try:
            t=yf.Ticker(ticker)
            info=t.info
            div_yield=safe_float(info.get("dividendYield",0))*100
            pe=safe_float(info.get("trailingPE",0))
        except: div_yield=0; pe=0

        return {"ticker":ticker,"name":name,"category":category,
            "price":round(price,2),"score":round(score,1),
            "ret_1y":round(ret_1y*100,1),"ret_6m":round(ret_6m*100,1),
            "ret_3m":round(ret_3m*100,1),"rsi":round(rsi_v,1),
            "sma50":round(sma50,2),"sma200":round(sma200,2),
            "above_200":above_200,"golden":golden,
            "vol_annual":round(vol_annual,1),"drawdown":round(drawdown,1),
            "div_yield":round(div_yield,2),"pe":round(pe,1)}
    except: return None

# ── Short Squeeze ─────────────────────────────────────────────
def analyse_squeeze(ticker):
    try:
        raw=yf.download(ticker,period="6mo",auto_adjust=True,progress=False,threads=False)
        if raw.empty or len(raw)<30: return None
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        c=raw["Close"]; h=raw["High"]; l=raw["Low"]; v=raw["Volume"]
        price=safe_float(c.iloc[-1]); avg_vol=safe_float(v.rolling(20).mean().iloc[-1])
        vs=safe_float(v.iloc[-1]/avg_vol) if avg_vol>0 else 0
        rsi_v=safe_float(rsi(c).iloc[-1]); atr_v=safe_float(calc_atr(h,l,c).iloc[-1])
        sma20=c.rolling(20).mean(); std20=c.rolling(20).std()
        bb_upper=safe_float((sma20+2*std20).iloc[-1]); bb_lower=safe_float((sma20-2*std20).iloc[-1])
        bb_w=safe_float(sma20.iloc[-1]); bb_width=round((bb_upper-bb_lower)/bb_w*100,1) if bb_w>0 else 0
        pvbb=round((price-bb_lower)/(bb_upper-bb_lower)*100,1) if (bb_upper-bb_lower)>0 else 50
        rsi_trend=slope(rsi(c).tail(5))
        m5=safe_float(c.pct_change(5).iloc[-1]); m10=safe_float(c.pct_change(10).iloc[-1])
        score=0; reasons=[]
        if vs>2.0:    score+=30; reasons.append(f"נפח {vs:.1f}x")
        elif vs>1.5:  score+=15; reasons.append(f"נפח {vs:.1f}x")
        if rsi_v>60:  score+=20; reasons.append(f"RSI {rsi_v:.0f}")
        if rsi_trend>0: score+=10; reasons.append("RSI עולה")
        if m5>0.03:   score+=15; reasons.append(f"5D +{m5*100:.1f}%")
        if m10>0.05:  score+=10; reasons.append(f"10D +{m10*100:.1f}%")
        if pvbb>75:   score+=15; reasons.append("שובר BB")
        if bb_width<10: score+=15; reasons.append("BB Squeeze")
        if score<40 or price<5 or avg_vol<200000: return None
        return {"ticker":ticker,"price":round(price,2),"squeeze_score":min(score,100),
            "vs":round(vs,2),"rsi":round(rsi_v,1),"bb_width":bb_width,"price_vs_bb":pvbb,
            "m5":round(m5*100,1),"m10":round(m10*100,1),"reasons":"; ".join(reasons[:3]),
            "stop":round(price-2.0*atr_v,2),"target":round(price*1.10,2)}
    except: return None

# ── Gap Detection ─────────────────────────────────────────────
def detect_gap(ticker):
    try:
        df=yf.download(ticker,period="5d",auto_adjust=True,progress=False,threads=False)
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        if len(df)<2: return None
        prev=safe_float(df["Close"].iloc[-2]); opn=safe_float(df["Open"].iloc[-1])
        cls=safe_float(df["Close"].iloc[-1])
        gap=(opn-prev)/prev*100 if prev>0 else 0
        avg_v=safe_float(df["Volume"].rolling(5).mean().iloc[-1])
        vr=safe_float(df["Volume"].iloc[-1])/avg_v if avg_v>0 else 0
        if abs(gap)<1.5 or vr<1.5: return None
        return {"ticker":ticker,"gap_pct":round(gap,2),"direction":"UP" if gap>0 else "DOWN",
            "vol_ratio":round(vr,2),"prev_close":round(prev,2),"open":round(opn,2),
            "close":round(cls,2),"holding":cls>opn if gap>0 else cls<opn}
    except: return None

# ── AI Analysis ───────────────────────────────────────────────
def ai_deep_analysis(data, api_key, regime=None, sectors=None):
    regime_ctx=f"מצב שוק: {regime.get('regime','?')} | SPY: ${regime.get('spy_price','?')} | VIX: {regime.get('vix','?')} | RSI SPY: {regime.get('rsi','?')} | חודש: {regime.get('ret_1m','?')}%" if regime else ""
    if sectors:
        top3_str = ", ".join([s['sector'] + " (" + f"{s['rs_1m']:+.1f}%" + ")" for s in sectors[:3]])
        sector_ctx = "סקטורים מובילים: " + top3_str
    else:
        sector_ctx = ""
    # Build news + conviction context for AI
    news_items_ai = get_stock_news(data.get("ticker",""))
    cat_sent_ai, cats_ai = detect_catalyst(news_items_ai)
    cv_ai = get_conviction_data(data.get("ticker",""))
    news_ctx = ""
    if news_items_ai:
        headlines = " | ".join([n["title"][:50] for n in news_items_ai[:3]])
        news_ctx = f"חדשות אחרונות: {headlines}"
        if cats_ai:
            news_ctx += "\nקטליזטורים: " + " | ".join([f"{i} {t}" for i,t,_ in cats_ai])
    conviction_ctx = ""
    if cv_ai.get("analyst_count",0) > 0:
        conviction_ctx = (
            f"המלצת אנליסטים: {cv_ai.get('recommendation','N/A')} "
            f"({cv_ai.get('analyst_count',0)} אנליסטים) | "
            f"יעד מחיר: ${cv_ai.get('price_target',0)} "
            f"(אפסייד: {cv_ai.get('price_target_upside',0)}%) | "
            f"בעלות מוסדית: {cv_ai.get('inst_ownership_pct',0)}%"
        )
    upgrades_ai = get_recent_upgrades(data.get("ticker",""))
    if upgrades_ai:
        ups_ai=[u for u in upgrades_ai if u["direction"]=="up"]
        downs_ai=[u for u in upgrades_ai if u["direction"]=="down"]
        if ups_ai:
            u=ups_ai[0]
            conviction_ctx += f"\n🆙 שדרוג אנליסט אחרון ({u['date']}): {u['firm']} {u['from']+' → ' if u['from'] else ''}{u['to']}"
        if downs_ai:
            d=downs_ai[0]
            conviction_ctx += f"\n⚠️ הורדת דירוג אחרונה ({d['date']}): {d['firm']} {d['from']+' → ' if d['from'] else ''}{d['to']}"

    prompt=f"""אתה טריידר מוסדי מנוסה המתמחה בסווינג טריידינג של 5-15 ימים על S&P 500.

חשוב: המניה הזו **כבר עברה סינון טכני קפדני** על ידי הסורק שלנו (ניקוד {data['score']}/100 מתוך 100).
המשמעות: RSI, MACD, ADX, OBV, נפח, מומנטום — כולם מצביעים על כיוון חיובי.
**תפקידך אינו להחליט אם להיכנס. תפקידך: למצוא את נקודת הכניסה הטובה ביותר, לאשר או לדחות את הסטופ/יעד, ולזהות סיכונים ספציפיים שיכולים לבטל את הסטאפ.**

ענה בעברית בלבד. היה ספציפי ומספרי — רמות מחיר מדויקות, לא תיאורים כלליים.

{regime_ctx}
{sector_ctx}
{news_ctx}
{conviction_ctx}

טיקר: {data['ticker']} | מחיר: ${data['price']} | ניקוד סורק: {data['score']}/100
SMA20: ${data['sma20']} | SMA50: ${data['sma50']} | SMA200: ${data['sma200']}
VWAP: ${data['vwap']} | {"מעל VWAP ✅" if data['above_vwap'] else "מתחת VWAP ⚠️"} ({data['vwap_dist']:+.1f}%)
RSI: {data['rsi']} | MFI: {data['mfi']} | ADX: {data['adx']} | MACD היסטוגרם: {data['macd_hist']}
נפח: {data['vs']}x ממוצע | OBV: {"עולה ✅" if data['obv_up'] else "יורד ⚠️"} | ביצועים vs SPY: {data['rs']}%
מומנטום 1M: {data['m1']}% | 3M: {data['m3']}% | ATR יומי: {data['atr_pct']}%
שיא 52W: ${data['high52']} | מרחק משיא: {data['dist_52h']}% | גיל טרנד: {data['trend_age']} ימים
הצעת סורק — כניסה: ${data['price']} | סטופ: ${data['stop']} | יעד 1: ${data['target']} | יעד 2: ${data['target2']}

**פורמט תשובה:**

## 📊 אישור טכני
מה מחזק את הסטאפ + מה עלול לערער אותו (רמות מחיר ספציפיות בלבד)

## 📰 קטליזטורים וחדשות
האם יש טריגר שמסביר את התנועה? האם מגולם במחיר כבר?

## 🏦 Smart Money
אנליסטים, בעלות מוסדית, כסף חכם — האם הם צד אחד עם הסטאפ?

## 🎯 תוכנית כניסה
- כניסה אופטימלית: $X (ציין אם לקנות עכשיו / לחכות לרמה / לחכות לפולבק)
- סטופ מוצע: $X (הסבר אם לשנות את הסטופ של הסורק)
- יעד 1 (5-7 ימים): $X
- יעד 2 (10-15 ימים): $X
- יחס R:R: X:1

## ⚠️ סיכונים שיבטלו את הסטאפ
(רק סיכונים ספציפיים ומדידים — לא "אי ודאות בשוק" כללית)

## ⭐ ציון סטאפ: X/10
(9-10 = כניסה מיידית | 7-8 = כניסה עם תנאי | 5-6 = לחכות לאישור | מתחת ל-5 = לדלג)

## 📋 סיכום בשורה אחת"""
    try:
        resp=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":api_key,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-5","max_tokens":3000,"messages":[{"role":"user","content":prompt}]},
            timeout=120)
        if resp.status_code==200: return resp.json()["content"][0]["text"]
        return f"שגיאה: {resp.status_code}"
    except Exception as e: return f"שגיאת חיבור: {str(e)[:80]}"

# ── UI Helpers ────────────────────────────────────────────────
def show_regime(r):
    if not r or r.get("regime")=="unknown": return
    reg=r["regime"]
    cls={"bullish":"regime-bull","bearish":"regime-bear","neutral":"regime-neut"}[reg]
    icon={"bullish":"🟢","bearish":"🔴","neutral":"🟡"}[reg]
    label={"bullish":"שורי — מתאים ללונגים","bearish":"דובי — זהירות","neutral":"ניטרלי — סלקטיבי"}[reg]
    checks=f"SMA50 {'✅' if r['above_50'] else '❌'} | SMA200 {'✅' if r['above_200'] else '❌'} | Golden {'✅' if r['golden'] else '❌'} | VIX {r['vix']} | RSI {r['rsi']}"
    st.markdown(f'<div class="{cls}"><b>{icon} שוק {label}</b><br><small style="color:#c9d1d9">{checks}</small><br><small style="color:#8b949e">SPY חודש: {r["ret_1m"]:+.1f}% | שבוע: {r["ret_5d"]:+.1f}%</small></div>',unsafe_allow_html=True)

def show_sectors(sectors):
    st.markdown("**📊 דירוג מגזרים vs SPY:**")
    for i,s in enumerate(sectors[:5]):
        c="#21ff87" if s["rs_1m"]>0 else "#ff7b72"
        m=["🥇","🥈","🥉","4️⃣","5️⃣"][i]
        st.markdown(f'<div class="sector-card">{m} <b>{s["sector"]}</b> ({s["etf"]}) | 1M: <span style="color:{c}">{s["rs_1m"]:+.1f}%</span> | 5D: <span style="color:{c}">{s["rs_5d"]:+.1f}%</span></div>',unsafe_allow_html=True)

def show_card(i, row, style="normal", show_earnings=False):
    sc_cls="score-high" if row["score"]>=70 else "score-mid" if row["score"]>=50 else "score-low"
    m3c="positive" if row["m3"]>0 else "negative"
    arrow="▲" if row["m3"]>0 else "▼"
    obv="↑" if row["obv_up"] else "↓"
    flags=" ".join(row.get("flags",[])) if row.get("flags") else ""
    cls="hc-card" if style=="hc" else "result-card"
    vc="vwap-above" if row.get("above_vwap") else "vwap-below"
    vi="✅" if row.get("above_vwap") else "⚠️"
    h52=row.get("high52",0)
    h52_str=f"${h52:.2f}" if h52 and h52>0 and not np.isnan(h52) else "N/A"
    flags_html = f'<div style="font-size:0.75rem;margin:4px 0;color:#f0b429">{flags}</div>' if flags else ''
    fire = '🔥' if style == 'hc' else ''
    base_note = (f' <span style="color:#8b949e;font-size:0.7rem">(בסיס: {row["base_score"]})</span>'
                  if row.get("base_score") is not None else '')
    html = (
        f'<div class="{cls}">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span class="ticker">#{i+1} {row["ticker"]} {fire}</span>'
        f'<span class="{sc_cls}">⭐ {row["score"]}{base_note}</span></div>'
        f'{flags_html}'
        f'<div class="row-item">💰 <span class="row-val">${row["price"]}</span> | VWAP: <span class="{vc}">{vi} ${row.get("vwap","-")} ({row.get("vwap_dist",0):+.1f}%)</span></div>'
        f'<div class="row-item">📈 3M: <span class="{m3c}">{arrow}{abs(row["m3"])}%</span> | Vol: <span class="row-val">{row["vs"]}x</span> | ADX: <span class="row-val">{row["adx"]}</span> | טרנד: <span class="row-val">{row.get("trend_age",0)}d</span></div>'
        f'<div class="row-item">RSI: <span class="row-val">{row["rsi"]}</span> | MFI: <span class="row-val">{row["mfi"]}</span> | OBV: <span class="row-val">{obv}</span> | SPY: <span class="row-val">{row["rs"]:+.1f}%</span></div>'
        f'<div class="row-item">📏 שיא 52W: <span class="row-val">{h52_str}</span> (מרחק: {row.get("dist_52h","N/A")}%)</div>'
        f'<div class="row-item">🛡️ כניסה: <span class="row-val">${row["price"]}</span> | סטופ: <span class="negative">${row["stop"]}</span> | יעד 1: <span class="positive">${row["target"]}</span> | יעד 2: <span class="positive">${row["target2"]}</span></div>'
        f'<div class="row-item">📝 <span style="color:#c9d6df">{row["setup"]}</span></div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    if show_earnings and row.get("earnings_days") is not None:
        d=row["earnings_days"]; st_=row.get("earnings_status","")
        col={"danger":"#ff7b72","warning":"#f0b429","caution":"#58a6ff"}.get(st_,"#8b949e")
        ic={"danger":"🚨","warning":"⚠️","caution":"📅"}.get(st_,"📅")
        st.markdown(f'<div class="earnings-warn" style="border-color:{col};color:{col}">{ic} דוח רווחים בעוד {d} ימים</div>',unsafe_allow_html=True)

def show_value_card(i, row):
    sc_cls="score-high" if row["score"]>=70 else "score-mid" if row["score"]>=50 else "score-low"
    r1y_c="positive" if row["ret_1y"]>0 else "negative"
    trend="✅ Golden Cross" if row["golden"] else "✅ מעל SMA200" if row["above_200"] else "⚠️ מתחת SMA200"
    cat_colors={"ETF":"#00d4ff","Dividend":"#21ff87","Value":"#f0b429","Sector":"#8b949e"}
    cat_c=cat_colors.get(row["category"],"#8b949e")
    st.markdown(f"""<div class="value-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="ticker">#{i+1} {row['ticker']}</span>
        <span class="{sc_cls}">⭐ {row['score']}</span>
      </div>
      <div class="row-item"><span style="color:{cat_c}">■ {row['category']}</span> | {row['name']}</div>
      <div class="row-item">💰 <span class="row-val">${row['price']}</span> | {trend}</div>
      <div class="row-item">📈 שנה: <span class="{r1y_c}">{row['ret_1y']:+.1f}%</span> | 6M: <span class="{'positive' if row['ret_6m']>0 else 'negative'}">{row['ret_6m']:+.1f}%</span> | 3M: <span class="{'positive' if row['ret_3m']>0 else 'negative'}">{row['ret_3m']:+.1f}%</span></div>
      <div class="row-item">RSI: <span class="row-val">{row['rsi']}</span> | תנודתיות: <span class="row-val">{row['vol_annual']}%</span> | ירידה מקסימלית: <span class="negative">{row['drawdown']:.1f}%</span></div>
      {'<div class="row-item">💰 דיבידנד: <span class="positive">'+str(row["div_yield"])+'%</span></div>' if row.get("div_yield",0)>0 else ''}
      {'<div class="row-item">P/E: <span class="row-val">'+str(row["pe"])+'</span></div>' if row.get("pe",0)>0 else ''}
    </div>""",unsafe_allow_html=True)

def show_squeeze_card(i, row):
    st.markdown(f"""<div class="ss-card">
      <div style="display:flex;justify-content:space-between">
        <span class="ticker">#{i+1} {row['ticker']} 💥</span>
        <span style="color:#ff7b72;font-weight:700">Squeeze: {row['squeeze_score']}</span>
      </div>
      <div class="row-item">💰 <span class="row-val">${row['price']}</span> | Vol: <span class="row-val">{row['vs']}x</span> | RSI: <span class="row-val">{row['rsi']}</span></div>
      <div class="row-item">BB Width: {row['bb_width']}% | מיקום: {row['price_vs_bb']}% | 5D: <span class="positive">{row['m5']:+.1f}%</span></div>
      <div class="row-item">🛡️ סטופ: <span class="negative">${row['stop']}</span> | יעד: <span class="positive">${row['target']}</span></div>
      <div class="row-item">🔥 {row['reasons']}</div>
    </div>""",unsafe_allow_html=True)

def show_gap_card(i, row):
    cls="positive" if row["direction"]=="UP" else "negative"
    arrow="▲" if row["direction"]=="UP" else "▼"
    hold="✅ מחזיק" if row["holding"] else "⚠️ נחלש"
    st.markdown(f"""<div class="gap-card">
      <div style="display:flex;justify-content:space-between">
        <span class="ticker">#{i+1} {row['ticker']}</span>
        <span class="{cls}">{arrow} {abs(row['gap_pct'])}% גאפ</span>
      </div>
      <div class="row-item">אמש: <span class="row-val">${row['prev_close']}</span> → פתיחה: <span class="row-val">${row['open']}</span> → עכשיו: <span class="row-val">${row['close']}</span></div>
      <div class="row-item">נפח: <span class="row-val">{row['vol_ratio']}x</span> | {hold}</div>
    </div>""",unsafe_allow_html=True)

def save_tracker(results):
    if "tracker" not in st.session_state: st.session_state["tracker"]=[]
    for r in results[:5]:
        st.session_state["tracker"].append({"date":datetime.now().strftime("%d/%m"),
            "ticker":r["ticker"],"entry":r["price"],
            "target":r.get("target",r["price"]*1.05),"stop":r.get("stop",r["price"]*0.95),"score":r["score"]})

def show_tracker():
    if "tracker" not in st.session_state or not st.session_state["tracker"]:
        st.info("אין עסקאות במעקב. הרץ סריקה כדי להוסיף."); return
    for t in st.session_state["tracker"]:
        try:
            cur=yf.download(t["ticker"],period="2d",auto_adjust=True,progress=False,threads=False)
            if isinstance(cur.columns,pd.MultiIndex): cur.columns=cur.columns.get_level_values(0)
            cur_p=safe_float(cur["Close"].iloc[-1]) if not cur.empty else t["entry"]
        except: cur_p=t["entry"]
        pnl=round((cur_p-t["entry"])/t["entry"]*100,2) if t["entry"]>0 else 0
        cls="positive" if pnl>0 else "negative"
        status="🎯 יעד" if cur_p>=t["target"] else "🛑 סטופ" if cur_p<=t["stop"] else "⏳ פתוח"
        st.markdown(f'<div class="tracker-row"><span class="ticker">{t["ticker"]}</span> | כניסה: ${t["entry"]} | עכשיו: ${cur_p:.2f} | <span class="{cls}">{"▲" if pnl>0 else "▼"}{abs(pnl)}%</span> | {status} | {t["date"]}</div>',unsafe_allow_html=True)
    if st.button("🗑️ נקה"): st.session_state["tracker"]=[]; st.rerun()

def run_ai_panel(r, api_key, regime=None, sectors=None):
    """הצגת ניתוח AI מלא — ניתן לקרוא מכל מצב"""
    show_card(0,r,show_earnings=r.get("earnings_days") is not None)
    with st.spinner("טוען חדשות ואנליסטים..."):
        news_items=get_stock_news(r["ticker"])
        cat_sent,cats=detect_catalyst(news_items)
        cv_data=get_conviction_data(r["ticker"])
        ups=get_recent_upgrades(r["ticker"])
    show_conviction_badge(cv_data)
    show_upgrade_badge(ups)
    show_news_card(r["ticker"],news_items,cat_sent,cats)
    if api_key:
        st.markdown("---"); st.markdown(f"### 🤖 ניתוח AI מעמיק — {r['ticker']}")
        with st.spinner("Claude מנתח... (עד 2 דקות)"):
            analysis=ai_deep_analysis(r,api_key,regime=regime,sectors=sectors)
            if "שגיאת חיבור" in analysis or "timed out" in analysis.lower():
                st.info("מנסה שוב..."); analysis=ai_deep_analysis(r,api_key,regime=regime,sectors=sectors)
        html=re.sub(r'^## (.+)$',r'<h2>\1</h2>',analysis,flags=re.MULTILINE)
        html=re.sub(r'^### (.+)$',r'<h3>\1</h3>',html,flags=re.MULTILINE)
        html=html.replace("\n","<br>")
        st.markdown(f'<div class="ai-card">{html}</div>',unsafe_allow_html=True)
        st.markdown("**📋 העתק ניתוח:**")
        st.code(analysis,language=None)
    else:
        st.info("💡 הוסף מפתח API לניתוח AI")

# ── MAIN ──────────────────────────────────────────────────────
def main():
    st.markdown('<div class="main-title">📈 SWING SCANNER PRO</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">Top-Down Analysis · {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>',unsafe_allow_html=True)
    st.markdown("---")

    MODES=[
        "🔍 סריקה Top-Down (מומלץ)",
        "🔥 High Conviction",
        "💥 Short Squeeze",
        "📊 Gap & Go",
        "🎯 מניה בודדת + AI",
        "📋 מניות ספציפיות",
        "💎 השקעה לטווח בינוני",
        "📈 Performance Tracker",
    ]
    mode=st.radio("בחר מצב:",MODES)

    def get_spy_close():
        spy=yf.download("SPY",period="1y",auto_adjust=True,progress=False,threads=False)
        if isinstance(spy.columns,pd.MultiIndex): spy.columns=spy.columns.get_level_values(0)
        return spy["Close"]

    # ── TOP-DOWN ──────────────────────────────────────────────
    if mode=="🔍 סריקה Top-Down (מומלץ)":
        top_n=st.slider("כמה מניות?",5,15,10)
        show_earn=st.checkbox("הצג אזהרות דוחות",value=True)
        n_sectors=st.slider("כמה מגזרים?",1,5,3)
        universe_opt = st.radio("Universe:", [
            "⚡ S&P 500 נבחר + מגזרים (~4 דק)",
            "🚀 QQQ 100 (~2 דק)",
            "💎 S&P 500 מלא — 500 מניות (~10 דק)",
        ])
        include_midcap = st.checkbox("הוסף מניות צמיחה (SNOW, PLTR, CRWD וכו')", value=False)
        check_upgrades = st.checkbox("🆙 בדוק שדרוגי אנליסטים אחרונים (Top results)", value=True)

        if st.button("🔍 סרוק Top-Down"):
            with st.spinner("שלב 1/3 — מצב שוק..."): regime=get_market_regime()
            st.session_state["last_regime"]=regime
            show_regime(regime)
            if regime.get("regime")=="bearish": st.error("⛔ שוק דובי — זהירות עם לונגים!")

            # Sentiment Panel
            with st.spinner("טוען מנטליות שוק..."):
                fg = get_fear_greed()
                pc = get_put_call()
            show_sentiment_panel(fg=fg, pc=pc)

            with st.spinner("שלב 2/3 — מדרג מגזרים..."): sectors=get_sector_ranking()
            st.session_state["last_sectors"]=sectors
            if sectors: st.markdown("---"); show_sectors(sectors)

            st.markdown("---")

            # Build ticker list based on universe choice
            if "מלא" in universe_opt:
                with st.spinner("טוען S&P 500 מלא מ-Wikipedia..."):
                    sp500_full = load_sp500_full()
                all_t = sp500_full if sp500_full else [t for s in SECTOR_ETFS.values() for t in s[1]]
                all_t = list(dict.fromkeys(all_t))
                st.info(f"נטענו {len(all_t)} מניות S&P 500")
            elif "QQQ" in universe_opt:
                all_t = list(dict.fromkeys([t for s in SECTOR_ETFS.values() for t in s[1]]))[:100]
            else:
                top_secs = sectors[:n_sectors]
                all_t = []
                for s in top_secs:
                    for t in s["stocks"]:
                        if t not in all_t: all_t.append(t)

            if include_midcap:
                all_t += [t for t in MIDCAP_GROWTH if t not in all_t]

            st.info(f"שלב 3/3 — סורק {len(all_t)} מניות...")
            spy_c=get_spy_close()
            sec_map={s["sector"]:s["score"] for s in sectors}
            if 'top_secs' not in locals():
                top_secs = sectors[:n_sectors]
            prog=st.progress(0); rs=[]; rr=[]
            for i,t in enumerate(all_t):
                t_sec=next((sec for sec,(etf,stks) in SECTOR_ETFS.items() if t in stks),"")
                sc=sec_map.get(t_sec,0)
                r,_=analyse_stock(t,spy_c,strict=True,sector_score=sc)
                if r: r["sector"]=t_sec; rs.append(r)
                else:
                    r2,_=analyse_stock(t,spy_c,strict=False,sector_score=sc)
                    if r2 and r2["score"]>=55: r2["sector"]=t_sec; rr.append(r2)
                prog.progress((i+1)/len(all_t),text=f"סורק {t}...")
            prog.empty()
            results=rs if rs else rr
            if not results: st.error("לא נמצאו מניות."); return
            if not rs: st.warning(f"⚠️ מציג {len(rr)} מניות עם פילטרים מקולים.")
            else: st.success(f"✅ {len(rs)} מניות עברו את כל הפילטרים!")
            results.sort(key=lambda x:x["score"],reverse=True)
            if check_upgrades:
                pool=results[:min(len(results),top_n+15)]
                with st.spinner("בודק שדרוגי אנליסטים אחרונים..."):
                    for row in pool:
                        ups=get_recent_upgrades(row["ticker"])
                        row["upgrades"]=ups
                        bonus=0
                        if any(u["direction"]=="up" for u in ups): bonus+=UPGRADE_SCORE_BONUS
                        if any(u["direction"]=="down" for u in ups): bonus+=DOWNGRADE_SCORE_PENALTY
                        row["upgrade_bonus"]=bonus
                        if bonus:
                            row["base_score"]=row["score"]
                            row["score"]=round(min(100,max(0,row["score"]+bonus)),1)
                results.sort(key=lambda x:x["score"],reverse=True)
            if show_earn:
                for row in results[:top_n]:
                    d,st_=get_earnings_info(row["ticker"]); row["earnings_days"]=d; row["earnings_status"]=st_
            for i,row in enumerate(results[:top_n]):
                show_card(i,row,show_earnings=show_earn)
                if check_upgrades:
                    show_upgrade_badge(row.get("upgrades",[]),row.get("upgrade_bonus",0))
                if st.button(f"🤖 נתח {row['ticker']} עם AI", key=f"ai_td_{row['ticker']}_{i}"):
                    st.session_state[f"show_ai_{row['ticker']}"]=True
                if st.session_state.get(f"show_ai_{row['ticker']}"):
                    api_key_td=st.text_input("מפתח API:",type="password",key=f"key_td_{row['ticker']}_{i}")
                    if api_key_td:
                        run_ai_panel(row,api_key_td,
                            regime=st.session_state.get("last_regime"),
                            sectors=st.session_state.get("last_sectors"))
            save_tracker(results[:top_n])
            csv=pd.DataFrame(results[:top_n]).to_csv(index=False).encode()
            st.download_button("⬇️ CSV",data=csv,file_name=f"topdown_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")

    # ── HIGH CONVICTION ───────────────────────────────────────
    elif mode=="🔥 High Conviction":
        opt=st.radio("Universe:",["🔍 Top-Down (מגזרים חזקים)","🚀 כל מניות הסקטורים","➕ כולל צמיחה"])
        st.info("ניקוד 68+ | ADX 25+ | Volume 1.5x+ | מומנטום 10%+ | מעל VWAP")
        if st.button("🔥 מצא High Conviction"):
            spy_c=get_spy_close()
            if "Top-Down" in opt:
                with st.spinner("טוען מגזרים..."): sectors=get_sector_ranking()
                tickers=[t for s in sectors[:3] for t in s["stocks"]]
                sec_map={s["sector"]:s["score"] for s in sectors}
            elif "צמיחה" in opt:
                tickers=list(dict.fromkeys([t for s in SECTOR_ETFS.values() for t in s[1]]+MIDCAP_GROWTH))
                sec_map={}
            else:
                tickers=list(dict.fromkeys([t for s in SECTOR_ETFS.values() for t in s[1]]))
                sec_map={}
            prog=st.progress(0); hc=[]; all_r=[]
            for i,t in enumerate(tickers):
                t_sec=next((s for s,(_,stks) in SECTOR_ETFS.items() if t in stks),"")
                sc=sec_map.get(t_sec,0)
                r,_=analyse_stock(t,spy_c,strict=True,sector_score=sc)
                if r:
                    all_r.append(r)
                    if r["score"]>=68 and r["adx"]>=25 and r["vs"]>=1.5 and r["m3"]>=10:
                        d,st_=get_earnings_info(t); r["earnings_days"]=d; r["earnings_status"]=st_
                        hc.append(r)
                prog.progress((i+1)/len(tickers),text=f"סורק {t}...")
            prog.empty()
            hc.sort(key=lambda x:x["score"],reverse=True); hc=hc[:3]
            if hc:
                st.success(f"🔥 {len(hc)} High Conviction!")
                for i,row in enumerate(hc):
                    show_card(i,row,style="hc",show_earnings=True)
                    show_upgrade_badge(get_recent_upgrades(row["ticker"]))
                    if st.button(f"🤖 נתח {row['ticker']} עם AI", key=f"ai_hc_{row['ticker']}_{i}"):
                        st.session_state[f"show_ai_{row['ticker']}"]=True
                    if st.session_state.get(f"show_ai_{row['ticker']}"):
                        api_key_hc=st.text_input("מפתח API:",type="password",key=f"key_hc_{row['ticker']}_{i}")
                        if api_key_hc:
                            run_ai_panel(row,api_key_hc,
                                regime=st.session_state.get("last_regime"),
                                sectors=st.session_state.get("last_sectors"))
            elif all_r:
                all_r.sort(key=lambda x:x["score"],reverse=True)
                st.warning("לא נמצאו HC מלאים — הטובות שנמצאו:")
                for i,row in enumerate(all_r[:3]): show_card(i,row,style="hc")
            else: st.warning("לא נמצאו מניות.")

    # ── SHORT SQUEEZE ─────────────────────────────────────────
    elif mode=="💥 Short Squeeze":
        opt=st.radio("Universe:",["🚀 סקטורים","➕ כולל צמיחה"])
        tickers=list(dict.fromkeys([t for s in SECTOR_ETFS.values() for t in s[1]]))
        if "צמיחה" in opt: tickers+=MIDCAP_GROWTH
        st.info("BB Squeeze + נפח פתאומי + RSI עולה | סיכון גבוה")
        if st.button("💥 סרוק"):
            prog=st.progress(0); sq=[]
            for i,t in enumerate(tickers):
                r=analyse_squeeze(t)
                if r: sq.append(r)
                prog.progress((i+1)/len(tickers),text=f"{t}...")
            prog.empty()
            sq.sort(key=lambda x:x["squeeze_score"],reverse=True); sq=sq[:5]
            if sq:
                st.success(f"💥 {len(sq)} מועמדות!")
                st.warning("⚠️ פוזיציה קטנה — סיכון גבוה!")
                for i,row in enumerate(sq): show_squeeze_card(i,row)
            else: st.warning("לא נמצאו. נסה בשעות מסחר.")

    # ── GAP & GO ──────────────────────────────────────────────
    elif mode=="📊 Gap & Go":
        tickers=list(dict.fromkeys([t for s in SECTOR_ETFS.values() for t in s[1]]+MIDCAP_GROWTH))
        st.info("גאפי פתיחה >1.5% על נפח גבוה — הרץ אחרי 16:30 ישראל")
        if st.button("📊 סרוק"):
            prog=st.progress(0); gaps=[]
            for i,t in enumerate(tickers):
                r=detect_gap(t)
                if r: gaps.append(r)
                prog.progress((i+1)/len(tickers),text=f"{t}...")
            prog.empty()
            ups=[g for g in gaps if g["direction"]=="UP"]; dns=[g for g in gaps if g["direction"]=="DOWN"]
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
                fg=get_fear_greed()
                pc=get_put_call()
            show_regime(regime)
            show_sentiment_panel(fg=fg,pc=pc)
            spy_c=get_spy_close()
            with st.spinner(f"מנתח {ticker_input}..."):
                r,err=analyse_stock(ticker_input,spy_c,strict=False)
            if not r: st.error(f"שגיאה: {err}"); return
            if show_earn:
                d,st_=get_earnings_info(ticker_input); r["earnings_days"]=d; r["earnings_status"]=st_
            r["sector"]=next((s for s,(_,stks) in SECTOR_ETFS.items() if ticker_input in stks),"אחר")
            run_ai_panel(r,api_key,regime=regime,sectors=sectors)

    # ── MULTIPLE ──────────────────────────────────────────────
    elif mode=="📋 מניות ספציפיות":
        custom=st.text_input("הכנס טיקרים (מופרדים בפסיק):","")
        st.caption("💡 ניתן להכניס כל טיקר: SNOW, PLTR, CRWD, AXSM, COIN וכו'")
        show_earn=st.checkbox("בדוק דוחות",value=True)
        tickers=[t.strip().upper() for t in custom.split(",") if t.strip()] if custom else []
        if not tickers: st.warning("הכנס לפחות טיקר אחד")
        else:
            st.info(f"מנתח: {', '.join(tickers)}")
            if st.button("📋 נתח עכשיו"):
                spy_c=get_spy_close()
                prog=st.progress(0); results=[]; failures=[]
                for i,t in enumerate(tickers):
                    r,err=analyse_stock(t,spy_c,strict=False)
                    if r:
                        r["sector"]=next((s for s,(_,stks) in SECTOR_ETFS.items() if t in stks),"אחר")
                        if show_earn:
                            d,st_=get_earnings_info(t); r["earnings_days"]=d; r["earnings_status"]=st_
                        results.append(r)
                    elif err: failures.append((t,err))
                    prog.progress((i+1)/len(tickers),text=f"{t}...")
                prog.empty()
                if not results: st.warning("לא ניתן לנתח."); return
                results.sort(key=lambda x:x["score"],reverse=True)
                st.success(f"✅ {len(results)} מניות")
                for i,row in enumerate(results):
                    show_card(i,row,show_earnings=show_earn)
                    if len(tickers)<=5:
                        ni=get_stock_news(row["ticker"])
                        cs,ca=detect_catalyst(ni)
                        cv=get_conviction_data(row["ticker"])
                        show_conviction_badge(cv)
                        show_upgrade_badge(get_recent_upgrades(row["ticker"]))
                        show_news_card(row["ticker"],ni,cs,ca)
                for t,err in failures:
                    st.markdown(f'<div style="color:#8b949e;font-size:0.78rem">❌ {t} — {err}</div>',unsafe_allow_html=True)
                csv=pd.DataFrame(results).to_csv(index=False).encode()
                st.download_button("⬇️ CSV",data=csv,file_name=f"specific_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")

    # ── LONG-TERM ─────────────────────────────────────────────
    elif mode=="💎 השקעה לטווח בינוני":
        st.markdown("### 💎 השקעה לטווח בינוני (6-24 חודשים)")
        st.info("ניתוח ETFs, מניות ערך ומניות דיבידנד — לתוכנית חיסכון והשקעה מאוזנת")

        cats=st.multiselect("סוגי נכסים:",["ETF","Dividend","Value","Sector"],default=["ETF","Dividend","Value"])
        filter_tickers=[(t,n,c) for t,n,c in LONGTERM_ETFS if c in cats]

        if st.button("💎 נתח השקעות"):
            prog=st.progress(0); results=[]
            for i,(t,n,c) in enumerate(filter_tickers):
                r=analyse_longterm(t,n,c)
                if r: results.append(r)
                prog.progress((i+1)/len(filter_tickers),text=f"מנתח {t}...")
            prog.empty()
            if not results: st.warning("לא ניתן לנתח."); return
            results.sort(key=lambda x:x["score"],reverse=True)
            st.success(f"✅ {len(results)} נכסים נותחו")

            # Group by category
            for cat in cats:
                cat_results=[r for r in results if r["category"]==cat]
                if not cat_results: continue
                cat_labels={"ETF":"📊 קרנות סל (ETF)","Dividend":"💰 מניות דיבידנד","Value":"🏦 מניות ערך","Sector":"🏭 סקטוריאלי"}
                st.markdown(f"#### {cat_labels.get(cat,cat)}")
                for i,row in enumerate(cat_results): show_value_card(i,row)

            st.markdown("---")
            st.markdown("""
            <div style="background:#161b22;border:1px solid #f0b429;border-radius:8px;padding:14px;color:#e6edf3;font-size:0.82rem">
            <b style="color:#f0b429">💡 עקרונות לתוכנית חיסכון:</b><br><br>
            • <b>פיזור</b> — לפחות 3-4 ETFs שונים<br>
            • <b>קביעות</b> — השקעה חודשית קבועה (Dollar Cost Averaging)<br>
            • <b>אופק</b> — מינימום 3-5 שנים<br>
            • <b>דיבידנדים</b> — השקע מחדש אוטומטית<br>
            • <b>עלויות</b> — בחר ETFs עם Expense Ratio נמוך (מתחת ל-0.2%)
            </div>""",unsafe_allow_html=True)

            csv=pd.DataFrame(results).to_csv(index=False).encode()
            st.download_button("⬇️ CSV",data=csv,file_name=f"longterm_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")

    # ── TRACKER ───────────────────────────────────────────────
    elif mode=="📈 Performance Tracker":
        show_tracker()

    st.markdown('<div class="disclaimer">⚠️ <b>אזהרת סיכון</b> — למטרות לימוד בלבד. אין המלצת השקעה. לעולם אל תסכן יותר מ-1.5-2% מההון שלך בעסקה אחת.</div>',unsafe_allow_html=True)

if __name__=="__main__":
    main()
