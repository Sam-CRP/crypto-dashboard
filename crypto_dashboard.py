#!/usr/bin/env python3
"""
🚀 Crypto Dashboard v4 - 신호등 버전
알림 시간: 독일 06:50, 21:20
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import time

# ============================================
# 설정
# ============================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# ============================================
# 신호등 판단 함수들
# ============================================

def get_ma_signal(distance: float) -> str:
    """120D MA 거리 신호등
    🟢 +5% 이상 (MA 위 건강)
    🟡 -5% ~ +5% (MA 근처)
    🔴 -5% 이하 (MA 아래 위험)
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
    """52주 고점 대비 신호등
    🟢 -15% 이내 (고점 근처)
    🟡 -15% ~ -40%
    🔴 -40% 이하 (크게 하락)
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
    """52주 저점 대비 신호등
    🟢 +100% 이상 (많이 상승)
    🟡 +30% ~ +100%
    🔴 +30% 이하 (저점 근처)
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
    """Fear & Greed 신호등
    🟢 ≤25 (극단적 공포 = 역발상 기회)
    🟡 26~74 (중립)
    🔴 ≥75 (극단적 탐욕 = 주의)
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
    """김치 프리미엄 신호등
    🟢 -1% ~ 2% (정상)
    🟡 2%~5% 또는 -1%~-3%
    🔴 >5% 또는 <-3%
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
    """Funding Rate 신호등 (%)
    🟢 -0.01% ~ 0.03% (정상)
    🟡 0.03%~0.08% 또는 -0.01%~-0.03%
    🔴 >0.08% 또는 <-0.03% (과열/과매도)
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
    """BTC 도미넌스 신호등
    🟢 50%~60% (균형)
    🟡 45%~50% 또는 60%~65%
    🔴 <45% 또는 >65%
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
    """US M2 YoY 신호등
    🟢 >5% (유동성 확장)
    🟡 0%~5%
    🔴 <0% (유동성 축소)
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
    """스테이블코인 시총 신호등
    🟢 >$200B
    🟡 $150B~$200B
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
# 데이터 수집 함수들
# ============================================

def get_btc_detailed() -> Dict[str, Any]:
    """BTC 상세 데이터"""
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
        print(f"❌ BTC 조회 실패: {e}")
        return {}


def get_eth_detailed() -> Dict[str, Any]:
    """ETH 상세 데이터"""
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
        print(f"❌ ETH 조회 실패: {e}")
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
        print(f"❌ Fear & Greed 조회 실패: {e}")
    return {}


def get_us_m2_supply() -> Dict[str, Any]:
    """FRED API - 미국 M2"""
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
            previous = float(data[1].get("value", 0))
            year_ago = float(data[12].get("value", current)) if len(data) > 12 else current
            
            return {
                "value_trillions": current / 1000,
                "yoy_change": ((current - year_ago) / year_ago * 100) if year_ago else 0,
            }
    except Exception as e:
        print(f"❌ M2 조회 실패: {e}")
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
        print(f"❌ Funding Rate 조회 실패: {e}")
    return {}


def get_kimchi_premium() -> Dict[str, Any]:
    """김치 프리미엄"""
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
        print(f"❌ 김치 프리미엄 조회 실패: {e}")
    return {}


def get_btc_dominance() -> Dict[str, Any]:
    """BTC 도미넌스"""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=15)
        data = response.json().get("data", {})
        
        return {
            "btc_dominance": round(data.get("market_cap_percentage", {}).get("btc", 0), 1),
        }
    except Exception as e:
        print(f"⚠️ 도미넌스 조회 실패: {e}")
    return {}


def get_stablecoin_supply() -> Dict[str, Any]:
    """스테이블코인 시총"""
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
        print(f"⚠️ 스테이블코인 조회 실패: {e}")
    return {}


# ============================================
# 리포트 생성
# ============================================

def generate_report(data: Dict[str, Any]) -> str:
    """텔레그램용 리포트 (신호등 포함)"""
    
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
    
    # BTC 신호등
    btc_ma_dist = btc.get('ma_120_distance')
    btc_ma_sig = get_ma_signal(btc_ma_dist)
    btc_52h_sig = get_52w_high_signal(btc.get('from_52w_high'))
    btc_52l_sig = get_52w_low_signal(btc.get('from_52w_low'))
    
    # ETH 신호등
    eth_ma_dist = eth.get('ma_120_distance')
    eth_ma_sig = get_ma_signal(eth_ma_dist)
    eth_52h_sig = get_52w_high_signal(eth.get('from_52w_high'))
    eth_52l_sig = get_52w_low_signal(eth.get('from_52w_low'))
    
    # 시장 지표 신호등
    fg_sig = get_fear_greed_signal(fg.get('value'))
    kp_sig = get_kimchi_signal(kp.get('premium_percent'))
    fr_sig = get_funding_signal(fr.get('rate_percent'))
    dom_sig = get_dominance_signal(dom.get('btc_dominance'))
    
    # 매크로 신호등
    m2_sig = get_m2_signal(m2.get('yoy_change'))
    stable_sig = get_stablecoin_signal(stable.get('total_billions'))
    
    # 포맷팅
    btc_ma_str = f"{btc_ma_dist:+.1f}%" if btc_ma_dist else "N/A"
    btc_ma_price = f"${btc.get('ma_120', 0):,.0f}" if btc.get('ma_120') else "N/A"
    eth_ma_str = f"{eth_ma_dist:+.1f}%" if eth_ma_dist else "N/A"
    eth_ma_price = f"${eth.get('ma_120', 0):,.0f}" if eth.get('ma_120') else "N/A"
    
    report = f"""📊 *크립토 대시보드 v4*
_{time_str} CET_

━━━━━━━━━━━━━━━━━━━

*BTC* ${btc.get('price_usd', 0):,.0f} ({btc.get('change_24h', 0):+.1f}%)
{btc_ma_sig} 120D MA: {btc_ma_price} ({btc_ma_str})
{btc_52h_sig} 52주 고점 대비: {btc.get('from_52w_high', 0):.1f}%
{btc_52l_sig} 52주 저점 대비: +{btc.get('from_52w_low', 0):.1f}%

*ETH* ${eth.get('price_usd', 0):,.0f} ({eth.get('change_24h', 0):+.1f}%)
{eth_ma_sig} 120D MA: {eth_ma_price} ({eth_ma_str})
{eth_52h_sig} 52주 고점 대비: {eth.get('from_52w_high', 0):.1f}%
{eth_52l_sig} 52주 저점 대비: +{eth.get('from_52w_low', 0):.1f}%

━━━━━━━━━━━━━━━━━━━

*시장 지표*
{fg_sig} Fear & Greed: {fg.get('value', 'N/A')} ({fg.get('classification', '')})
{kp_sig} 김치프리미엄: {kp.get('premium_percent', 'N/A')}%
{fr_sig} Funding Rate: {fr.get('rate_percent', 0):.4f}%
{dom_sig} BTC 도미넌스: {dom.get('btc_dominance', 'N/A')}%

━━━━━━━━━━━━━━━━━━━

*매크로*
{m2_sig} US M2: ${m2.get('value_trillions', 0):.2f}T (YoY {m2.get('yoy_change', 0):+.1f}%)
⚪ USD/KRW: {kp.get('usd_krw', 0):,.0f}
{stable_sig} 스테이블: ${stable.get('total_billions', 0):.0f}B

━━━━━━━━━━━━━━━━━━━
🔗 [ETF](https://sosovalue.com/assets/etf/us-btc-spot) • [SOPR](https://charts.bgeometrics.com/lth_sopr.html) • [MVRV](https://charts.bgeometrics.com/mvrv.html) • [M2](https://charts.bgeometrics.com/m2_global.html)

━━━━━━━━━━━━━━━━━━━
📋 *신호등 기준*

*가격*
• 120D MA: 🟢+5%↑ 🟡±5% 🔴-5%↓
• 52주高: 🟢-15%내 🟡-40%내 🔴-40%↓
• 52주低: 🟢+100%↑ 🟡+30%↑ 🔴+30%↓

*시장*
• F&G: 🟢≤25 🟡26-74 🔴≥75
• 김프: 🟢-1~2% 🟡-3~5% 🔴>5/<-3
• 펀딩: 🟢-0.01~0.03 🟡~0.08 🔴>0.08
• 도미: 🟢50-60% 🟡45-65% 🔴<45/>65

*매크로*
• M2: 🟢YoY+5%↑ 🟡0-5% 🔴<0%
• 스테이블: 🟢>$200B 🟡$150-200B 🔴<$150B
"""
    return report.strip()


# ============================================
# 텔레그램 발송
# ============================================

def send_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram 미설정")
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
            print("✅ 텔레그램 발송 성공")
            return True
        else:
            print(f"❌ 발송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 발송 오류: {e}")
    return False


# ============================================
# 메인
# ============================================

def main():
    print("🚀 크립토 대시보드 v4 시작...")
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
    
    print("📊 김치 프리미엄...")
    data["kimchi_premium"] = get_kimchi_premium()
    time.sleep(1)
    
    print("📊 도미넌스...")
    data["dominance"] = get_btc_dominance()
    time.sleep(1)
    
    print("📊 스테이블코인...")
    data["stablecoin"] = get_stablecoin_supply()
    
    print("=" * 40)
    
    report = generate_report(data)
    print("\n" + report)
    send_telegram(report)
    
    # 저장
    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 완료!")


if __name__ == "__main__":
    main()
