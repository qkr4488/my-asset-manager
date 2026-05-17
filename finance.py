"""
finance.py - 금융 계산 모듈
복리 계산, 적금/예금 만기 금액, 주식 가격 조회 등을 제공합니다.
"""
from datetime import datetime, timedelta


def compound_deposit(principal, annual_rate, period_months,
                     compound_period=12, tax_rate=15.4):
    """
    예금(거치식)의 복리 계산
    principal: 원금
    annual_rate: 연이율 (%)
    period_months: 기간(개월)
    compound_period: 연 복리 횟수 (12=월복리, 4=분기복리, 1=단리에 가까운 연복리)
    tax_rate: 이자소득세율 (%)
    """
    r = annual_rate / 100.0
    n = compound_period
    t = period_months / 12.0
    final = principal * ((1 + r / n) ** (n * t))
    interest = final - principal
    tax = interest * (tax_rate / 100.0)
    net_interest = interest - tax
    after_tax_total = principal + net_interest
    return {
        "principal": principal,
        "interest_gross": interest,
        "tax": tax,
        "interest_net": net_interest,
        "total": after_tax_total,
    }


def compound_savings(monthly_payment, annual_rate, period_months,
                     compound_period=12, tax_rate=15.4):
    """
    적금(매월 납입식)의 복리 계산
    각 회차 납입금에 대해 남은 기간 동안 복리가 적용됩니다.
    """
    r = annual_rate / 100.0
    n = compound_period
    total_principal = monthly_payment * period_months
    total_value = 0.0

    for k in range(period_months):
        # k번째 납입금이 만기까지 남은 개월 수
        remaining_months = period_months - k
        t = remaining_months / 12.0
        fv = monthly_payment * ((1 + r / n) ** (n * t))
        total_value += fv

    interest = total_value - total_principal
    tax = interest * (tax_rate / 100.0)
    net_interest = interest - tax
    after_tax_total = total_principal + net_interest
    return {
        "principal": total_principal,
        "interest_gross": interest,
        "tax": tax,
        "interest_net": net_interest,
        "total": after_tax_total,
    }


def calculate_deposit(deposit_row):
    """DB row(dict)로부터 자동 계산"""
    name = deposit_row.get("deposit_type", "예금")
    if name == "적금":
        return compound_savings(
            monthly_payment=deposit_row["principal"],
            annual_rate=deposit_row["interest_rate"],
            period_months=deposit_row["period_months"],
            compound_period=deposit_row.get("compound_period", 12),
            tax_rate=deposit_row.get("tax_rate", 15.4),
        )
    else:
        return compound_deposit(
            principal=deposit_row["principal"],
            annual_rate=deposit_row["interest_rate"],
            period_months=deposit_row["period_months"],
            compound_period=deposit_row.get("compound_period", 12),
            tax_rate=deposit_row.get("tax_rate", 15.4),
        )


def maturity_date(start_date_str, period_months):
    """시작일로부터 만기일 계산"""
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    # 단순한 월 더하기
    month = start.month - 1 + period_months
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, 28)  # 안전한 일자
    return datetime(year, month, day).strftime("%Y-%m-%d")


def fetch_stock_price(ticker):
    """
    yfinance를 사용하여 현재 주가를 가져옵니다.
    한국 주식은 ticker에 .KS (코스피) 또는 .KQ (코스닥)를 붙여야 합니다.
    예: 삼성전자 -> '005930.KS', 카카오 -> '035720.KS'
    실패 시 None을 반환합니다.
    """
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        # 가장 최신 종가를 조회
        hist = t.history(period="2d")
        if hist.empty:
            info = t.info
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            return float(price) if price else None
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"[fetch_stock_price] {ticker} 조회 실패: {e}")
        return None
