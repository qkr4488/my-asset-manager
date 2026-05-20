"""
finance.py - 금융 계산 + 주가/뉴스 조회
"""
from datetime import datetime, timedelta, date


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


def current_deposit_value(deposit_row, as_of=None):
    """
    시작일~오늘 현재까지 실제로 누적된 원금+이자 (세전).
    """
    as_of = as_of or date.today()
    if isinstance(as_of, datetime):
        as_of = as_of.date()
    start = datetime.strptime(deposit_row["start_date"], "%Y-%m-%d").date()

    period = int(deposit_row["period_months"])
    r = deposit_row["interest_rate"] / 100.0
    n = int(deposit_row.get("compound_period", 12) or 12)
    dtype = deposit_row.get("deposit_type", "예금")
    pay = float(deposit_row["principal"])

    if as_of < start:
        if dtype == "적금":
            principal_so_far = 0.0
            current_value = 0.0
        else:
            principal_so_far = pay
            current_value = pay
        return {
            "current_value": current_value,
            "principal_so_far": principal_so_far,
            "interest": 0.0,
            "elapsed_months": 0,
            "period_months": period,
            "is_matured": False,
            "progress_pct": 0.0,
        }

    elapsed = (as_of.year - start.year) * 12 + (as_of.month - start.month)
    if as_of.day < start.day:
        elapsed -= 1
    elapsed = max(0, elapsed)

    is_matured = elapsed >= period
    eff_months = min(elapsed, period)

    if dtype == "적금":
        if is_matured:
            total = 0.0
            for k in range(period):
                months_held = period - k
                t = months_held / 12.0
                total += pay * ((1 + r / n) ** (n * t))
            principal_so_far = pay * period
            current_value = total
        else:
            total = 0.0
            for k in range(eff_months):
                months_held = eff_months - k
                t = months_held / 12.0
                total += pay * ((1 + r / n) ** (n * t))
            principal_so_far = pay * eff_months
            current_value = total
    else:
        t = eff_months / 12.0
        current_value = pay * ((1 + r / n) ** (n * t))
        principal_so_far = pay

    return {
        "current_value": current_value,
        "principal_so_far": principal_so_far,
        "interest": current_value - principal_so_far,
        "elapsed_months": eff_months,
        "period_months": period,
        "is_matured": is_matured,
        "progress_pct": (eff_months / period * 100) if period else 0,
    }


def insurance_stats(ins_row, as_of=None):
    """
    보험 계약의 진행 상황 계산
    """
    as_of = as_of or date.today()
    if isinstance(as_of, datetime):
        as_of = as_of.date()
    start = datetime.strptime(ins_row["start_date"], "%Y-%m-%d").date()
    monthly = float(ins_row.get("monthly_premium") or 0)

    def months_between(a, b):
        m = (b.year - a.year) * 12 + (b.month - a.month)
        if b.day < a.day:
            m -= 1
        return max(0, m)

    if as_of < start:
        months_paid = 0
    else:
        months_paid = months_between(start, as_of)

    pay_end_str = ins_row.get("payment_end_date")
    if pay_end_str:
        pay_end = datetime.strptime(pay_end_str, "%Y-%m-%d").date()
        max_months = months_between(start, pay_end)
        months_paid = min(months_paid, max_months)
        payment_progress = (months_paid / max_months * 100) if max_months else 0
        payment_done = months_paid >= max_months
        payment_months_left = max(0, max_months - months_paid)
    else:
        payment_progress = None
        payment_done = False
        payment_months_left = None

    total_paid = months_paid * monthly

    maturity_str = ins_row.get("maturity_date")
    if maturity_str:
        maturity = datetime.strptime(maturity_str, "%Y-%m-%d").date()
        days_to_maturity = (maturity - as_of).days
        months_to_maturity = months_between(as_of, maturity) if maturity > as_of else 0
        is_expired = as_of > maturity
    else:
        days_to_maturity = None
        months_to_maturity = None
        is_expired = False

    return {
        "months_paid": months_paid,
        "total_paid": total_paid,
        "months_to_maturity": months_to_maturity,
        "days_to_maturity": days_to_maturity,
        "payment_progress": payment_progress,
        "payment_done": payment_done,
        "payment_months_left": payment_months_left,
        "is_expired": is_expired,
    }


def fetch_stock_quote(ticker):
    """
    개선된 주가 조회: 여러 경로를 시도하고 출처/통화까지 함께 반환.
    """
    try:
        import yfinance as yf
    except Exception as e:
        print(f"[fetch] yfinance 미설치: {e}")
        return None

    try:
        t = yf.Ticker(ticker)

        # 1) fast_info
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
    """yfinance Ticker.news로 종목 관련 뉴스 가져오기"""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        items = t.news or []
        result = []
        for it in items[:limit]:
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
