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


def fetch_stock_name(ticker):
    """
    티커 → 종목명 자동 조회.
    한국: '삼성전자', 미국: 'Apple Inc.' 등 yfinance가 제공하는 표시명.
    실패하면 None.
    """
    if not ticker:
        return None
    try:
        import yfinance as yf
    except Exception as e:
        print(f"[fetch_stock_name] yfinance 미설치: {e}")
        return None

    try:
        t = yf.Ticker(ticker)

        # 1) fast_info — 빠르고 가벼움
        try:
            fi = t.fast_info
            for key in ("longName", "shortName", "name"):
                try:
                    v = (fi[key] if hasattr(fi, "__getitem__")
                         else getattr(fi, key, None))
                    if v and isinstance(v, str) and v.strip():
                        return v.strip()
                except Exception:
                    pass
        except Exception:
            pass

        # 2) info — 가장 풍부 (longName / shortName)
        try:
            info = t.info or {}
            for key in ("longName", "shortName", "displayName"):
                v = info.get(key)
                if v and isinstance(v, str) and v.strip():
                    return v.strip()
        except Exception:
            pass

        # 3) get_info() (구버전 호환)
        try:
            info = t.get_info() if hasattr(t, "get_info") else {}
            for key in ("longName", "shortName"):
                v = (info or {}).get(key)
                if v:
                    return str(v).strip()
        except Exception:
            pass

        return None
    except Exception as e:
        print(f"[fetch_stock_name] {ticker} 실패: {e}")
        return None


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


def analyze_stock(ticker, period="1y"):
    """
    yfinance 가격 이력 기반 기술적 분석.
    이동평균, RSI, 볼린저밴드, 피보나치 되돌림으로
    지지선/저항선/추천 매매구간/추세를 자동 산출.

    period: '3mo' | '6mo' | '1y' | '2y'
    반환: dict 또는 None (실패/데이터 부족 시)
    """
    if not ticker:
        return None
    try:
        import yfinance as yf
        import pandas as pd
        import math
    except Exception as e:
        print(f"[analyze_stock] 라이브러리 미설치: {e}")
        return None

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        if hist.empty or len(hist) < 20:
            return None

        close = hist["Close"].dropna()
        high = hist["High"].dropna()
        low = hist["Low"].dropna()
        if len(close) < 20:
            return None

        def safe_last(s):
            try:
                v = s.iloc[-1]
                return float(v) if not pd.isna(v) else None
            except Exception:
                return None

        current = safe_last(close)
        if not current or current <= 0:
            return None

        # ===== 이동평균선 =====
        ma5 = safe_last(close.rolling(5).mean())
        ma20 = safe_last(close.rolling(20).mean())
        ma60 = safe_last(close.rolling(60).mean()) if len(close) >= 60 else None
        ma120 = safe_last(close.rolling(120).mean()) if len(close) >= 120 else None

        # ===== 기간별 고가/저가 =====
        n20 = min(20, len(high))
        n60 = min(60, len(high))
        high_20 = float(high.tail(n20).max())
        low_20 = float(low.tail(n20).min())
        high_60 = float(high.tail(n60).max())
        low_60 = float(low.tail(n60).min())
        high_52w = float(high.max())
        low_52w = float(low.min())

        # ===== RSI(14) =====
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        last_gain = safe_last(gain) or 0.0
        last_loss = safe_last(loss) or 0.0
        if last_loss == 0:
            rsi = 100.0 if last_gain > 0 else 50.0
        else:
            rs = last_gain / last_loss
            rsi = 100.0 - 100.0 / (1.0 + rs)

        # ===== 볼린저밴드 (MA20 ± 2σ) =====
        std20 = safe_last(close.rolling(20).std()) or 0.0
        bb_upper = (ma20 + 2.0 * std20) if ma20 else None
        bb_lower = (ma20 - 2.0 * std20) if ma20 else None
        if bb_upper and bb_lower and bb_upper > bb_lower:
            bb_pos = (current - bb_lower) / (bb_upper - bb_lower)
            bb_pos = max(0.0, min(1.0, bb_pos))
        else:
            bb_pos = 0.5

        # ===== 피보나치 되돌림 (최근 60일 swing) =====
        swing_high = high_60
        swing_low = low_60
        diff = swing_high - swing_low
        if diff <= 0:
            diff = max(swing_high * 0.01, 1.0)
        fib_236 = swing_high - diff * 0.236
        fib_382 = swing_high - diff * 0.382
        fib_500 = swing_high - diff * 0.500
        fib_618 = swing_high - diff * 0.618

        # ===== 지지선 / 저항선 =====
        # 지지선 후보: 현재가 아래쪽 가격들
        sup_candidates = []
        for v in (low_20, ma20, ma60, fib_500, fib_618, low_60, bb_lower):
            if v and not math.isnan(v) and v < current and v > 0:
                sup_candidates.append(v)
        if sup_candidates:
            support_near = max(sup_candidates)  # 현재가에 가장 가까운 지지선
            support_far = min(sup_candidates)   # 더 아래 지지선
        else:
            support_near = current * 0.95
            support_far = current * 0.90

        # 저항선 후보: 현재가 위쪽 가격들
        res_candidates = []
        for v in (high_20, high_60, fib_236, fib_382, bb_upper, high_52w):
            if v and not math.isnan(v) and v > current:
                res_candidates.append(v)
        if res_candidates:
            resistance_near = min(res_candidates)
            resistance_far = max(res_candidates)
        else:
            resistance_near = current * 1.05
            resistance_far = current * 1.10

        # ===== 추천 매매 구간 =====
        # 매수 구간: support_far ~ support_near (가까운 지지선에서 1차, 약한 지지선에서 2차)
        buy_zone_low = support_far
        buy_zone_high = support_near
        sell_zone_low = resistance_near
        sell_zone_high = resistance_far
        stop_loss = support_far * 0.97  # 약한 지지선보다 3% 아래

        # ===== 추세 판단 =====
        if ma60 and ma20 and current > ma20 > ma60:
            trend = "📈 상승 추세"
            trend_color = "accent"
        elif ma60 and ma20 and current < ma20 < ma60:
            trend = "📉 하락 추세"
            trend_color = "danger"
        elif ma20 and current > ma20:
            trend = "↗ 단기 상승"
            trend_color = "accent"
        elif ma20 and current < ma20:
            trend = "↘ 단기 하락"
            trend_color = "danger"
        else:
            trend = "→ 횡보"
            trend_color = "muted"

        # ===== 종합 신호 =====
        signals = []
        if rsi < 30:
            signals.append(("🟢", f"RSI {rsi:.1f} — 과매도 구간, 단기 반등 가능성 ↑"))
        elif rsi > 70:
            signals.append(("🔴", f"RSI {rsi:.1f} — 과매수 구간, 단기 조정 위험 ↑"))
        else:
            signals.append(("⚪", f"RSI {rsi:.1f} — 중립 구간"))

        if bb_pos < 0.2:
            signals.append(("🟢", f"볼린저밴드 하단 근접 ({bb_pos * 100:.0f}%) "
                                  f"— 평균 회귀 매수 시점 가능"))
        elif bb_pos > 0.8:
            signals.append(("🔴", f"볼린저밴드 상단 근접 ({bb_pos * 100:.0f}%) "
                                  f"— 평균 회귀 조정 가능"))
        else:
            signals.append(("⚪", f"볼린저밴드 중앙 부근 ({bb_pos * 100:.0f}%)"))

        if ma20:
            if current > ma20:
                signals.append(("🟢", f"20일선({_fmt_num(ma20)}) 위 — 단기 강세"))
            else:
                signals.append(("🔴", f"20일선({_fmt_num(ma20)}) 아래 — 단기 약세"))
        if ma60:
            if current > ma60:
                signals.append(("🟢", f"60일선({_fmt_num(ma60)}) 위 — 중기 강세"))
            else:
                signals.append(("🔴", f"60일선({_fmt_num(ma60)}) 아래 — 중기 약세"))

        # 52주 위치
        rng = high_52w - low_52w
        if rng > 0:
            pos_52w = (current - low_52w) / rng * 100
            if pos_52w < 25:
                signals.append(("🟢", f"52주 저점 부근 (저점 +{pos_52w:.0f}%) "
                                      f"— 저가 매수 관점 검토"))
            elif pos_52w > 75:
                signals.append(("🔴", f"52주 고점 부근 (저점 +{pos_52w:.0f}%) "
                                      f"— 신규 진입 부담"))

        # ===== 스코어로 추천 코멘트 (신중·실용형) =====
        score = 0.0
        if rsi < 30:
            score += 2
        elif rsi < 40:
            score += 1
        elif rsi > 70:
            score -= 2
        elif rsi > 60:
            score -= 1

        if bb_pos < 0.2:
            score += 1.5
        elif bb_pos < 0.35:
            score += 0.5
        elif bb_pos > 0.8:
            score -= 1.5
        elif bb_pos > 0.65:
            score -= 0.5

        if ma20:
            score += 0.5 if current > ma20 else -0.5
        if ma60:
            score += 0.5 if current > ma60 else -0.5

        if rng > 0:
            pos_52w = (current - low_52w) / rng
            if pos_52w < 0.25:
                score += 1
            elif pos_52w > 0.85:
                score -= 1

        # 신중·실용형 코멘트
        if score >= 2.5:
            verdict = "🟢 매수 관심 구간"
            verdict_detail = (
                "여러 지표가 매수에 우호적입니다. 추천 매수가 구간에서 "
                "분할매수(1차 30% / 2차 30% / 3차 40%)를 고려해보세요. "
                "단, 손절선 아래로 빠지면 손실 확정 후 재진입 검토."
            )
            verdict_kind = "buy"
        elif score >= 1:
            verdict = "🟡 분할 매수 / 관심 권장"
            verdict_detail = (
                "긍정 신호가 우세하지만 결정적이지는 않습니다. "
                "추천 매수가 구간(지지선)에 가까워질 때 소량 분할매수 고려. "
                "결과에 베팅하지 말고 평균단가를 낮추는 전략."
            )
            verdict_kind = "buy_soft"
        elif score >= -1:
            verdict = "🟡 관망 권장"
            verdict_detail = (
                "신호가 혼재되어 있습니다. 추세 명확화 전까지 "
                "신규 진입은 보류하고, 지지선 접근/저항선 돌파 신호 확인 후 결정."
            )
            verdict_kind = "watch"
        elif score >= -2.5:
            verdict = "🟠 진입 자제 / 보유분 점검"
            verdict_detail = (
                "단기 조정 신호가 우세합니다. 신규 매수보다는 "
                "보유분의 매도 추천 구간 도달 여부 점검을 권장."
            )
            verdict_kind = "watch_neg"
        else:
            verdict = "🔴 매도 관심 / 진입 자제"
            verdict_detail = (
                "다수 지표가 과열·하락 신호를 보입니다. 신규 진입 부담이 크고, "
                "보유분은 매도 추천 구간 도달 시 일부 차익실현 검토."
            )
            verdict_kind = "sell"

        # ===== 단기 모멘텀 예측 (참고용) =====
        recent_ret = close.pct_change().tail(20).mean()
        if recent_ret is not None and not pd.isna(recent_ret):
            forecast_20d = current * (1.0 + float(recent_ret) * 20)
        else:
            forecast_20d = current

        # ===== 미니 차트용: 최근 60일 종가 + 날짜 =====
        recent = close.tail(60)
        recent_closes = [float(v) for v in recent.values]
        try:
            recent_dates = [d.strftime("%Y-%m-%d") for d in recent.index]
        except Exception:
            recent_dates = []

        # 통화 추정
        currency = _guess_currency(ticker)

        return {
            "ticker": ticker.upper(),
            "currency": currency,
            "period": period,
            "current": current,
            "ma5": ma5, "ma20": ma20, "ma60": ma60, "ma120": ma120,
            "high_20": high_20, "low_20": low_20,
            "high_60": high_60, "low_60": low_60,
            "high_52w": high_52w, "low_52w": low_52w,
            "rsi": rsi,
            "bb_upper": bb_upper, "bb_lower": bb_lower, "bb_pos": bb_pos,
            "fib_236": fib_236, "fib_382": fib_382,
            "fib_500": fib_500, "fib_618": fib_618,
            "support_near": support_near,
            "support_far": support_far,
            "resistance_near": resistance_near,
            "resistance_far": resistance_far,
            "buy_zone_low": buy_zone_low,
            "buy_zone_high": buy_zone_high,
            "sell_zone_low": sell_zone_low,
            "sell_zone_high": sell_zone_high,
            "stop_loss": stop_loss,
            "trend": trend,
            "trend_color": trend_color,
            "signals": signals,
            "verdict": verdict,
            "verdict_detail": verdict_detail,
            "verdict_kind": verdict_kind,
            "score": round(score, 2),
            "forecast_20d": forecast_20d,
            "recent_closes": recent_closes,
            "recent_dates": recent_dates,
            "data_points": len(close),
        }
    except Exception as e:
        print(f"[analyze_stock] {ticker} 실패: {e}")
        return None


def _fmt_num(n):
    """내부용 - 종목명 코멘트에 들어가는 숫자 포맷"""
    try:
        if abs(n) >= 1000:
            return f"{n:,.0f}"
        return f"{n:,.2f}"
    except Exception:
        return str(n)
