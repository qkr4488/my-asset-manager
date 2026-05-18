"""
finance.py - 금융 계산 + 주가/뉴스 조회
"""
from datetime import datetime, timedelta


def compound_deposit(principal, annual_rate, period_months,
                     compound_period=12, tax_rate=15.4):
    r = annual_rate / 100.0
    n = compound_period
    t = period_months / 12.0
    final = principal * ((1 + r / n) ** (n * t))
    interest = final - principal
    tax = interest * (tax_rate / 100.0)
    net_interest = interest - tax
    return {
        "principal": principal,
        "interest_gross": interest,
        "tax": tax,
        "interest_net": net_interest,
        "total": principal + net_interest,
    }


def compound_savings(monthly_payment, annual_rate, period_months,
                     compound_period=12, tax_rate=15.4):
    r = annual_rate / 100.0
    n = compound_period
    total_principal = monthly_payment * period_months
    total_value = 0.0
    for k in range(period_months):
        remaining_months = period_months - k
        t = remaining_months / 12.0
        fv = monthly_payment * ((1 + r / n) ** (n * t))
        total_value += fv
    interest = total_value - total_principal
    tax = interest * (tax_rate / 100.0)
    net_interest = interest - tax
    return {
        "principal": total_principal,
        "interest_gross": interest,
        "tax": tax,
        "interest_net": net_interest,
        "total": total_principal + net_interest,
    }


def calculate_deposit(deposit_row):
    if deposit_row.get("deposit_type", "예금") == "적금":
        return compound_savings(
            deposit_row["principal"],
            deposit_row["interest_rate"],
            deposit_row["period_months"],
            deposit_row.get("compound_period", 12),
            deposit_row.get("tax_rate", 15.4),
        )
    return compound_deposit(
        deposit_row["principal"],
        deposit_row["interest_rate"],
        deposit_row["period_months"],
        deposit_row.get("compound_period", 12),
        deposit_row.get("tax_rate", 15.4),
    )


def maturity_date(start_date_str, period_months):
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    month = start.month - 1 + period_months
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, 28)
    return datetime(year, month, day).strftime("%Y-%m-%d")


def fetch_stock_quote(ticker):
    """
    개선된 주가 조회: 여러 경로를 시도하고 출처/통화까지 함께 반환.
    반환: {'price': float, 'currency': str, 'source': str, 'name': str|None}
          실패 시 None
    """
    try:
        import yfinance as yf
    except Exception as e:
        print(f"[fetch] yfinance 미설치: {e}")
        return None

    try:
        t = yf.Ticker(ticker)

        # 1) fast_info (가장 빠르고 신뢰성 있음)
        try:
            fi = t.fast_info
            price = None
            for key in ("last_price", "lastPrice", "regular_market_price",
                        "regularMarketPrice"):
                try:
                    v = fi[key] if hasattr(fi, "__getitem__") else getattr(fi, key, None)
                    if v and v > 0:
                        price = float(v)
                        break
                except Exception:
                    pass
            currency = None
            for key in ("currency",):
                try:
                    v = fi[key] if hasattr(fi, "__getitem__") else getattr(fi, key, None)
                    if v:
                        currency = str(v)
                        break
                except Exception:
                    pass
            if price:
                return {
                    "price": price,
                    "currency": currency or _guess_currency(ticker),
                    "source": "fast_info",
                    "name": None,
                }
        except Exception:
            pass

        # 2) history
        try:
            hist = t.history(period="5d")
            if not hist.empty:
                price = float(hist["Close"].dropna().iloc[-1])
                if price > 0:
                    return {
                        "price": price,
                        "currency": _guess_currency(ticker),
                        "source": "history",
                        "name": None,
                    }
        except Exception:
            pass

        # 3) info
        try:
            info = t.info or {}
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if price:
                return {
                    "price": float(price),
                    "currency": info.get("currency") or _guess_currency(ticker),
                    "source": "info",
                    "name": info.get("shortName"),
                }
        except Exception:
            pass

        return None
    except Exception as e:
        print(f"[fetch_stock_quote] {ticker} 실패: {e}")
        return None


def _guess_currency(ticker):
    t = ticker.upper()
    if t.endswith(".KS") or t.endswith(".KQ"):
        return "KRW"
    if t.endswith(".T"):
        return "JPY"
    if t.endswith(".HK"):
        return "HKD"
    if t.endswith(".L"):
        return "GBP"
    return "USD"


def fetch_stock_news(ticker, limit=10):
    """
    yfinance Ticker.news로 종목 관련 뉴스 가져오기.
    반환: 리스트[{'title','publisher','link','time','ticker'}]
    """
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        items = t.news or []
        result = []
        for it in items[:limit]:
            # yfinance 신규 포맷은 'content' 안에 내용이 있고, 구형은 평탄
            content = it.get("content") or it
            title = content.get("title")
            if not title:
                continue
            pub = (content.get("provider") or {}).get("displayName") or content.get(
                "publisher", "")
            link = (content.get("canonicalUrl") or {}).get("url") or content.get(
                "link", "")
            ts = content.get("pubDate") or content.get("providerPublishTime")
            if isinstance(ts, (int, float)):
                ts = datetime.fromtimestamp(ts).isoformat(timespec="minutes")
            result.append({
                "title": title,
                "publisher": pub,
                "link": link,
                "time": ts or "",
                "ticker": ticker,
            })
        return result
    except Exception as e:
        print(f"[fetch_stock_news] {ticker} 실패: {e}")
        return []
