#!/usr/bin/env python3
"""
🚀 Crypto Dashboard - 매일 아침 자동 업데이트
무료 데이터 소스만 사용하여 비트코인 온체인/매크로 지표 수집

실행: python crypto_dashboard.py
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

# Telegram 설정 (선택사항 - 환경변수로 설정)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# FRED API 키 (https://fred.stlouisfed.org/docs/api/api_key.html 에서 무료 발급)
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# ============================================
# 데이터 수집 함수들
# ============================================

def get_btc_price() -> Dict[str, Any]:
    """CoinGecko에서 BTC 가격 및 기본 데이터 (무료)"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        market_data = data.get("market_data", {})
        return {
            "price_usd": market_data.get("current_price", {}).get("usd", 0),
            "price_krw": market_data.get("current_price", {}).get("krw", 0),
            "change_24h": market_data.get("price_change_percentage_24h", 0),
            "change_7d": market_data.get("price_change_percentage_7d", 0),
            "market_cap": market_data.get("market_cap", {}).get("usd", 0),
            "ath": market_data.get("ath", {}).get("usd", 0),
            "ath_change": market_data.get("ath_change_percentage", {}).get("usd", 0),
        }
    except Exception as e:
        print(f"❌ BTC 가격 조회 실패: {e}")
        return {}


def get_eth_price() -> Dict[str, Any]:
    """CoinGecko에서 ETH 가격 (무료)"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "ethereum",
            "vs_currencies": "usd,krw",
            "include_24hr_change": "true",
            "include_7d_change": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json().get("ethereum", {})
        
        return {
            "price_usd": data.get("usd", 0),
            "price_krw": data.get("krw", 0),
            "change_24h": data.get("usd_24h_change", 0),
        }
    except Exception as e:
        print(f"❌ ETH 가격 조회 실패: {e}")
        return {}


def get_fear_greed_index() -> Dict[str, Any]:
    """Alternative.me Fear & Greed Index (무료)"""
    try:
        url = "https://api.alternative.me/fng/"
        params = {"limit": 7}  # 최근 7일
        response = requests.get(url, params=params, timeout=10)
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
    """FRED API에서 미국 M2 통화량 (무료 - API 키 필요)"""
    if not FRED_API_KEY:
        print("⚠️ FRED_API_KEY 환경변수가 설정되지 않았습니다")
        return {}
    
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "M2SL",
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 13,  # 최근 13개월 (YoY 계산용)
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json().get("observations", [])
        
        if len(data) >= 2:
            current = float(data[0].get("value", 0))
            previous = float(data[1].get("value", 0))
            year_ago = float(data[12].get("value", current)) if len(data) > 12 else current
            
            return {
                "value_billions": current,
                "value_trillions": current / 1000,
                "date": data[0].get("date", ""),
                "mom_change": ((current - previous) / previous * 100) if previous else 0,
                "yoy_change": ((current - year_ago) / year_ago * 100) if year_ago else 0,
            }
    except Exception as e:
        print(f"❌ M2 조회 실패: {e}")
    return {}


def get_funding_rate() -> Dict[str, Any]:
    """Binance에서 BTC Funding Rate (무료)"""
    try:
        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        params = {"symbol": "BTCUSDT", "limit": 1}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data:
            rate = float(data[0].get("fundingRate", 0))
            return {
                "rate": rate,
                "rate_percent": rate * 100,
                "annualized": rate * 100 * 3 * 365,  # 8시간마다 3번
                "status": "과열" if rate > 0.001 else "정상" if rate > -0.001 else "과매도",
            }
    except Exception as e:
        print(f"❌ Funding Rate 조회 실패: {e}")
    return {}


def get_open_interest() -> Dict[str, Any]:
    """Binance에서 BTC Open Interest (무료)"""
    try:
        url = "https://fapi.binance.com/fapi/v1/openInterest"
        params = {"symbol": "BTCUSDT"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        oi_btc = float(data.get("openInterest", 0))
        
        # 가격 조회해서 USD 환산
        btc_price = get_btc_price().get("price_usd", 0)
        oi_usd = oi_btc * btc_price if btc_price else 0
        
        return {
            "btc": oi_btc,
            "usd": oi_usd,
            "usd_billions": oi_usd / 1_000_000_000,
        }
    except Exception as e:
        print(f"❌ Open Interest 조회 실패: {e}")
    return {}


def get_etf_flow_sosovalue() -> Dict[str, Any]:
    """SoSoValue에서 ETF Flow (웹에서 수동 확인 필요 - API 제한적)"""
    # SoSoValue API는 제한적이므로 수동 입력 또는 스크래핑 필요
    # 여기서는 URL만 제공
    return {
        "btc_etf_url": "https://sosovalue.com/assets/etf/us-btc-spot",
        "eth_etf_url": "https://sosovalue.com/assets/etf/us-eth-spot",
        "note": "수동 확인 필요 (자동 스크래핑 어려움)",
    }


def get_kimchi_premium() -> Dict[str, Any]:
    """업비트/바이낸스 비교로 김치 프리미엄 계산"""
    try:
        # 업비트 BTC 가격 (KRW)
        upbit_url = "https://api.upbit.com/v1/ticker"
        upbit_response = requests.get(upbit_url, params={"markets": "KRW-BTC"}, timeout=10)
        upbit_price = upbit_response.json()[0].get("trade_price", 0)
        
        # 바이낸스 BTC 가격 (USDT)
        binance_url = "https://api.binance.com/api/v3/ticker/price"
        binance_response = requests.get(binance_url, params={"symbol": "BTCUSDT"}, timeout=10)
        binance_price = float(binance_response.json().get("price", 0))
        
        # 환율 (USD/KRW)
        fx_url = "https://api.exchangerate-api.com/v4/latest/USD"
        fx_response = requests.get(fx_url, timeout=10)
        usd_krw = fx_response.json().get("rates", {}).get("KRW", 1300)
        
        # 김치 프리미엄 계산
        binance_krw = binance_price * usd_krw
        premium = ((upbit_price - binance_krw) / binance_krw * 100) if binance_krw else 0
        
        return {
            "upbit_krw": upbit_price,
            "binance_usdt": binance_price,
            "binance_krw": binance_krw,
            "usd_krw": usd_krw,
            "premium_percent": round(premium, 2),
            "status": "과열" if premium > 5 else "정상" if premium > -2 else "역프리미엄",
        }
    except Exception as e:
        print(f"❌ 김치 프리미엄 조회 실패: {e}")
    return {}


# ============================================
# 분석 및 판단 로직
# ============================================

def analyze_market(data: Dict[str, Any]) -> Dict[str, Any]:
    """수집된 데이터를 기반으로 시장 분석"""
    
    signals = {
        "bullish": [],
        "bearish": [],
        "neutral": [],
    }
    
    # Fear & Greed 분석
    fg = data.get("fear_greed", {})
    if fg:
        value = fg.get("value", 50)
        if value <= 20:
            signals["bullish"].append(f"극단적 공포 ({value}) - 역발상 매수 기회")
        elif value <= 40:
            signals["neutral"].append(f"공포 구간 ({value})")
        elif value >= 80:
            signals["bearish"].append(f"극단적 탐욕 ({value}) - 조정 가능성")
        elif value >= 60:
            signals["neutral"].append(f"탐욕 구간 ({value})")
    
    # M2 분석
    m2 = data.get("m2_supply", {})
    if m2:
        yoy = m2.get("yoy_change", 0)
        if yoy > 5:
            signals["bullish"].append(f"M2 YoY +{yoy:.1f}% - 유동성 확대")
        elif yoy > 0:
            signals["neutral"].append(f"M2 YoY +{yoy:.1f}%")
        else:
            signals["bearish"].append(f"M2 YoY {yoy:.1f}% - 유동성 축소")
    
    # Funding Rate 분석
    fr = data.get("funding_rate", {})
    if fr:
        rate = fr.get("rate_percent", 0)
        if rate > 0.1:
            signals["bearish"].append(f"Funding Rate 과열 ({rate:.3f}%)")
        elif rate < -0.05:
            signals["bullish"].append(f"Funding Rate 과매도 ({rate:.3f}%)")
        else:
            signals["neutral"].append(f"Funding Rate 정상 ({rate:.3f}%)")
    
    # 김치 프리미엄 분석
    kp = data.get("kimchi_premium", {})
    if kp:
        premium = kp.get("premium_percent", 0)
        if premium > 5:
            signals["bearish"].append(f"김치 프리미엄 과열 ({premium:.1f}%)")
        elif premium < -2:
            signals["bullish"].append(f"김치 역프리미엄 ({premium:.1f}%)")
        else:
            signals["neutral"].append(f"김치 프리미엄 정상 ({premium:.1f}%)")
    
    # BTC 가격 분석
    btc = data.get("btc", {})
    if btc:
        change_7d = btc.get("change_7d", 0)
        ath_change = btc.get("ath_change", 0)
        
        if change_7d < -15:
            signals["bullish"].append(f"7일 급락 ({change_7d:.1f}%) - 반등 가능성")
        elif change_7d > 15:
            signals["bearish"].append(f"7일 급등 ({change_7d:.1f}%) - 조정 가능성")
        
        if ath_change < -50:
            signals["bullish"].append(f"ATH 대비 {ath_change:.0f}% - 저점 매수 구간")
    
    # 종합 판단
    bullish_count = len(signals["bullish"])
    bearish_count = len(signals["bearish"])
    
    if bullish_count > bearish_count + 1:
        overall = "🟢 BULLISH"
        action = "분할 매수 고려"
    elif bearish_count > bullish_count + 1:
        overall = "🔴 BEARISH"
        action = "매수 대기, 리스크 관리"
    else:
        overall = "🟡 NEUTRAL"
        action = "관망, 확인 후 대응"
    
    return {
        "signals": signals,
        "overall": overall,
        "action": action,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
    }


# ============================================
# 리포트 생성
# ============================================

def generate_report(data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """텔레그램/콘솔용 리포트 생성"""
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    btc = data.get("btc", {})
    eth = data.get("eth", {})
    fg = data.get("fear_greed", {})
    m2 = data.get("m2_supply", {})
    fr = data.get("funding_rate", {})
    kp = data.get("kimchi_premium", {})
    
    report = f"""
📊 **크립토 대시보드** ({now})

━━━━━━━━━━━━━━━━━━━━━━

💰 **가격 현황**
• BTC: ${btc.get('price_usd', 0):,.0f} ({btc.get('change_24h', 0):+.1f}% 24h)
• ETH: ${eth.get('price_usd', 0):,.0f} ({eth.get('change_24h', 0):+.1f}% 24h)
• BTC ATH 대비: {btc.get('ath_change', 0):.0f}%

━━━━━━━━━━━━━━━━━━━━━━

📈 **시장 지표**
• Fear & Greed: {fg.get('value', 'N/A')} ({fg.get('classification', '')})
  └ 어제: {fg.get('yesterday', 'N/A')} | 7일전: {fg.get('week_ago', 'N/A')}
• 김치 프리미엄: {kp.get('premium_percent', 'N/A')}% ({kp.get('status', '')})
• Funding Rate: {fr.get('rate_percent', 0):.4f}% ({fr.get('status', '')})

━━━━━━━━━━━━━━━━━━━━━━

💵 **매크로**
• US M2: ${m2.get('value_trillions', 0):.2f}T (YoY {m2.get('yoy_change', 0):+.1f}%)
• USD/KRW: {kp.get('usd_krw', 0):,.0f}

━━━━━━━━━━━━━━━━━━━━━━

🎯 **시그널 분석**

🟢 Bullish ({analysis.get('bullish_count', 0)}):
{chr(10).join('• ' + s for s in analysis.get('signals', {}).get('bullish', ['없음'])) or '• 없음'}

🔴 Bearish ({analysis.get('bearish_count', 0)}):
{chr(10).join('• ' + s for s in analysis.get('signals', {}).get('bearish', ['없음'])) or '• 없음'}

━━━━━━━━━━━━━━━━━━━━━━

**종합 판단: {analysis.get('overall', 'N/A')}**
**액션: {analysis.get('action', 'N/A')}**

━━━━━━━━━━━━━━━━━━━━━━
📌 수동 확인 필요:
• ETF Flow: sosovalue.com/assets/etf/us-btc-spot
• LTH-SOPR: charts.bgeometrics.com/lth_sopr.html
• MVRV: charts.bgeometrics.com/mvrv.html
• 글로벌 M2: charts.bgeometrics.com/m2_global.html
"""
    return report.strip()


# ============================================
# 알림 발송
# ============================================

def send_telegram(message: str) -> bool:
    """텔레그램으로 메시지 발송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram 설정이 없습니다. 콘솔에만 출력합니다.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ 텔레그램 발송 성공")
            return True
        else:
            print(f"❌ 텔레그램 발송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 텔레그램 발송 오류: {e}")
    return False


# ============================================
# 메인 실행
# ============================================

def main():
    print("🚀 크립토 대시보드 데이터 수집 시작...")
    print("=" * 50)
    
    # 데이터 수집
    data = {}
    
    print("📊 BTC 가격 조회 중...")
    data["btc"] = get_btc_price()
    time.sleep(1)  # Rate limit 방지
    
    print("📊 ETH 가격 조회 중...")
    data["eth"] = get_eth_price()
    time.sleep(1)
    
    print("📊 Fear & Greed Index 조회 중...")
    data["fear_greed"] = get_fear_greed_index()
    time.sleep(1)
    
    print("📊 US M2 Supply 조회 중...")
    data["m2_supply"] = get_us_m2_supply()
    time.sleep(1)
    
    print("📊 Funding Rate 조회 중...")
    data["funding_rate"] = get_funding_rate()
    time.sleep(1)
    
    print("📊 김치 프리미엄 조회 중...")
    data["kimchi_premium"] = get_kimchi_premium()
    
    print("📊 ETF Flow URL 확인...")
    data["etf_flow"] = get_etf_flow_sosovalue()
    
    print("=" * 50)
    print("🔍 시장 분석 중...")
    
    # 분석
    analysis = analyze_market(data)
    
    # 리포트 생성
    report = generate_report(data, analysis)
    
    # 콘솔 출력
    print("\n" + report)
    
    # 텔레그램 발송
    send_telegram(report)
    
    # JSON 파일로 저장 (GitHub Actions에서 히스토리 추적용)
    output = {
        "timestamp": datetime.now().isoformat(),
        "data": data,
        "analysis": analysis,
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 히스토리 추가
    history_file = "data/history.json"
    history = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    
    history.append(output)
    history = history[-30:]  # 최근 30일만 유지
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 완료! data/latest.json에 저장됨")
    
    return output


if __name__ == "__main__":
    main()
