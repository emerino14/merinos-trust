import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm
from datetime import datetime, timezone, timedelta
import json
import warnings
import requests
from pathlib import Path
warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).parent

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE INSTRUMENTOS
# ══════════════════════════════════════════════════════════════════

INSTRUMENTS = {
    "MNQ": {
        "label"         : "MNQ — Nasdaq",
        "emoji"         : "📈",
        "etf"           : "QQQ",
        "futures"       : "NQ=F",
        "fut_label"     : "NQ / MNQ",
        "history_file"  : BASE_DIR / "levels_history.json",
        "accent"        : "#58a6ff",
        "pine_name"     : "MNQ · Gamma Histórico",
        "gex_threshold" : 0.3e9,
        "description"   : "Micro E-mini Nasdaq-100 · Proxy: QQQ",
    },
    "MES": {
        "label"         : "MES — S&P 500",
        "emoji"         : "🏛️",
        "etf"           : "SPY",
        "futures"       : "ES=F",
        "fut_label"     : "ES / MES",
        "history_file"  : BASE_DIR / "mes_history.json",
        "accent"        : "#3fb950",
        "pine_name"     : "MES · Gamma Histórico",
        "gex_threshold" : 1.0e9,
        "description"   : "Micro E-mini S&P 500 · Proxy: SPY",
    },
    "GC": {
        "label"         : "MGC — Micro Oro",
        "emoji"         : "🥇",
        "etf"           : "GLD",
        "futures"       : "GC=F",
        "fut_label"     : "GC / MGC",
        "history_file"  : BASE_DIR / "gc_history.json",
        "accent"        : "#e3b341",
        "pine_name"     : "GC · Gamma Histórico",
        "gex_threshold" : 0.05e9,
        "description"   : "Micro Gold Futures · Proxy: GLD",
    },
    "BTC": {
        "label"         : "BTC — Bitcoin",
        "emoji"         : "₿",
        "etf"           : "IBIT",
        "futures"       : "BTC-USD",
        "fut_label"     : "BTC",
        "history_file"  : BASE_DIR / "btc_history.json",
        "accent"        : "#f78166",
        "pine_name"     : "BTC · Gamma Histórico",
        "gex_threshold" : 0.1e9,
        "description"   : "Bitcoin · Proxy: IBIT (BlackRock)",
    },
}

# ══════════════════════════════════════════════════════════════════
# PÁGINA Y ESTILOS
# ══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Merino's Trust",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN — ACCIONES BUDGET (~$400)
# ══════════════════════════════════════════════════════════════════

STOCKS_BUDGET = {
    "BAC":  {"name":"Bank of America",     "sector":"Financiero",    "emoji":"🏦","accent":"#0070f3","notes":"Muy líquido · Aprende aquí · Earnings ~Jul"},
    "WFC":  {"name":"Wells Fargo",          "sector":"Financiero",    "emoji":"🏦","accent":"#d62728","notes":"Muy líquido · Soporte Berkshire · Earnings ~Jul"},
    "SOFI": {"name":"SoFi Technologies",    "sector":"Fintech",       "emoji":"💳","accent":"#17becf","notes":"Alta IV · Sensible a tasas Fed · Earnings ~Jul"},
    "OXY":  {"name":"Occidental Petroleum", "sector":"Energía",       "emoji":"⛽","accent":"#8c564b","notes":"Soporte Buffett · Correlación WTI · Earnings ~Aug"},
    "DVN":  {"name":"Devon Energy",         "sector":"Energía",       "emoji":"⛽","accent":"#e377c2","notes":"Post-fusión · Uptrend · Earnings ~Aug"},
    "GM":   {"name":"General Motors",       "sector":"Automotriz",    "emoji":"🚗","accent":"#2196f3","notes":"Breakout técnico · Earnings Q2"},
    "MARA": {"name":"MARA Holdings",        "sector":"Cripto/Digital","emoji":"₿", "accent":"#f7931a","notes":"Alta IV · BTC proxy · Earnings ~May pasado"},
    "RIVN": {"name":"Rivian Automotive",    "sector":"EV/Tech",       "emoji":"⚡","accent":"#4caf50","notes":"Alta IV · EV catalizador · Earnings ~Aug"},
    "DKNG": {"name":"DraftKings",           "sector":"Gaming",        "emoji":"🎰","accent":"#9c27b0","notes":"Zona soporte 52w · IV alta · Earnings Q2"},
}

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN — ACCIONES TOP 20 (MÁS COTIZADAS)
# ══════════════════════════════════════════════════════════════════

STOCKS_TOP20 = {
    "AAPL": {"name":"Apple",            "sector":"Tech/Consumer",   "emoji":"🍎","accent":"#a2aaad","notes":"Mega-cap · Opciones ultra-líquidas · Earnings ~Jul"},
    "NVDA": {"name":"Nvidia",           "sector":"Semiconductores", "emoji":"🤖","accent":"#76b900","notes":"IA líder · Alta IV · Earnings ~May"},
    "META": {"name":"Meta Platforms",   "sector":"Social/Tech",     "emoji":"📘","accent":"#0866ff","notes":"Momentum fuerte · Earnings ~Jul"},
    "TSLA": {"name":"Tesla",            "sector":"EV/Tech",         "emoji":"⚡","accent":"#e82127","notes":"Muy volátil · Alta IV · Earnings ~Jul"},
    "MSFT": {"name":"Microsoft",        "sector":"Tech/Cloud",      "emoji":"🪟","accent":"#00a4ef","notes":"Opciones líquidas · IA catalizador · Earnings ~Jul"},
    "AMZN": {"name":"Amazon",           "sector":"E-commerce/Cloud","emoji":"📦","accent":"#ff9900","notes":"Alta liquidez · AWS driver · Earnings ~Aug"},
    "GOOGL":{"name":"Alphabet",         "sector":"Tech/AI",         "emoji":"🔍","accent":"#4285f4","notes":"Búsqueda + IA · Earnings ~Jul"},
    "AMD":  {"name":"AMD",              "sector":"Semiconductores", "emoji":"🔴","accent":"#ed1c24","notes":"IA chips · Compite vs NVDA · Earnings ~Jul"},
    "PLTR": {"name":"Palantir",         "sector":"IA/Defense",      "emoji":"🛡️","accent":"#7c3aed","notes":"Alta IV · Contratos gobierno · Earnings ~Aug"},
    "COIN": {"name":"Coinbase",         "sector":"Cripto/Fintech",  "emoji":"🔵","accent":"#0052ff","notes":"Correlación BTC alta · Muy volátil · Earnings ~Aug"},
    "MSTR": {"name":"MicroStrategy",    "sector":"Cripto/BTC",      "emoji":"₿", "accent":"#f7931a","notes":"BTC proxy apalancado · IV extrema · Earnings ~Aug"},
    "NFLX": {"name":"Netflix",          "sector":"Streaming",       "emoji":"🎬","accent":"#e50914","notes":"Crecimiento estable · Earnings ~Jul"},
    "AVGO": {"name":"Broadcom",         "sector":"Semiconductores", "emoji":"🔌","accent":"#cc0000","notes":"IA infraestructura · Earnings ~Sep"},
    "SMCI": {"name":"Super Micro",      "sector":"IA Hardware",     "emoji":"💻","accent":"#00a651","notes":"Servidores IA · Alta IV · Earnings ~Aug"},
    "HOOD": {"name":"Robinhood",        "sector":"Fintech",         "emoji":"🏹","accent":"#00c805","notes":"Cripto + options platform · Earnings ~Aug"},
    "RDDT": {"name":"Reddit",           "sector":"Social/Media",    "emoji":"👾","accent":"#ff4500","notes":"IPO 2024 · Alta IV · Earnings ~Aug"},
    "ARM":  {"name":"ARM Holdings",     "sector":"Semiconductores", "emoji":"💪","accent":"#0091bd","notes":"IPO 2023 · IA chips · Earnings ~Aug"},
    "CRWD": {"name":"CrowdStrike",      "sector":"Ciberseguridad",  "emoji":"🛡️","accent":"#fc4c02","notes":"Líder en seguridad · Earnings ~Sep"},
    "ORCL": {"name":"Oracle",           "sector":"Cloud/IA",        "emoji":"☁️","accent":"#f80000","notes":"Cloud + IA · Earnings ~Jun"},
    "CBRS": {"name":"Cerebras Systems", "sector":"IA Hardware",     "emoji":"🧠","accent":"#9333ea","notes":"Chips IA · Si ya cotiza en mercado"},
}

st.markdown("""
<style>
    .main { background-color: #0d1117; }
    .regime-box {
        padding: 18px 16px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 16px;
    }
    .positive-regime { background: linear-gradient(135deg,#0a2e1a,#0d4a28); border: 2px solid #00c851; }
    .negative-regime { background: linear-gradient(135deg,#2e0a0a,#4a0d0d); border: 2px solid #ff4444; }
    .neutral-regime  { background: linear-gradient(135deg,#2a2600,#3d3700); border: 2px solid #ffbb33; }

    .mini-card {
        padding: 16px 14px;
        border-radius: 10px;
        text-align: center;
        background: #161b22;
        border: 1px solid #30363d;
        margin-bottom: 8px;
    }
    .market-banner {
        padding: 8px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        font-size: 0.85rem;
    }
    .rth-banner   { background: #0a2e1a; border: 1px solid #00c851; color: #00c851; }
    .pre-banner   { background: #2a2600; border: 1px solid #ffbb33; color: #ffbb33; }
    .closed-banner{ background: #1e2130; border: 1px solid #555;    color: #888;    }

    div[data-testid="stMetricValue"] { font-size: 1.45rem !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 1px; }

    /* Tab accent colors */
    button[data-baseweb="tab"]:nth-child(2)  { border-bottom-color: #58a6ff !important; }
    button[data-baseweb="tab"]:nth-child(3)  { border-bottom-color: #3fb950 !important; }
    button[data-baseweb="tab"]:nth-child(4)  { border-bottom-color: #e3b341 !important; }
    button[data-baseweb="tab"]:nth-child(5)  { border-bottom-color: #f78166 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# MARKET HOURS HELPER
# ══════════════════════════════════════════════════════════════════

def market_status():
    """Devuelve (status_str, banner_class) según el horario ET."""
    et = timezone(timedelta(hours=-4))  # EDT (verano)
    now_et = datetime.now(et)
    h, m = now_et.hour, now_et.minute
    total_min = h * 60 + m
    day = now_et.weekday()  # 0=Lun, 6=Dom

    if day >= 5:
        return f"⚫ Mercado CERRADO — {now_et.strftime('%A %H:%M ET')}", "closed-banner"
    elif 9 * 60 + 30 <= total_min < 16 * 60:
        return f"🟢 RTH ABIERTO — {now_et.strftime('%H:%M ET')} · Cierre en {15*60+60 - total_min}min", "rth-banner"
    elif 4 * 60 <= total_min < 9 * 60 + 30:
        mins_to_open = (9 * 60 + 30) - total_min
        return f"🟡 PRE-MARKET — Apertura RTH en {mins_to_open}min ({now_et.strftime('%H:%M ET')})", "pre-banner"
    elif 16 * 60 <= total_min < 20 * 60:
        return f"🟡 AFTER HOURS — {now_et.strftime('%H:%M ET')}", "pre-banner"
    else:
        return f"⚫ Mercado CERRADO (overnight) — {now_et.strftime('%H:%M ET')}", "closed-banner"


# ══════════════════════════════════════════════════════════════════
# BLACK-SCHOLES Y GEX
# ══════════════════════════════════════════════════════════════════

def bs_gamma(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    try:
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        return float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))
    except Exception:
        return 0.0


def calcular_gex(calls, puts, spot, T, r=0.05):
    strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
    rows = []
    for K in strikes:
        c = calls[calls['strike'] == K]
        p = puts[puts['strike'] == K]
        call_oi  = int(c['openInterest'].values[0]) if len(c) > 0 else 0
        call_iv  = float(c['impliedVolatility'].values[0]) if len(c) > 0 else 0.0
        put_oi   = int(p['openInterest'].values[0]) if len(p) > 0 else 0
        put_iv   = float(p['impliedVolatility'].values[0]) if len(p) > 0 else 0.0
        call_gamma = bs_gamma(spot, K, T, r, call_iv)
        put_gamma  = bs_gamma(spot, K, T, r, put_iv)
        gex = (call_oi * call_gamma - put_oi * put_gamma) * 100 * spot
        rows.append({
            'strike'     : K,
            'gex'        : gex,
            'call_oi'    : call_oi,
            'put_oi'     : put_oi,
            'call_iv_pct': call_iv * 100,
            'put_iv_pct' : put_iv * 100,
        })
    return pd.DataFrame(rows)


def calcular_max_pain(calls, puts):
    all_strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
    pain = {}
    for P in all_strikes:
        cv = sum(max(0.0, P - k) * max(0, oi)
                 for k, oi in zip(calls['strike'], calls['openInterest'].fillna(0)))
        pv = sum(max(0.0, k - P) * max(0, oi)
                 for k, oi in zip(puts['strike'], puts['openInterest'].fillna(0)))
        pain[P] = cv + pv
    return min(pain, key=pain.get) if pain else None


# ══════════════════════════════════════════════════════════════════
# GREEKS ADICIONALES — VANNA, CHARM, SKEW
# ══════════════════════════════════════════════════════════════════

def bs_vanna(S, K, T, r, sigma):
    """Vanna = ∂Delta/∂IV = ∂Vega/∂S. Mide cuánto cambia el delta cuando cambia la IV."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    try:
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        return float(-norm.pdf(d1) * d2 / sigma)
    except:
        return 0.0

def bs_charm(S, K, T, r, sigma):
    """Charm = ∂Delta/∂t. Máximo en las últimas horas de opciones 0DTE."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    try:
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        return float(-norm.pdf(d1) * (2*r*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T)))
    except:
        return 0.0

def bs_delta(S, K, T, r, sigma, opt_type='call'):
    if T <= 0 or sigma <= 0:
        return 0.0
    try:
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        return float(norm.cdf(d1)) if opt_type == 'call' else float(norm.cdf(d1) - 1)
    except:
        return 0.0

def calcular_exposures_extra(calls, puts, spot, T, r=0.05):
    """Calcula Vanna Exposure y Charm Exposure por strike."""
    rows = []
    strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
    for K in strikes:
        c = calls[calls['strike'] == K]
        p = puts[puts['strike'] == K]
        call_oi = int(c['openInterest'].values[0]) if len(c) > 0 else 0
        call_iv = float(c['impliedVolatility'].values[0]) if len(c) > 0 else 0.0
        put_oi  = int(p['openInterest'].values[0]) if len(p) > 0 else 0
        put_iv  = float(p['impliedVolatility'].values[0]) if len(p) > 0 else 0.0

        call_vanna = bs_vanna(spot, K, T, r, call_iv)
        put_vanna  = bs_vanna(spot, K, T, r, put_iv)
        call_charm = bs_charm(spot, K, T, r, call_iv)
        put_charm  = bs_charm(spot, K, T, r, put_iv)

        # Vanna Exposure (positivo = dealers compran cuando IV sube)
        vex = (call_oi * call_vanna - put_oi * put_vanna) * 100 * spot
        # Charm Exposure (delta decay diario que genera re-hedging)
        cex = (call_oi * call_charm - put_oi * put_charm) * 100

        rows.append({'strike': K, 'vanna_exp': vex, 'charm_exp': cex})
    return pd.DataFrame(rows)

def calcular_skew_25d(calls, puts, spot, T, r=0.05):
    """Risk Reversal 25-delta: positivo = put skew (bajista), negativo = call skew (alcista)."""
    try:
        calls = calls.copy(); puts = puts.copy()
        calls['delta'] = calls.apply(lambda row: bs_delta(spot, row['strike'], T, r,
                                     row['impliedVolatility'], 'call'), axis=1)
        puts['delta']  = puts.apply( lambda row: bs_delta(spot, row['strike'], T, r,
                                     row['impliedVolatility'], 'put'),  axis=1)
        call_25 = calls.iloc[(calls['delta'] - 0.25).abs().argsort()[:1]]
        put_25  = puts.iloc[ (puts['delta']  - (-0.25)).abs().argsort()[:1]]
        c_iv = float(call_25['impliedVolatility'].values[0]) if len(call_25) > 0 else 0.0
        p_iv = float(put_25['impliedVolatility'].values[0])  if len(put_25)  > 0 else 0.0
        return round((p_iv - c_iv) * 100, 2)
    except:
        return 0.0

# ══════════════════════════════════════════════════════════════════
# VIX — TERM STRUCTURE Y RÉGIMEN
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def cargar_vix():
    """Carga el term structure completo del VIX y el VXN (Nasdaq Vol)."""
    tickers = {
        'VIX9D': '^VIX9D',
        'VIX'  : '^VIX',
        'VIX3M': '^VIX3M',
        'VIX6M': '^VIX6M',
        'VXN'  : '^VXN',   # VIX del Nasdaq 100
    }
    result = {}
    for name, sym in tickers.items():
        try:
            h = yf.Ticker(sym).history(period='5d', interval='5m')
            if h.empty:
                h = yf.Ticker(sym).history(period='1mo', interval='1d')
            result[name] = round(float(h['Close'].iloc[-1]), 2) if not h.empty else None
        except:
            result[name] = None

    vix   = result.get('VIX')
    vix9d = result.get('VIX9D')
    ratio = round(vix9d / vix, 3) if vix and vix9d and vix > 0 else None

    # Interpretación
    if vix and vix < 15:
        vix_regime = "Complacencia 🟢"
    elif vix and vix < 20:
        vix_regime = "Normal ⚪"
    elif vix and vix < 30:
        vix_regime = "Elevado 🟡"
    else:
        vix_regime = "Pánico 🔴"

    ts_regime = None
    if ratio:
        ts_regime = "Backwardation ⚠️" if ratio > 1.0 else "Contango ✅"

    result['ratio'] = ratio
    result['vix_regime']= vix_regime
    result['ts_regime'] = ts_regime
    return result

# ══════════════════════════════════════════════════════════════════
# DERIBIT — BTC GEX EN TIEMPO REAL (GRATUITO)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def cargar_btc_gex_deribit():
    """
    Obtiene el GEX de Bitcoin directamente desde Deribit API (gratis, sin autenticación).
    Deribit = >85% del mercado global de opciones BTC.
    """
    try:
        # Precio spot de BTC
        r = requests.get(
            "https://www.deribit.com/api/v2/public/get_index_price",
            params={"index_name": "btc_usd"}, timeout=8
        )
        spot = float(r.json()['result']['index_price'])

        # Opciones activas BTC
        r2 = requests.get(
            "https://www.deribit.com/api/v2/public/get_instruments",
            params={"currency": "BTC", "kind": "option", "expired": False}, timeout=8
        )
        instruments = r2.json().get('result', [])

        # Filtrar ±20% del spot y vencimientos próximos (≤45 días)
        now_ts = datetime.now().timestamp() * 1000
        relevant = [
            inst for inst in instruments
            if abs(inst.get('strike', 0) - spot) / spot <= 0.20
            and inst.get('expiration_timestamp', 0) - now_ts <= 45 * 86400 * 1000
        ]

        rows = []
        for inst in relevant[:80]:  # máximo 80 para no saturar
            try:
                r3 = requests.get(
                    "https://www.deribit.com/api/v2/public/get_ticker",
                    params={"instrument_name": inst['instrument_name']}, timeout=5
                )
                tick   = r3.json().get('result', {})
                greeks = tick.get('greeks', {})
                gamma  = greeks.get('gamma', 0) or 0
                oi     = tick.get('open_interest', 0) or 0
                # En Deribit: OI en contratos BTC (1 contrato = 1 BTC)
                # GEX = gamma × OI × spot² × 0.01 (por 1% de movimiento)
                gex = gamma * oi * spot**2 * 0.01
                if inst['option_type'] == 'put':
                    gex = -gex
                rows.append({
                    'strike'     : inst['strike'],
                    'option_type': inst['option_type'],
                    'gex'        : gex,
                    'oi'         : oi,
                    'iv'         : (tick.get('mark_iv') or 0),
                    'expiry'     : inst['instrument_name'].split('-')[1],
                })
            except:
                continue

        if not rows:
            return None

        df = pd.DataFrame(rows)
        gex_by_strike = df.groupby('strike')['gex'].sum().reset_index()
        gex_by_strike.columns = ['strike', 'gex']

        total_gex   = float(gex_by_strike['gex'].sum())
        max_pain_k  = gex_by_strike.loc[gex_by_strike['gex'].abs().idxmin(), 'strike'] if not gex_by_strike.empty else None

        # ATM IV
        atm_calls = df[(df['option_type'] == 'call')]
        if not atm_calls.empty:
            atm_row = atm_calls.iloc[(atm_calls['strike'] - spot).abs().argsort()[:1]]
            atm_iv  = float(atm_row['iv'].values[0]) if len(atm_row) > 0 else 0.0
        else:
            atm_iv = 0.0

        # OI calls vs puts
        call_oi = df[df['option_type'] == 'call']['oi'].sum()
        put_oi  = df[df['option_type'] == 'put']['oi'].sum()
        pc_oi   = put_oi / call_oi if call_oi > 0 else 1.0

        return {
            'source'     : 'Deribit',
            'spot'       : spot,
            'gex_df'     : gex_by_strike,
            'total_gex'  : total_gex,
            'total_gex_bn': total_gex / 1e9,
            'max_pain_fut': max_pain_k,
            'atm_iv'     : atm_iv,
            'pc_oi'      : pc_oi,
            'last_update': datetime.now().strftime("%H:%M:%S"),
        }
    except Exception as e:
        return None

# ══════════════════════════════════════════════════════════════════
# CARGA DE DATOS — GENÉRICA
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def get_expiries(etf_ticker: str):
    return list(yf.Ticker(etf_ticker).options)


@st.cache_data(ttl=900)
def cargar_datos(ikey: str, expiry: str):
    cfg = INSTRUMENTS[ikey]
    etf_tick = cfg["etf"]
    fut_tick  = cfg["futures"]

    etf = yf.Ticker(etf_tick)
    hist = etf.history(period="5d", interval="5m")
    if hist.empty:
        hist = etf.history(period="1mo", interval="1d")
    if hist.empty:
        raise ValueError(f"No se pudo obtener precio de {etf_tick}.")
    spot = float(hist['Close'].iloc[-1])

    # Precio del subyacente / futuros para conversión
    try:
        fut_hist = yf.Ticker(fut_tick).history(period="5d", interval="5m")
        if fut_hist.empty:
            fut_hist = yf.Ticker(fut_tick).history(period="1mo", interval="1d")
        fut_price = float(fut_hist['Close'].iloc[-1]) if not fut_hist.empty else None
    except Exception:
        fut_price = None

    if fut_price is None or fut_price <= 0:
        # Fallback: estimar ratio conocido
        fallback = {"MNQ": 40.0, "MES": 10.0, "GC": 10.5, "BTC": 1750.0}
        fut_price = spot * fallback.get(ikey, 10.0)

    ratio = fut_price / spot

    # Cadena de opciones
    chain = etf.option_chain(expiry)
    calls = chain.calls.copy()
    puts  = chain.puts.copy()

    for df in [calls, puts]:
        df.dropna(subset=['openInterest', 'impliedVolatility'], inplace=True)
        df['openInterest'] = df['openInterest'].fillna(0).astype(int)
        df['volume'] = df['volume'].fillna(0).astype(int)

    # Rango ±15% del spot
    low  = spot * 0.85
    high = spot * 1.15
    calls = calls[(calls['strike'] >= low) & (calls['strike'] <= high)].reset_index(drop=True)
    puts  = puts [(puts['strike']  >= low) & (puts['strike']  <= high)].reset_index(drop=True)

    exp_dt = datetime.strptime(expiry, "%Y-%m-%d")
    T = max((exp_dt - datetime.now()).days / 365.0, 1 / 365.0)

    gex_df   = calcular_gex(calls, puts, spot, T)
    max_pain = calcular_max_pain(calls, puts)
    total_gex = float(gex_df['gex'].sum())

    total_call_oi  = int(calls['openInterest'].sum())
    total_put_oi   = int(puts['openInterest'].sum())
    total_call_vol = int(calls['volume'].sum())
    total_put_vol  = int(puts['volume'].sum())
    pc_oi  = total_put_oi  / total_call_oi  if total_call_oi  > 0 else 1.0
    pc_vol = total_put_vol / total_call_vol if total_call_vol > 0 else 1.0

    atm_row = calls.iloc[(calls['strike'] - spot).abs().argsort()[:1]]
    atm_iv  = float(atm_row['impliedVolatility'].values[0]) * 100 if len(atm_row) > 0 else 0.0

    # Expected Move ±1σ
    em_dollar = spot * (atm_iv/100) * np.sqrt(T) * 0.6827
    em_pct    = em_dollar / spot * 100

    # Skew 25-delta
    skew_rr = calcular_skew_25d(calls, puts, spot, T)

    # Vanna & Charm exposures
    try:
        extra_df = calcular_exposures_extra(calls, puts, spot, T)
        total_vex = float(extra_df['vanna_exp'].sum())
        total_cex = float(extra_df['charm_exp'].sum())
    except:
        extra_df   = pd.DataFrame()
        total_vex  = 0.0
        total_cex  = 0.0

    return {
        'ikey'        : ikey,
        'spot'        : spot,
        'fut_price'   : fut_price,
        'ratio'       : ratio,
        'expiry'      : expiry,
        'gex_df'      : gex_df,
        'extra_df'    : extra_df,
        'total_gex'   : total_gex,
        'total_gex_bn': total_gex / 1e9,
        'total_vex'   : total_vex,
        'total_cex'   : total_cex,
        'max_pain_etf': max_pain,
        'max_pain_fut': max_pain * ratio if max_pain else None,
        'pc_oi'       : pc_oi,
        'pc_vol'      : pc_vol,
        'atm_iv'      : atm_iv,
        'em_dollar'   : em_dollar,
        'em_pct'      : em_pct,
        'skew_rr'     : skew_rr,
        'calls'       : calls,
        'puts'        : puts,
        'last_update' : datetime.now().strftime("%H:%M:%S"),
    }


# ══════════════════════════════════════════════════════════════════
# HISTORIAL — GENÉRICO
# ══════════════════════════════════════════════════════════════════

def load_history(ikey: str) -> dict:
    path = INSTRUMENTS[ikey]["history_file"]
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def log_daily_levels(data: dict):
    ikey  = data['ikey']
    today = datetime.now().strftime("%Y-%m-%d")
    ratio = data['ratio']
    gex   = data['total_gex']
    gex_df = data['gex_df']
    thr   = INSTRUMENTS[ikey]['gex_threshold']

    regime_str = "Positivo" if gex > thr else ("Negativo" if gex < -thr else "Neutro")
    regime_int = 0 if regime_str == "Positivo" else (1 if regime_str == "Negativo" else 2)

    nearby = gex_df.copy()
    nearby['fut'] = (nearby['strike'] * ratio).round(0).astype(int)

    def top_levels(df, n=5):
        lvls = df['fut'].tolist();  gexs = (df['gex'] / 1e6).round(1).tolist()
        while len(lvls) < n: lvls.append(0)
        while len(gexs) < n: gexs.append(0.0)
        return lvls[:n], gexs[:n]

    pos_df = nearby[nearby['gex'] > 0].nlargest(5, 'gex')
    neg_df = nearby[nearby['gex'] < 0].nsmallest(5, 'gex')
    pos_levels, pos_gex_m = top_levels(pos_df)
    neg_levels, neg_gex_m = top_levels(neg_df)

    entry = {
        "regime"      : regime_str,
        "regime_int"  : regime_int,
        "total_gex_bn": round(data['total_gex_bn'], 3),
        "fut_price"   : round(data['fut_price'], 1),
        "max_pain_fut": round(data['max_pain_fut'], 1) if data['max_pain_fut'] else 0,
        "pos_levels"  : pos_levels,
        "neg_levels"  : neg_levels,
        "pos_gex_m"   : pos_gex_m,
        "neg_gex_m"   : neg_gex_m,
        "expiry"      : data['expiry'],
        "atm_iv"      : round(data['atm_iv'], 2),
        "pc_oi"       : round(data['pc_oi'], 3),
        "saved_at"    : datetime.now().strftime("%H:%M"),
    }

    history = load_history(ikey)
    history[today] = entry
    path = INSTRUMENTS[ikey]["history_file"]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════
# PINE SCRIPT — GENÉRICO
# ══════════════════════════════════════════════════════════════════

def generate_pine_script(ikey: str, history: dict) -> str:
    if not history:
        return ""
    cfg  = INSTRUMENTS[ikey]
    days = sorted(history.keys())

    dates = []
    p1s, p2s, p3s, p4s, p5s = [], [], [], [], []
    n1s, n2s, n3s, n4s, n5s = [], [], [], [], []
    gp1s, gp2s, gp3s, gp4s, gp5s = [], [], [], [], []
    gn1s, gn2s, gn3s, gn4s, gn5s = [], [], [], [], []
    mps, regs = [], []

    for day in days:
        d   = history[day]
        pos = d.get('pos_levels', [0]*5); pgx = d.get('pos_gex_m', [0.0]*5)
        neg = d.get('neg_levels', [0]*5); ngx = d.get('neg_gex_m', [0.0]*5)
        while len(pos) < 5: pos.append(0); pgx = (pgx + [0.0]*5)[:5]
        while len(neg) < 5: neg.append(0); ngx = (ngx + [0.0]*5)[:5]
        dates.append(int(day.replace("-", "")))
        p1s.append(float(pos[0])); p2s.append(float(pos[1])); p3s.append(float(pos[2]))
        p4s.append(float(pos[3])); p5s.append(float(pos[4]))
        n1s.append(float(neg[0])); n2s.append(float(neg[1])); n3s.append(float(neg[2]))
        n4s.append(float(neg[3])); n5s.append(float(neg[4]))
        gp1s.append(float(pgx[0])); gp2s.append(float(pgx[1])); gp3s.append(float(pgx[2]))
        gp4s.append(float(pgx[3])); gp5s.append(float(pgx[4]))
        gn1s.append(float(ngx[0])); gn2s.append(float(ngx[1])); gn3s.append(float(ngx[2]))
        gn4s.append(float(ngx[3])); gn5s.append(float(ngx[4]))
        mps.append(float(d.get('max_pain_fut', 0)))
        regs.append(int(d.get('regime_int', 2)))

    fi  = lambda a: ", ".join(str(v) for v in a)
    ff  = lambda a: ", ".join(f"{v:.0f}" for v in a)
    fg  = lambda a: ", ".join(f"{v:.1f}" for v in a)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pname = cfg['pine_name']

    return f"""//@version=6
// ══════════════════════════════════════════════════════════════════
// {pname}  |  Auto-generado por Multi-Market Dashboard
// Actualizado : {now}
// Días        : {len(days)}  ({days[0]} → {days[-1]})
// ══════════════════════════════════════════════════════════════════
indicator("{pname}", overlay=true, max_lines_count=500, max_labels_count=500)

show_regime  = input.bool(true,  "Fondo de régimen",          group="⚙️ Visual")
show_mp      = input.bool(true,  "Mostrar Max Pain",           group="⚙️ Visual")
show_gex_val = input.bool(true,  "Mostrar $ GEX en etiqueta", group="⚙️ Visual")
lbl_size_in  = input.string("small","Tamaño etiqueta", options=["tiny","small","normal"], group="⚙️ Visual")
lw_main      = input.int(2, "Grosor línea principal", group="⚙️ Visual", minval=1, maxval=4)
lw_sec       = input.int(1, "Grosor líneas secundarias", group="⚙️ Visual", minval=1, maxval=4)
show_table   = input.bool(true, "Tabla sticky", group="⚙️ Visual")

C_POS = color.new(#00c851, 20)
C_NEG = color.new(#ff4444, 20)
C_MP  = color.new(#ffbb33, 30)

get_f(array<float> a, int i) =>
    v = i >= 0 and i < array.size(a) ? array.get(a, i) : 0.0
    v > 0.0 ? v : float(na)

get_n(array<float> a, int i) =>
    i >= 0 and i < array.size(a) ? array.get(a, i) : 0.0

lbl_sz() =>
    lbl_size_in == "tiny" ? size.tiny : lbl_size_in == "normal" ? size.normal : size.small

fill_row(table t, int r, string pfx, float lvl, float gm, bool is_pos, color col) =>
    if not na(lvl)
        _gx = show_gex_val and gm != 0.0 ? (is_pos ? "+" : "") + str.tostring(math.round(gm)) + "M" : ""
        table.cell(t, 0, r, pfx, text_color=col, text_size=size.small, bgcolor=color.new(col, 82))
        table.cell(t, 1, r, str.tostring(math.round(lvl), "#,###"), text_color=color.white, text_size=size.small, bgcolor=color.new(#0d1117, 20))
        table.cell(t, 2, r, _gx, text_color=col, text_size=size.tiny, bgcolor=color.new(#0d1117, 20))
    else
        _tr = color.new(#0d1117, 100)
        table.cell(t, 0, r, "", bgcolor=_tr, text_size=size.tiny)
        table.cell(t, 1, r, "", bgcolor=_tr, text_size=size.tiny)
        table.cell(t, 2, r, "", bgcolor=_tr, text_size=size.tiny)

draw_lbl(int bi, float lvl, string pfx, float gm, bool is_pos, color col) =>
    label result = na
    if not na(lvl)
        gx_part = show_gex_val and gm != 0.0 ? "  " + (is_pos ? "+" : "") + str.tostring(math.round(gm)) + "M" : ""
        txt = pfx + "  " + str.tostring(math.round(lvl), "#,###") + gx_part
        result := label.new(bi, lvl, txt, color=color.new(col,45), textcolor=color.white,
                  style=label.style_label_left, size=lbl_sz(), xloc=xloc.bar_index)
    result

var hist_dates = array.from({fi(dates)})
var pos1 = array.from({ff(p1s)})
var pos2 = array.from({ff(p2s)})
var pos3 = array.from({ff(p3s)})
var pos4 = array.from({ff(p4s)})
var pos5 = array.from({ff(p5s)})
var neg1 = array.from({ff(n1s)})
var neg2 = array.from({ff(n2s)})
var neg3 = array.from({ff(n3s)})
var neg4 = array.from({ff(n4s)})
var neg5 = array.from({ff(n5s)})
var maxp = array.from({ff(mps)})
var regs = array.from({fi(regs)})
var gxp1 = array.from({fg(gp1s)})
var gxp2 = array.from({fg(gp2s)})
var gxp3 = array.from({fg(gp3s)})
var gxp4 = array.from({fg(gp4s)})
var gxp5 = array.from({fg(gp5s)})
var gxn1 = array.from({fg(gn1s)})
var gxn2 = array.from({fg(gn2s)})
var gxn3 = array.from({fg(gn3s)})
var gxn4 = array.from({fg(gn4s)})
var gxn5 = array.from({fg(gn5s)})

bar_date = year * 10000 + month * 100 + dayofmonth
idx = -1
for i = 0 to array.size(hist_dates) - 1
    if array.get(hist_dates, i) == bar_date
        idx := i
        break

p1v = get_f(pos1, idx); p2v = get_f(pos2, idx); p3v = get_f(pos3, idx)
p4v = get_f(pos4, idx); p5v = get_f(pos5, idx)
n1v = get_f(neg1, idx); n2v = get_f(neg2, idx); n3v = get_f(neg3, idx)
n4v = get_f(neg4, idx); n5v = get_f(neg5, idx)
mpv = show_mp ? get_f(maxp, idx) : float(na)

plot(p1v, "GEX+ 1", C_POS, lw_main, plot.style_linebr)
plot(p2v, "GEX+ 2", C_POS, lw_sec,  plot.style_linebr)
plot(p3v, "GEX+ 3", C_POS, lw_sec,  plot.style_linebr)
plot(p4v, "GEX+ 4", C_POS, lw_sec,  plot.style_linebr)
plot(p5v, "GEX+ 5", C_POS, lw_sec,  plot.style_linebr)
plot(n1v, "GEX- 1", C_NEG, lw_main, plot.style_linebr)
plot(n2v, "GEX- 2", C_NEG, lw_sec,  plot.style_linebr)
plot(n3v, "GEX- 3", C_NEG, lw_sec,  plot.style_linebr)
plot(n4v, "GEX- 4", C_NEG, lw_sec,  plot.style_linebr)
plot(n5v, "GEX- 5", C_NEG, lw_sec,  plot.style_linebr)
plot(mpv, "MaxPain", C_MP, lw_sec, plot.style_linebr)

reg = idx >= 0 and idx < array.size(regs) ? array.get(regs, idx) : -1
var label[] _s_lbls = array.new<label>()
var line[]  _s_lns  = array.new<line>()
var table   _tbl    = na

day_changed = ta.change(bar_date) != 0 and not na(bar_date[1])
if day_changed
    di = idx[1]
    bi = bar_index
    _p1 = get_f(pos1, di)
    if not na(_p1)
        draw_lbl(bi, _p1, "▲ GEX+1", get_n(gxp1, di), true, C_POS)
    _p2 = get_f(pos2, di)
    if not na(_p2)
        draw_lbl(bi, _p2, "▲ GEX+2", get_n(gxp2, di), true, C_POS)
    _p3 = get_f(pos3, di)
    if not na(_p3)
        draw_lbl(bi, _p3, "▲ GEX+3", get_n(gxp3, di), true, C_POS)
    _p4 = get_f(pos4, di)
    if not na(_p4)
        draw_lbl(bi, _p4, "▲ GEX+4", get_n(gxp4, di), true, C_POS)
    _p5 = get_f(pos5, di)
    if not na(_p5)
        draw_lbl(bi, _p5, "▲ GEX+5", get_n(gxp5, di), true, C_POS)
    _n1 = get_f(neg1, di)
    if not na(_n1)
        draw_lbl(bi, _n1, "▼ GEX-1", get_n(gxn1, di), false, C_NEG)
    _n2 = get_f(neg2, di)
    if not na(_n2)
        draw_lbl(bi, _n2, "▼ GEX-2", get_n(gxn2, di), false, C_NEG)
    _n3 = get_f(neg3, di)
    if not na(_n3)
        draw_lbl(bi, _n3, "▼ GEX-3", get_n(gxn3, di), false, C_NEG)
    _n4 = get_f(neg4, di)
    if not na(_n4)
        draw_lbl(bi, _n4, "▼ GEX-4", get_n(gxn4, di), false, C_NEG)
    _n5 = get_f(neg5, di)
    if not na(_n5)
        draw_lbl(bi, _n5, "▼ GEX-5", get_n(gxn5, di), false, C_NEG)
    if show_mp
        _mp = get_f(maxp, di)
        if not na(_mp)
            draw_lbl(bi, _mp, "⚡MaxPain", 0.0, true, C_MP)

if barstate.islast and idx >= 0
    for _l in _s_lbls
        label.delete(_l)
    for _ln in _s_lns
        line.delete(_ln)
    array.clear(_s_lbls)
    array.clear(_s_lns)
    _off = 50
    _bi  = bar_index + _off
    _bi0 = bar_index
    if not na(p1v)
        array.push(_s_lns,  line.new(_bi0, p1v, _bi, p1v, color=color.new(C_POS,50), width=lw_main))
        array.push(_s_lbls, draw_lbl(_bi, p1v, "▲ GEX+1", get_n(gxp1, idx), true,  C_POS))
    if not na(p2v)
        array.push(_s_lns,  line.new(_bi0, p2v, _bi, p2v, color=color.new(C_POS,50), width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, p2v, "▲ GEX+2", get_n(gxp2, idx), true,  C_POS))
    if not na(p3v)
        array.push(_s_lns,  line.new(_bi0, p3v, _bi, p3v, color=color.new(C_POS,50), width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, p3v, "▲ GEX+3", get_n(gxp3, idx), true,  C_POS))
    if not na(p4v)
        array.push(_s_lns,  line.new(_bi0, p4v, _bi, p4v, color=color.new(C_POS,50), width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, p4v, "▲ GEX+4", get_n(gxp4, idx), true,  C_POS))
    if not na(p5v)
        array.push(_s_lns,  line.new(_bi0, p5v, _bi, p5v, color=color.new(C_POS,50), width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, p5v, "▲ GEX+5", get_n(gxp5, idx), true,  C_POS))
    if not na(n1v)
        array.push(_s_lns,  line.new(_bi0, n1v, _bi, n1v, color=color.new(C_NEG,50), width=lw_main))
        array.push(_s_lbls, draw_lbl(_bi, n1v, "▼ GEX-1", get_n(gxn1, idx), false, C_NEG))
    if not na(n2v)
        array.push(_s_lns,  line.new(_bi0, n2v, _bi, n2v, color=color.new(C_NEG,50), width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, n2v, "▼ GEX-2", get_n(gxn2, idx), false, C_NEG))
    if not na(n3v)
        array.push(_s_lns,  line.new(_bi0, n3v, _bi, n3v, color=color.new(C_NEG,50), width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, n3v, "▼ GEX-3", get_n(gxn3, idx), false, C_NEG))
    if not na(n4v)
        array.push(_s_lns,  line.new(_bi0, n4v, _bi, n4v, color=color.new(C_NEG,50), width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, n4v, "▼ GEX-4", get_n(gxn4, idx), false, C_NEG))
    if not na(n5v)
        array.push(_s_lns,  line.new(_bi0, n5v, _bi, n5v, color=color.new(C_NEG,50), width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, n5v, "▼ GEX-5", get_n(gxn5, idx), false, C_NEG))
    if show_mp and not na(mpv)
        array.push(_s_lns,  line.new(_bi0, mpv, _bi, mpv, color=color.new(C_MP,50),  width=lw_sec))
        array.push(_s_lbls, draw_lbl(_bi, mpv, "⚡MaxPain", 0.0, true, C_MP))

    if not show_table
        if not na(_tbl): table.delete(_tbl); _tbl := na
    else
        if na(_tbl)
            _tbl := table.new(position.middle_right, 3, 13,
                     bgcolor=color.new(#0d1117,10), border_color=color.new(color.gray,65),
                     border_width=1, frame_color=color.new(color.gray,55), frame_width=1)
        _hbg = color.new(#1a1a2e,25)
        table.cell(_tbl,0,0," Nivel  ",text_color=color.gray,text_size=size.tiny,bgcolor=_hbg)
        table.cell(_tbl,1,0," Precio ",text_color=color.gray,text_size=size.tiny,bgcolor=_hbg)
        table.cell(_tbl,2,0," GEX $  ",text_color=color.gray,text_size=size.tiny,bgcolor=_hbg)
        fill_row(_tbl, 1,"▲ GEX+1",p1v,get_n(gxp1,idx),true,C_POS)
        fill_row(_tbl, 2,"▲ GEX+2",p2v,get_n(gxp2,idx),true,C_POS)
        fill_row(_tbl, 3,"▲ GEX+3",p3v,get_n(gxp3,idx),true,C_POS)
        fill_row(_tbl, 4,"▲ GEX+4",p4v,get_n(gxp4,idx),true,C_POS)
        fill_row(_tbl, 5,"▲ GEX+5",p5v,get_n(gxp5,idx),true,C_POS)
        fill_row(_tbl, 6,"⚡MaxPain",show_mp ? mpv : float(na),0.0,true,C_MP)
        fill_row(_tbl, 7,"▼ GEX-1",n1v,get_n(gxn1,idx),false,C_NEG)
        fill_row(_tbl, 8,"▼ GEX-2",n2v,get_n(gxn2,idx),false,C_NEG)
        fill_row(_tbl, 9,"▼ GEX-3",n3v,get_n(gxn3,idx),false,C_NEG)
        fill_row(_tbl,10,"▼ GEX-4",n4v,get_n(gxn4,idx),false,C_NEG)
        fill_row(_tbl,11,"▼ GEX-5",n5v,get_n(gxn5,idx),false,C_NEG)
        _rc = reg==0 ? C_POS : reg==1 ? C_NEG : C_MP
        _rt = reg==0 ? "● GEX Positivo" : reg==1 ? "● GEX Negativo" : "● GEX Neutro"
        _fbg = color.new(#0d1117,15)
        table.cell(_tbl,0,12,_rt,text_color=_rc,text_size=size.tiny,bgcolor=_fbg)
        table.cell(_tbl,1,12,"",text_size=size.tiny,bgcolor=_fbg)
        table.cell(_tbl,2,12,"",text_size=size.tiny,bgcolor=_fbg)

bgcolor(show_regime and reg==0 ? color.new(#00c851,97) :
        show_regime and reg==1 ? color.new(#ff4444,97) : na, title="Régimen gamma")
"""


# ══════════════════════════════════════════════════════════════════
# CHART — GENÉRICO
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def cargar_candles(ticker: str, period: str, interval: str):
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
        if hist.empty:
            return []
        hist = hist.reset_index()
        time_col = 'Datetime' if 'Datetime' in hist.columns else 'Date'
        records = []
        for _, row in hist.iterrows():
            ts = int(row[time_col].timestamp())
            records.append({
                'time' : ts,
                'open' : round(float(row['Open']),  2),
                'high' : round(float(row['High']),  2),
                'low'  : round(float(row['Low']),   2),
                'close': round(float(row['Close']), 2),
            })
        return records
    except Exception:
        return []


def preparar_niveles_chart(gex_df, ratio, max_pain_fut, spot_fut, n=6):
    levels = []
    spot_etf = spot_fut / ratio
    low_f  = spot_etf * 0.93
    high_f = spot_etf * 1.07
    nearby = gex_df[(gex_df['strike'] >= low_f) & (gex_df['strike'] <= high_f)]

    for _, row in nearby[nearby['gex'] > 0].nlargest(n, 'gex').iterrows():
        nq_lvl = round(row['strike'] * ratio, 2)
        gex_m  = row['gex'] / 1e6
        levels.append({'price': nq_lvl, 'color': '#00c851', 'width': 2,
                        'dashed': True, 'title': f'GEX +${gex_m:.0f}M'})

    for _, row in nearby[nearby['gex'] < 0].nsmallest(n, 'gex').iterrows():
        nq_lvl = round(row['strike'] * ratio, 2)
        gex_m  = row['gex'] / 1e6
        levels.append({'price': nq_lvl, 'color': '#ff4444', 'width': 2,
                        'dashed': True, 'title': f'GEX ${gex_m:.0f}M'})

    if max_pain_fut:
        levels.append({'price': round(max_pain_fut, 2), 'color': '#ffbb33',
                        'width': 2, 'dashed': True, 'title': 'Max Pain'})
    return levels


def build_chart_html(candles: list, levels: list, ticker_label: str, height: int = 540) -> str:
    candles_json = json.dumps(candles)
    levels_json  = json.dumps(levels)
    return f"""<!DOCTYPE html><html><head>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:#1e2130; }}
  #tv-chart {{ width:100%; height:{height}px; }}
  #ohlc-legend {{
    position:absolute; top:8px; left:8px; z-index:100;
    background:rgba(20,23,36,0.82); border:1px solid #2d3250;
    border-radius:6px; padding:5px 10px;
    color:#c9d1d9; font-family:'Courier New',monospace; font-size:12px;
    pointer-events:none;
  }}
  #level-legend {{
    position:absolute; top:8px; right:8px; z-index:100;
    background:rgba(20,23,36,0.82); border:1px solid #2d3250;
    border-radius:6px; padding:6px 10px;
    color:#c9d1d9; font-family:'Courier New',monospace; font-size:11px;
    pointer-events:none; max-width:210px;
  }}
</style>
</head><body>
<div style="position:relative;">
  <div id="tv-chart"></div>
  <div id="ohlc-legend">{ticker_label}</div>
  <div id="level-legend">
    <span style="color:#00c851;">&#9644;</span> GEX Positivo (freno)<br>
    <span style="color:#ff4444;">&#9644;</span> GEX Negativo (aceleración)<br>
    <span style="color:#ffbb33;">&#9644;</span> Max Pain
  </div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
<script>
const candleData  = {candles_json};
const gammaLevels = {levels_json};
const chart = LightweightCharts.createChart(document.getElementById('tv-chart'), {{
  layout: {{ background:{{color:'#1e2130'}}, textColor:'#c9d1d9' }},
  grid: {{ vertLines:{{color:'#252840'}}, horzLines:{{color:'#252840'}} }},
  crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
  rightPriceScale: {{ borderColor:'#2d3250' }},
  timeScale: {{ borderColor:'#2d3250', timeVisible:true, secondsVisible:false }},
  width: document.getElementById('tv-chart').clientWidth,
  height: {height},
}});
const series = chart.addCandlestickSeries({{
  upColor:'#00c851', downColor:'#ff4444',
  borderVisible:false, wickUpColor:'#00c851', wickDownColor:'#ff4444',
}});
if (candleData.length > 0) series.setData(candleData);
const LS = LightweightCharts.LineStyle;
gammaLevels.forEach(lvl => {{
  series.createPriceLine({{
    price: lvl.price, color: lvl.color, lineWidth: lvl.width || 2,
    lineStyle: lvl.dashed ? LS.Dashed : LS.Solid,
    title: lvl.title, axisLabelVisible: true,
  }});
}});
chart.timeScale().fitContent();
new ResizeObserver(entries => {{
  chart.applyOptions({{ width: entries[0].contentRect.width }});
}}).observe(document.getElementById('tv-chart'));
const legend = document.getElementById('ohlc-legend');
chart.subscribeCrosshairMove(param => {{
  if (!param.time) {{ legend.innerHTML = '{ticker_label}'; return; }}
  const d = param.seriesData.get(series);
  if (!d) return;
  const chg = d.close - d.open;
  const chgPct = (chg / d.open * 100).toFixed(2);
  const color = chg >= 0 ? '#00c851' : '#ff4444';
  const sign = chg >= 0 ? '+' : '';
  legend.innerHTML =
    `<span style="color:#aaa;">O</span> ${{d.open.toFixed(2)}} &nbsp;`+
    `<span style="color:#aaa;">H</span> ${{d.high.toFixed(2)}} &nbsp;`+
    `<span style="color:#aaa;">L</span> ${{d.low.toFixed(2)}} &nbsp;`+
    `<span style="color:#aaa;">C</span> ${{d.close.toFixed(2)}} &nbsp;`+
    `<span style="color:${{color}};">(${{sign}}${{chg.toFixed(2)}} / ${{sign}}${{chgPct}}%)</span>`;
}});
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════
# STOCKS — CARGA DE DATOS (Budget + Top 20)
# ══════════════════════════════════════════════════════════════════

IV_HISTORY_FILE = BASE_DIR / "stocks_iv_history.json"

def _load_iv_history() -> dict:
    if not IV_HISTORY_FILE.exists(): return {}
    try:
        with open(IV_HISTORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def _save_iv_history(ticker: str, iv: float):
    today = datetime.now().strftime("%Y-%m-%d")
    hist  = _load_iv_history()
    if ticker not in hist: hist[ticker] = []
    if today not in [e['date'] for e in hist[ticker]]:
        hist[ticker].append({"date": today, "iv": round(iv, 4)})
        hist[ticker] = hist[ticker][-252:]
    with open(IV_HISTORY_FILE, 'w', encoding='utf-8') as f: json.dump(hist, f, indent=2)

def _iv_rank(ticker: str, current_iv: float):
    entries = _load_iv_history().get(ticker, [])
    if len(entries) < 10: return None, None
    ivs = [e['iv'] for e in entries]
    iv_min, iv_max = min(ivs), max(ivs)
    if iv_max == iv_min: return 50.0, 50.0
    return round((current_iv - iv_min)/(iv_max - iv_min)*100, 1), round(sum(1 for v in ivs if v < current_iv)/len(ivs)*100, 1)

@st.cache_data(ttl=3600)
def get_expiries_stock(ticker: str):
    try: return list(yf.Ticker(ticker).options)[:12]
    except: return []

@st.cache_data(ttl=900)
def cargar_datos_stock(ticker: str, expiry: str):
    tk = yf.Ticker(ticker)
    h  = tk.history(period="5d", interval="15m")
    if h.empty:
        h = tk.history(period="1mo", interval="1d")
    if h.empty: raise ValueError(f"Sin precio para {ticker}")
    spot = float(h['Close'].iloc[-1])
    h2   = tk.history(period="5d", interval="1d")
    prev = float(h2['Close'].iloc[-2]) if len(h2) >= 2 else spot
    change_pct = (spot - prev) / prev * 100 if prev else 0.0

    chain = tk.option_chain(expiry)
    calls, puts = chain.calls.copy(), chain.puts.copy()
    for df in [calls, puts]:
        df.dropna(subset=['openInterest','impliedVolatility'], inplace=True)
        df['openInterest'] = df['openInterest'].fillna(0).astype(int)
        df['volume']       = df['volume'].fillna(0).astype(int)
    lo, hi = spot*0.80, spot*1.20
    calls = calls[(calls['strike']>=lo)&(calls['strike']<=hi)].reset_index(drop=True)
    puts  = puts[ (puts['strike'] >=lo)&(puts['strike'] <=hi)].reset_index(drop=True)

    exp_dt = datetime.strptime(expiry, "%Y-%m-%d")
    T = max((exp_dt - datetime.now()).days/365.0, 1/365.0)
    dte = max((exp_dt - datetime.now()).days, 0)

    gex_df   = calcular_gex(calls, puts, spot, T)
    max_pain = calcular_max_pain(calls, puts)
    total_gex = float(gex_df['gex'].sum())

    tc_oi = int(calls['openInterest'].sum()); tp_oi = int(puts['openInterest'].sum())
    tc_v  = int(calls['volume'].sum());       tp_v  = int(puts['volume'].sum())
    pc_oi = tp_oi/tc_oi if tc_oi>0 else 1.0
    pc_vol= tp_v/tc_v   if tc_v >0 else 1.0

    atm_row = calls.iloc[(calls['strike']-spot).abs().argsort()[:1]]
    atm_iv  = float(atm_row['impliedVolatility'].values[0])*100 if len(atm_row)>0 else 0.0
    em_d    = spot*(atm_iv/100)*np.sqrt(T)*0.6827
    em_p    = em_d/spot*100

    skew = calcular_skew_25d(calls, puts, spot, T)
    rr_val = skew if isinstance(skew, float) else skew.get('risk_reversal', 0.0)

    try:
        cal = tk.calendar
        earnings = str(cal.columns[0].date()) if cal is not None and not cal.empty and hasattr(cal.columns[0],'date') else "N/D"
    except: earnings = "N/D"

    if atm_iv > 0: _save_iv_history(ticker, atm_iv)
    iv_rank, iv_pct = _iv_rank(ticker, atm_iv)

    return {'ticker':ticker,'spot':spot,'change_pct':change_pct,'expiry':expiry,'dte':dte,'T':T,
            'gex_df':gex_df,'total_gex':total_gex,'total_gex_m':total_gex/1e6,
            'max_pain':max_pain,'pc_oi':pc_oi,'pc_vol':pc_vol,'atm_iv':atm_iv,
            'em_dollar':em_d,'em_pct':em_p,'skew_rr':rr_val,
            'calls':calls,'puts':puts,'iv_rank':iv_rank,'iv_pct':iv_pct,
            'earnings':earnings,'last_update':datetime.now().strftime("%H:%M:%S")}

@st.cache_data(ttl=3600)
def cargar_historico_stock(ticker: str, period: str = "1y"):
    hist = yf.Ticker(ticker).history(period=period, interval="1d")
    if hist.empty: return pd.DataFrame()
    hist = hist.reset_index()
    hist['SMA20']  = hist['Close'].rolling(20).mean()
    hist['SMA40']  = hist['Close'].rolling(40).mean()
    hist['SMA100'] = hist['Close'].rolling(100).mean()
    hist['SMA200'] = hist['Close'].rolling(200).mean()
    std = hist['Close'].rolling(20).std()
    hist['BB_upper'] = hist['SMA20'] + 2*std
    hist['BB_lower'] = hist['SMA20'] - 2*std
    delta = hist['Close'].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain/loss
    hist['RSI'] = 100 - (100/(1+rs))
    return hist

def _hist_to_tv(hist: pd.DataFrame):
    """Convert daily df to lightweight-charts candle + indicator lists."""
    tc = 'Date' if 'Date' in hist.columns else 'Datetime'
    candles, ma20, ma40, ma100, ma200, rsi = [], [], [], [], [], []
    for _, row in hist.iterrows():
        try:
            ds = str(row[tc])[:10]
            if pd.isna(row['Close']): continue
            candles.append({'time':ds,'open':round(float(row['Open']),4),
                            'high':round(float(row['High']),4),'low':round(float(row['Low']),4),
                            'close':round(float(row['Close']),4)})
            for lst, col in [(ma20,'SMA20'),(ma40,'SMA40'),(ma100,'SMA100'),(ma200,'SMA200'),(rsi,'RSI')]:
                v = row.get(col, float('nan'))
                if not pd.isna(v): lst.append({'time':ds,'value':round(float(v),4)})
        except: continue
    return candles, ma20, ma40, ma100, ma200, rsi

def build_stock_chart_html(hist: pd.DataFrame, gex_df: pd.DataFrame, spot: float,
                            max_pain, em_dollar: float, ticker: str, height: int = 620) -> str:
    candles, ma20, ma40, ma100, ma200, rsi_data = _hist_to_tv(hist)
    # GEX levels
    levels = []
    nearby = gex_df[(gex_df['strike']>=spot*0.92)&(gex_df['strike']<=spot*1.08)]
    for _, r in nearby[nearby['gex']>0].nlargest(5,'gex').iterrows():
        levels.append({'price':round(float(r['strike']),2),'color':'#00c851','width':2,'dashed':True,'title':f'GEX+ ${r["gex"]/1e6:.1f}M'})
    for _, r in nearby[nearby['gex']<0].nsmallest(5,'gex').iterrows():
        levels.append({'price':round(float(r['strike']),2),'color':'#ff4444','width':2,'dashed':True,'title':f'GEX- ${r["gex"]/1e6:.1f}M'})
    if max_pain:
        levels.append({'price':round(float(max_pain),2),'color':'#ffbb33','width':2,'dashed':True,'title':'Max Pain'})
    if em_dollar > 0:
        levels.append({'price':round(spot+em_dollar,2),'color':'rgba(255,255,255,0.35)','width':1,'dashed':True,'title':'+1σ'})
        levels.append({'price':round(spot-em_dollar,2),'color':'rgba(255,255,255,0.35)','width':1,'dashed':True,'title':'-1σ'})

    mh = int(height*0.72); rh = height - mh - 6
    cj  = json.dumps(candles);   lj = json.dumps(levels)
    m20j= json.dumps(ma20);      m40j= json.dumps(ma40)
    m100j=json.dumps(ma100);     m200j=json.dumps(ma200)
    rj  = json.dumps(rsi_data)
    return f"""<!DOCTYPE html><html><head>
<style>*{{box-sizing:border-box;margin:0;padding:0;}}body{{background:#1e2130;}}
#legend{{position:absolute;top:6px;left:8px;z-index:100;background:rgba(20,23,36,.85);
  border:1px solid #2d3250;border-radius:5px;padding:4px 8px;color:#c9d1d9;
  font-family:'Courier New',monospace;font-size:11px;pointer-events:none;}}
</style></head><body>
<div id="wrap" style="position:relative;">
  <div id="legend">{ticker}</div>
  <div id="tv-main" style="height:{mh}px;width:100%;"></div>
  <div style="height:4px;background:#161b22;"></div>
  <div id="tv-rsi"  style="height:{rh}px;width:100%;"></div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
<script>
const LS=LightweightCharts.LineStyle;
const base={{layout:{{background:{{color:'#1e2130'}},textColor:'#c9d1d9'}},
  grid:{{vertLines:{{color:'#252840'}},horzLines:{{color:'#252840'}}}},
  rightPriceScale:{{borderColor:'#2d3250'}},
  crosshair:{{mode:LightweightCharts.CrosshairMode.Normal}}}};
const cMain=LightweightCharts.createChart(document.getElementById('tv-main'),
  {{...base,timeScale:{{borderColor:'#2d3250',visible:false}},width:document.getElementById('wrap').clientWidth,height:{mh}}});
const cRSI=LightweightCharts.createChart(document.getElementById('tv-rsi'),
  {{...base,timeScale:{{borderColor:'#2d3250',timeVisible:true}},width:document.getElementById('wrap').clientWidth,height:{rh}}});
const cs=cMain.addCandlestickSeries({{upColor:'#00c851',downColor:'#ff4444',borderVisible:false,wickUpColor:'#00c851',wickDownColor:'#ff4444'}});
cs.setData({cj});
{lj}.forEach(l=>cs.createPriceLine({{price:l.price,color:l.color,lineWidth:l.width,lineStyle:l.dashed?LS.Dashed:LS.Solid,title:l.title,axisLabelVisible:true}}));
const ma20s=cMain.addLineSeries({{color:'#58a6ff',lineWidth:1.5,title:'SMA20',priceLineVisible:false,lastValueVisible:false}});ma20s.setData({m20j});
const ma40s=cMain.addLineSeries({{color:'#3fb950',lineWidth:1.5,title:'SMA40',priceLineVisible:false,lastValueVisible:false}});ma40s.setData({m40j});
const ma100s=cMain.addLineSeries({{color:'#e3b341',lineWidth:2,title:'SMA100',priceLineVisible:false,lastValueVisible:false}});ma100s.setData({m100j});
const ma200s=cMain.addLineSeries({{color:'#ff6b6b',lineWidth:2.5,title:'SMA200',priceLineVisible:false,lastValueVisible:false}});ma200s.setData({m200j});
const rs=cRSI.addLineSeries({{color:'#c792ea',lineWidth:1.5,priceLineVisible:false,lastValueVisible:true}});rs.setData({rj});
[{{p:70,c:'rgba(255,68,68,0.5)',t:'OB'}},{{p:50,c:'rgba(255,255,255,0.18)',t:''}},{{p:30,c:'rgba(0,200,81,0.5)',t:'OS'}}].forEach(l=>
  rs.createPriceLine({{price:l.p,color:l.c,lineWidth:1,lineStyle:LS.Dashed,title:l.t,axisLabelVisible:true}}));
cMain.timeScale().subscribeVisibleLogicalRangeChange(r=>{{if(r!==null)cRSI.timeScale().setVisibleLogicalRange(r);}});
cRSI.timeScale().subscribeVisibleLogicalRangeChange(r=>{{if(r!==null)cMain.timeScale().setVisibleLogicalRange(r);}});
cMain.timeScale().fitContent();
const leg=document.getElementById('legend');
cMain.subscribeCrosshairMove(p=>{{
  if(!p.time){{leg.innerHTML='{ticker}';return;}}
  const d=p.seriesData.get(cs);if(!d)return;
  const ch=d.close-d.open,pct=(ch/d.open*100).toFixed(2),col=ch>=0?'#00c851':'#ff4444',sg=ch>=0?'+':'';
  leg.innerHTML=`<span style='color:#aaa'>O</span> ${{d.open.toFixed(2)}} <span style='color:#aaa'>H</span> ${{d.high.toFixed(2)}} <span style='color:#aaa'>L</span> ${{d.low.toFixed(2)}} <span style='color:#aaa'>C</span> ${{d.close.toFixed(2)}} <span style='color:${{col}}'>(${{sg}}${{ch.toFixed(2)}} ${{sg}}${{pct}}%)</span>`;
}});
new ResizeObserver(e=>{{const w=e[0].contentRect.width;cMain.applyOptions({{width:w}});cRSI.applyOptions({{width:w}});}}).observe(document.getElementById('wrap'));
</script></body></html>"""

# ══════════════════════════════════════════════════════════════════
# RENDERER — OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════

def render_overview(all_data: dict):
    """Renderiza el tab de Overview con cards de los 4 instrumentos."""

    st.markdown("### 🎯 Estado del Mercado — Resumen")
    st.caption("Régimen gamma y métricas clave de los 4 instrumentos en un solo vistazo.")

    cols = st.columns(4)

    for idx, (ikey, cfg) in enumerate(INSTRUMENTS.items()):
        with cols[idx]:
            data = all_data.get(ikey)
            accent = cfg["accent"]

            if data is None:
                st.markdown(f"""
                <div class="mini-card" style="border-color:{accent}40;">
                    <div style="font-size:1.3rem;">{cfg['emoji']}</div>
                    <div style="color:{accent}; font-weight:bold; font-size:0.9rem;">{cfg['label']}</div>
                    <div style="color:#666; margin-top:8px; font-size:0.8rem;">Sin datos</div>
                </div>
                """, unsafe_allow_html=True)
                continue

            thr = cfg["gex_threshold"]
            gex = data['total_gex']

            if gex > thr:
                regime_icon  = "🟢"
                regime_label = "GEX POSITIVO"
                regime_color = "#00c851"
                regime_bg    = "rgba(0,200,81,0.08)"
                regime_border= "#00c851"
            elif gex < -thr:
                regime_icon  = "🔴"
                regime_label = "GEX NEGATIVO"
                regime_color = "#ff4444"
                regime_bg    = "rgba(255,68,68,0.08)"
                regime_border= "#ff4444"
            else:
                regime_icon  = "🟡"
                regime_label = "NEUTRO"
                regime_color = "#ffbb33"
                regime_bg    = "rgba(255,187,51,0.08)"
                regime_border= "#ffbb33"

            fut_str = f"{data['fut_price']:,.0f}" if data['fut_price'] < 100000 else f"{data['fut_price']:,.0f}"
            mp_str  = f"{data['max_pain_fut']:,.0f}" if data['max_pain_fut'] else "N/D"
            gex_str = f"{data['total_gex_bn']:+.2f}B"

            st.markdown(f"""
            <div style="
                padding:16px 14px; border-radius:12px; text-align:center;
                background:{regime_bg}; border:2px solid {regime_border};
                margin-bottom:8px;
            ">
                <div style="font-size:1.6rem; margin-bottom:4px;">{cfg['emoji']}</div>
                <div style="color:{accent}; font-weight:700; font-size:0.85rem; letter-spacing:1px;">
                    {cfg['label']}
                </div>
                <div style="color:{regime_color}; font-size:1.05rem; font-weight:bold; margin:8px 0 4px 0;">
                    {regime_icon} {regime_label}
                </div>
                <div style="color:#e6edf3; font-size:1.15rem; font-weight:bold;">
                    {cfg['fut_label'].split('/')[0].strip()}: {fut_str}
                </div>
                <div style="color:{regime_color}; font-size:0.85rem; margin-top:4px;">
                    GEX: {gex_str}
                </div>
                <hr style="border-color:#30363d; margin:8px 0;">
                <div style="display:flex; justify-content:space-between; font-size:0.78rem; color:#8b949e;">
                    <span>MaxPain<br><b style="color:#ffbb33;">{mp_str}</b></span>
                    <span>IV ATM<br><b style="color:#c9d1d9;">{data['atm_iv']:.1f}%</b></span>
                    <span>P/C<br><b style="color:#c9d1d9;">{data['pc_oi']:.2f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── Tabla comparativa de niveles clave ──────────────────────
    st.markdown("#### 📋 Niveles Clave Hoy — Comparativo")

    rows_overview = []
    for ikey, cfg in INSTRUMENTS.items():
        data = all_data.get(ikey)
        if data is None:
            continue
        gex_df = data['gex_df']
        ratio  = data['ratio']
        gex_plot = gex_df[gex_df['gex'].abs() > 0].copy()
        gex_plot['fut_level'] = gex_plot['strike'] * ratio

        top_pos = gex_plot[gex_plot['gex'] > 0].nlargest(3, 'gex')
        top_neg = gex_plot[gex_plot['gex'] < 0].nsmallest(3, 'gex')

        pos_lvls = " / ".join(f"{v:,.0f}" for v in top_pos['fut_level'].values) if not top_pos.empty else "—"
        neg_lvls = " / ".join(f"{v:,.0f}" for v in top_neg['fut_level'].values) if not top_neg.empty else "—"

        thr = cfg["gex_threshold"]
        gex = data['total_gex']
        regime = "🟢 Positivo" if gex > thr else ("🔴 Negativo" if gex < -thr else "🟡 Neutro")

        rows_overview.append({
            "Instrumento"  : f"{cfg['emoji']} {cfg['label']}",
            "Régimen"      : regime,
            "GEX Total"    : f"{data['total_gex_bn']:+.2f}B",
            "Precio"       : f"{data['fut_price']:,.1f}",
            "Max Pain"     : f"{data['max_pain_fut']:,.0f}" if data['max_pain_fut'] else "—",
            "Resistencias GEX+" : pos_lvls,
            "Soportes GEX-"     : neg_lvls,
            "IV ATM"       : f"{data['atm_iv']:.1f}%",
            "P/C Ratio"    : f"{data['pc_oi']:.2f}",
        })

    if rows_overview:
        st.dataframe(pd.DataFrame(rows_overview), hide_index=True, use_container_width=True)

    st.divider()

    # ── Gráfico comparativo GEX total ───────────────────────────
    st.markdown("#### 📊 GEX Total por Instrumento")
    valid = {k: v for k, v in all_data.items() if v is not None}
    if valid:
        fig_cmp = go.Figure()
        for ikey, data in valid.items():
            cfg = INSTRUMENTS[ikey]
            color_bar = "#00c851" if data['total_gex'] > 0 else "#ff4444"
            fig_cmp.add_trace(go.Bar(
                x=[cfg['label']],
                y=[data['total_gex_bn']],
                name=cfg['label'],
                marker_color=cfg['accent'],
                opacity=0.85,
                hovertemplate=f"<b>{cfg['label']}</b><br>GEX: %{{y:.2f}}B<extra></extra>",
            ))
        fig_cmp.add_hline(y=0, line_color='white', line_width=1)
        fig_cmp.update_layout(
            plot_bgcolor='#1e2130', paper_bgcolor='#0d1117', font_color='white',
            height=280, showlegend=False,
            xaxis=dict(gridcolor='#2d3250'),
            yaxis=dict(title="GEX (Billones $)", gridcolor='#2d3250',
                       zeroline=True, zerolinecolor='#555'),
            margin=dict(t=10, b=30),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# RENDERER — TAB POR INSTRUMENTO
# ══════════════════════════════════════════════════════════════════

def render_instrument_tab(ikey: str, data: dict | None, expiry: str):
    cfg    = INSTRUMENTS[ikey]
    accent = cfg["accent"]

    if data is None:
        st.error(f"No se pudieron cargar datos para {cfg['label']}. Verifica tu conexión.")
        return

    spot       = data['spot']
    ratio      = data['ratio']
    gex_df     = data['gex_df']
    total_gex  = data['total_gex']
    total_gex_bn = data['total_gex_bn']
    fut_price  = data['fut_price']
    mp_etf     = data['max_pain_etf']
    mp_fut     = data['max_pain_fut']
    thr        = cfg["gex_threshold"]

    # ── Caja de régimen ─────────────────────────────────────────
    if total_gex > thr:
        cls, icon = "positive-regime", "🟢"
        title = "GAMMA POSITIVO — Mercado en RANGO"
        desc  = "Los market makers estabilizan el precio. Funciona mejor el fade de extremos."
        color = "#00c851"
    elif total_gex < -thr:
        cls, icon = "negative-regime", "🔴"
        title = "GAMMA NEGATIVO — Mercado TENDENCIAL"
        desc  = "Los market makers amplifican movimientos. El momentum y rupturas funcionan mejor."
        color = "#ff4444"
    else:
        cls, icon = "neutral-regime", "🟡"
        title = "GAMMA NEUTRO — Zona de Transición"
        desc  = "El mercado puede moverse en cualquier dirección. Reducir tamaño y esperar definición."
        color = "#ffbb33"

    st.markdown(f"""
    <div class="regime-box {cls}">
        <h2 style="margin:0; color:{color};">{icon} {title}</h2>
        <p style="margin:8px 0 4px 0; font-size:1rem; opacity:0.9;">{desc}</p>
        <p style="margin:4px 0; font-size:1.25rem; font-weight:bold; color:{color};">
            GEX Total: {total_gex_bn:+.2f}B &nbsp;·&nbsp;
            Proxy: {cfg['etf']} → {cfg['fut_label']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Métricas clave ───────────────────────────────────────────
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        src = data.get('source', '')
        st.metric(cfg['etf'] + " Precio",
                  f"${spot:.2f}" if ikey != 'BTC' else f"${spot:,.0f}",
                  delta="Deribit ✅" if src == 'Deribit' else None,
                  delta_color="off")
    with c2:
        st.metric(cfg['fut_label'], f"{fut_price:,.1f}" if ikey != 'BTC' else f"{fut_price:,.0f}")
    with c3:
        if mp_etf:
            diff_pct = (mp_etf - spot) / spot * 100
            st.metric("Max Pain",
                      f"${mp_etf:.0f}" if ikey != 'BTC' else f"${mp_etf:,.0f}",
                      delta=f"{diff_pct:+.1f}% vs precio")
        else:
            st.metric("Max Pain", "N/D")
    with c4:
        pc = data['pc_oi']
        if pc > 1.2:
            sent, dc = "Bajista", "inverse"
        elif pc < 0.8:
            sent, dc = "Alcista", "normal"
        else:
            sent, dc = "Neutro", "off"
        st.metric("Put/Call (OI)", f"{pc:.2f}", delta=sent, delta_color=dc)
    with c5:
        iv = data['atm_iv']
        st.metric("IV ATM", f"{iv:.1f}%")
    with c6:
        em = data.get('em_dollar', 0)
        em_p = data.get('em_pct', 0)
        st.metric("Expected Move (±1σ)", f"±{em:.1f}" if ikey != 'BTC' else f"±${em:,.0f}",
                  delta=f"±{em_p:.1f}% del precio", delta_color="off")
    with c7:
        rr = data.get('skew_rr', 0.0)
        if ikey == 'BTC':
            st.metric("Skew 25d", "Ver Deribit", delta_color="off")
        elif rr > 2:
            st.metric("Skew 25d (RR)", f"{rr:+.1f}%", delta="Put skew 🔴", delta_color="off")
        elif rr < -2:
            st.metric("Skew 25d (RR)", f"{rr:+.1f}%", delta="Call skew 🟢", delta_color="off")
        else:
            st.metric("Skew 25d (RR)", f"{rr:+.1f}%", delta="Neutro ⚪", delta_color="off")

    st.divider()

    # ── GEX por Strike ───────────────────────────────────────────
    st.subheader("📊 Gamma Exposure por Strike")
    st.caption(f"Verde = zona de frenado · Rojo = zona de aceleración · "
               f"Ratio de conversión: 1 {cfg['etf']} = {ratio:.1f} {cfg['fut_label'].split('/')[0].strip()}")

    gex_plot = gex_df[gex_df['gex'].abs() > 0].copy()
    gex_plot['fut_level'] = gex_plot['strike'] * ratio
    pos = gex_plot[gex_plot['gex'] >= 0]
    neg = gex_plot[gex_plot['gex'] <  0]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pos['strike'], y=pos['gex'] / 1e6,
        name="GEX Positivo (frena movimiento)",
        marker_color='#00c851', opacity=0.85,
        customdata=pos[['fut_level']],
        hovertemplate=(f"{cfg['etf']} Strike: $%{{x:.0f}}<br>"
                       f"{cfg['fut_label']}: %{{customdata[0]:,.0f}}<br>"
                       f"GEX: %{{y:.1f}}M<extra></extra>")
    ))
    fig.add_trace(go.Bar(
        x=neg['strike'], y=neg['gex'] / 1e6,
        name="GEX Negativo (acelera movimiento)",
        marker_color='#ff4444', opacity=0.85,
        customdata=neg[['fut_level']],
        hovertemplate=(f"{cfg['etf']} Strike: $%{{x:.0f}}<br>"
                       f"{cfg['fut_label']}: %{{customdata[0]:,.0f}}<br>"
                       f"GEX: %{{y:.1f}}M<extra></extra>")
    ))
    fig.add_vline(x=spot, line_color='white', line_width=2, line_dash='dash',
                  annotation_text=f"Precio ${spot:.2f}", annotation_font_color='white',
                  annotation_position="top right")
    if mp_etf:
        fig.add_vline(x=mp_etf, line_color='#ffbb33', line_width=1.5, line_dash='dot',
                      annotation_text=f"Max Pain ${mp_etf:.0f}", annotation_font_color='#ffbb33',
                      annotation_position="top left")
    fig.update_layout(
        plot_bgcolor='#1e2130', paper_bgcolor='#0d1117', font_color='white',
        height=420, barmode='overlay',
        legend=dict(bgcolor='#1e2130', bordercolor='#2d3250', borderwidth=1),
        xaxis=dict(title=f"Strike {cfg['etf']} ($)", gridcolor='#2d3250', tickformat='$,.0f'),
        yaxis=dict(title="GEX (Millones $)", gridcolor='#2d3250',
                   zeroline=True, zerolinecolor='#444'),
        hovermode='x unified', margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Niveles clave ────────────────────────────────────────────
    st.subheader(f"🎯 Niveles Clave para {cfg['fut_label']}")
    col_res, col_sop = st.columns(2)

    with col_res:
        st.markdown(f"##### 🟢 Resistencias Gamma (GEX+)")
        top_res = (gex_plot[gex_plot['gex'] > 0]
                   .nlargest(6, 'gex')[['strike', 'fut_level', 'gex', 'call_oi']].copy())
        if not top_res.empty:
            top_res[cfg['etf']]      = top_res['strike'].map(lambda x: f"${x:.0f}")
            top_res[cfg['fut_label']]= top_res['fut_level'].map(lambda x: f"{x:,.0f}")
            top_res['GEX']           = top_res['gex'].map(lambda x: f"${x/1e6:.1f}M")
            top_res['Call OI']       = top_res['call_oi'].map(lambda x: f"{x:,}")
            top_res['Señal']         = '🟢 Resistencia'
            st.dataframe(top_res[[cfg['etf'], cfg['fut_label'], 'GEX', 'Call OI', 'Señal']],
                         hide_index=True, use_container_width=True)
        else:
            st.info("Sin datos de resistencias gamma.")

    with col_sop:
        st.markdown(f"##### 🔴 Soportes / Aceleración (GEX-)")
        top_sop = (gex_plot[gex_plot['gex'] < 0]
                   .nsmallest(6, 'gex')[['strike', 'fut_level', 'gex', 'put_oi']].copy())
        if not top_sop.empty:
            top_sop[cfg['etf']]      = top_sop['strike'].map(lambda x: f"${x:.0f}")
            top_sop[cfg['fut_label']]= top_sop['fut_level'].map(lambda x: f"{x:,.0f}")
            top_sop['GEX']           = top_sop['gex'].map(lambda x: f"${x/1e6:.1f}M")
            top_sop['Put OI']        = top_sop['put_oi'].map(lambda x: f"{x:,}")
            top_sop['Señal']         = '🔴 Aceleración'
            st.dataframe(top_sop[[cfg['etf'], cfg['fut_label'], 'GEX', 'Put OI', 'Señal']],
                         hide_index=True, use_container_width=True)
        else:
            st.info("Sin datos de soportes gamma.")

    st.divider()

    # ── Open Interest Calls vs Puts ──────────────────────────────
    st.subheader("📈 Open Interest por Strike — Calls vs Puts")
    st.caption("Concentraciones altas = niveles importantes de opciones")

    calls_oi = data['calls'][['strike', 'openInterest']].copy()
    puts_oi  = data['puts'][['strike', 'openInterest']].copy()

    fig_oi = go.Figure()
    fig_oi.add_trace(go.Bar(
        x=calls_oi['strike'], y=calls_oi['openInterest'],
        name='Calls (alcistas)', marker_color='rgba(0,200,81,0.75)',
        hovertemplate="Strike: $%{x:.0f}<br>Call OI: %{y:,}<extra></extra>"
    ))
    fig_oi.add_trace(go.Bar(
        x=puts_oi['strike'], y=-puts_oi['openInterest'],
        name='Puts (bajistas)', marker_color='rgba(255,68,68,0.75)',
        hovertemplate="Strike: $%{x:.0f}<br>Put OI: %{y:,}<extra></extra>"
    ))
    fig_oi.add_vline(x=spot, line_color='white', line_width=2, line_dash='dash',
                     annotation_text=f"${spot:.2f}", annotation_font_color='white')
    fig_oi.update_layout(
        plot_bgcolor='#1e2130', paper_bgcolor='#0d1117', font_color='white',
        height=320, barmode='overlay',
        legend=dict(bgcolor='#1e2130'),
        xaxis=dict(title=f"Strike {cfg['etf']} ($)", gridcolor='#2d3250', tickformat='$,.0f'),
        yaxis=dict(title="OI  (Calls ↑ | Puts ↓)", gridcolor='#2d3250',
                   zeroline=True, zerolinecolor='#555'),
        hovermode='x unified', margin=dict(t=10, b=40),
    )
    st.plotly_chart(fig_oi, use_container_width=True)

    st.divider()

    # ── Chart de velas con niveles ────────────────────────────────────────────────
    st.subheader(f"📈 Chart {cfg['fut_label']} + Niveles Gamma")
    st.caption("Velas del subyacente con niveles GEX superpuestos")

    tf_col, h_col = st.columns([2, 1])
    with tf_col:
        timeframe = st.radio(
            "Temporalidad", ["1m", "5m", "15m", "1h", "4h"],
            horizontal=True, index=1, key=f"tf_{ikey}"
        )
    with h_col:
        chart_height = st.slider("Altura del chart", 400, 700, 520, 20, key=f"ch_{ikey}")

    TF_MAP = {"1m": ("1d","1m"), "5m": ("5d","5m"), "15m": ("10d","15m"),
              "1h": ("1mo","60m"), "4h": ("3mo","1d")}
    period_str, interval_str = TF_MAP[timeframe]

    with st.spinner(f"Cargando velas de {cfg['futures']}..."):
        candles = cargar_candles(cfg['futures'], period_str, interval_str)

    gamma_levels = preparar_niveles_chart(
        gex_df, data['ratio'], data['max_pain_fut'], data['fut_price'], n=6)

    if not candles:
        st.warning(f"No se pudieron cargar velas de {cfg['futures']}. "
                   "Verifica tu conexión o intenta en horario de mercado.")
    else:
        chart_html = build_chart_html(candles, gamma_levels, cfg['fut_label'], height=chart_height)
        components.html(chart_html, height=chart_height + 20, scrolling=False)

        with st.expander("Ver niveles trazados en el chart"):
            lvl_df = pd.DataFrame(gamma_levels)
            if not lvl_df.empty:
                lvl_df['Dirección'] = lvl_df['color'].map({
                    '#00c851': '🟢 Resistencia GEX',
                    '#ff4444': '🔴 Aceleración GEX',
                    '#ffbb33': '🟡 Max Pain',
                })
                lvl_df = lvl_df.rename(columns={'price': 'Nivel', 'title': 'Etiqueta'})
                st.dataframe(lvl_df[['Nivel', 'Etiqueta', 'Dirección']],
                             hide_index=True, use_container_width=True)

    st.divider()

    # ── Historial ────────────────────────────────────────────────────────────────────
    st.subheader("📅 Historial de Niveles Gamma")
    history = load_history(ikey)

    if not history:
        st.info("Aún no hay historial. Los niveles de hoy se guardan automáticamente al abrir el dashboard.")
    else:
        days_sorted = sorted(history.keys(), reverse=True)
        n_days = len(days_sorted)

        m1, m2, m3, m4 = st.columns(4)
        regimes_all = [history[d].get('regime', 'Neutro') for d in days_sorted]
        with m1: st.metric("Días registrados", n_days)
        with m2:
            pos_count = regimes_all.count('Positivo')
            st.metric("Días GEX Positivo 🟢", pos_count, delta=f"{pos_count/n_days*100:.0f}%")
        with m3:
            neg_count = regimes_all.count('Negativo')
            st.metric("Días GEX Negativo 🔴", neg_count, delta=f"{neg_count/n_days*100:.0f}%")
        with m4: st.metric("Primer registro", days_sorted[-1])

        hist_df = pd.DataFrame([
            {'Fecha': d, 'GEX (B)': history[d].get('total_gex_bn', 0),
             'Régimen': history[d].get('regime', 'Neutro')}
            for d in days_sorted
        ]).sort_values('Fecha')

        fig_hist = go.Figure()
        colors_bar = ['#00c851' if r == 'Positivo' else '#ff4444' if r == 'Negativo' else '#ffbb33'
                      for r in hist_df['Régimen']]
        fig_hist.add_trace(go.Bar(
            x=hist_df['Fecha'], y=hist_df['GEX (B)'],
            marker_color=colors_bar,
            hovertemplate="<b>%{x}</b><br>GEX: %{y:.2f}B<extra></extra>"
        ))
        fig_hist.add_hline(y=0, line_color='white', line_width=1)
        fig_hist.update_layout(
            plot_bgcolor='#1e2130', paper_bgcolor='#0d1117', font_color='white',
            height=200, margin=dict(t=10, b=30),
            xaxis=dict(gridcolor='#2d3250'),
            yaxis=dict(title="GEX (B $)", gridcolor='#2d3250'),
            showlegend=False,
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        with st.expander(f"Ver tabla completa ({n_days} días)"):
            rows = []
            for d in days_sorted:
                h   = history[d]
                pos = h.get('pos_levels', [0]*5)
                neg = h.get('neg_levels', [0]*5)
                reg = h.get('regime', '—')
                icon = '🟢' if reg == 'Positivo' else ('🔴' if reg == 'Negativo' else '🟡')
                rows.append({
                    'Fecha'       : d,
                    'Régimen'     : f"{icon} {reg}",
                    'Precio'      : f"{h.get('fut_price', 0):,.1f}",
                    'Max Pain'    : f"{h.get('max_pain_fut', 0):,.0f}",
                    'GEX+ Top 1'  : f"{pos[0]:,.0f}" if pos[0] else '—',
                    'GEX- Top 1'  : f"{neg[0]:,.0f}" if neg[0] else '—',
                    'IV%'         : f"{h.get('atm_iv', 0):.1f}%",
                    'P/C Ratio'   : f"{h.get('pc_oi', 0):.2f}",
                    'Expiración'  : h.get('expiry', '—'),
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        # Pine Script
        st.divider()
        st.markdown("#### 📌 Exportar a TradingView")
        pine_code = generate_pine_script(ikey, history)
        col_dl, col_info = st.columns([1, 2])
        with col_dl:
            st.download_button(
                label="⬇️ Descargar Pine Script",
                data=pine_code.encode('utf-8'),
                file_name=f"{ikey}_Gamma_{datetime.now().strftime('%Y%m%d')}.pine",
                mime="text/plain",
                use_container_width=True,
                key=f"pine_{ikey}",
            )
        with col_info:
            st.info(f"📁 `{ikey}_Gamma_{{datetime.now().strftime('%Y%m%d')}}.pine` · "
                    f"{n_days} días · {n_days * 10} niveles gamma")

        with st.expander("Ver código Pine Script"):
            st.code(pine_code, language='javascript')


# ══════════════════════════════════════════════════════════════════
# HOMEPAGE
# ══════════════════════════════════════════════════════════════════

def render_homepage():
    st.markdown("""
    <div style="text-align:center;padding:32px 0 16px 0;">
        <div style="font-size:3.2rem;">🏦</div>
        <h1 style="font-size:2.6rem;font-weight:800;color:#e6edf3;margin:8px 0 4px 0;">Merino's Trust</h1>
        <p style="color:#8b949e;font-size:1.05rem;margin:0;">Trading Analytics Platform · Gamma Exposure & Options Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### ¿Qué es Merino's Trust?")
    st.markdown("""
Merino's Trust es una plataforma personal de análisis de opciones financieras diseñada para identificar
regímenes de mercado a través del **Gamma Exposure (GEX)** — la métrica que cuantifica la posición neta
de los *market makers* en el mercado de derivados. Cuando el GEX es positivo, los creadores de mercado
actúan como estabilizadores: venden cuando el precio sube y compran cuando baja, empujando el mercado
hacia un rango. Cuando el GEX es negativo, amplifican los movimientos, creando condiciones tendenciales.

El objetivo de la plataforma es ayudar a **tomar mejores decisiones de entrada y salida en opciones**,
entendiendo en qué régimen está cada instrumento antes de colocar cualquier trade.
La plataforma está construida para operar con un presupuesto inicial de ~$400 USD,
con un horizonte de trade de 3 días a 2 semanas.
    """)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:#161b22;border:2px solid #58a6ff;border-radius:12px;padding:20px;">
            <h3 style="color:#58a6ff;margin:0 0 10px 0;">📊 Futuros</h3>
            <p style="color:#c9d1d9;font-size:0.9rem;margin:0 0 10px 0;">
            Análisis GEX de los 4 futuros micro del CME más Bitcoin,
            con datos en tiempo real desde Yahoo Finance y Deribit.
            </p>
            <ul style="color:#8b949e;font-size:0.85rem;margin:0;padding-left:18px;">
                <li>MNQ · Micro Nasdaq-100</li>
                <li>MES · Micro S&P 500</li>
                <li>MGC · Micro Oro</li>
                <li>BTC · Bitcoin (Deribit)</li>
            </ul>
            <div style="margin-top:12px;font-size:0.8rem;color:#58a6ff;">
            Incluye: GEX · Vanna · Charm · VIX Term Structure · Expected Move · Pine Script
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:#161b22;border:2px solid #3fb950;border-radius:12px;padding:20px;">
            <h3 style="color:#3fb950;margin:0 0 10px 0;">📈 Opciones</h3>
            <p style="color:#c9d1d9;font-size:0.9rem;margin:0 0 10px 0;">
            Seguimiento de acciones individuales con análisis de GEX, IV Rank,
            Expected Move y gráficos TradingView con medias móviles.
            </p>
            <ul style="color:#8b949e;font-size:0.85rem;margin:0;padding-left:18px;">
                <li><b style="color:#ffbb33;">Budget (~$400):</b> 9 acciones asequibles</li>
                <li><b style="color:#ff6b6b;">Top 20:</b> Las más cotizadas del mercado</li>
            </ul>
            <div style="margin-top:12px;font-size:0.8rem;color:#3fb950;">
            Incluye: GEX por strike · MAs 20/40/100/200 · RSI · Max Pain · Skew · Earnings alert
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Conceptos Clave")
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown('<div style="background:#0a2e1a;border:1px solid #00c851;border-radius:8px;padding:12px;text-align:center"><b style="color:#00c851">GEX Positivo</b><br><span style="color:#c9d1d9;font-size:0.8rem">Market makers estabilizan precio. Mercado en RANGO. Vende extremos.</span></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="background:#2e0a0a;border:1px solid #ff4444;border-radius:8px;padding:12px;text-align:center"><b style="color:#ff4444">GEX Negativo</b><br><span style="color:#c9d1d9;font-size:0.8rem">Market makers amplifican movimientos. Mercado TENDENCIAL. Sigue el momentum.</span></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div style="background:#2a2600;border:1px solid #ffbb33;border-radius:8px;padding:12px;text-align:center"><b style="color:#ffbb33">Max Pain</b><br><span style="color:#c9d1d9;font-size:0.8rem">Strike donde expiran con pérdida máxima los compradores. Actúa como imán al vencimiento.</span></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div style="background:#1a1a2e;border:1px solid #c792ea;border-radius:8px;padding:12px;text-align:center"><b style="color:#c792ea">Expected Move</b><br><span style="color:#c9d1d9;font-size:0.8rem">Movimiento ±1σ implícito en opciones. Define el rango probable hasta vencimiento.</span></div>', unsafe_allow_html=True)

    st.caption("Datos: Yahoo Finance + Deribit API · Gratis · Sin API key requerida · Actualizado en tiempo real")


# ══════════════════════════════════════════════════════════════════
# STOCK SECTION RENDERER (Budget + Top 20)
# ══════════════════════════════════════════════════════════════════

def render_stock_section(stocks_dict: dict, section_key: str, expiry_by_stock: dict):
    """Unified renderer for any stock section."""

    # ── Data loading ──────────────────────────────────────────────
    all_sdata = {}
    with st.spinner("Cargando datos de acciones..."):
        for ticker in stocks_dict:
            exp = expiry_by_stock.get(f"{section_key}_{ticker}")
            if not exp:
                all_sdata[ticker] = None
                continue
            try:
                all_sdata[ticker] = cargar_datos_stock(ticker, exp)
            except Exception:
                all_sdata[ticker] = None

    # ── Overview grid ─────────────────────────────────────────────
    tickers = list(stocks_dict.keys())
    cols_per_row = 3 if len(tickers) <= 9 else 4
    st.markdown("### 📊 Overview — Estado del Portafolio")
    for ri in range(0, len(tickers), cols_per_row):
        cols = st.columns(cols_per_row)
        for ci, col in enumerate(cols):
            if ri+ci >= len(tickers): break
            tk  = tickers[ri+ci]
            cfg = stocks_dict[tk]
            d   = all_sdata.get(tk)
            with col:
                if d is None:
                    st.markdown(f'<div style="padding:12px;background:#161b22;border:1px solid {cfg["accent"]}30;border-radius:10px;text-align:center;margin-bottom:8px;"><div style="font-size:1.2rem">{cfg["emoji"]}</div><b style="color:{cfg["accent"]}">{tk}</b><div style="color:#666;font-size:0.8rem">Sin datos</div></div>', unsafe_allow_html=True)
                    continue
                thr = abs(d['spot'])*0.01e6
                rc,rl = ("#00c851","GEX+") if d['total_gex']>thr else (("#ff4444","GEX-") if d['total_gex']<-thr else ("#ffbb33","NEUTRO"))
                cc = "#00c851" if d['change_pct']>=0 else "#ff4444"
                ivr = f"IVR:{d['iv_rank']:.0f}" if d['iv_rank'] is not None else "IVR:—"
                st.markdown(f'''<div style="padding:12px;border-radius:10px;background:rgba(0,0,0,0.1);border:2px solid {rc};text-align:center;margin-bottom:8px;">
                    <div style="font-size:1.2rem">{cfg["emoji"]}</div>
                    <div style="color:{cfg["accent"]};font-weight:700;font-size:0.85rem">{tk} — {cfg["name"]}</div>
                    <div style="color:#e6edf3;font-size:1.1rem;font-weight:bold">${d["spot"]:.2f} <span style="color:{cc};font-size:0.8rem">{d["change_pct"]:+.1f}%</span></div>
                    <div style="color:{rc};font-size:0.85rem;font-weight:bold">{rl} · ${d["total_gex_m"]:.1f}M</div>
                    <div style="display:flex;justify-content:space-around;font-size:0.75rem;color:#8b949e;margin-top:6px">
                        <span>IV<br><b style="color:#c9d1d9">{d["atm_iv"]:.0f}%</b></span>
                        <span>EM<br><b style="color:#ffbb33">±${d["em_dollar"]:.2f}</b></span>
                        <span>{ivr}<br><b style="color:#c9d1d9">{"acum." if d["iv_rank"] is None else ""}</b></span>
                        <span>DTE<br><b style="color:#c9d1d9">{d["dte"]}d</b></span>
                    </div>
                </div>''', unsafe_allow_html=True)

    st.divider()

    # ── Stock selector for detail ─────────────────────────────────
    st.markdown("### 🔍 Análisis Detallado")
    options = [f"{stocks_dict[t]['emoji']} {t} — {stocks_dict[t]['name']}" for t in tickers]
    sel_idx = st.selectbox("Selecciona una acción", range(len(options)),
                           format_func=lambda x: options[x], key=f"sel_{section_key}")
    sel_ticker = tickers[sel_idx]
    d = all_sdata.get(sel_ticker)
    cfg = stocks_dict[sel_ticker]

    if d is None:
        st.error(f"No se pudieron cargar datos para {sel_ticker}.")
        return

    spot = d['spot']

    # Earnings alert
    if d['earnings'] != "N/D":
        try:
            dte_e = (datetime.strptime(d['earnings'],"%Y-%m-%d")-datetime.now()).days
            if dte_e <= 14:
                st.markdown(f'<div style="padding:8px 14px;border-radius:8px;margin-bottom:10px;background:#2e1a00;border:1px solid #ff9800;color:#ff9800;font-size:0.85rem">⚠️ EARNINGS en {dte_e} días ({d["earnings"]}) — IV crush post-earnings puede afectar tus opciones. Considera cerrar antes.</div>', unsafe_allow_html=True)
        except: pass

    # Regime box
    thr = abs(spot)*0.01e6
    if d['total_gex']>thr:   cls,icon,color,title,desc = "positive-regime","🟢","#00c851","GAMMA POSITIVO — Precio tiende a RANGO","Market makers estabilizan. Compra en extremos, vende en medios."
    elif d['total_gex']<-thr: cls,icon,color,title,desc = "negative-regime","🔴","#ff4444","GAMMA NEGATIVO — Precio puede TENDENCIAR","Market makers amplifican. El momentum funciona. Breakouts son reales."
    else:                      cls,icon,color,title,desc = "neutral-regime","🟡","#ffbb33","GAMMA NEUTRO — Zona de transición","Puede ir en cualquier dirección. Reducir tamaño, esperar catalizador."
    st.markdown(f'<div class="regime-box {cls}"><h2 style="margin:0;color:{color}">{icon} {cfg["emoji"]} {sel_ticker} — {title}</h2><p style="margin:6px 0 4px 0;font-size:0.9rem;opacity:0.9">{desc}</p><p style="margin:4px 0;font-size:1rem;font-weight:bold;color:{color}">GEX: ${d["total_gex_m"]:.1f}M · Expiración: {d["expiry"]} ({d["dte"]} DTE)</p></div>', unsafe_allow_html=True)

    # Metrics
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric("Precio",f"${spot:.2f}",delta=f"{d['change_pct']:+.1f}%")
    with c2: st.metric("IV ATM",f"{d['atm_iv']:.1f}%",delta=f"Rank: {d['iv_rank']:.0f}" if d['iv_rank'] is not None else "Rank: acum.",delta_color="off")
    with c3: st.metric("Expected Move",f"±${d['em_dollar']:.2f}",delta=f"±{d['em_pct']:.1f}%",delta_color="off")
    with c4:
        mp=d['max_pain']; diff=(mp-spot)/spot*100 if mp else 0
        st.metric("Max Pain",f"${mp:.2f}" if mp else "N/D",delta=f"{diff:+.1f}% vs spot" if mp else "",delta_color="off")
    with c5:
        pc=d['pc_oi']; sent=("Bajista" if pc>1.2 else ("Alcista" if pc<0.8 else "Neutro"))
        st.metric("P/C Ratio",f"{pc:.2f}",delta=sent,delta_color="off")
    with c6:
        rr=d['skew_rr']; sk=("Put skew 🔴" if rr>2 else ("Call skew 🟢" if rr<-2 else "Neutro ⚪"))
        st.metric("Skew 25d",f"{rr:+.1f}%",delta=sk,delta_color="off")

    st.divider()

    # TradingView Chart
    st.subheader(f"📈 Chart {sel_ticker} — {cfg['name']} (TradingView)")
    period_map={"3M":"3mo","6M":"6mo","1A":"1y","2A":"2y"}
    chart_period = st.radio("Período",list(period_map.keys()),horizontal=True,index=2,key=f"cp_{section_key}_{sel_ticker}")
    chart_h = st.slider("Altura del chart",450,800,630,20,key=f"ch_{section_key}_{sel_ticker}")

    with st.spinner(f"Cargando historia de {sel_ticker}..."):
        hist = cargar_historico_stock(sel_ticker, period_map[chart_period])

    if hist.empty:
        st.warning("No se pudo cargar el historial de precios.")
    else:
        chart_html = build_stock_chart_html(hist, d['gex_df'], spot, d['max_pain'], d['em_dollar'], sel_ticker, chart_h)
        components.html(chart_html, height=chart_h+10, scrolling=False)

    st.divider()

    # GEX Bar Chart
    st.subheader("📊 Gamma Exposure por Strike")
    gp = d['gex_df'][d['gex_df']['gex'].abs()>0]
    fg = go.Figure()
    fg.add_trace(go.Bar(x=gp[gp['gex']>=0]['strike'],y=gp[gp['gex']>=0]['gex']/1e6,name="GEX+ (frena)",marker_color='#00c851',opacity=0.85,hovertemplate="Strike: $%{x:.2f}<br>GEX: %{y:.2f}M<extra></extra>"))
    fg.add_trace(go.Bar(x=gp[gp['gex']<0]['strike'],y=gp[gp['gex']<0]['gex']/1e6,name="GEX- (acelera)",marker_color='#ff4444',opacity=0.85,hovertemplate="Strike: $%{x:.2f}<br>GEX: %{y:.2f}M<extra></extra>"))
    fg.add_vline(x=spot,line_color='white',line_width=2,line_dash='dash',annotation_text=f"${spot:.2f}",annotation_font_color='white')
    if d['max_pain']: fg.add_vline(x=d['max_pain'],line_color='#ffbb33',line_width=1.5,line_dash='dot',annotation_text=f"MaxPain ${d['max_pain']:.2f}",annotation_font_color='#ffbb33',annotation_position="top left")
    fg.update_layout(plot_bgcolor='#1e2130',paper_bgcolor='#0d1117',font_color='white',height=320,barmode='overlay',legend=dict(bgcolor='#1e2130'),xaxis=dict(title="Strike ($)",gridcolor='#2d3250'),yaxis=dict(title="GEX (M$)",gridcolor='#2d3250',zeroline=True,zerolinecolor='#444'),hovermode='x unified',margin=dict(t=10,b=40))
    st.plotly_chart(fg,use_container_width=True)

    # Notes
    if cfg.get('notes'):
        st.caption(f"📌 {cfg['notes']}")


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:8px 0 12px 0;">
        <div style="font-size:1.8rem">🏦</div>
        <div style="color:#e6edf3;font-weight:800;font-size:1.1rem">Merino's Trust</div>
        <div style="color:#8b949e;font-size:0.72rem">Trading Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    page = st.radio("Navegación", [
        "🏠 Inicio",
        "📊 Futuros",
        "💰 Opciones — Budget",
        "🚀 Opciones — Top 20",
    ], label_visibility="collapsed")

    st.divider()

    # Expiry selectors for futures
    expiry_selections = {}
    if page == "📊 Futuros":
        st.markdown("**Expiraciones — Futuros**")
        for ikey, cfg in INSTRUMENTS.items():
            try:
                exps = get_expiries(cfg['etf'])[:10]
                labels = [f"{e} ({(datetime.strptime(e,'%Y-%m-%d')-datetime.now()).days}d)" for e in exps]
                sel = st.selectbox(f"{cfg['emoji']} {ikey}",range(len(labels)),format_func=lambda x,_l=labels:_l[x],key=f"exp_{ikey}")
                expiry_selections[ikey] = exps[sel]
            except Exception as ex:
                st.error(f"{ikey}: {ex}")
                expiry_selections[ikey] = None
        st.divider()

    # Expiry selectors for stocks
    stock_expiry = {}
    if page in ["💰 Opciones — Budget","🚀 Opciones — Top 20"]:
        sdict = STOCKS_BUDGET if page == "💰 Opciones — Budget" else STOCKS_TOP20
        sk    = "budget" if page == "💰 Opciones — Budget" else "top20"
        st.markdown("**Expiraciones — Acciones**")
        for ticker,cfg in sdict.items():
            try:
                exps = get_expiries_stock(ticker)
                if not exps: stock_expiry[f"{sk}_{ticker}"] = None; continue
                labels = [f"{e} ({(datetime.strptime(e,'%Y-%m-%d')-datetime.now()).days}d)" for e in exps[:8]]
                sel = st.selectbox(f"{cfg['emoji']} {ticker}",range(len(labels)),format_func=lambda x,_l=labels:_l[x],key=f"sexp_{sk}_{ticker}")
                stock_expiry[f"{sk}_{ticker}"] = exps[sel]
            except Exception:
                stock_expiry[f"{sk}_{ticker}"] = None
        st.divider()

    if st.button("🔄 Actualizar datos",use_container_width=True):
        st.cache_data.clear(); st.rerun()

    st.divider()
    st.markdown("**🌡️ VIX — Term Structure**")
    try:
        vix_data = cargar_vix()
        v9=vix_data.get('VIX9D'); v30=vix_data.get('VIX'); v3m=vix_data.get('VIX3M')
        v6m=vix_data.get('VIX6M'); vxn=vix_data.get('VXN'); ratio_vix=vix_data.get('ratio')
        vc = "#00c851" if v30 and v30<15 else ("#ffbb33" if v30 and v30<25 else "#ff4444")
        tc = "#00c851" if vix_data.get('ts_regime','').startswith('Contango') else "#ff4444"
        st.markdown(f'<div style="background:#161b22;border-radius:8px;padding:10px 12px;font-size:0.8rem">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px"><span style="color:#8b949e">VIX 9D</span><b style="color:{vc}">{v9 or "—"}</b></div>'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px"><span style="color:#8b949e">VIX 30D</span><b style="color:{vc}">{v30 or "—"}</b></div>'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px"><span style="color:#8b949e">VIX 3M</span><b style="color:#c9d1d9">{v3m or "—"}</b></div>'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px"><span style="color:#8b949e">VXN</span><b style="color:#58a6ff">{vxn or "—"}</b></div>'
            f'<hr style="border-color:#30363d;margin:5px 0">'
            f'<div style="color:#8b949e">VIX9D/VIX: <b style="color:{tc}">{ratio_vix or "—"}</b></div>'
            f'<div style="color:{tc};font-size:0.74rem">{vix_data.get("ts_regime","—")}</div>'
            f'<div style="color:{vc};font-size:0.74rem">{vix_data.get("vix_regime","—")}</div>'
            f'</div>',unsafe_allow_html=True)
    except: st.caption("VIX no disponible")

    st.divider()
    st.markdown("**Guía rápida**")
    st.markdown("- 🟢 **GEX+** → RANGO\n- 🔴 **GEX-** → TENDENCIA\n- 🟡 **Neutro** → Transición\n- ⚡ **Max Pain** → Imán al vencimiento\n- ⚠️ **VIX>1** → Stress inminente")
    st.caption("Yahoo Finance + Deribit · Gratis · Sin API key")



# ════════════════════════════════════════════════════════════════
# ROUTING PRINCIPAL
# ════════════════════════════════════════════════════════════════

status_text, banner_cls = market_status()
st.markdown(f'<div class="market-banner {banner_cls}">{status_text}</div>', unsafe_allow_html=True)

# ── INICIO ──────────────────────────────────────────────────────
if page == "🏠 Inicio":
    render_homepage()

# ── FUTUROS ─────────────────────────────────────────────────────
elif page == "📊 Futuros":
    st.title("📊 Futuros — Gamma Exposure")
    st.caption("MNQ · MES · MGC (Oro) · BTC — Análisis via opciones ETF + Deribit")

    all_data = {}
    for ikey in INSTRUMENTS:
        expiry = expiry_selections.get(ikey)
        if expiry is None:
            all_data[ikey] = None
            continue
        if ikey == "BTC":
            try:
                with st.spinner("Cargando BTC desde Deribit..."):
                    dbt = cargar_btc_gex_deribit()
            except Exception:
                dbt = None
            if dbt:
                spot = dbt['spot']
                all_data[ikey] = {
                    'ikey':'BTC','spot':spot,'fut_price':spot,'ratio':1.0,'expiry':expiry,
                    'gex_df':dbt['gex_df'],'extra_df':pd.DataFrame(),
                    'total_gex':dbt['total_gex'],'total_gex_bn':dbt['total_gex_bn'],
                    'total_vex':0.0,'total_cex':0.0,
                    'max_pain_etf':dbt['max_pain_fut'],'max_pain_fut':dbt['max_pain_fut'],
                    'pc_oi':dbt['pc_oi'],'pc_vol':dbt['pc_oi'],'atm_iv':dbt['atm_iv'],
                    'em_dollar':spot*(dbt['atm_iv']/100)*np.sqrt(1/52)*0.6827,
                    'em_pct':(dbt['atm_iv']/100)*np.sqrt(1/52)*0.6827*100,
                    'skew_rr':0.0,'calls':pd.DataFrame(),'puts':pd.DataFrame(),
                    'last_update':dbt['last_update'],'source':'Deribit',
                }
                try: log_daily_levels(all_data[ikey])
                except: pass
                continue
        try:
            with st.spinner(f"Cargando {INSTRUMENTS[ikey]['label']}..."):
                d = cargar_datos(ikey, expiry)
            all_data[ikey] = d
            try: log_daily_levels(d)
            except: pass
        except Exception as e:
            all_data[ikey] = None
            st.warning(f"⚠️ {INSTRUMENTS[ikey]['label']}: {e}")

    tab_ov, tab_mnq, tab_mes, tab_gc, tab_btc = st.tabs([
        "🏠 Overview","📈 MNQ — Nasdaq","🏛️ MES — S&P 500","🥇 MGC — Oro","₿ BTC — Bitcoin"])
    with tab_ov:   render_overview(all_data)
    with tab_mnq:  render_instrument_tab("MNQ", all_data.get("MNQ"), expiry_selections.get("MNQ",""))
    with tab_mes:  render_instrument_tab("MES", all_data.get("MES"), expiry_selections.get("MES",""))
    with tab_gc:   render_instrument_tab("GC",  all_data.get("GC"),  expiry_selections.get("GC",""))
    with tab_btc:  render_instrument_tab("BTC", all_data.get("BTC"), expiry_selections.get("BTC",""))

# ── OPCIONES BUDGET ──────────────────────────────────────────────
elif page == "💰 Opciones — Budget":
    st.title("💰 Opciones — Budget (~$400)")
    st.caption("BAC · WFC · SOFI · OXY · DVN · GM · MARA · RIVN · DKNG — Acciones asequibles para empezar")
    render_stock_section(STOCKS_BUDGET, "budget", stock_expiry)

# ── OPCIONES TOP 20 ──────────────────────────────────────────────
elif page == "🚀 Opciones — Top 20":
    st.title("🚀 Opciones — Top 20 del Mercado")
    st.caption("Las 20 acciones con mayor liquidez y volumen de opciones en EE.UU.")
    render_stock_section(STOCKS_TOP20, "top20", stock_expiry)


# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════

st.divider()
st.caption(
    f"Multi-Market Dashboard · Datos via Yahoo Finance (gratuito) · "
    f"Actualizado: {datetime.now().strftime('%H:%M:%S')} · "
    f"Expirations: MNQ={expiry_selections.get('MNQ','—')} "
    f"MES={expiry_selections.get('MES','—')} "
    f"GC={expiry_selections.get('GC','—')} "
    f"BTC={expiry_selections.get('BTC','—')}"
)
