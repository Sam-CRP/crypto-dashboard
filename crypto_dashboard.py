#!/usr/bin/env python3
"""
🚀 Crypto Dashboard v3 - 맞춤 버전
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
# 데이터 수집 함수들
# ============================================

def get_btc_detailed() -> Dict[str, Any]:
    """BTC 상세 데이터 (가격, 52주 고저, 120일 MA)"""
    try:
        # 현재 가격 및 기본 데이터
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
        ath = market_data.get("ath", {}).get("usd", 0)
        ath_change = market_data.get("ath_change_percentage", {}).get("usd", 0)
        
        result = {
            "price_usd": current_price,
            "price_krw": market_data.get("current_price", {}).get("krw", 0),
            "change_24h": market_data.get("price_change_percentage_24h", 0),
            "change_7d": market_data.get("price_change_percentage_7d", 0),
            "ath": ath,
            "ath_change": ath_change,
        }
        
        # 52주 고저 및 120일 MA 계산을 위한 히스토리 데이터
        time.sleep(1)  # Rate limit
        history_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        history_params = {
            "vs_currency": "usd",
            "days": "365",  # 1년 데이터
            "interval": "daily"
        }
        history_response = requests.get(history_url, params=history_params, timeout=15)
        history_data = history_response.json()
        
        prices = [p[1] for p in history_data.get("prices", [])]
        
        if prices:
            # 52주 최고/최저
            high_52w = max(prices)
            low_52w = min(prices)
            
            # 52주 최고 대비 하락폭
            from_52w_high = ((current_price - high_52w) / high_52w * 100) if high_52w else 0
            
            # 52주 최저 대비 상승폭
            from_52w_low = ((current_price - low_52w) / low_52w * 100) if low_52w else 0
            
            result["high_52w"] = high_52w
            result["low_52w"] = low_52w
            result["from_52w_high"] = from_52w_high
            result["from_52w_low"] = from_52w_low
            
            # 120일 MA 계산
            if len(prices) >= 120:
                ma_120 = sum(prices[-120:]) / 120
                ma_distance = ((current_price - ma_120) / ma_120 * 100) if ma_120 else 0
                result["ma_120"] = ma_120
                result["ma_120_distance"] = ma_distance
            else:
                result["ma_120"] = None
                result["ma_120_distance"] = None
        
        return result
        
    except Exception as e:
        print(f"❌ BTC 상세 조회 실패: {e}")
        return {}


def get_eth_detailed() -> Dict[str, Any]:
    """ETH 상세 데이터 (가격, 52주 고저, 120일 MA)"""
    try:
        # 현재 가격
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
        
        # 52주 고저 및 120일 MA
        time.sleep(1)
        history_url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
        history_params = {
            "vs_currency": "usd",
            "days": "365",
            "interval": "daily"
        }
        history_response = requests.get(history_url, params=history_params, timeout=15)
        history_data = history_response.json()
        
        prices = [p[1] for p in history_data.get("prices", [])]
        
        if prices:
            high_52w = max(prices)
            low_52w = min(prices)
            
            from_52w_high = ((current_price - high_52w) / high_52w * 100) if high_52w else 0
            from_52w_low = ((current_price - low_52w) / low_52w * 100) if low_52w else 0
            
            result["high_52w"] = high_52w
            result["low_52w"] = low_52w
            result["from_52w_high"] = from_52w_high
            result["from_52w_low"] = from_52w_low
            
            if len(prices) >= 120:
                ma_120 = sum(prices[-120:]) / 120
                ma_distance = ((current_price - ma_120) / ma_120 * 100) if ma_120 else 0
                result["ma_120"] = ma_120
                result["ma_120_distance"] = ma_distance
            else:
                result["ma_120"] = None
                result["ma_120_distance"] = None
        
        return result
        
    except Exception as e:
        print(f"❌ ETH 상세 조회 실패: {e}")
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
            week_ago = data[6] if len(data) > 6 else current
            
            return {
                "value": int(current.get("value", 0)),
                "classification": current.get("value_classification", ""),
                "yesterday": int(yesterday.get("value", 0)),
                "week_ago": int(week_ago.get("value", 0)),
                "change": int(current.get("value", 0)) - int(yesterday.get("value", 0)),
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
                "date": data[0].get("date", ""),
                "mom_change": ((current - previous) / previous * 100) if previous else 0,
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
            return {
                "rate_percent": rate * 100,
                "status": "🔴과열" if rate > 0.001 else "🟢정상" if rate > -0.001 else "🔵과매도",
            }
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
            "status": "🔴과열" if premium > 5 else "🟢정상" if premium > -2 else "🔵역프",
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
            "eth_dominance": round(data.get("market_cap_percentage", {}).get("eth", 0), 1),
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
        
        return {
            "usdt_billions": usdt,
            "usdc_billions": usdc,
            "total_billions": usdt + usdc,
        }
    except Exception as e:
        print(f"⚠️ 스테이블코인 조회 실패: {e}")
    return {}


# ============================================
# 시그널 분석 (매매 추천 없음)
# ============================================

def analyze_signals(data: Dict[str, Any]) -> Dict[str, Any]:
    """시장 시그널 분석 - 정보 제공만, 추천 없음"""
    
    signals = {
        "bullish": [],
        "bearish": [],
        "neutral": [],
    }
    
    # Fear & Greed
    fg = data.get("fear_greed", {})
    if fg:
        value = fg.get("value", 50)
        if value <= 25:
            signals["bullish"].append(f"극단적 공포 ({value})")
        elif value >= 75:
            signals["bearish"].append(f"극단적 탐욕 ({value})")
        else:
            signals["neutral"].append(f"Fear & Greed {value}")
    
    # 120일 MA 거리
    btc = data.get("btc", {})
    if btc:
        ma_dist = btc.get("ma_120_distance")
        if ma_dist is not None:
            if ma_dist < -20:
                signals["bullish"].append(f"120D MA 대비 {ma_dist:.1f}%")
            elif ma_dist > 50:
                signals["bearish"].append(f"120D MA 대비 +{ma_dist:.1f}%")
            elif ma_dist < 0:
                signals["neutral"].append(f"120D MA 아래 ({ma_dist:.1f}%)")
            else:
                signals["neutral"].append(f"120D MA 위 (+{ma_dist:.1f}%)")
    
    # Funding Rate
    fr = data.get("funding_rate", {})
    if fr:
        rate = fr.get("rate_percent", 0)
        if rate > 0.05:
            signals["bearish"].append(f"Funding 과열 ({rate:.3f}%)")
        elif rate < -0.01:
            signals["bullish"].append(f"Funding 과매도 ({rate:.3f}%)")
    
    # 김치 프리미엄
    kp = data.get("kimchi_premium", {})
    if kp:
        premium = kp.get("premium_percent", 0)
        if premium > 5:
            signals["bearish"].append(f"김프 과열 ({premium:.1f}%)")
        elif premium < -2:
            signals["bullish"].append(f"김프 역프리미엄 ({premium:.1f}%)")
    
    return {
        "signals": signals,
        "bullish_count": len(signals["bullish"]),
        "bearish_count": len(signals["bearish"]),
    }


# ============================================
# 리포트 생성
# ============================================

def generate_report(data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """텔레그램용 리포트"""
    
    now = datetime.utcnow() + timedelta(hours=1)  # UTC+1 (독일)
    time_str = now.strftime("%Y-%m-%d %H:%M")
    
    btc = data.get("btc", {})
    eth = data.get("eth", {})
    fg = data.get("fear_greed", {})
    m2 = data.get("m2_supply", {})
    fr = data.get("funding_rate", {})
    kp = data.get("kimchi_premium", {})
    dom = data.get("dominance", {})
    stable = data.get("stablecoin", {})
    
    # 시그널
    bullish = analysis.get("signals", {}).get("bullish", [])
    bearish = analysis.get("signals", {}).get("bearish", [])
    
    bullish_text = "\n".join(f"  • {s}" for s in bullish) if bullish else "  • 없음"
    bearish_text = "\n".join(f"  • {s}" for s in bearish) if bearish else "  • 없음"
    
    # 120D MA 포맷
    btc_ma = btc.get('ma_120_distance')
    btc_ma_str = f"{btc_ma:+.1f}%" if btc_ma is not None else "N/A"
    btc_ma_price = f"${btc.get('ma_120', 0):,.0f}" if btc.get('ma_120') else "N/A"
    
    eth_ma = eth.get('ma_120_distance')
    eth_ma_str = f"{eth_ma:+.1f}%" if eth_ma is not None else "N/A"
    eth_ma_price = f"${eth.get('ma_120', 0):,.0f}" if eth.get('ma_120') else "N/A"
    
    report = f"""📊 *크립토 대시보드*
_{time_str} CET_

━━━━━━━━━━━━━━━━━━━

*BTC* ${btc.get('price_usd', 0):,.0f} ({btc.get('change_24h', 0):+.1f}%)
• 120D MA: {btc_ma_price} ({btc_ma_str})
• 52주 최고 대비: {btc.get('from_52w_high', 0):.1f}%
• 52주 최저 대비: +{btc.get('from_52w_low', 0):.1f}%

*ETH* ${eth.get('price_usd', 0):,.0f} ({eth.get('change_24h', 0):+.1f}%)
• 120D MA: {eth_ma_price} ({eth_ma_str})
• 52주 최고 대비: {eth.get('from_52w_high', 0):.1f}%
• 52주 최저 대비: +{eth.get('from_52w_low', 0):.1f}%

━━━━━━━━━━━━━━━━━━━

*시장 지표*
• Fear & Greed: {fg.get('value', 'N/A')} ({fg.get('classification', '')})
• 김치프리미엄: {kp.get('premium_percent', 'N/A')}% {kp.get('status', '')}
• Funding: {fr.get('rate_percent', 0):.4f}% {fr.get('status', '')}
• BTC 도미넌스: {dom.get('btc_dominance', 'N/A')}%

━━━━━━━━━━━━━━━━━━━

*매크로*
• US M2: ${m2.get('value_trillions', 0):.2f}T (YoY {m2.get('yoy_change', 0):+.1f}%)
• USD/KRW: {kp.get('usd_krw', 0):,.0f}
• 스테이블: ${stable.get('total_billions', 0):.0f}B

━━━━━━━━━━━━━━━━━━━

*시그널*
🟢 Bullish ({analysis.get('bullish_count', 0)}):
{bullish_text}

🔴 Bearish ({analysis.get('bearish_count', 0)}):
{bearish_text}

━━━━━━━━━━━━━━━━━━━
🔗 [ETF Flow](https://sosovalue.com/assets/etf/us-btc-spot) • [LTH-SOPR](https://charts.bgeometrics.com/lth_sopr.html) • [MVRV](https://charts.bgeometrics.com/mvrv.html) • [글로벌M2](https://charts.bgeometrics.com/m2_global.html)
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
    print("🚀 크립토 대시보드 시작...")
    print("=" * 40)
    
    data = {}
    
    print("📊 BTC 데이터...")
    data["btc"] = get_btc_detailed()
    time.sleep(2)
    
    print("📊 ETH 데이터...")
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
    print("🔍 분석 중...")
    
    analysis = analyze_signals(data)
    report = generate_report(data, analysis)
    
    print("\n" + report)
    send_telegram(report)
    
    # 저장
    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "analysis": analysis,
        }, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 완료!")


if __name__ == "__main__":
    main()
