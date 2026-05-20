"""
app.py - 내 자산 관리자 v2
- 가계부, 적금/예금 복리, 주식, 주식 매매손익, 기타 자산, 갓생살기(습관+목표+To-Do), 뉴스
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import threading
import webbrowser
import random

from database import Database
from finance import (
    compound_deposit, compound_savings, calculate_deposit,
    maturity_date, fetch_stock_quote, fetch_stock_news,
    current_deposit_value, insurance_stats,
)

# ==================== 색상/테마 ====================
BG = "#f4f6fb"
CARD_BG = "#ffffff"
PRIMARY = "#2c5fb3"
ACCENT = "#5cb85c"
DANGER = "#d9534f"
WARN = "#f0ad4e"
FG = "#1a2540"
MUTED = "#7a8aa3"
SOFT = "#eef2f9"

CATEGORY_COLORS = {
    "건강": "#5cb85c", "재정": "#f0ad4e", "학습": "#4a90e2",
    "커리어": "#9b59b6", "관계": "#e67e22", "취미": "#1abc9c",
    "기타": "#7a8aa3",
}

QUOTES = [
    "작은 진전도 진전이다. 매일 한 걸음씩.",
    "어제의 나보다 오늘 더 나은 내가 되자.",
    "운이 좋아지는 가장 확실한 방법은, 매일 같은 자리에 있는 것.",
    "성공은 일상의 작은 노력이 쌓인 결과다.",
    "할 일을 미루면 미래의 내가 갚는다.",
    "동기는 잠시지만, 습관은 영원하다.",
    "1%씩 매일 좋아진다면, 1년 후 37배 성장한다.",
    "지금 시작하기에 가장 좋은 시간은 오늘이다.",
    "완벽보다 꾸준함이 이긴다.",
    "오늘 흘린 땀은 내일의 자유다.",
]


def won(n):
    try:
        return f"{n:,.0f}원"
    except Exception:
        return str(n)


def money(n, currency="KRW"):
    try:
        if currency == "KRW":
            return f"{n:,.0f}원"
        if currency == "USD":
            return f"${n:,.2f}"
        if currency == "JPY":
            return f"¥{n:,.0f}"
        return f"{n:,.2f} {currency}"
    except Exception:
        return str(n)


class AssetManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("내 자산 관리자 v2")
        self.geometry("1200x780")
        self.configure(bg=BG)
        self.minsize(1000, 680)

        self.db = Database()
        self.today_quote = random.choice(QUOTES)

        self._setup_style()
        self._build_ui()
        self.refresh_all()

    # ============ 스타일 ============
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9),
                        font=("Malgun Gothic", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", PRIMARY)],
                  foreground=[("selected", "white")])
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("TLabel", background=BG, foreground=FG,
                        font=("Malgun Gothic", 10))
        style.configure("Header.TLabel", font=("Malgun Gothic", 16, "bold"),
                        foreground=PRIMARY, background=BG)
        style.configure("Sub.TLabel", font=("Malgun Gothic", 11, "bold"),
                        foreground=FG, background=BG)
        style.configure("TButton", font=("Malgun Gothic", 10), padding=6)
        style.configure("Primary.TButton", padding=8)
        style.map("Primary.TButton",
                  background=[("active", "#214f96")])
        style.configure("Treeview", font=("Malgun Gothic", 10), rowheight=26)
        style.configure("Treeview.Heading", font=("Malgun Gothic", 10, "bold"))
        style.configure("Habit.Horizontal.TProgressbar",
                        troughcolor=SOFT, background=ACCENT)
        style.configure("Goal.Horizontal.TProgressbar",
                        troughcolor=SOFT, background=PRIMARY)

    # ============ UI ============
    def _build_ui(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=20, pady=(14, 4))
        tk.Label(top, text="💰 내 자산 관리자", bg=BG, fg=PRIMARY,
                 font=("Malgun Gothic", 18, "bold")).pack(side="left")
        self.summary_label = tk.Label(top, text="", bg=BG, fg=MUTED,
                                      font=("Malgun Gothic", 11))
        self.summary_label.pack(side="right")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=20, pady=8)

        self.tab_dashboard = ttk.Frame(self.nb)
        self.tab_ledger = ttk.Frame(self.nb)
        self.tab_deposit = ttk.Frame(self.nb)
        self.tab_stock = ttk.Frame(self.nb)
        self.tab_trade = ttk.Frame(self.nb)
        self.tab_asset = ttk.Frame(self.nb)
        self.tab_insurance = ttk.Frame(self.nb)
        self.tab_godlife = ttk.Frame(self.nb)
        self.tab_news = ttk.Frame(self.nb)

        self.nb.add(self.tab_dashboard, text="📊 대시보드")
        self.nb.add(self.tab_ledger, text="💳 가계부")
        self.nb.add(self.tab_deposit, text="🏦 적금/예금")
        self.nb.add(self.tab_stock, text="📈 주식/ETF")
        self.nb.add(self.tab_trade, text="💱 매매손익")
        self.nb.add(self.tab_asset, text="🏠 기타 자산")
        self.nb.add(self.tab_insurance, text="🛡 보험")
        self.nb.add(self.tab_godlife, text="✨ 갓생살기")
        self.nb.add(self.tab_news, text="📰 뉴스")

        self._build_dashboard()
        self._build_ledger()
        self._build_deposit()
        self._build_stock()
        self._build_trade()
        self._build_asset()
        self._build_insurance()
        self._build_godlife()
        self._build_news()

    # ==================== 대시보드 ====================
    def _build_dashboard(self):
        frame = self.tab_dashboard
        ttk.Label(frame, text="자산 현황 요약",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(20, 6))

        # 명언
        quote = tk.Label(frame, text=f"💬  {self.today_quote}",
                         bg=BG, fg=MUTED, font=("Malgun Gothic", 11, "italic"))
        quote.pack(anchor="w", padx=20, pady=(0, 10))

        cards = tk.Frame(frame, bg=BG)
        cards.pack(fill="x", padx=20, pady=4)
        self.card_total = self._make_card(cards, "총 자산", "0원", PRIMARY)
        self.card_total.grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self.card_cash = self._make_card(cards, "현금/기타", "0원", "#4a90e2")
        self.card_cash.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self.card_deposit = self._make_card(cards, "적금/예금 (현재가치)", "0원", ACCENT)
        self.card_deposit.grid(row=0, column=2, padx=6, pady=6, sticky="ew")
        self.card_stock = self._make_card(cards, "주식 평가액", "0원", "#e67e22")
        self.card_stock.grid(row=0, column=3, padx=6, pady=6, sticky="ew")
        for c in range(4):
            cards.columnconfigure(c, weight=1)

        # 2행 카드
        cards2 = tk.Frame(frame, bg=BG)
        cards2.pack(fill="x", padx=20, pady=4)
        self.card_stock_pnl = self._make_card(cards2, "주식 평가손익", "0원", "#9b59b6")
        self.card_stock_pnl.grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self.card_realized = self._make_card(cards2, "올해 실현손익", "0원", "#16a085")
        self.card_realized.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self.card_month = self._make_card(cards2, "이번 달 잔액", "0원", PRIMARY)
        self.card_month.grid(row=0, column=2, padx=6, pady=6, sticky="ew")
        self.card_points = self._make_card(cards2, "갓생 포인트", "0 pt", "#e91e63")
        self.card_points.grid(row=0, column=3, padx=6, pady=6, sticky="ew")
        for c in range(4):
            cards2.columnconfigure(c, weight=1)

        # 이번 달 수입/지출
        ttk.Label(frame, text="이번 달 수입/지출",
                  style="Sub.TLabel").pack(anchor="w", padx=20, pady=(16, 4))
        mb = tk.Frame(frame, bg=CARD_BG, relief="flat")
        mb.pack(fill="x", padx=20, pady=4)
        self.lbl_income = tk.Label(mb, text="수입: 0원", bg=CARD_BG, fg=ACCENT,
                                   font=("Malgun Gothic", 12, "bold"),
                                   padx=20, pady=12)
        self.lbl_income.pack(side="left")
        self.lbl_expense = tk.Label(mb, text="지출: 0원", bg=CARD_BG, fg=DANGER,
                                    font=("Malgun Gothic", 12, "bold"),
                                    padx=20, pady=12)
        self.lbl_expense.pack(side="left")
        self.lbl_balance = tk.Label(mb, text="잔액: 0원", bg=CARD_BG, fg=PRIMARY,
                                    font=("Malgun Gothic", 12, "bold"),
                                    padx=20, pady=12)
        self.lbl_balance.pack(side="left")

        # 오늘/내일
        ttk.Label(frame, text="오늘 / 내일 할 일",
                  style="Sub.TLabel").pack(anchor="w", padx=20, pady=(14, 4))
        sb = tk.Frame(frame, bg=CARD_BG)
        sb.pack(fill="both", expand=True, padx=20, pady=4)
        self.dash_schedule = tk.Text(sb, height=8, font=("Malgun Gothic", 10),
                                     bg=CARD_BG, fg=FG, relief="flat",
                                     padx=14, pady=10)
        self.dash_schedule.pack(fill="both", expand=True)
        self.dash_schedule.configure(state="disabled")

    def _make_card(self, parent, title, value, color):
        f = tk.Frame(parent, bg=CARD_BG, bd=0, highlightthickness=0)
        bar = tk.Frame(f, bg=color, height=4)
        bar.pack(fill="x")
        inner = tk.Frame(f, bg=CARD_BG)
        inner.pack(fill="both", expand=True, padx=14, pady=12)
        tk.Label(inner, text=title, bg=CARD_BG, fg=MUTED,
                 font=("Malgun Gothic", 10)).pack(anchor="w")
        val = tk.Label(inner, text=value, bg=CARD_BG, fg=FG,
                       font=("Malgun Gothic", 15, "bold"))
        val.pack(anchor="w", pady=(4, 0))
        f.value_label = val
        return f

    def refresh_dashboard(self):
        assets = self.db.get_assets()
        cash_total = sum(a["value"] for a in assets)

        deposits = self.db.get_deposits()
        # 현재 진행 시점까지 누적된 가치 (세전)
        deposit_total = sum(current_deposit_value(d)["current_value"]
                            for d in deposits)

        stocks = self.db.get_stocks()
        stock_value = 0
        stock_cost = 0
        for s in stocks:
            cur = s["current_price"] if s["current_price"] else s["avg_price"]
            stock_value += cur * s["quantity"]
            stock_cost += s["avg_price"] * s["quantity"]
        stock_pnl = stock_value - stock_cost

        total = cash_total + deposit_total + stock_value
        self.card_total.value_label.config(text=won(total))
        self.card_cash.value_label.config(text=won(cash_total))
        self.card_deposit.value_label.config(text=won(deposit_total))
        self.card_stock.value_label.config(text=won(stock_value))

        pnl_color = ACCENT if stock_pnl >= 0 else DANGER
        self.card_stock_pnl.value_label.config(
            text=f"{'+' if stock_pnl >= 0 else ''}{won(stock_pnl)}",
            fg=pnl_color)

        year = datetime.now().year
        realized = self.db.get_trade_summary(year=year)
        self.card_realized.value_label.config(
            text=f"{'+' if realized >= 0 else ''}{won(realized)}",
            fg=ACCENT if realized >= 0 else DANGER)

        now = datetime.now()
        s = self.db.get_monthly_summary(now.year, now.month)
        bal = s["income"] - s["expense"]
        self.card_month.value_label.config(
            text=f"{'+' if bal >= 0 else ''}{won(bal)}",
            fg=ACCENT if bal >= 0 else DANGER)
        self.lbl_income.config(text=f"수입: {won(s['income'])}")
        self.lbl_expense.config(text=f"지출: {won(s['expense'])}")
        self.lbl_balance.config(text=f"잔액: {won(bal)}")

        pts = self.db.get_total_points()
        today_pts = self.db.get_today_points()
        self.card_points.value_label.config(
            text=f"{pts:,} pt  (오늘 +{today_pts})")

        today = date.today().strftime("%Y-%m-%d")
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        today_sch = self.db.get_schedules(today)
        tomorrow_sch = self.db.get_schedules(tomorrow)

        self.dash_schedule.configure(state="normal")
        self.dash_schedule.delete("1.0", "end")
        self.dash_schedule.insert("end", f"[오늘 {today}]\n", "h")
        if today_sch:
            for sch in today_sch:
                mark = "✅" if sch["done"] else "⬜"
                self.dash_schedule.insert(
                    "end", f"  {mark} {sch['title']}  ({sch['priority']})\n")
        else:
            self.dash_schedule.insert("end", "  (등록된 일정 없음)\n", "muted")
        self.dash_schedule.insert("end", f"\n[내일 {tomorrow}]\n", "h")
        if tomorrow_sch:
            for sch in tomorrow_sch:
                mark = "✅" if sch["done"] else "⬜"
                self.dash_schedule.insert(
                    "end", f"  {mark} {sch['title']}  ({sch['priority']})\n")
        else:
            self.dash_schedule.insert("end", "  (등록된 일정 없음)\n", "muted")
        self.dash_schedule.tag_config("h", font=("Malgun Gothic", 11, "bold"),
                                     foreground=PRIMARY)
        self.dash_schedule.tag_config("muted", foreground=MUTED)
        self.dash_schedule.configure(state="disabled")

        self.summary_label.config(text=f"총 자산: {won(total)}")

    # ==================== 가계부 ====================
    def _build_ledger(self):
        frame = self.tab_ledger
        ttk.Label(frame, text="가계부 - 수입/지출 관리",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(18, 8))

        form = tk.LabelFrame(frame, text="새 거래 추가", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=10, bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="날짜", bg=BG).grid(row=0, column=0, sticky="w", padx=4)
        self.tx_date = tk.Entry(form, width=12)
        self.tx_date.insert(0, date.today().strftime("%Y-%m-%d"))
        self.tx_date.grid(row=0, column=1, padx=4)
        tk.Label(form, text="구분", bg=BG).grid(row=0, column=2, sticky="w", padx=4)
        self.tx_type = ttk.Combobox(form, values=["income", "expense"],
                                    width=10, state="readonly")
        self.tx_type.set("expense")
        self.tx_type.grid(row=0, column=3, padx=4)
        tk.Label(form, text="카테고리", bg=BG).grid(row=0, column=4, sticky="w", padx=4)
        self.tx_cat = ttk.Combobox(form, values=[
            "식비", "교통", "주거", "통신", "쇼핑", "의료", "교육",
            "여가", "급여", "용돈", "투자수익", "기타"
        ], width=10)
        self.tx_cat.set("식비")
        self.tx_cat.grid(row=0, column=5, padx=4)
        tk.Label(form, text="금액", bg=BG).grid(row=0, column=6, sticky="w", padx=4)
        self.tx_amount = tk.Entry(form, width=12)
        self.tx_amount.grid(row=0, column=7, padx=4)

        # 결제수단 + 할부
        tk.Label(form, text="결제수단", bg=BG).grid(
            row=1, column=0, sticky="w", padx=4, pady=(8, 0))
        self.tx_method = ttk.Combobox(
            form, values=["현금", "체크카드", "신용카드", "계좌이체",
                          "간편결제", "기타"],
            width=10, state="readonly")
        self.tx_method.set("현금")
        self.tx_method.grid(row=1, column=1, padx=4, pady=(8, 0), sticky="w")
        self.tx_method.bind("<<ComboboxSelected>>", self._on_method_change)

        tk.Label(form, text="할부", bg=BG).grid(
            row=1, column=2, sticky="w", padx=4, pady=(8, 0))
        self.tx_install = ttk.Combobox(
            form,
            values=["일시불", "2개월", "3개월", "4개월", "5개월", "6개월",
                    "7개월", "8개월", "9개월", "10개월", "12개월",
                    "18개월", "24개월", "36개월"],
            width=8, state="disabled")
        self.tx_install.set("일시불")
        self.tx_install.grid(row=1, column=3, padx=4, pady=(8, 0), sticky="w")

        tk.Label(form, text="메모", bg=BG).grid(
            row=2, column=0, sticky="w", padx=4, pady=(8, 0))
        self.tx_memo = tk.Entry(form, width=60)
        self.tx_memo.grid(row=2, column=1, columnspan=5, padx=4,
                          pady=(8, 0), sticky="we")
        ttk.Button(form, text="추가", command=self.add_transaction).grid(
            row=2, column=6, columnspan=2, padx=4, pady=(8, 0), sticky="we")

        # 기간 필터
        filt = tk.LabelFrame(frame, text="📅 기간 필터", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=8, bd=1, relief="solid")
        filt.pack(fill="x", padx=20, pady=(8, 4))

        self.tx_period = tk.StringVar(value="이번 달")
        for label in ("이번 주", "이번 달", "지난 달", "3개월", "올해",
                      "전체", "사용자 지정"):
            tk.Radiobutton(
                filt, text=label, variable=self.tx_period, value=label,
                bg=BG, fg=FG, font=("Malgun Gothic", 9),
                selectcolor=CARD_BG, activebackground=SOFT,
                command=self.refresh_ledger
            ).pack(side="left", padx=4)

        custom_frame = tk.Frame(filt, bg=BG)
        custom_frame.pack(side="left", padx=(14, 0))
        tk.Label(custom_frame, text="시작:", bg=BG,
                 font=("Malgun Gothic", 9)).pack(side="left")
        self.tx_from = tk.Entry(custom_frame, width=11,
                                 font=("Malgun Gothic", 9))
        self.tx_from.insert(0, date.today().replace(day=1).strftime("%Y-%m-%d"))
        self.tx_from.pack(side="left", padx=2)
        tk.Label(custom_frame, text="~ 종료:", bg=BG,
                 font=("Malgun Gothic", 9)).pack(side="left")
        self.tx_to = tk.Entry(custom_frame, width=11,
                               font=("Malgun Gothic", 9))
        self.tx_to.insert(0, date.today().strftime("%Y-%m-%d"))
        self.tx_to.pack(side="left", padx=2)
        ttk.Button(custom_frame, text="적용", width=6,
                   command=lambda: (self.tx_period.set("사용자 지정"),
                                    self.refresh_ledger())
                   ).pack(side="left", padx=4)

        # 기간 요약
        self.tx_summary = tk.Label(frame, text="", bg=CARD_BG, fg=FG,
                                    font=("Malgun Gothic", 11, "bold"),
                                    pady=12, padx=16, anchor="w")
        self.tx_summary.pack(fill="x", padx=20, pady=(0, 4))

        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=4)
        cols = ("id", "date", "type", "category", "amount",
                "method", "install", "memo")
        headers = ("ID", "날짜", "구분", "카테고리", "금액",
                   "결제수단", "할부", "메모")
        widths = (40, 95, 60, 90, 110, 90, 70, 320)
        self.tx_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.tx_tree.heading(c, text=h)
            self.tx_tree.column(c, width=w, anchor="w")
        self.tx_tree.tag_configure("inc", foreground=ACCENT)
        self.tx_tree.tag_configure("exp", foreground=DANGER)
        self.tx_tree.tag_configure("install", background="#fff8e1")
        self.tx_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.tx_tree.yview)
        sb.pack(side="right", fill="y")
        self.tx_tree.configure(yscrollcommand=sb.set)
        btn_row = tk.Frame(frame, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=(4, 12))
        ttk.Button(btn_row, text="선택 삭제",
                   command=self.delete_transaction).pack(side="right")
        ttk.Button(btn_row, text="이 할부 전체 삭제",
                   command=self.delete_installment_group).pack(side="right", padx=6)

    def _on_method_change(self, _event=None):
        """결제수단이 신용카드일 때만 할부 콤보 활성화"""
        if self.tx_method.get() == "신용카드":
            self.tx_install.configure(state="readonly")
        else:
            self.tx_install.set("일시불")
            self.tx_install.configure(state="disabled")

    def add_transaction(self):
        try:
            amount = float(self.tx_amount.get().replace(",", ""))
            method = self.tx_method.get()
            # 할부 개월 파싱
            install_months = 1
            if method == "신용카드":
                val = self.tx_install.get()
                if val != "일시불":
                    install_months = int(val.replace("개월", ""))
            self.db.add_transaction(
                self.tx_date.get(), self.tx_type.get(),
                self.tx_cat.get(), amount, self.tx_memo.get(),
                payment_method=method, installment_months=install_months
            )
            self.tx_amount.delete(0, "end")
            self.tx_memo.delete(0, "end")
            self.tx_install.set("일시불")
            self.refresh_ledger()
            self.refresh_dashboard()
        except ValueError:
            messagebox.showerror("입력 오류", "금액은 숫자로 입력해주세요.")

    def delete_transaction(self):
        sel = self.tx_tree.selection()
        if not sel:
            return
        tid = self.tx_tree.item(sel[0])["values"][0]
        self.db.delete_transaction(tid)
        self.refresh_ledger()
        self.refresh_dashboard()

    def delete_installment_group(self):
        """선택한 거래가 할부면 같은 할부 묶음 전체 삭제"""
        sel = self.tx_tree.selection()
        if not sel:
            return
        tid = self.tx_tree.item(sel[0])["values"][0]
        # 해당 거래의 group_id 조회
        group_id = None
        for t in self.db.get_transactions():
            if t["id"] == tid:
                group_id = t.get("installment_group_id")
                break
        if not group_id:
            messagebox.showinfo("안내", "선택한 항목은 할부 거래가 아닙니다. "
                                       "'선택 삭제'를 사용하세요.")
            return
        if messagebox.askyesno("할부 전체 삭제",
                               "이 할부에 속한 모든 회차를 삭제할까요?"):
            self.db.delete_installment_group(group_id)
            self.refresh_ledger()
            self.refresh_dashboard()

    def _resolve_ledger_period(self):
        """선택된 기간 필터를 (start_str, end_str, label) 로 변환"""
        today = date.today()
        period = self.tx_period.get() if hasattr(self, "tx_period") else "이번 달"

        if period == "이번 주":
            # 월요일 시작
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
        elif period == "이번 달":
            start = today.replace(day=1)
            # 다음 달 1일 - 1일
            if today.month == 12:
                end = date(today.year, 12, 31)
            else:
                end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        elif period == "지난 달":
            first_this = today.replace(day=1)
            end = first_this - timedelta(days=1)
            start = end.replace(day=1)
        elif period == "3개월":
            # 오늘 포함 최근 90일
            start = today - timedelta(days=89)
            end = today
        elif period == "올해":
            start = date(today.year, 1, 1)
            end = date(today.year, 12, 31)
        elif period == "사용자 지정":
            try:
                start = datetime.strptime(self.tx_from.get(), "%Y-%m-%d").date()
                end = datetime.strptime(self.tx_to.get(), "%Y-%m-%d").date()
            except Exception:
                start = today.replace(day=1)
                end = today
        else:  # 전체
            return None, None, "전체 기간"
        return (start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d"),
                f"{period}  ({start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')})")

    def refresh_ledger(self):
        for i in self.tx_tree.get_children():
            self.tx_tree.delete(i)
        start_str, end_str, label = self._resolve_ledger_period()
        txs = self.db.get_transactions(start_date=start_str, end_date=end_str)

        total_income = 0
        total_expense = 0
        for r in txs:
            kind = "수입" if r["type"] == "income" else "지출"
            sign = "+" if r["type"] == "income" else "-"
            if r["type"] == "income":
                total_income += r["amount"]
            else:
                total_expense += r["amount"]
            # 할부 표시
            inst_months = r.get("installment_months") or 1
            inst_idx = r.get("installment_index") or 1
            if inst_months and inst_months > 1:
                install_disp = f"{inst_idx}/{inst_months}"
                tags = ("exp", "install") if r["type"] == "expense" else ("inc", "install")
            else:
                install_disp = "일시불"
                tags = ("inc",) if r["type"] == "income" else ("exp",)
            self.tx_tree.insert("", "end", tags=tags, values=(
                r["id"], r["date"], kind, r["category"],
                f"{sign}{won(r['amount'])}",
                r.get("payment_method") or "현금",
                install_disp,
                r["memo"] or ""
            ))

        balance = total_income - total_expense
        bal_color = ACCENT if balance >= 0 else DANGER
        sign = "+" if balance >= 0 else ""
        self.tx_summary.config(
            text=f"📅 {label}    "
                 f"💰 수입 {won(total_income)}    "
                 f"💸 지출 {won(total_expense)}    "
                 f"📊 잔액 {sign}{won(balance)}    "
                 f"📝 {len(txs)}건",
            fg=bal_color)

    # ==================== 적금/예금 ====================
    def _build_deposit(self):
        frame = self.tab_deposit
        ttk.Label(frame, text="적금 / 예금 (복리 계산)",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(18, 8))

        form = tk.LabelFrame(frame, text="새 적금/예금 등록", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=10, bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=6)

        row1 = tk.Frame(form, bg=BG)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="상품명", bg=BG).pack(side="left", padx=4)
        self.dp_name = tk.Entry(row1, width=20)
        self.dp_name.pack(side="left", padx=4)
        tk.Label(row1, text="종류", bg=BG).pack(side="left", padx=4)
        self.dp_type = ttk.Combobox(row1, values=["예금", "적금"],
                                     width=8, state="readonly")
        self.dp_type.set("예금")
        self.dp_type.pack(side="left", padx=4)
        tk.Label(row1, text="원금/월납입금", bg=BG).pack(side="left", padx=4)
        self.dp_principal = tk.Entry(row1, width=14)
        self.dp_principal.pack(side="left", padx=4)
        tk.Label(row1, text="연이율(%)", bg=BG).pack(side="left", padx=4)
        self.dp_rate = tk.Entry(row1, width=8)
        self.dp_rate.pack(side="left", padx=4)

        row2 = tk.Frame(form, bg=BG)
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="기간(개월)", bg=BG).pack(side="left", padx=4)
        self.dp_period = tk.Entry(row2, width=8)
        self.dp_period.pack(side="left", padx=4)
        tk.Label(row2, text="복리주기(연)", bg=BG).pack(side="left", padx=4)
        self.dp_compound = ttk.Combobox(
            row2, values=["12 (월)", "4 (분기)", "2 (반기)", "1 (연)"],
            width=10)
        self.dp_compound.set("12 (월)")
        self.dp_compound.pack(side="left", padx=4)
        tk.Label(row2, text="이자세율(%)", bg=BG).pack(side="left", padx=4)
        self.dp_tax = tk.Entry(row2, width=8)
        self.dp_tax.insert(0, "15.4")
        self.dp_tax.pack(side="left", padx=4)
        tk.Label(row2, text="시작일", bg=BG).pack(side="left", padx=4)
        self.dp_start = tk.Entry(row2, width=12)
        self.dp_start.insert(0, date.today().strftime("%Y-%m-%d"))
        self.dp_start.pack(side="left", padx=4)

        btn_row = tk.Frame(form, bg=BG)
        btn_row.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_row, text="계산만 보기",
                   command=self.preview_deposit).pack(side="left", padx=4)
        ttk.Button(btn_row, text="등록",
                   command=self.add_deposit).pack(side="left", padx=4)
        self.dp_preview = tk.Label(form, text="", bg=BG, fg=PRIMARY,
                                    font=("Malgun Gothic", 10, "bold"),
                                    pady=6)
        self.dp_preview.pack(anchor="w")

        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("id", "name", "type", "principal", "rate", "period",
                "start", "maturity", "elapsed", "current", "maturity_total")
        headers = ("ID", "상품명", "종류", "원금/월납", "이율", "기간(월)",
                   "시작일", "만기일", "경과(개월)", "현재가치", "만기금액(세후)")
        widths = (40, 130, 60, 90, 60, 70, 100, 100, 80, 110, 120)
        self.dp_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.dp_tree.heading(c, text=h)
            self.dp_tree.column(c, width=w, anchor="w")
        self.dp_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.dp_tree.yview)
        sb.pack(side="right", fill="y")
        self.dp_tree.configure(yscrollcommand=sb.set)
        ttk.Button(frame, text="선택 삭제", command=self.delete_deposit).pack(
            anchor="e", padx=20, pady=(0, 12))

    def _parse_compound(self):
        try:
            return int(self.dp_compound.get().split()[0])
        except Exception:
            return 12

    def _calc_from_form(self):
        principal = float(self.dp_principal.get().replace(",", ""))
        rate = float(self.dp_rate.get())
        period = int(self.dp_period.get())
        compound = self._parse_compound()
        tax = float(self.dp_tax.get() or 15.4)
        if self.dp_type.get() == "적금":
            return compound_savings(principal, rate, period, compound, tax)
        return compound_deposit(principal, rate, period, compound, tax)

    def preview_deposit(self):
        try:
            r = self._calc_from_form()
            self.dp_preview.config(text=(
                f"💡 예상 만기 금액(세후): {won(r['total'])}  |  "
                f"원금: {won(r['principal'])}  |  "
                f"세후이자: {won(r['interest_net'])} (세금 {won(r['tax'])})"
            ))
        except Exception as e:
            messagebox.showerror("입력 오류", f"숫자 입력을 확인해주세요.\n{e}")

    def add_deposit(self):
        try:
            principal = float(self.dp_principal.get().replace(",", ""))
            rate = float(self.dp_rate.get())
            period = int(self.dp_period.get())
            compound = self._parse_compound()
            tax = float(self.dp_tax.get() or 15.4)
            self.db.add_deposit(
                self.dp_name.get(), self.dp_type.get(),
                principal, rate, period, self.dp_start.get(),
                tax, compound, ""
            )
            for w in (self.dp_name, self.dp_principal, self.dp_rate, self.dp_period):
                w.delete(0, "end")
            self.dp_preview.config(text="")
            self.refresh_deposit()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("입력 오류", f"입력을 확인해주세요.\n{e}")

    def delete_deposit(self):
        sel = self.dp_tree.selection()
        if not sel:
            return
        did = self.dp_tree.item(sel[0])["values"][0]
        self.db.delete_deposit(did)
        self.refresh_deposit()
        self.refresh_dashboard()

    def refresh_deposit(self):
        for i in self.dp_tree.get_children():
            self.dp_tree.delete(i)
        for d in self.db.get_deposits():
            calc = calculate_deposit(d)
            cur = current_deposit_value(d)
            mdate = maturity_date(d["start_date"], d["period_months"])
            elapsed_disp = (f"{cur['elapsed_months']}/{cur['period_months']}"
                            + (" ✅" if cur["is_matured"] else ""))
            self.dp_tree.insert("", "end", values=(
                d["id"], d["name"], d["deposit_type"],
                won(d["principal"]), f"{d['interest_rate']}%",
                d["period_months"], d["start_date"], mdate,
                elapsed_disp, won(cur["current_value"]), won(calc["total"])
            ))

    # ==================== 주식/ETF (개선) ====================
    def _build_stock(self):
        frame = self.tab_stock
        top = tk.Frame(frame, bg=BG)
        top.pack(fill="x", padx=20, pady=(18, 4))
        ttk.Label(top, text="주식 / ETF 포트폴리오",
                  style="Header.TLabel").pack(side="left")
        ttk.Button(top, text="❓ 티커 예시",
                   command=self.show_ticker_examples).pack(side="right")
        tk.Label(frame, text="💡 주식과 ETF 모두 동일 방식으로 등록 가능. "
                            "한국: 005930.KS / 069500.KS (KODEX 200) | "
                            "미국: AAPL, SPY, QQQ. "
                            "가격이 이상하면 종목 선택 후 '수동 모드 토글'.",
                 bg=BG, fg=MUTED, font=("Malgun Gothic", 9)).pack(
            anchor="w", padx=20)

        form = tk.LabelFrame(frame, text="새 종목 추가", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=10, bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="티커", bg=BG).grid(row=0, column=0, padx=4)
        self.st_ticker = tk.Entry(form, width=12)
        self.st_ticker.grid(row=0, column=1, padx=4)
        tk.Label(form, text="종목명", bg=BG).grid(row=0, column=2, padx=4)
        self.st_name = tk.Entry(form, width=16)
        self.st_name.grid(row=0, column=3, padx=4)
        tk.Label(form, text="수량", bg=BG).grid(row=0, column=4, padx=4)
        self.st_qty = tk.Entry(form, width=8)
        self.st_qty.grid(row=0, column=5, padx=4)
        tk.Label(form, text="평균매수가", bg=BG).grid(row=0, column=6, padx=4)
        self.st_avg = tk.Entry(form, width=12)
        self.st_avg.grid(row=0, column=7, padx=4)
        tk.Label(form, text="통화", bg=BG).grid(row=0, column=8, padx=4)
        self.st_currency = ttk.Combobox(form, values=["KRW", "USD", "JPY"],
                                         width=6, state="readonly")
        self.st_currency.set("KRW")
        self.st_currency.grid(row=0, column=9, padx=4)
        ttk.Button(form, text="추가", command=self.add_stock).grid(
            row=0, column=10, padx=8)

        tb = tk.Frame(frame, bg=BG)
        tb.pack(fill="x", padx=20, pady=4)
        ttk.Button(tb, text="🔄 시세 일괄 업데이트",
                   command=self.update_all_prices).pack(side="left")
        ttk.Button(tb, text="✏️ 선택 가격 수동 변경",
                   command=self.manual_update_price).pack(side="left", padx=6)
        ttk.Button(tb, text="🔒 수동 모드 토글",
                   command=self.toggle_manual_mode).pack(side="left")
        self.st_status = tk.Label(tb, text="", bg=BG, fg=MUTED,
                                   font=("Malgun Gothic", 9))
        self.st_status.pack(side="left", padx=10)
        ttk.Button(tb, text="선택 삭제",
                   command=self.delete_stock).pack(side="right")

        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=8)
        cols = ("id", "ticker", "name", "qty", "avg", "current",
                "value", "pnl", "pnl_pct", "src", "mode", "updated")
        headers = ("ID", "티커", "종목명", "수량", "평균매수가", "현재가",
                   "평가액", "손익", "수익률", "출처", "모드", "업데이트")
        widths = (40, 90, 130, 60, 90, 90, 110, 110, 70, 70, 60, 130)
        self.st_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.st_tree.heading(c, text=h)
            self.st_tree.column(c, width=w, anchor="w")
        self.st_tree.tag_configure("plus", foreground=ACCENT)
        self.st_tree.tag_configure("minus", foreground=DANGER)
        self.st_tree.tag_configure("warn", background="#fff3cd")
        self.st_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.st_tree.yview)
        sb.pack(side="right", fill="y")
        self.st_tree.configure(yscrollcommand=sb.set)

        # 요약 줄
        self.st_summary = tk.Label(frame, text="", bg=BG, fg=FG,
                                    font=("Malgun Gothic", 11, "bold"))
        self.st_summary.pack(anchor="e", padx=20, pady=(0, 12))

    def show_ticker_examples(self):
        """자주 쓰는 한국/미국 주식·ETF 티커 안내 창"""
        dlg = tk.Toplevel(self)
        dlg.title("티커 예시 (주식 / ETF)")
        dlg.geometry("560x520")
        dlg.configure(bg=BG)

        head = tk.Label(dlg, text="자주 쓰는 티커 예시", bg=BG, fg=PRIMARY,
                        font=("Malgun Gothic", 13, "bold"))
        head.pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(dlg, text="아래 티커를 그대로 복사해서 '티커'란에 입력하세요.",
                 bg=BG, fg=MUTED, font=("Malgun Gothic", 9)).pack(
            anchor="w", padx=16, pady=(0, 8))

        text = tk.Text(dlg, font=("Malgun Gothic", 10), bg=CARD_BG, fg=FG,
                       padx=14, pady=10, relief="flat", height=22)
        text.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        content = [
            ("h", "🇰🇷 한국 주식 (코스피 .KS / 코스닥 .KQ)"),
            ("t", "  005930.KS   삼성전자"),
            ("t", "  000660.KS   SK하이닉스"),
            ("t", "  035420.KS   NAVER"),
            ("t", "  035720.KS   카카오"),
            ("t", "  005380.KS   현대차"),
            ("t", "  051910.KS   LG화학"),
            ("t", "  247540.KQ   에코프로비엠"),
            ("t", "  086520.KQ   에코프로"),
            ("h", "\n🇰🇷 한국 ETF (KODEX, TIGER, ACE 등)"),
            ("t", "  069500.KS   KODEX 200"),
            ("t", "  102110.KS   TIGER 200"),
            ("t", "  360750.KS   TIGER 미국S&P500"),
            ("t", "  133690.KS   TIGER 미국나스닥100"),
            ("t", "  381180.KS   TIGER 미국필라델피아반도체나스닥"),
            ("t", "  371460.KS   TIGER 차이나전기차SOLACTIVE"),
            ("t", "  229200.KS   KODEX 코스닥150"),
            ("t", "  114800.KS   KODEX 인버스"),
            ("t", "  252670.KS   KODEX 200선물인버스2X"),
            ("t", "  411060.KS   ACE 미국30년국채액티브(H)"),
            ("h", "\n🇺🇸 미국 주식 (접미사 없음)"),
            ("t", "  AAPL   Apple"),
            ("t", "  MSFT   Microsoft"),
            ("t", "  NVDA   NVIDIA"),
            ("t", "  TSLA   Tesla"),
            ("t", "  GOOGL  Alphabet"),
            ("t", "  AMZN   Amazon"),
            ("h", "\n🇺🇸 미국 ETF"),
            ("t", "  SPY    SPDR S&P 500"),
            ("t", "  VOO    Vanguard S&P 500"),
            ("t", "  QQQ    Invesco NASDAQ 100"),
            ("t", "  VTI    Vanguard Total Stock Market"),
            ("t", "  SCHD   Schwab US Dividend"),
            ("t", "  SOXX   iShares Semiconductor"),
            ("t", "  TLT    iShares 20+ Year Treasury"),
            ("h", "\n💡 통화 자동 추정"),
            ("t", "  .KS / .KQ → KRW (원화)"),
            ("t", "  접미사 없음 → USD (달러)"),
            ("t", "  .T → JPY, .HK → HKD, .L → GBP"),
        ]
        text.tag_config("h", font=("Malgun Gothic", 11, "bold"),
                        foreground=PRIMARY)
        text.tag_config("t", font=("Malgun Gothic", 10))
        for tag, line in content:
            text.insert("end", line + "\n", tag)
        text.configure(state="disabled")

        ttk.Button(dlg, text="닫기",
                   command=dlg.destroy).pack(pady=(0, 12))

    def add_stock(self):
        try:
            qty = float(self.st_qty.get())
            avg = float(self.st_avg.get().replace(",", ""))
            self.db.add_stock(
                self.st_ticker.get().strip().upper(),
                self.st_name.get().strip(),
                qty, avg, self.st_currency.get()
            )
            for e in (self.st_ticker, self.st_name, self.st_qty, self.st_avg):
                e.delete(0, "end")
            self.refresh_stock()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("입력 오류", f"숫자 입력을 확인해주세요.\n{e}")

    def manual_update_price(self):
        sel = self.st_tree.selection()
        if not sel:
            return
        sid = self.st_tree.item(sel[0])["values"][0]
        dlg = tk.Toplevel(self)
        dlg.title("현재가 수동 입력")
        dlg.geometry("280x130")
        tk.Label(dlg, text="새로운 현재가:", font=("Malgun Gothic", 10)).pack(pady=10)
        e = tk.Entry(dlg, width=20)
        e.pack()
        e.focus()

        def save():
            try:
                price = float(e.get().replace(",", ""))
                self.db.update_stock_price(sid, price, source="manual")
                self.db.toggle_stock_manual(sid, True)
                dlg.destroy()
                self.refresh_stock()
                self.refresh_dashboard()
            except Exception as ex:
                messagebox.showerror("오류", str(ex))

        ttk.Button(dlg, text="저장", command=save).pack(pady=8)
        dlg.bind("<Return>", lambda _: save())

    def toggle_manual_mode(self):
        sel = self.st_tree.selection()
        if not sel:
            return
        vals = self.st_tree.item(sel[0])["values"]
        sid = vals[0]
        # 현재 모드 확인
        for s in self.db.get_stocks():
            if s["id"] == sid:
                new_mode = not bool(s["use_manual"])
                self.db.toggle_stock_manual(sid, new_mode)
                self.refresh_stock()
                self.st_status.config(
                    text=f"{vals[1]}: 수동 모드 {'ON' if new_mode else 'OFF'}")
                return

    def update_all_prices(self):
        self.st_status.config(text="시세 가져오는 중...")
        self.update_idletasks()

        def worker():
            stocks = self.db.get_stocks()
            ok = fail = skip = warn = 0
            messages = []
            for s in stocks:
                if s.get("use_manual"):
                    skip += 1
                    continue
                quote = fetch_stock_quote(s["ticker"])
                if quote and quote["price"] > 0:
                    p = quote["price"]
                    # 이상치 경고: 평균매수가와 ±70% 이상 차이
                    if s["avg_price"] > 0:
                        diff_pct = (p - s["avg_price"]) / s["avg_price"] * 100
                        if abs(diff_pct) > 70:
                            warn += 1
                            messages.append(
                                f"⚠️ {s['ticker']}: 평균가 대비 {diff_pct:+.0f}% — "
                                f"확인 필요 (가져온 가격 {p:,.2f} {quote['currency']})")
                    self.db.update_stock_price(
                        s["id"], p, source=quote["source"],
                        currency=quote["currency"])
                    ok += 1
                else:
                    fail += 1
                    messages.append(f"❌ {s['ticker']}: 가격 조회 실패")

            def done():
                msg = f"완료: 성공 {ok} / 실패 {fail} / 수동제외 {skip}"
                if warn:
                    msg += f" / 경고 {warn}"
                self.st_status.config(text=msg)
                if messages:
                    messagebox.showwarning(
                        "주가 조회 알림", "\n".join(messages[:10]))
                self.refresh_stock()
                self.refresh_dashboard()
            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def delete_stock(self):
        sel = self.st_tree.selection()
        if not sel:
            return
        sid = self.st_tree.item(sel[0])["values"][0]
        self.db.delete_stock(sid)
        self.refresh_stock()
        self.refresh_dashboard()

    def refresh_stock(self):
        for i in self.st_tree.get_children():
            self.st_tree.delete(i)
        total_value = 0
        total_cost = 0
        for s in self.db.get_stocks():
            cur = s["current_price"] if s["current_price"] else s["avg_price"]
            value = cur * s["quantity"]
            cost = s["avg_price"] * s["quantity"]
            pnl = value - cost
            pct = (pnl / cost * 100) if cost else 0
            total_value += value
            total_cost += cost
            currency = s.get("currency", "KRW")
            mode = "수동" if s.get("use_manual") else "API"
            src = s.get("price_source") or "-"
            tag = "plus" if pnl >= 0 else "minus"
            # 평균매수가와 너무 차이나면 경고색
            warn = (s["avg_price"] > 0 and
                    abs((cur - s["avg_price"]) / s["avg_price"]) > 0.7)
            tags = (tag, "warn") if warn else (tag,)
            self.st_tree.insert("", "end", tags=tags, values=(
                s["id"], s["ticker"], s["name"], s["quantity"],
                money(s["avg_price"], currency), money(cur, currency),
                money(value, currency),
                f"{'+' if pnl >= 0 else ''}{money(pnl, currency)}",
                f"{pct:+.2f}%", src, mode,
                s["last_updated"] or "-"
            ))
        # 요약
        total_pnl = total_value - total_cost
        total_pct = (total_pnl / total_cost * 100) if total_cost else 0
        sign = "+" if total_pnl >= 0 else ""
        color = ACCENT if total_pnl >= 0 else DANGER
        self.st_summary.config(
            text=f"총 평가액: {won(total_value)}  |  "
                 f"총 원가: {won(total_cost)}  |  "
                 f"평가손익: {sign}{won(total_pnl)} ({total_pct:+.2f}%)",
            fg=color)

    # ==================== 매매 손익 ====================
    def _build_trade(self):
        frame = self.tab_trade
        ttk.Label(frame, text="주식 매매 손익 가계부",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(frame, text="💡 매수/매도를 기록하면 평균매수가 기준으로 실현손익이 자동 계산됩니다.",
                 bg=BG, fg=MUTED, font=("Malgun Gothic", 9)).pack(
            anchor="w", padx=20, pady=(0, 6))

        form = tk.LabelFrame(frame, text="새 매매 기록", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=10, bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="날짜", bg=BG).grid(row=0, column=0, padx=4)
        self.tr_date = tk.Entry(form, width=12)
        self.tr_date.insert(0, date.today().strftime("%Y-%m-%d"))
        self.tr_date.grid(row=0, column=1, padx=4)
        tk.Label(form, text="구분", bg=BG).grid(row=0, column=2, padx=4)
        self.tr_type = ttk.Combobox(form, values=["buy", "sell"],
                                     width=8, state="readonly")
        self.tr_type.set("buy")
        self.tr_type.grid(row=0, column=3, padx=4)
        tk.Label(form, text="티커", bg=BG).grid(row=0, column=4, padx=4)
        self.tr_ticker = tk.Entry(form, width=12)
        self.tr_ticker.grid(row=0, column=5, padx=4)
        tk.Label(form, text="종목명", bg=BG).grid(row=0, column=6, padx=4)
        self.tr_name = tk.Entry(form, width=14)
        self.tr_name.grid(row=0, column=7, padx=4)
        tk.Label(form, text="수량", bg=BG).grid(row=1, column=0, padx=4, pady=(8, 0))
        self.tr_qty = tk.Entry(form, width=12)
        self.tr_qty.grid(row=1, column=1, padx=4, pady=(8, 0))
        tk.Label(form, text="가격", bg=BG).grid(row=1, column=2, padx=4, pady=(8, 0))
        self.tr_price = tk.Entry(form, width=12)
        self.tr_price.grid(row=1, column=3, padx=4, pady=(8, 0))
        tk.Label(form, text="수수료/세금", bg=BG).grid(row=1, column=4, padx=4, pady=(8, 0))
        self.tr_fees = tk.Entry(form, width=10)
        self.tr_fees.insert(0, "0")
        self.tr_fees.grid(row=1, column=5, padx=4, pady=(8, 0))
        tk.Label(form, text="메모", bg=BG).grid(row=1, column=6, padx=4, pady=(8, 0))
        self.tr_memo = tk.Entry(form, width=18)
        self.tr_memo.grid(row=1, column=7, padx=4, pady=(8, 0))
        ttk.Button(form, text="추가", command=self.add_trade).grid(
            row=0, column=8, rowspan=2, padx=8, sticky="ns")

        tb = tk.Frame(frame, bg=BG)
        tb.pack(fill="x", padx=20, pady=4)
        tk.Label(tb, text="연도 필터:", bg=BG).pack(side="left")
        self.tr_year = ttk.Combobox(tb, width=10, state="readonly",
                                     values=["전체"] + [str(y) for y in range(
                                         datetime.now().year, datetime.now().year - 10, -1)])
        self.tr_year.set(str(datetime.now().year))
        self.tr_year.pack(side="left", padx=4)
        self.tr_year.bind("<<ComboboxSelected>>", lambda _: self.refresh_trade())
        ttk.Button(tb, text="선택 삭제", command=self.delete_trade).pack(side="right")

        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=8)
        cols = ("id", "date", "type", "ticker", "name", "qty", "price", "amount", "fees", "pnl", "memo")
        headers = ("ID", "날짜", "구분", "티커", "종목명", "수량", "가격", "거래금액", "수수료", "실현손익", "메모")
        widths = (40, 90, 60, 80, 120, 70, 90, 110, 80, 110, 200)
        self.tr_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.tr_tree.heading(c, text=h)
            self.tr_tree.column(c, width=w, anchor="w")
        self.tr_tree.tag_configure("plus", foreground=ACCENT)
        self.tr_tree.tag_configure("minus", foreground=DANGER)
        self.tr_tree.tag_configure("buy", foreground="#4a90e2")
        self.tr_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.tr_tree.yview)
        sb.pack(side="right", fill="y")
        self.tr_tree.configure(yscrollcommand=sb.set)

        self.tr_summary = tk.Label(frame, text="", bg=BG, fg=FG,
                                    font=("Malgun Gothic", 11, "bold"))
        self.tr_summary.pack(anchor="e", padx=20, pady=(0, 12))

    def add_trade(self):
        try:
            ticker = self.tr_ticker.get().strip().upper()
            name = self.tr_name.get().strip()
            qty = float(self.tr_qty.get())
            price = float(self.tr_price.get().replace(",", ""))
            fees = float(self.tr_fees.get().replace(",", "") or 0)
            trade_type = self.tr_type.get()

            # 매도면 평균매수가 기준으로 실현손익 계산
            realized = 0
            if trade_type == "sell":
                avg_buy, _ = self.db.get_avg_buy_price(ticker)
                if avg_buy > 0:
                    realized = (price - avg_buy) * qty - fees

            self.db.add_stock_trade(
                self.tr_date.get(), ticker, name, trade_type,
                qty, price, fees, realized, self.tr_memo.get()
            )
            for e in (self.tr_ticker, self.tr_name, self.tr_qty,
                       self.tr_price, self.tr_memo):
                e.delete(0, "end")
            self.tr_fees.delete(0, "end")
            self.tr_fees.insert(0, "0")
            self.refresh_trade()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("입력 오류", f"입력을 확인해주세요.\n{e}")

    def delete_trade(self):
        sel = self.tr_tree.selection()
        if not sel:
            return
        tid = self.tr_tree.item(sel[0])["values"][0]
        self.db.delete_stock_trade(tid)
        self.refresh_trade()
        self.refresh_dashboard()

    def refresh_trade(self):
        for i in self.tr_tree.get_children():
            self.tr_tree.delete(i)
        year = self.tr_year.get() if hasattr(self, "tr_year") else "전체"
        year_arg = None if year == "전체" else year
        trades = self.db.get_stock_trades(year=year_arg)
        total_pnl = 0
        total_buy = 0
        total_sell = 0
        for t in trades:
            amount = t["quantity"] * t["price"]
            if t["trade_type"] == "buy":
                total_buy += amount + (t["fees"] or 0)
                tag = "buy"
                pnl_disp = "-"
            else:
                total_sell += amount - (t["fees"] or 0)
                total_pnl += t["realized_pnl"] or 0
                tag = "plus" if (t["realized_pnl"] or 0) >= 0 else "minus"
                rp = t["realized_pnl"] or 0
                pnl_disp = f"{'+' if rp >= 0 else ''}{won(rp)}"
            self.tr_tree.insert("", "end", tags=(tag,), values=(
                t["id"], t["date"], t["trade_type"], t["ticker"], t["name"],
                t["quantity"], won(t["price"]), won(amount), won(t["fees"] or 0),
                pnl_disp, t["memo"] or ""
            ))
        sign = "+" if total_pnl >= 0 else ""
        self.tr_summary.config(
            text=f"매수 {won(total_buy)}  |  매도 {won(total_sell)}  |  "
                 f"실현손익 {sign}{won(total_pnl)}",
            fg=ACCENT if total_pnl >= 0 else DANGER)

    # ==================== 기타 자산 ====================
    def _build_asset(self):
        frame = self.tab_asset
        ttk.Label(frame, text="기타 자산 (현금, 부동산 등)",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(18, 8))

        form = tk.LabelFrame(frame, text="새 자산 추가", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=10, bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="이름", bg=BG).grid(row=0, column=0, padx=4)
        self.as_name = tk.Entry(form, width=20)
        self.as_name.grid(row=0, column=1, padx=4)
        tk.Label(form, text="종류", bg=BG).grid(row=0, column=2, padx=4)
        self.as_type = ttk.Combobox(form, values=[
            "현금", "부동산", "암호화폐", "자동차", "기타"
        ], width=10, state="readonly")
        self.as_type.set("현금")
        self.as_type.grid(row=0, column=3, padx=4)
        tk.Label(form, text="평가액", bg=BG).grid(row=0, column=4, padx=4)
        self.as_value = tk.Entry(form, width=16)
        self.as_value.grid(row=0, column=5, padx=4)
        tk.Label(form, text="메모", bg=BG).grid(row=0, column=6, padx=4)
        self.as_memo = tk.Entry(form, width=24)
        self.as_memo.grid(row=0, column=7, padx=4)
        ttk.Button(form, text="추가", command=self.add_asset).grid(
            row=0, column=8, padx=8)

        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("id", "name", "type", "value", "memo", "updated")
        headers = ("ID", "이름", "종류", "평가액", "메모", "업데이트")
        widths = (40, 200, 100, 140, 300, 160)
        self.as_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.as_tree.heading(c, text=h)
            self.as_tree.column(c, width=w, anchor="w")
        self.as_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.as_tree.yview)
        sb.pack(side="right", fill="y")
        self.as_tree.configure(yscrollcommand=sb.set)
        tb = tk.Frame(frame, bg=BG)
        tb.pack(fill="x", padx=20, pady=(0, 12))
        ttk.Button(tb, text="선택 금액 수정",
                   command=self.update_asset).pack(side="right", padx=6)
        ttk.Button(tb, text="선택 삭제",
                   command=self.delete_asset).pack(side="right")

    def add_asset(self):
        try:
            value = float(self.as_value.get().replace(",", ""))
            self.db.add_asset(self.as_name.get(), self.as_type.get(),
                              value, self.as_memo.get())
            for e in (self.as_name, self.as_value, self.as_memo):
                e.delete(0, "end")
            self.refresh_asset()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("입력 오류", f"숫자 입력을 확인해주세요.\n{e}")

    def update_asset(self):
        sel = self.as_tree.selection()
        if not sel:
            return
        aid = self.as_tree.item(sel[0])["values"][0]
        dlg = tk.Toplevel(self)
        dlg.title("자산 금액 수정")
        dlg.geometry("280x120")
        tk.Label(dlg, text="새로운 평가액:").pack(pady=10)
        e = tk.Entry(dlg, width=20)
        e.pack()
        e.focus()

        def save():
            try:
                self.db.update_asset(aid, float(e.get().replace(",", "")))
                dlg.destroy()
                self.refresh_asset()
                self.refresh_dashboard()
            except Exception as ex:
                messagebox.showerror("오류", str(ex))
        ttk.Button(dlg, text="저장", command=save).pack(pady=8)
        dlg.bind("<Return>", lambda _: save())

    def delete_asset(self):
        sel = self.as_tree.selection()
        if not sel:
            return
        aid = self.as_tree.item(sel[0])["values"][0]
        self.db.delete_asset(aid)
        self.refresh_asset()
        self.refresh_dashboard()

    def refresh_asset(self):
        for i in self.as_tree.get_children():
            self.as_tree.delete(i)
        for a in self.db.get_assets():
            self.as_tree.insert("", "end", values=(
                a["id"], a["name"], a["asset_type"],
                won(a["value"]), a["memo"] or "",
                a["updated_at"] or "-"
            ))

    # ==================== 보험 ====================
    def _build_insurance(self):
        frame = self.tab_insurance
        top = tk.Frame(frame, bg=BG)
        top.pack(fill="x", padx=20, pady=(18, 4))
        ttk.Label(top, text="🛡 보험 관리",
                  style="Header.TLabel").pack(side="left")
        ttk.Button(top, text="🔗 내보험찾기 (공식 통합조회)",
                   command=lambda: webbrowser.open("https://cont.insure.or.kr/")
                   ).pack(side="right")
        tk.Label(frame, text="💡 개인 앱이 보험사 DB에 접근할 수는 없어요. "
                            "내보험찾기에서 한 번 조회한 뒤 아래에 등록해 두면 "
                            "총 납입금/만기 D-day/진행률이 자동 계산됩니다.",
                 bg=BG, fg=MUTED, font=("Malgun Gothic", 9),
                 wraplength=1000, justify="left").pack(
            anchor="w", padx=20, pady=(0, 4))

        # 상단 요약 카드
        cards = tk.Frame(frame, bg=BG)
        cards.pack(fill="x", padx=20, pady=6)
        self.ins_card_month = self._make_card(cards, "월 보험료 합계", "0원", "#9b59b6")
        self.ins_card_month.grid(row=0, column=0, padx=6, pady=4, sticky="ew")
        self.ins_card_total = self._make_card(cards, "총 누적 납입", "0원", "#4a90e2")
        self.ins_card_total.grid(row=0, column=1, padx=6, pady=4, sticky="ew")
        self.ins_card_count = self._make_card(cards, "보유 계약 수", "0건", ACCENT)
        self.ins_card_count.grid(row=0, column=2, padx=6, pady=4, sticky="ew")
        self.ins_card_alert = self._make_card(cards, "30일 내 만기", "0건", DANGER)
        self.ins_card_alert.grid(row=0, column=3, padx=6, pady=4, sticky="ew")
        for c in range(4):
            cards.columnconfigure(c, weight=1)

        # 입력 폼
        form = tk.LabelFrame(frame, text="새 보험 등록", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=8, bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=6)

        r1 = tk.Frame(form, bg=BG)
        r1.pack(fill="x", pady=2)
        tk.Label(r1, text="보험사", bg=BG).pack(side="left", padx=4)
        self.ins_company = tk.Entry(r1, width=14)
        self.ins_company.pack(side="left", padx=4)
        tk.Label(r1, text="상품명", bg=BG).pack(side="left", padx=4)
        self.ins_name = tk.Entry(r1, width=22)
        self.ins_name.pack(side="left", padx=4)
        tk.Label(r1, text="종류", bg=BG).pack(side="left", padx=4)
        self.ins_cat = ttk.Combobox(r1, values=[
            "실손", "암", "종신", "정기", "건강", "치아",
            "운전자", "자동차", "화재", "여행자", "연금", "변액", "기타"
        ], width=10, state="readonly")
        self.ins_cat.set("실손")
        self.ins_cat.pack(side="left", padx=4)
        tk.Label(r1, text="피보험자", bg=BG).pack(side="left", padx=4)
        self.ins_person = tk.Entry(r1, width=10)
        self.ins_person.pack(side="left", padx=4)
        tk.Label(r1, text="월 보험료", bg=BG).pack(side="left", padx=4)
        self.ins_premium = tk.Entry(r1, width=12)
        self.ins_premium.pack(side="left", padx=4)

        r2 = tk.Frame(form, bg=BG)
        r2.pack(fill="x", pady=4)
        tk.Label(r2, text="가입일", bg=BG).pack(side="left", padx=4)
        self.ins_start = tk.Entry(r2, width=12)
        self.ins_start.insert(0, date.today().strftime("%Y-%m-%d"))
        self.ins_start.pack(side="left", padx=4)
        tk.Label(r2, text="만기일 (없으면 비움)", bg=BG).pack(side="left", padx=4)
        self.ins_maturity = tk.Entry(r2, width=12)
        self.ins_maturity.pack(side="left", padx=4)
        tk.Label(r2, text="납입종료일", bg=BG).pack(side="left", padx=4)
        self.ins_pay_end = tk.Entry(r2, width=12)
        self.ins_pay_end.pack(side="left", padx=4)
        tk.Label(r2, text="보장/메모", bg=BG).pack(side="left", padx=4)
        self.ins_coverage = tk.Entry(r2, width=24)
        self.ins_coverage.pack(side="left", padx=4)
        ttk.Button(r2, text="추가", command=self.add_insurance).pack(
            side="left", padx=8)

        # 알림 영역
        self.ins_alert = tk.Label(frame, text="", bg=BG, fg=DANGER,
                                   font=("Malgun Gothic", 10, "bold"))
        self.ins_alert.pack(anchor="w", padx=20, pady=(4, 0))

        # 목록
        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=8)
        cols = ("id", "company", "name", "category", "person",
                "premium", "start", "maturity", "dday",
                "paid_months", "total_paid", "pay_status")
        headers = ("ID", "보험사", "상품명", "종류", "피보험자",
                   "월보험료", "가입일", "만기일", "D-day",
                   "납입(월)", "총납입", "납입상태")
        widths = (40, 90, 140, 70, 70, 90, 95, 95, 80, 80, 110, 100)
        self.ins_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.ins_tree.heading(c, text=h)
            self.ins_tree.column(c, width=w, anchor="w")
        self.ins_tree.tag_configure("expiring", background="#fff3cd")
        self.ins_tree.tag_configure("expired", foreground=MUTED)
        self.ins_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.ins_tree.yview)
        sb.pack(side="right", fill="y")
        self.ins_tree.configure(yscrollcommand=sb.set)
        ttk.Button(frame, text="선택 삭제",
                   command=self.delete_insurance).pack(anchor="e",
                                                         padx=20, pady=(0, 12))

    def add_insurance(self):
        try:
            company = self.ins_company.get().strip()
            name = self.ins_name.get().strip()
            if not company or not name:
                messagebox.showwarning("입력 필요", "보험사와 상품명을 입력해주세요.")
                return
            premium = float((self.ins_premium.get() or "0").replace(",", ""))
            self.db.add_insurance(
                company=company, name=name, category=self.ins_cat.get(),
                insured_person=self.ins_person.get().strip(),
                monthly_premium=premium,
                start_date=self.ins_start.get(),
                maturity_date=self.ins_maturity.get().strip() or None,
                payment_end_date=self.ins_pay_end.get().strip() or None,
                coverage=self.ins_coverage.get(),
            )
            for e in (self.ins_company, self.ins_name, self.ins_person,
                       self.ins_premium, self.ins_maturity,
                       self.ins_pay_end, self.ins_coverage):
                e.delete(0, "end")
            self.refresh_insurance()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("입력 오류", f"입력을 확인해주세요.\n{e}")

    def delete_insurance(self):
        sel = self.ins_tree.selection()
        if not sel:
            return
        iid = self.ins_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("삭제 확인", "이 보험 계약을 삭제할까요?"):
            self.db.delete_insurance(iid)
            self.refresh_insurance()
            self.refresh_dashboard()

    def refresh_insurance(self):
        for i in self.ins_tree.get_children():
            self.ins_tree.delete(i)
        insurances = self.db.get_insurances()
        total_monthly = 0
        total_paid = 0
        expiring_soon = []
        for ins in insurances:
            stats = insurance_stats(ins)
            total_monthly += ins["monthly_premium"] or 0
            total_paid += stats["total_paid"]

            # 만기 D-day
            if stats["days_to_maturity"] is None:
                dday = "종신"
            elif stats["is_expired"]:
                dday = "만료"
            elif stats["days_to_maturity"] == 0:
                dday = "오늘"
            elif stats["days_to_maturity"] > 0:
                dday = f"D-{stats['days_to_maturity']}"
            else:
                dday = f"D+{-stats['days_to_maturity']}"

            # 납입 상태
            if stats["payment_progress"] is None:
                pay_status = "납입중"
            elif stats["payment_done"]:
                pay_status = "✅ 완료"
            else:
                pay_status = f"{stats['payment_progress']:.0f}% (남{stats['payment_months_left']}월)"

            tag = ()
            if stats["is_expired"]:
                tag = ("expired",)
            elif (stats["days_to_maturity"] is not None
                  and 0 <= stats["days_to_maturity"] <= 30):
                tag = ("expiring",)
                expiring_soon.append(f"{ins['name']} ({dday})")

            self.ins_tree.insert("", "end", tags=tag, values=(
                ins["id"], ins["company"], ins["name"], ins["category"],
                ins["insured_person"] or "-",
                won(ins["monthly_premium"] or 0),
                ins["start_date"],
                ins["maturity_date"] or "종신/평생",
                dday,
                stats["months_paid"],
                won(stats["total_paid"]),
                pay_status,
            ))

        # 카드 갱신
        self.ins_card_month.value_label.config(text=won(total_monthly))
        self.ins_card_total.value_label.config(text=won(total_paid))
        self.ins_card_count.value_label.config(text=f"{len(insurances)}건")
        self.ins_card_alert.value_label.config(text=f"{len(expiring_soon)}건")

        # 알림 라벨
        if expiring_soon:
            self.ins_alert.config(
                text=f"⚠️ 만기 임박: {', '.join(expiring_soon[:5])}")
        else:
            self.ins_alert.config(text="")

    # ==================== 갓생살기 ====================
    def _build_godlife(self):
        frame = self.tab_godlife
        # 상단: 명언 + 포인트
        top = tk.Frame(frame, bg=BG)
        top.pack(fill="x", padx=20, pady=(14, 4))
        tk.Label(top, text="✨ 갓생살기 프로젝트", bg=BG, fg=PRIMARY,
                 font=("Malgun Gothic", 16, "bold")).pack(side="left")
        self.godlife_summary = tk.Label(top, text="", bg=BG, fg=MUTED,
                                         font=("Malgun Gothic", 10))
        self.godlife_summary.pack(side="right")
        tk.Label(frame, text=f"💬  {self.today_quote}",
                 bg=BG, fg=FG, font=("Malgun Gothic", 11, "italic")).pack(
            anchor="w", padx=20, pady=(0, 8))

        # 서브 탭
        sub = ttk.Notebook(frame)
        sub.pack(fill="both", expand=True, padx=14, pady=4)

        self.sub_habit = ttk.Frame(sub)
        self.sub_goal = ttk.Frame(sub)
        self.sub_todo = ttk.Frame(sub)
        sub.add(self.sub_habit, text="🔥 습관 트래커")
        sub.add(self.sub_goal, text="🎯 장기 목표")
        sub.add(self.sub_todo, text="📋 오늘 할 일")

        self._build_habit()
        self._build_goal()
        self._build_todo()

    # ---- 습관 ----
    def _build_habit(self):
        frame = self.sub_habit

        # 추가 폼
        form = tk.LabelFrame(frame, text="새 습관 추가", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=8, bd=1, relief="solid")
        form.pack(fill="x", padx=14, pady=8)

        tk.Label(form, text="아이콘", bg=BG).pack(side="left", padx=4)
        self.hb_icon = tk.Entry(form, width=4)
        self.hb_icon.insert(0, "🏃")
        self.hb_icon.pack(side="left", padx=4)
        tk.Label(form, text="습관 이름", bg=BG).pack(side="left", padx=4)
        self.hb_name = tk.Entry(form, width=22)
        self.hb_name.pack(side="left", padx=4)
        tk.Label(form, text="카테고리", bg=BG).pack(side="left", padx=4)
        self.hb_cat = ttk.Combobox(form, values=list(CATEGORY_COLORS.keys()),
                                    width=10, state="readonly")
        self.hb_cat.set("건강")
        self.hb_cat.pack(side="left", padx=4)
        tk.Label(form, text="포인트", bg=BG).pack(side="left", padx=4)
        self.hb_pts = tk.Entry(form, width=6)
        self.hb_pts.insert(0, "10")
        self.hb_pts.pack(side="left", padx=4)
        ttk.Button(form, text="추가", command=self.add_habit).pack(side="left", padx=8)

        # 카드 리스트 (스크롤 가능)
        wrap = tk.Frame(frame, bg=BG)
        wrap.pack(fill="both", expand=True, padx=14, pady=4)
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.habit_container = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=self.habit_container, anchor="nw")
        self.habit_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._habit_canvas = canvas

    def add_habit(self):
        name = self.hb_name.get().strip()
        if not name:
            messagebox.showwarning("입력 필요", "습관 이름을 입력해주세요.")
            return
        try:
            pts = int(self.hb_pts.get() or 10)
        except ValueError:
            pts = 10
        cat = self.hb_cat.get()
        self.db.add_habit(
            name=name, icon=self.hb_icon.get() or "✅",
            color=CATEGORY_COLORS.get(cat, ACCENT),
            points=pts, category=cat
        )
        self.hb_name.delete(0, "end")
        self.refresh_habit()
        self.refresh_dashboard()

    def refresh_habit(self):
        # 기존 카드 제거
        for w in self.habit_container.winfo_children():
            w.destroy()

        habits = self.db.get_habits()
        if not habits:
            tk.Label(self.habit_container,
                     text="아직 등록된 습관이 없어요. 위에서 첫 습관을 추가해보세요!",
                     bg=BG, fg=MUTED,
                     font=("Malgun Gothic", 11)).pack(pady=30)
            self._update_godlife_summary()
            return

        today = date.today().strftime("%Y-%m-%d")
        for h in habits:
            self._make_habit_card(h, today)
        self._update_godlife_summary()

    def _make_habit_card(self, habit, today):
        card = tk.Frame(self.habit_container, bg=CARD_BG, bd=0,
                        highlightthickness=1, highlightbackground=SOFT)
        card.pack(fill="x", padx=4, pady=4)

        # 좌측 색띠
        bar = tk.Frame(card, bg=habit["color"], width=6)
        bar.pack(side="left", fill="y")

        inner = tk.Frame(card, bg=CARD_BG)
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # 상단: 아이콘 + 이름 + streak + 포인트
        top = tk.Frame(inner, bg=CARD_BG)
        top.pack(fill="x")
        tk.Label(top, text=f"{habit['icon']}  {habit['name']}",
                 bg=CARD_BG, fg=FG,
                 font=("Malgun Gothic", 12, "bold")).pack(side="left")
        streak = self.db.calculate_streak(habit["id"])
        tk.Label(top, text=f"🔥 {streak}일 연속", bg=CARD_BG, fg=DANGER,
                 font=("Malgun Gothic", 10, "bold")).pack(side="left", padx=14)
        tk.Label(top, text=f"+{habit['points']}pt | {habit['category']}",
                 bg=CARD_BG, fg=MUTED,
                 font=("Malgun Gothic", 9)).pack(side="left", padx=8)

        # 우측 버튼
        btn_frame = tk.Frame(top, bg=CARD_BG)
        btn_frame.pack(side="right")
        logs = self.db.get_habit_logs(habit["id"], days=8)
        checked = today in logs
        btn_text = "✅ 오늘 완료" if checked else "⬜ 오늘 체크"
        btn_bg = ACCENT if checked else SOFT
        btn_fg = "white" if checked else FG
        b = tk.Button(btn_frame, text=btn_text, bg=btn_bg, fg=btn_fg,
                       font=("Malgun Gothic", 10, "bold"),
                       relief="flat", padx=12, pady=6,
                       command=lambda hid=habit["id"]: self.toggle_habit(hid))
        b.pack(side="right", padx=4)
        tk.Button(btn_frame, text="삭제", bg=CARD_BG, fg=MUTED,
                   relief="flat", font=("Malgun Gothic", 9),
                   command=lambda hid=habit["id"]: self.delete_habit(hid)).pack(side="right")

        # 하단: 최근 7일 도트
        dot_row = tk.Frame(inner, bg=CARD_BG)
        dot_row.pack(fill="x", pady=(8, 0))
        tk.Label(dot_row, text="최근 7일: ", bg=CARD_BG, fg=MUTED,
                 font=("Malgun Gothic", 9)).pack(side="left")
        for i in range(6, -1, -1):
            d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            done = d in logs
            color = habit["color"] if done else SOFT
            dot = tk.Label(dot_row, text="●" if done else "○",
                           bg=CARD_BG, fg=color,
                           font=("Malgun Gothic", 14))
            dot.pack(side="left", padx=2)
            label_text = (date.today() - timedelta(days=i)).strftime("%m/%d")
            tk.Label(dot_row, text=label_text, bg=CARD_BG, fg=MUTED,
                     font=("Malgun Gothic", 8)).pack(side="left", padx=(0, 6))

    def toggle_habit(self, hid):
        today = date.today().strftime("%Y-%m-%d")
        self.db.toggle_habit_log(hid, today)
        self.refresh_habit()
        self.refresh_dashboard()

    def delete_habit(self, hid):
        if messagebox.askyesno("삭제 확인", "이 습관과 모든 기록을 삭제할까요?"):
            self.db.delete_habit(hid)
            self.refresh_habit()
            self.refresh_dashboard()

    def _update_godlife_summary(self):
        habits = self.db.get_habits()
        today = date.today().strftime("%Y-%m-%d")
        done_today = 0
        for h in habits:
            if today in self.db.get_habit_logs(h["id"], days=1):
                done_today += 1
        total_pts = self.db.get_total_points()
        today_pts = self.db.get_today_points()
        goals = self.db.get_goals(status="active")
        self.godlife_summary.config(
            text=f"오늘 완료: {done_today}/{len(habits)} | "
                 f"오늘 +{today_pts}pt | 총 {total_pts}pt | "
                 f"진행중 목표 {len(goals)}개")

    # ---- 목표 ----
    def _build_goal(self):
        frame = self.sub_goal
        form = tk.LabelFrame(frame, text="새 장기 목표 추가", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=8, bd=1, relief="solid")
        form.pack(fill="x", padx=14, pady=8)

        tk.Label(form, text="제목", bg=BG).pack(side="left", padx=4)
        self.gl_title = tk.Entry(form, width=28)
        self.gl_title.pack(side="left", padx=4)
        tk.Label(form, text="카테고리", bg=BG).pack(side="left", padx=4)
        self.gl_cat = ttk.Combobox(form, values=list(CATEGORY_COLORS.keys()),
                                    width=10, state="readonly")
        self.gl_cat.set("재정")
        self.gl_cat.pack(side="left", padx=4)
        tk.Label(form, text="목표일", bg=BG).pack(side="left", padx=4)
        self.gl_date = tk.Entry(form, width=12)
        self.gl_date.pack(side="left", padx=4)
        tk.Label(form, text="설명", bg=BG).pack(side="left", padx=4)
        self.gl_desc = tk.Entry(form, width=20)
        self.gl_desc.pack(side="left", padx=4)
        ttk.Button(form, text="추가", command=self.add_goal).pack(side="left", padx=8)

        wrap = tk.Frame(frame, bg=BG)
        wrap.pack(fill="both", expand=True, padx=14, pady=4)
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.goal_container = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=self.goal_container, anchor="nw")
        self.goal_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def add_goal(self):
        title = self.gl_title.get().strip()
        if not title:
            messagebox.showwarning("입력 필요", "목표 제목을 입력해주세요.")
            return
        cat = self.gl_cat.get()
        self.db.add_goal(
            title=title,
            description=self.gl_desc.get(),
            category=cat,
            target_date=self.gl_date.get() or None,
            color=CATEGORY_COLORS.get(cat, ACCENT)
        )
        self.gl_title.delete(0, "end")
        self.gl_date.delete(0, "end")
        self.gl_desc.delete(0, "end")
        self.refresh_goal()
        self.refresh_dashboard()

    def refresh_goal(self):
        for w in self.goal_container.winfo_children():
            w.destroy()
        goals = self.db.get_goals()
        if not goals:
            tk.Label(self.goal_container,
                     text="장기 목표를 추가하면 카테고리별로 진행률을 추적할 수 있어요.",
                     bg=BG, fg=MUTED,
                     font=("Malgun Gothic", 11)).pack(pady=30)
            self._update_godlife_summary()
            return
        # 2열 카드 그리드
        col = 0
        row = 0
        for g in goals:
            self._make_goal_card(g, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        for c in range(2):
            self.goal_container.columnconfigure(c, weight=1)
        self._update_godlife_summary()

    def _make_goal_card(self, goal, row, col):
        card = tk.Frame(self.goal_container, bg=CARD_BG, bd=0,
                        highlightthickness=1, highlightbackground=SOFT)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        bar = tk.Frame(card, bg=goal["color"], height=5)
        bar.pack(fill="x")
        inner = tk.Frame(card, bg=CARD_BG)
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        top = tk.Frame(inner, bg=CARD_BG)
        top.pack(fill="x")
        tk.Label(top, text=goal["title"], bg=CARD_BG, fg=FG,
                 font=("Malgun Gothic", 12, "bold"),
                 wraplength=300, justify="left").pack(side="left", anchor="w")
        if goal["status"] == "completed":
            tk.Label(top, text="✅ 완료", bg=CARD_BG, fg=ACCENT,
                     font=("Malgun Gothic", 10, "bold")).pack(side="right")

        meta = tk.Frame(inner, bg=CARD_BG)
        meta.pack(fill="x", pady=(6, 4))
        tk.Label(meta, text=f"📂 {goal['category']}", bg=CARD_BG, fg=goal["color"],
                 font=("Malgun Gothic", 9, "bold")).pack(side="left")
        if goal["target_date"]:
            tk.Label(meta, text=f"📅 {goal['target_date']}", bg=CARD_BG,
                     fg=MUTED, font=("Malgun Gothic", 9)).pack(side="left", padx=10)

        if goal["description"]:
            tk.Label(inner, text=goal["description"], bg=CARD_BG, fg=MUTED,
                     font=("Malgun Gothic", 9), wraplength=320,
                     justify="left").pack(anchor="w", pady=(2, 6))

        # 진행률
        pr = tk.Frame(inner, bg=CARD_BG)
        pr.pack(fill="x", pady=(4, 4))
        tk.Label(pr, text=f"진행률: {goal['progress']}%", bg=CARD_BG, fg=FG,
                 font=("Malgun Gothic", 10, "bold")).pack(side="left")
        bar_bg = tk.Frame(inner, bg=SOFT, height=10)
        bar_bg.pack(fill="x", pady=(2, 8))
        fill_w = max(1, int(goal["progress"]))
        fill = tk.Frame(bar_bg, bg=goal["color"], height=10)
        fill.place(relwidth=fill_w / 100, relheight=1)

        # 진행률 조절 + 삭제
        btns = tk.Frame(inner, bg=CARD_BG)
        btns.pack(fill="x")
        for delta, label in [(-10, "-10"), (-5, "-5"), (+5, "+5"), (+10, "+10"), (100, "완료")]:
            tk.Button(btns, text=label, bg=SOFT, fg=FG, relief="flat",
                      font=("Malgun Gothic", 9), padx=8,
                      command=lambda d=delta, gid=goal["id"], cur=goal["progress"]:
                      self.adjust_goal(gid, cur, d)).pack(side="left", padx=2)
        tk.Button(btns, text="삭제", bg=CARD_BG, fg=DANGER, relief="flat",
                  font=("Malgun Gothic", 9),
                  command=lambda gid=goal["id"]: self.delete_goal(gid)).pack(side="right")

    def adjust_goal(self, gid, current, delta):
        if delta == 100:
            new = 100
        else:
            new = current + delta
        self.db.update_goal_progress(gid, new)
        self.refresh_goal()
        self.refresh_dashboard()

    def delete_goal(self, gid):
        if messagebox.askyesno("삭제 확인", "이 목표를 삭제할까요?"):
            self.db.delete_goal(gid)
            self.refresh_goal()
            self.refresh_dashboard()

    # ---- 오늘 할 일 ----
    def _build_todo(self):
        frame = self.sub_todo
        form = tk.LabelFrame(frame, text="새 할 일 추가", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=8, bd=1, relief="solid")
        form.pack(fill="x", padx=14, pady=8)

        tk.Label(form, text="날짜", bg=BG).grid(row=0, column=0, padx=4)
        self.td_date = tk.Entry(form, width=12)
        self.td_date.insert(0, date.today().strftime("%Y-%m-%d"))
        self.td_date.grid(row=0, column=1, padx=4)
        tk.Label(form, text="제목", bg=BG).grid(row=0, column=2, padx=4)
        self.td_title = tk.Entry(form, width=30)
        self.td_title.grid(row=0, column=3, padx=4)
        tk.Label(form, text="우선순위", bg=BG).grid(row=0, column=4, padx=4)
        self.td_pri = ttk.Combobox(form, values=["high", "normal", "low"],
                                    width=8, state="readonly")
        self.td_pri.set("normal")
        self.td_pri.grid(row=0, column=5, padx=4)
        tk.Label(form, text="설명", bg=BG).grid(row=1, column=0, padx=4, pady=(6, 0))
        self.td_desc = tk.Entry(form, width=60)
        self.td_desc.grid(row=1, column=1, columnspan=4, padx=4, pady=(6, 0), sticky="we")
        ttk.Button(form, text="추가", command=self.add_todo).grid(
            row=1, column=5, padx=4, pady=(6, 0), sticky="we")

        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=14, pady=8)
        cols = ("id", "done", "date", "priority", "title", "description")
        headers = ("ID", "완료", "날짜", "우선순위", "제목", "설명")
        widths = (40, 60, 100, 90, 220, 400)
        self.td_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.td_tree.heading(c, text=h)
            self.td_tree.column(c, width=w, anchor="w")
        self.td_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.td_tree.yview)
        sb.pack(side="right", fill="y")
        self.td_tree.configure(yscrollcommand=sb.set)

        tb = tk.Frame(frame, bg=BG)
        tb.pack(fill="x", padx=14, pady=(0, 8))
        ttk.Button(tb, text="완료 체크 토글",
                   command=self.toggle_todo).pack(side="left", padx=4)
        ttk.Button(tb, text="선택 삭제",
                   command=self.delete_todo).pack(side="right")

    def add_todo(self):
        title = self.td_title.get().strip()
        if not title:
            return
        self.db.add_schedule(self.td_date.get(), title,
                              self.td_desc.get(), self.td_pri.get())
        self.td_title.delete(0, "end")
        self.td_desc.delete(0, "end")
        self.refresh_todo()
        self.refresh_dashboard()

    def toggle_todo(self):
        sel = self.td_tree.selection()
        if not sel:
            return
        sid = self.td_tree.item(sel[0])["values"][0]
        current = self.td_tree.item(sel[0])["values"][1] == "✅"
        self.db.toggle_schedule(sid, not current)
        self.refresh_todo()
        self.refresh_dashboard()

    def delete_todo(self):
        sel = self.td_tree.selection()
        if not sel:
            return
        sid = self.td_tree.item(sel[0])["values"][0]
        self.db.delete_schedule(sid)
        self.refresh_todo()
        self.refresh_dashboard()

    def refresh_todo(self):
        for i in self.td_tree.get_children():
            self.td_tree.delete(i)
        for s in self.db.get_schedules():
            self.td_tree.insert("", "end", values=(
                s["id"], "✅" if s["done"] else "⬜",
                s["date"], s["priority"],
                s["title"], s["description"] or ""
            ))

    # ==================== 뉴스 ====================
    def _build_news(self):
        frame = self.tab_news
        top = tk.Frame(frame, bg=BG)
        top.pack(fill="x", padx=20, pady=(18, 4))
        tk.Label(top, text="📰 주식 뉴스 타임라인", bg=BG, fg=PRIMARY,
                 font=("Malgun Gothic", 16, "bold")).pack(side="left")
        ttk.Button(top, text="🔄 보유종목 뉴스 업데이트",
                   command=self.update_news).pack(side="right")
        self.news_status = tk.Label(frame, text="뉴스를 업데이트하면 보유 종목별 최신 기사가 표시됩니다.",
                                     bg=BG, fg=MUTED,
                                     font=("Malgun Gothic", 9))
        self.news_status.pack(anchor="w", padx=20, pady=(0, 6))

        wrap = tk.Frame(frame, bg=BG)
        wrap.pack(fill="both", expand=True, padx=20, pady=4)
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.news_container = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=self.news_container, anchor="nw")
        self.news_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def update_news(self):
        self.news_status.config(text="뉴스 가져오는 중...")
        self.update_idletasks()

        def worker():
            stocks = self.db.get_stocks()
            all_items = []
            for s in stocks:
                items = fetch_stock_news(s["ticker"], limit=5)
                # 종목명 보강
                for it in items:
                    it["stock_name"] = s["name"] or s["ticker"]
                all_items.extend(items)
            # 시간 내림차순 정렬
            all_items.sort(key=lambda x: x.get("time") or "", reverse=True)

            def done():
                self._render_news(all_items)
                self.news_status.config(
                    text=f"총 {len(all_items)}개 기사 ({datetime.now().strftime('%H:%M')})")
            self.after(0, done)
        threading.Thread(target=worker, daemon=True).start()

    def _render_news(self, items):
        for w in self.news_container.winfo_children():
            w.destroy()
        if not items:
            tk.Label(self.news_container,
                     text="가져온 뉴스가 없습니다. 보유 종목을 먼저 등록하거나, "
                          "yfinance가 해당 티커의 뉴스를 제공하지 않을 수 있어요.",
                     bg=BG, fg=MUTED, wraplength=800,
                     font=("Malgun Gothic", 11)).pack(pady=30)
            return

        # 날짜별로 그룹
        groups = {}
        for it in items:
            day = (it.get("time") or "")[:10] or "기타"
            groups.setdefault(day, []).append(it)

        for day in sorted(groups.keys(), reverse=True):
            day_label = tk.Label(self.news_container, text=f"📅 {day}",
                                  bg=BG, fg=PRIMARY,
                                  font=("Malgun Gothic", 12, "bold"))
            day_label.pack(anchor="w", padx=6, pady=(10, 4))
            for it in groups[day]:
                self._make_news_card(it)

    def _make_news_card(self, item):
        card = tk.Frame(self.news_container, bg=CARD_BG, bd=0,
                        highlightthickness=1, highlightbackground=SOFT)
        card.pack(fill="x", padx=20, pady=3)
        bar = tk.Frame(card, bg=PRIMARY, width=4)
        bar.pack(side="left", fill="y")
        inner = tk.Frame(card, bg=CARD_BG)
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        title = tk.Label(inner, text=item.get("title", ""), bg=CARD_BG, fg=FG,
                         font=("Malgun Gothic", 11, "bold"),
                         wraplength=800, justify="left", cursor="hand2")
        title.pack(anchor="w")
        link = item.get("link")
        if link:
            title.bind("<Button-1>", lambda _, u=link: webbrowser.open(u))

        meta = tk.Frame(inner, bg=CARD_BG)
        meta.pack(fill="x", pady=(4, 0))
        tk.Label(meta, text=f"📈 {item.get('stock_name', item.get('ticker', ''))}",
                 bg=CARD_BG, fg=ACCENT,
                 font=("Malgun Gothic", 9, "bold")).pack(side="left")
        tk.Label(meta, text=f"  ·  {item.get('publisher', '')}", bg=CARD_BG, fg=MUTED,
                 font=("Malgun Gothic", 9)).pack(side="left")
        if item.get("time"):
            tk.Label(meta, text=f"  ·  {item['time']}", bg=CARD_BG, fg=MUTED,
                     font=("Malgun Gothic", 9)).pack(side="left")
        if link:
            tk.Label(meta, text="🔗 열기", bg=CARD_BG, fg=PRIMARY,
                     font=("Malgun Gothic", 9, "underline"),
                     cursor="hand2").pack(side="right")

    # ==================== 공통 ====================
    def refresh_all(self):
        self.refresh_ledger()
        self.refresh_deposit()
        self.refresh_stock()
        self.refresh_trade()
        self.refresh_asset()
        self.refresh_insurance()
        self.refresh_habit()
        self.refresh_goal()
        self.refresh_todo()
        self.refresh_dashboard()


if __name__ == "__main__":
    app = AssetManagerApp()
    app.mainloop()
