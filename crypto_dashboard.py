#!/usr/bin/env python3
"""
🚀 Crypto Dashboard v5
- Traffic light indicators
- Telegram + Outlook email
- Schedule: Germany 06:50, 21:20
"""

import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any
import time

# ============================================
# CONFIG
# ============================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")

# ============================================
# TRAFFIC LIGHT FUNCTIONS
# ============================================

def get_ma_signal(distance: float) -> str:
    """120D MA distance
    🟢 +5% or higher (healthy above MA)
    🟡 -5% to +5% (near MA)
    🔴 -5% or lower (danger below MA)
    """
    if distance is None:
        return "⚪"
    if distance >= 5:
        return "🟢"
    elif distance >= -5:
        return "🟡"
    else:
        return "🔴"


def get_52w_high_signal(change: float) -> str:
    """52-week high distance
    🟢 within -15% (near high)
    🟡 -15% to -40%
    🔴 -40% or lower (far from high)
    """
    if change is None:
        return "⚪"
    if change >= -15:
        return "🟢"
    elif change >= -40:
        return "🟡"
    else:
        return "🔴"


def get_52w_low_signal(change: float) -> str:
    """52-week low distance
    🟢 +100% or higher (far from low)
    🟡 +30% to +100%
    🔴 +30% or lower (near low)
    """
    if change is None:
        return "⚪"
    if change >= 100:
        return "🟢"
    elif change >= 30:
        return "🟡"
    else:
        return "🔴"


def get_fear_greed_signal(value: int) -> str:
    """Fear & Greed Index
    🟢 ≤25 (extreme fear = opportunity)
    🟡 26-74 (neutral)
    🔴 ≥75 (extreme greed = caution)
    """
    if value is None:
        return "⚪"
    if value <= 25:
        return "🟢"
    elif value <= 74:
        return "🟡"
    else:
        return "🔴"


def get_kimchi_signal(premium: float) -> str:
    """Kimchi Premium
    🟢 -1% to 2% (normal)
    🟡 2%-5% or -1% to -3%
    🔴 >5% or <-3%
    """
    if premium is None:
        return "⚪"
    if -1 <= premium <= 2:
        return "🟢"
    elif -3 <= premium <= 5:
        return "🟡"
    else:
        return "🔴"


def get_funding_signal(rate: float) -> str:
    """Funding Rate (%)
    🟢 -0.01% to 0.03% (normal)
    🟡 0.03% to 0.08% or -0.01% to -0.03%
    🔴 >0.08% or <-0.03% (overheated/oversold)
    """
    if rate is None:
        return "⚪"
    if -0.01 <= rate <= 0.03:
        return "🟢"
    elif -0.03 <= rate <= 0.08:
        return "🟡"
    else:
        return "🔴"


def get_dominance_signal(dom: float) -> str:
    """BTC Dominance
    🟢 50%-60% (balanced)
    🟡 45%-50% or 60%-65%
    🔴 <45% or >65%
    """
    if dom is None:
        return "⚪"
    if 50 <= dom <= 60:
        return "🟢"
    elif 45 <= dom <= 65:
        return "🟡"
    else:
        return "🔴"


def get_m2_signal(yoy: float) -> str:
    """US M2 YoY
    🟢 >5% (liquidity expansion)
    🟡 0%-5%
    🔴 <0% (liquidity contraction)
    """
    if yoy is None:
        return "⚪"
    if yoy > 5:
        return "🟢"
    elif yoy >= 0:
        return "🟡"
    else:
        return "🔴"


def get_stablecoin_signal(total_b: float) -> str:
    """Stablecoin Market Cap
    🟢 >$200B
    🟡 $150B-$200B
    🔴 <$150B
    """
    if total_b is None:
        return "⚪"
    if total_b > 200:
        return "🟢"
    elif total_b >= 150:
        return "🟡"
    else:
        return "🔴"


# ============================================
# DATA COLLECTION
# ============================================

def get_btc_detailed() -> Dict[str, Any]:
    """BTC detailed data"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        market_data = data.get("market_data", {})
        
        current_price = market_data.get("current_price", {}).get("usd", 0)
        
        result = {
            "price_usd": current_price,
            "price_krw": market_data.get("current_price", {}).get("krw", 0),
            "change_24h": market_data.get("price_change_percentage_24h", 0),
            "change_7d": market_data.get("price_change_percentage_7d", 0),
        }
        
        time.sleep(1)
        history_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        history_params = {"vs_currency": "usd", "days": "365", "interval": "daily"}
        history_response = requests.get(history_url, params=history_params, timeout=15)
        prices = [p[1] for p in history_response.json().get("prices", [])]
        
        if prices:
            high_52w = max(prices)
            low_52w = min(prices)
            result["high_52w"] = high_52w
            result["low_52w"] = low_52w
            result["from_52w_high"] = ((current_price - high_52w) / high_52w * 100)
            result["from_52w_low"] = ((current_price - low_52w) / low_52w * 100)
            
            if len(prices) >= 120:
                ma_120 = sum(prices[-120:]) / 120
                result["ma_120"] = ma_120
                result["ma_120_distance"] = ((current_price - ma_120) / ma_120 * 100)
        
        return result
    except Exception as e:
        print(f"❌ BTC fetch failed: {e}")
        return {}


def get_eth_detailed() -> Dict[str, Any]:
    """ETH detailed data"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/ethereum"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        market_data = data.get("market_data", {})
        
        current_price = market_data.get("current_price", {}).get("usd", 0)
        
        result = {
            "price_usd": current_price,
            "price_krw": market_data.get("current_price", {}).get("krw", 0),
            "change_24h": market_data.get("price_change_percentage_24h", 0),
            "change_7d": market_data.get("price_change_percentage_7d", 0),
        }
        
        time.sleep(1)
        history_url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
        history_params = {"vs_currency": "usd", "days": "365", "interval": "daily"}
        history_response = requests.get(history_url, params=history_params, timeout=15)
        prices = [p[1] for p in history_response.json().get("prices", [])]
        
        if prices:
            high_52w = max(prices)
            low_52w = min(prices)
            result["high_52w"] = high_52w
            result["low_52w"] = low_52w
            result["from_52w_high"] = ((current_price - high_52w) / high_52w * 100)
            result["from_52w_low"] = ((current_price - low_52w) / low_52w * 100)
            
            if len(prices) >= 120:
                ma_120 = sum(prices[-120:]) / 120
                result["ma_120"] = ma_120
                result["ma_120_distance"] = ((current_price - ma_120) / ma_120 * 100)
        
        return result
    except Exception as e:
        print(f"❌ ETH fetch failed: {e}")
        return {}


def get_fear_greed_index() -> Dict[str, Any]:
    """Fear & Greed Index"""
    try:
        url = "https://api.alternative.me/fng/"
        params = {"limit": 7}
        response = requests.get(url, params=params, timeout=15)
        data = response.json().get("data", [])
        
        if data:
            current = data[0]
            yesterday = data[1] if len(data) > 1 else current
            return {
                "value": int(current.get("value", 0)),
                "classification": current.get("value_classification", ""),
                "yesterday": int(yesterday.get("value", 0)),
            }
    except Exception as e:
        print(f"❌ Fear & Greed fetch failed: {e}")
    return {}


def get_us_m2_supply() -> Dict[str, Any]:
    """FRED API - US M2"""
    if not FRED_API_KEY:
        return {}
    
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "M2SL",
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 13,
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json().get("observations", [])
        
        if len(data) >= 2:
            current = float(data[0].get("value", 0))
            year_ago = float(data[12].get("value", current)) if len(data) > 12 else current
            
            return {
                "value_trillions": current / 1000,
                "yoy_change": ((current - year_ago) / year_ago * 100) if year_ago else 0,
            }
    except Exception as e:
        print(f"❌ M2 fetch failed: {e}")
    return {}


def get_funding_rate() -> Dict[str, Any]:
    """Binance Funding Rate"""
    try:
        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        params = {"symbol": "BTCUSDT", "limit": 1}
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if data:
            rate = float(data[0].get("fundingRate", 0))
            return {"rate_percent": rate * 100}
    except Exception as e:
        print(f"❌ Funding Rate fetch failed: {e}")
    return {}


def get_kimchi_premium() -> Dict[str, Any]:
    """Kimchi Premium"""
    try:
        upbit_response = requests.get(
            "https://api.upbit.com/v1/ticker", 
            params={"markets": "KRW-BTC"}, 
            timeout=15
        )
        upbit_price = upbit_response.json()[0].get("trade_price", 0)
        
        binance_response = requests.get(
            "https://api.binance.com/api/v3/ticker/price", 
            params={"symbol": "BTCUSDT"}, 
            timeout=15
        )
        binance_price = float(binance_response.json().get("price", 0))
        
        fx_response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=15)
        usd_krw = fx_response.json().get("rates", {}).get("KRW", 1300)
        
        binance_krw = binance_price * usd_krw
        premium = ((upbit_price - binance_krw) / binance_krw * 100) if binance_krw else 0
        
        return {
            "premium_percent": round(premium, 2),
            "usd_krw": usd_krw,
        }
    except Exception as e:
        print(f"❌ Kimchi Premium fetch failed: {e}")
    return {}


def get_btc_dominance() -> Dict[str, Any]:
    """BTC Dominance"""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=15)
        data = response.json().get("data", {})
        
        return {
            "btc_dominance": round(data.get("market_cap_percentage", {}).get("btc", 0), 1),
        }
    except Exception as e:
        print(f"⚠️ Dominance fetch failed: {e}")
    return {}


def get_stablecoin_supply() -> Dict[str, Any]:
    """Stablecoin Market Cap"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "tether,usd-coin",
            "vs_currencies": "usd",
            "include_market_cap": "true"
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        usdt = data.get("tether", {}).get("usd_market_cap", 0) / 1e9
        usdc = data.get("usd-coin", {}).get("usd_market_cap", 0) / 1e9
        
        return {"total_billions": usdt + usdc}
    except Exception as e:
        print(f"⚠️ Stablecoin fetch failed: {e}")
    return {}


# ============================================
# REPORT GENERATION
# ============================================

def generate_report(data: Dict[str, Any]) -> str:
    """Generate Telegram report with traffic lights"""
    
    now = datetime.utcnow() + timedelta(hours=1)
    time_str = now.strftime("%Y-%m-%d %H:%M")
    
    btc = data.get("btc", {})
    eth = data.get("eth", {})
    fg = data.get("fear_greed", {})
    m2 = data.get("m2_supply", {})
    fr = data.get("funding_rate", {})
    kp = data.get("kimchi_premium", {})
    dom = data.get("dominance", {})
    stable = data.get("stablecoin", {})
    
    # BTC signals
    btc_ma_dist = btc.get('ma_120_distance')
    btc_ma_sig = get_ma_signal(btc_ma_dist)
    btc_52h_sig = get_52w_high_signal(btc.get('from_52w_high'))
    btc_52l_sig = get_52w_low_signal(btc.get('from_52w_low'))
    
    # ETH signals
    eth_ma_dist = eth.get('ma_120_distance')
    eth_ma_sig = get_ma_signal(eth_ma_dist)
    eth_52h_sig = get_52w_high_signal(eth.get('from_52w_high'))
    eth_52l_sig = get_52w_low_signal(eth.get('from_52w_low'))
    
    # Market signals
    fg_sig = get_fear_greed_signal(fg.get('value'))
    kp_sig = get_kimchi_signal(kp.get('premium_percent'))
    fr_sig = get_funding_signal(fr.get('rate_percent'))
    dom_sig = get_dominance_signal(dom.get('btc_dominance'))
    
    # Macro signals
    m2_sig = get_m2_signal(m2.get('yoy_change'))
    stable_sig = get_stablecoin_signal(stable.get('total_billions'))
    
    # Formatting
    btc_ma_str = f"{btc_ma_dist:+.1f}%" if btc_ma_dist else "N/A"
    btc_ma_price = f"${btc.get('ma_120', 0):,.0f}" if btc.get('ma_120') else "N/A"
    eth_ma_str = f"{eth_ma_dist:+.1f}%" if eth_ma_dist else "N/A"
    eth_ma_price = f"${eth.get('ma_120', 0):,.0f}" if eth.get('ma_120') else "N/A"
    
    report = f"""📊 *Crypto Dashboard v5*
_{time_str} CET_

━━━━━━━━━━━━━━━━━━━

*BTC* ${btc.get('price_usd', 0):,.0f} ({btc.get('change_24h', 0):+.1f}%)
{btc_ma_sig} 120D MA: {btc_ma_price} ({btc_ma_str})
{btc_52h_sig} vs 52w High: {btc.get('from_52w_high', 0):.1f}%
{btc_52l_sig} vs 52w Low: +{btc.get('from_52w_low', 0):.1f}%

*ETH* ${eth.get('price_usd', 0):,.0f} ({eth.get('change_24h', 0):+.1f}%)
{eth_ma_sig} 120D MA: {eth_ma_price} ({eth_ma_str})
{eth_52h_sig} vs 52w High: {eth.get('from_52w_high', 0):.1f}%
{eth_52l_sig} vs 52w Low: +{eth.get('from_52w_low', 0):.1f}%

━━━━━━━━━━━━━━━━━━━

*Market Indicators*
{fg_sig} Fear & Greed: {fg.get('value', 'N/A')} ({fg.get('classification', '')})
{kp_sig} Kimchi Premium: {kp.get('premium_percent', 'N/A')}%
{fr_sig} Funding Rate: {fr.get('rate_percent', 0):.4f}%
{dom_sig} BTC Dominance: {dom.get('btc_dominance', 'N/A')}%

━━━━━━━━━━━━━━━━━━━

*Macro*
{m2_sig} US M2: ${m2.get('value_trillions', 0):.2f}T (YoY {m2.get('yoy_change', 0):+.1f}%)
⚪ USD/KRW: {kp.get('usd_krw', 0):,.0f}
{stable_sig} Stablecoin: ${stable.get('total_billions', 0):.0f}B

━━━━━━━━━━━━━━━━━━━
🔗 [ETF](https://sosovalue.com/assets/etf/us-btc-spot) • [SOPR](https://charts.bgeometrics.com/lth_sopr.html) • [MVRV](https://charts.bgeometrics.com/mvrv.html) • [M2](https://charts.bgeometrics.com/m2_global.html)

━━━━━━━━━━━━━━━━━━━
📋 *Signal Criteria*

*Price*
• 120D MA: 🟢+5%↑ 🟡±5% 🔴-5%↓
• 52w High: 🟢-15% 🟡-40% 🔴-40%↓
• 52w Low: 🟢+100%↑ 🟡+30%↑ 🔴+30%↓

*Market*
• F&G: 🟢≤25 🟡26-74 🔴≥75
• Kimchi: 🟢-1~2% 🟡-3~5% 🔴>5/<-3
• Funding: 🟢-0.01~0.03 🟡~0.08 🔴>0.08
• Dom: 🟢50-60% 🟡45-65% 🔴<45/>65

*Macro*
• M2: 🟢YoY+5%↑ 🟡0-5% 🔴<0%
• Stable: 🟢>$200B 🟡$150-200B 🔴<$150B
"""
    return report.strip()


def generate_email_report(data: Dict[str, Any]) -> str:
    """Generate HTML email report"""
    
    now = datetime.utcnow() + timedelta(hours=1)
    time_str = now.strftime("%Y-%m-%d %H:%M")
    
    btc = data.get("btc", {})
    eth = data.get("eth", {})
    fg = data.get("fear_greed", {})
    m2 = data.get("m2_supply", {})
    fr = data.get("funding_rate", {})
    kp = data.get("kimchi_premium", {})
    dom = data.get("dominance", {})
    stable = data.get("stablecoin", {})
    
    # Signals
    btc_ma_dist = btc.get('ma_120_distance')
    btc_ma_sig = get_ma_signal(btc_ma_dist)
    btc_52h_sig = get_52w_high_signal(btc.get('from_52w_high'))
    btc_52l_sig = get_52w_low_signal(btc.get('from_52w_low'))
    
    eth_ma_dist = eth.get('ma_120_distance')
    eth_ma_sig = get_ma_signal(eth_ma_dist)
    eth_52h_sig = get_52w_high_signal(eth.get('from_52w_high'))
    eth_52l_sig = get_52w_low_signal(eth.get('from_52w_low'))
    
    fg_sig = get_fear_greed_signal(fg.get('value'))
    kp_sig = get_kimchi_signal(kp.get('premium_percent'))
    fr_sig = get_funding_signal(fr.get('rate_percent'))
    dom_sig = get_dominance_signal(dom.get('btc_dominance'))
    m2_sig = get_m2_signal(m2.get('yoy_change'))
    stable_sig = get_stablecoin_signal(stable.get('total_billions'))
    
    btc_ma_str = f"{btc_ma_dist:+.1f}%" if btc_ma_dist else "N/A"
    btc_ma_price = f"${btc.get('ma_120', 0):,.0f}" if btc.get('ma_120') else "N/A"
    eth_ma_str = f"{eth_ma_dist:+.1f}%" if eth_ma_dist else "N/A"
    eth_ma_price = f"${eth.get('ma_120', 0):,.0f}" if eth.get('ma_120') else "N/A"
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            h2 {{ color: #555; margin-top: 25px; }}
            .section {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .price {{ font-size: 24px; font-weight: bold; }}
            .change-pos {{ color: green; }}
            .change-neg {{ color: red; }}
            table {{ width: 100%; border-collapse: collapse; }}
            td {{ padding: 8px 0; }}
            .signal {{ font-size: 18px; }}
            .links {{ margin-top: 20px; }}
            .links a {{ margin-right: 15px; color: #0066cc; }}
            .criteria {{ background: #e8f4f8; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 12px; }}
            .criteria h3 {{ margin-top: 0; }}
        </style>
    </head>
    <body>
        <h1>📊 Crypto Dashboard</h1>
        <p><em>{time_str} CET</em></p>
        
        <div class="section">
            <h2>BTC <span class="price">${btc.get('price_usd', 0):,.0f}</span> 
            <span class="{'change-pos' if btc.get('change_24h', 0) >= 0 else 'change-neg'}">({btc.get('change_24h', 0):+.1f}%)</span></h2>
            <table>
                <tr><td class="signal">{btc_ma_sig}</td><td>120D MA: {btc_ma_price} ({btc_ma_str})</td></tr>
                <tr><td class="signal">{btc_52h_sig}</td><td>vs 52w High: {btc.get('from_52w_high', 0):.1f}%</td></tr>
                <tr><td class="signal">{btc_52l_sig}</td><td>vs 52w Low: +{btc.get('from_52w_low', 0):.1f}%</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>ETH <span class="price">${eth.get('price_usd', 0):,.0f}</span>
            <span class="{'change-pos' if eth.get('change_24h', 0) >= 0 else 'change-neg'}">({eth.get('change_24h', 0):+.1f}%)</span></h2>
            <table>
                <tr><td class="signal">{eth_ma_sig}</td><td>120D MA: {eth_ma_price} ({eth_ma_str})</td></tr>
                <tr><td class="signal">{eth_52h_sig}</td><td>vs 52w High: {eth.get('from_52w_high', 0):.1f}%</td></tr>
                <tr><td class="signal">{eth_52l_sig}</td><td>vs 52w Low: +{eth.get('from_52w_low', 0):.1f}%</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Market Indicators</h2>
            <table>
                <tr><td class="signal">{fg_sig}</td><td>Fear & Greed: {fg.get('value', 'N/A')} ({fg.get('classification', '')})</td></tr>
                <tr><td class="signal">{kp_sig}</td><td>Kimchi Premium: {kp.get('premium_percent', 'N/A')}%</td></tr>
                <tr><td class="signal">{fr_sig}</td><td>Funding Rate: {fr.get('rate_percent', 0):.4f}%</td></tr>
                <tr><td class="signal">{dom_sig}</td><td>BTC Dominance: {dom.get('btc_dominance', 'N/A')}%</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Macro</h2>
            <table>
                <tr><td class="signal">{m2_sig}</td><td>US M2: ${m2.get('value_trillions', 0):.2f}T (YoY {m2.get('yoy_change', 0):+.1f}%)</td></tr>
                <tr><td class="signal">⚪</td><td>USD/KRW: {kp.get('usd_krw', 0):,.0f}</td></tr>
                <tr><td class="signal">{stable_sig}</td><td>Stablecoin: ${stable.get('total_billions', 0):.0f}B</td></tr>
            </table>
        </div>
        
        <div class="links">
            <strong>🔗 Manual Check:</strong><br><br>
            <a href="https://sosovalue.com/assets/etf/us-btc-spot">ETF Flow</a>
            <a href="https://charts.bgeometrics.com/lth_sopr.html">LTH-SOPR</a>
            <a href="https://charts.bgeometrics.com/mvrv.html">MVRV</a>
            <a href="https://charts.bgeometrics.com/m2_global.html">Global M2</a>
        </div>
        
        <div class="criteria">
            <h3>📋 Signal Criteria</h3>
            <p><strong>Price:</strong> 120D MA: 🟢+5%↑ 🟡±5% 🔴-5%↓ | 52w High: 🟢-15% 🟡-40% 🔴-40%↓ | 52w Low: 🟢+100%↑ 🟡+30%↑ 🔴+30%↓</p>
            <p><strong>Market:</strong> F&G: 🟢≤25 🟡26-74 🔴≥75 | Kimchi: 🟢-1~2% 🟡-3~5% 🔴>5/<-3 | Funding: 🟢-0.01~0.03 🟡~0.08 🔴>0.08 | Dom: 🟢50-60% 🟡45-65% 🔴<45/>65</p>
            <p><strong>Macro:</strong> M2: 🟢YoY+5%↑ 🟡0-5% 🔴<0% | Stable: 🟢>$200B 🟡$150-200B 🔴<$150B</p>
        </div>
    </body>
    </html>
    """
    return html


# ============================================
# SEND FUNCTIONS
# ============================================

def send_telegram(message: str) -> bool:
    """Send via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("✅ Telegram sent")
            return True
        else:
            print(f"❌ Telegram failed: {response.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")
    return False


def send_email(html_content: str) -> bool:
    """Send via Outlook email"""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("⚠️ Email not configured")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 Crypto Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_ADDRESS
        
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        # Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg.as_string())
        
        print("✅ Email sent")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
    return False


# ============================================
# MAIN
# ============================================

def main():
    print("🚀 Crypto Dashboard v5 starting...")
    print("=" * 40)
    
    data = {}
    
    print("📊 BTC...")
    data["btc"] = get_btc_detailed()
    time.sleep(2)
    
    print("📊 ETH...")
    data["eth"] = get_eth_detailed()
    time.sleep(2)
    
    print("📊 Fear & Greed...")
    data["fear_greed"] = get_fear_greed_index()
    time.sleep(1)
    
    print("📊 US M2...")
    data["m2_supply"] = get_us_m2_supply()
    time.sleep(1)
    
    print("📊 Funding Rate...")
    data["funding_rate"] = get_funding_rate()
    time.sleep(1)
    
    print("📊 Kimchi Premium...")
    data["kimchi_premium"] = get_kimchi_premium()
    time.sleep(1)
    
    print("📊 Dominance...")
    data["dominance"] = get_btc_dominance()
    time.sleep(1)
    
    print("📊 Stablecoin...")
    data["stablecoin"] = get_stablecoin_supply()
    
    print("=" * 40)
    
    # Generate reports
    telegram_report = generate_report(data)
    email_report = generate_email_report(data)
    
    print("\n" + telegram_report)
    
    # Send
    send_telegram(telegram_report)
    send_email(email_report)
    
    # Save
    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
