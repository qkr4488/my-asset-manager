"""
app.py - 내 자산 관리자 (가계부 + 적금/예금 + 주식 + 일정)
실행: python app.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import threading

from database import Database
from finance import (
    compound_deposit, compound_savings, calculate_deposit,
    maturity_date, fetch_stock_price,
)

# ====== 색상 테마 ======
BG = "#f4f6fb"
PRIMARY = "#2c5fb3"
ACCENT = "#5cb85c"
DANGER = "#d9534f"
FG = "#1a2540"
MUTED = "#7a8aa3"


def won(n):
    """숫자를 한국 원화 형식 문자열로 변환"""
    try:
        return f"{n:,.0f}원"
    except Exception:
        return str(n)


class AssetManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("내 자산 관리자 - My Asset Manager")
        self.geometry("1100x720")
        self.configure(bg=BG)
        self.minsize(950, 640)

        self.db = Database()

        self._setup_style()
        self._build_ui()
        self.refresh_all()

    # ---------- 스타일 ----------
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10),
                        font=("Malgun Gothic", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", PRIMARY)],
                  foreground=[("selected", "white")])
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG,
                        font=("Malgun Gothic", 10))
        style.configure("Header.TLabel", font=("Malgun Gothic", 16, "bold"),
                        foreground=PRIMARY, background=BG)
        style.configure("Sub.TLabel", font=("Malgun Gothic", 11, "bold"),
                        foreground=FG, background=BG)
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("TButton", font=("Malgun Gothic", 10), padding=6)
        style.configure("Primary.TButton", foreground="white",
                        background=PRIMARY, padding=8)
        style.map("Primary.TButton",
                  background=[("active", "#214f96")])
        style.configure("Treeview", font=("Malgun Gothic", 10), rowheight=26)
        style.configure("Treeview.Heading", font=("Malgun Gothic", 10, "bold"))

    # ---------- UI ----------
    def _build_ui(self):
        # 상단 타이틀
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=20, pady=(16, 6))
        tk.Label(top, text="💰 내 자산 관리자", bg=BG, fg=PRIMARY,
                 font=("Malgun Gothic", 18, "bold")).pack(side="left")
        self.summary_label = tk.Label(top, text="", bg=BG, fg=MUTED,
                                      font=("Malgun Gothic", 11))
        self.summary_label.pack(side="right")

        # 탭
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_dashboard = ttk.Frame(self.nb)
        self.tab_ledger = ttk.Frame(self.nb)
        self.tab_deposit = ttk.Frame(self.nb)
        self.tab_stock = ttk.Frame(self.nb)
        self.tab_asset = ttk.Frame(self.nb)
        self.tab_schedule = ttk.Frame(self.nb)

        self.nb.add(self.tab_dashboard, text="📊 대시보드")
        self.nb.add(self.tab_ledger, text="💳 가계부")
        self.nb.add(self.tab_deposit, text="🏦 적금/예금")
        self.nb.add(self.tab_stock, text="📈 주식")
        self.nb.add(self.tab_asset, text="🏠 기타 자산")
        self.nb.add(self.tab_schedule, text="📅 일정/목표")

        self._build_dashboard()
        self._build_ledger()
        self._build_deposit()
        self._build_stock()
        self._build_asset()
        self._build_schedule()

    # ========== 대시보드 ==========
    def _build_dashboard(self):
        frame = self.tab_dashboard
        ttk.Label(frame, text="자산 현황 요약", style="Header.TLabel").pack(
            anchor="w", padx=20, pady=(20, 10))

        # 카드 영역
        cards = tk.Frame(frame, bg=BG)
        cards.pack(fill="x", padx=20, pady=10)

        self.card_total = self._make_card(cards, "총 자산", "0원", PRIMARY)
        self.card_total.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        self.card_cash = self._make_card(cards, "현금/기타", "0원", "#4a90e2")
        self.card_cash.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.card_deposit = self._make_card(cards, "적금/예금 (현재가치)", "0원", ACCENT)
        self.card_deposit.grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        self.card_stock = self._make_card(cards, "주식 평가액", "0원", "#e67e22")
        self.card_stock.grid(row=0, column=3, padx=8, pady=8, sticky="ew")

        for c in range(4):
            cards.columnconfigure(c, weight=1)

        # 이번 달 요약
        ttk.Label(frame, text="이번 달 수입/지출", style="Sub.TLabel").pack(
            anchor="w", padx=20, pady=(20, 6))
        month_box = tk.Frame(frame, bg="white", relief="flat", bd=0)
        month_box.pack(fill="x", padx=20, pady=4)
        self.lbl_income = tk.Label(month_box, text="수입: 0원",
                                   bg="white", fg=ACCENT,
                                   font=("Malgun Gothic", 12, "bold"),
                                   padx=20, pady=14)
        self.lbl_income.pack(side="left")
        self.lbl_expense = tk.Label(month_box, text="지출: 0원",
                                    bg="white", fg=DANGER,
                                    font=("Malgun Gothic", 12, "bold"),
                                    padx=20, pady=14)
        self.lbl_expense.pack(side="left")
        self.lbl_balance = tk.Label(month_box, text="잔액: 0원",
                                    bg="white", fg=PRIMARY,
                                    font=("Malgun Gothic", 12, "bold"),
                                    padx=20, pady=14)
        self.lbl_balance.pack(side="left")

        # 오늘/내일 일정
        ttk.Label(frame, text="오늘 / 내일 할 일", style="Sub.TLabel").pack(
            anchor="w", padx=20, pady=(20, 6))
        sch_box = tk.Frame(frame, bg="white")
        sch_box.pack(fill="both", expand=True, padx=20, pady=4)
        self.dash_schedule = tk.Text(sch_box, height=10,
                                     font=("Malgun Gothic", 10),
                                     bg="white", fg=FG, relief="flat",
                                     padx=14, pady=10)
        self.dash_schedule.pack(fill="both", expand=True)
        self.dash_schedule.configure(state="disabled")

    def _make_card(self, parent, title, value, color):
        f = tk.Frame(parent, bg="white", bd=0, highlightthickness=0)
        bar = tk.Frame(f, bg=color, height=4)
        bar.pack(fill="x")
        inner = tk.Frame(f, bg="white")
        inner.pack(fill="both", expand=True, padx=16, pady=14)
        tk.Label(inner, text=title, bg="white", fg=MUTED,
                 font=("Malgun Gothic", 10)).pack(anchor="w")
        val = tk.Label(inner, text=value, bg="white", fg=FG,
                       font=("Malgun Gothic", 16, "bold"))
        val.pack(anchor="w", pady=(6, 0))
        f.value_label = val
        return f

    def refresh_dashboard(self):
        # 자산 합계
        assets = self.db.get_assets()
        cash_total = sum(a["value"] for a in assets)

        # 적금/예금 만기 가치
        deposits = self.db.get_deposits()
        deposit_total = 0
        for d in deposits:
            calc = calculate_deposit(d)
            deposit_total += calc["total"]

        # 주식 평가액
        stocks = self.db.get_stocks()
        stock_total = sum((s["current_price"] or s["avg_price"]) * s["quantity"]
                          for s in stocks)

        total = cash_total + deposit_total + stock_total

        self.card_total.value_label.config(text=won(total))
        self.card_cash.value_label.config(text=won(cash_total))
        self.card_deposit.value_label.config(text=won(deposit_total))
        self.card_stock.value_label.config(text=won(stock_total))

        # 이번 달 수입/지출
        now = datetime.now()
        s = self.db.get_monthly_summary(now.year, now.month)
        self.lbl_income.config(text=f"수입: {won(s['income'])}")
        self.lbl_expense.config(text=f"지출: {won(s['expense'])}")
        self.lbl_balance.config(text=f"잔액: {won(s['income'] - s['expense'])}")

        # 일정
        today = date.today().strftime("%Y-%m-%d")
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        today_sch = self.db.get_schedules(today)
        tomorrow_sch = self.db.get_schedules(tomorrow)

        self.dash_schedule.configure(state="normal")
        self.dash_schedule.delete("1.0", "end")
        self.dash_schedule.insert("end", f"[오늘 {today}]\n", "h")
        if today_sch:
            for s in today_sch:
                mark = "✅" if s["done"] else "⬜"
                self.dash_schedule.insert(
                    "end", f"  {mark} {s['title']}  ({s['priority']})\n")
        else:
            self.dash_schedule.insert("end", "  (등록된 일정 없음)\n", "muted")

        self.dash_schedule.insert("end", f"\n[내일 {tomorrow}]\n", "h")
        if tomorrow_sch:
            for s in tomorrow_sch:
                mark = "✅" if s["done"] else "⬜"
                self.dash_schedule.insert(
                    "end", f"  {mark} {s['title']}  ({s['priority']})\n")
        else:
            self.dash_schedule.insert("end", "  (등록된 일정 없음)\n", "muted")

        self.dash_schedule.tag_config("h", font=("Malgun Gothic", 11, "bold"),
                                     foreground=PRIMARY)
        self.dash_schedule.tag_config("muted", foreground=MUTED)
        self.dash_schedule.configure(state="disabled")

        self.summary_label.config(text=f"총 자산: {won(total)}")

    # ========== 가계부 ==========
    def _build_ledger(self):
        frame = self.tab_ledger
        ttk.Label(frame, text="가계부 - 수입/지출 관리",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(20, 10))

        # 입력 폼
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

        tk.Label(form, text="메모", bg=BG).grid(row=1, column=0, sticky="w",
                                                padx=4, pady=(8, 0))
        self.tx_memo = tk.Entry(form, width=60)
        self.tx_memo.grid(row=1, column=1, columnspan=5, padx=4,
                          pady=(8, 0), sticky="we")

        ttk.Button(form, text="추가", style="Primary.TButton",
                   command=self.add_transaction).grid(
            row=1, column=6, columnspan=2, padx=4, pady=(8, 0), sticky="we")

        # 거래 목록
        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("id", "date", "type", "category", "amount", "memo")
        self.tx_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        widths = (50, 100, 80, 100, 120, 400)
        for c, w in zip(cols, widths):
            self.tx_tree.heading(c, text=c.upper())
            self.tx_tree.column(c, width=w, anchor="w")
        self.tx_tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.tx_tree.yview)
        sb.pack(side="right", fill="y")
        self.tx_tree.configure(yscrollcommand=sb.set)

        ttk.Button(frame, text="선택 삭제", command=self.delete_transaction).pack(
            anchor="e", padx=20, pady=(0, 12))

    def add_transaction(self):
        try:
            amount = float(self.tx_amount.get().replace(",", ""))
            self.db.add_transaction(
                self.tx_date.get(), self.tx_type.get(),
                self.tx_cat.get(), amount, self.tx_memo.get()
            )
            self.tx_amount.delete(0, "end")
            self.tx_memo.delete(0, "end")
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

    def refresh_ledger(self):
        for i in self.tx_tree.get_children():
            self.tx_tree.delete(i)
        for r in self.db.get_transactions():
            self.tx_tree.insert("", "end", values=(
                r["id"], r["date"], r["type"], r["category"],
                won(r["amount"]), r["memo"] or ""
            ))

    # ========== 적금/예금 ==========
    def _build_deposit(self):
        frame = self.tab_deposit
        ttk.Label(frame, text="적금 / 예금 (복리 계산)",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(20, 10))

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
            row2, values=[("12 (월)", 12), ("4 (분기)", 4),
                          ("2 (반기)", 2), ("1 (연)", 1)],
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
        ttk.Button(btn_row, text="계산만 보기", command=self.preview_deposit).pack(
            side="left", padx=4)
        ttk.Button(btn_row, text="등록", style="Primary.TButton",
                   command=self.add_deposit).pack(side="left", padx=4)

        self.dp_preview = tk.Label(form, text="", bg=BG, fg=PRIMARY,
                                    font=("Malgun Gothic", 10, "bold"),
                                    pady=6)
        self.dp_preview.pack(anchor="w")

        # 목록
        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("id", "name", "type", "principal", "rate", "period",
                "start", "maturity", "total", "interest")
        headers = ("ID", "상품명", "종류", "원금/월납", "이율", "기간(월)",
                   "시작일", "만기일", "만기금액(세후)", "세후이자")
        self.dp_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h in zip(cols, headers):
            self.dp_tree.heading(c, text=h)
            self.dp_tree.column(c, width=100, anchor="w")
        self.dp_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.dp_tree.yview)
        sb.pack(side="right", fill="y")
        self.dp_tree.configure(yscrollcommand=sb.set)

        ttk.Button(frame, text="선택 삭제", command=self.delete_deposit).pack(
            anchor="e", padx=20, pady=(0, 12))

    def _parse_compound(self):
        val = self.dp_compound.get()
        # "12 (월)" 같은 형태에서 숫자만 추출
        try:
            return int(val.split()[0])
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
            self.dp_name.delete(0, "end")
            self.dp_principal.delete(0, "end")
            self.dp_rate.delete(0, "end")
            self.dp_period.delete(0, "end")
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
            mdate = maturity_date(d["start_date"], d["period_months"])
            self.dp_tree.insert("", "end", values=(
                d["id"], d["name"], d["deposit_type"],
                won(d["principal"]), f"{d['interest_rate']}%",
                d["period_months"], d["start_date"], mdate,
                won(calc["total"]), won(calc["interest_net"])
            ))

    # ========== 주식 ==========
    def _build_stock(self):
        frame = self.tab_stock
        ttk.Label(frame, text="주식 포트폴리오",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(20, 10))

        info = tk.Label(frame, text="💡 한국 주식은 종목코드 뒤에 .KS(코스피) 또는 .KQ(코스닥)를 붙이세요. "
                                    "예: 삼성전자 → 005930.KS",
                        bg=BG, fg=MUTED, font=("Malgun Gothic", 9))
        info.pack(anchor="w", padx=20)

        form = tk.LabelFrame(frame, text="새 종목 추가", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=10, bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="티커", bg=BG).grid(row=0, column=0, padx=4)
        self.st_ticker = tk.Entry(form, width=14)
        self.st_ticker.grid(row=0, column=1, padx=4)
        tk.Label(form, text="종목명", bg=BG).grid(row=0, column=2, padx=4)
        self.st_name = tk.Entry(form, width=18)
        self.st_name.grid(row=0, column=3, padx=4)
        tk.Label(form, text="수량", bg=BG).grid(row=0, column=4, padx=4)
        self.st_qty = tk.Entry(form, width=10)
        self.st_qty.grid(row=0, column=5, padx=4)
        tk.Label(form, text="평균매수가", bg=BG).grid(row=0, column=6, padx=4)
        self.st_avg = tk.Entry(form, width=12)
        self.st_avg.grid(row=0, column=7, padx=4)
        tk.Label(form, text="통화", bg=BG).grid(row=0, column=8, padx=4)
        self.st_currency = ttk.Combobox(form, values=["KRW", "USD"],
                                         width=6, state="readonly")
        self.st_currency.set("KRW")
        self.st_currency.grid(row=0, column=9, padx=4)
        ttk.Button(form, text="추가", style="Primary.TButton",
                   command=self.add_stock).grid(row=0, column=10, padx=8)

        toolbar = tk.Frame(frame, bg=BG)
        toolbar.pack(fill="x", padx=20, pady=4)
        ttk.Button(toolbar, text="🔄 시세 일괄 업데이트 (API)",
                   command=self.update_all_prices).pack(side="left")
        self.st_status = tk.Label(toolbar, text="", bg=BG, fg=MUTED,
                                   font=("Malgun Gothic", 9))
        self.st_status.pack(side="left", padx=10)
        ttk.Button(toolbar, text="선택 삭제",
                   command=self.delete_stock).pack(side="right")
        ttk.Button(toolbar, text="선택 가격 수동 변경",
                   command=self.manual_update_price).pack(side="right", padx=6)

        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("id", "ticker", "name", "qty", "avg", "current",
                "value", "pnl", "pnl_pct", "updated")
        headers = ("ID", "티커", "종목명", "수량", "평균매수가", "현재가",
                   "평가액", "손익", "수익률", "업데이트")
        widths = (40, 90, 130, 70, 90, 90, 110, 110, 80, 130)
        self.st_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.st_tree.heading(c, text=h)
            self.st_tree.column(c, width=w, anchor="w")
        self.st_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.st_tree.yview)
        sb.pack(side="right", fill="y")
        self.st_tree.configure(yscrollcommand=sb.set)

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
        dlg.geometry("260x110")
        tk.Label(dlg, text="새로운 현재가:").pack(pady=10)
        e = tk.Entry(dlg)
        e.pack()

        def save():
            try:
                self.db.update_stock_price(sid, float(e.get().replace(",", "")))
                dlg.destroy()
                self.refresh_stock()
                self.refresh_dashboard()
            except Exception as ex:
                messagebox.showerror("오류", str(ex))

        ttk.Button(dlg, text="저장", command=save).pack(pady=8)

    def update_all_prices(self):
        self.st_status.config(text="시세 가져오는 중... (yfinance)")
        self.update_idletasks()

        def worker():
            stocks = self.db.get_stocks()
            ok = fail = 0
            for s in stocks:
                price = fetch_stock_price(s["ticker"])
                if price:
                    self.db.update_stock_price(s["id"], price)
                    ok += 1
                else:
                    fail += 1

            def done():
                self.st_status.config(
                    text=f"업데이트 완료: 성공 {ok}건, 실패 {fail}건")
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
        for s in self.db.get_stocks():
            cur = s["current_price"] or s["avg_price"]
            value = cur * s["quantity"]
            cost = s["avg_price"] * s["quantity"]
            pnl = value - cost
            pct = (pnl / cost * 100) if cost else 0
            self.st_tree.insert("", "end", values=(
                s["id"], s["ticker"], s["name"], s["quantity"],
                won(s["avg_price"]), won(cur), won(value),
                won(pnl), f"{pct:+.2f}%",
                s["last_updated"] or "-"
            ))

    # ========== 기타 자산 ==========
    def _build_asset(self):
        frame = self.tab_asset
        ttk.Label(frame, text="기타 자산 (현금, 부동산 등)",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(20, 10))

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
        ttk.Button(form, text="추가", style="Primary.TButton",
                   command=self.add_asset).grid(row=0, column=8, padx=8)

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

        toolbar = tk.Frame(frame, bg=BG)
        toolbar.pack(fill="x", padx=20, pady=(0, 12))
        ttk.Button(toolbar, text="선택 금액 수정",
                   command=self.update_asset).pack(side="right", padx=6)
        ttk.Button(toolbar, text="선택 삭제",
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
        dlg.geometry("260x110")
        tk.Label(dlg, text="새로운 평가액:").pack(pady=10)
        e = tk.Entry(dlg)
        e.pack()

        def save():
            try:
                self.db.update_asset(aid, float(e.get().replace(",", "")))
                dlg.destroy()
                self.refresh_asset()
                self.refresh_dashboard()
            except Exception as ex:
                messagebox.showerror("오류", str(ex))
        ttk.Button(dlg, text="저장", command=save).pack(pady=8)

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

    # ========== 일정 ==========
    def _build_schedule(self):
        frame = self.tab_schedule
        ttk.Label(frame, text="일정 / 목표 관리",
                  style="Header.TLabel").pack(anchor="w", padx=20, pady=(20, 10))

        form = tk.LabelFrame(frame, text="새 일정 추가", bg=BG, fg=FG,
                              font=("Malgun Gothic", 10, "bold"),
                              padx=10, pady=10, bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=6)

        tk.Label(form, text="날짜", bg=BG).grid(row=0, column=0, padx=4)
        self.sc_date = tk.Entry(form, width=12)
        self.sc_date.insert(0, (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"))
        self.sc_date.grid(row=0, column=1, padx=4)

        tk.Label(form, text="제목", bg=BG).grid(row=0, column=2, padx=4)
        self.sc_title = tk.Entry(form, width=30)
        self.sc_title.grid(row=0, column=3, padx=4)

        tk.Label(form, text="우선순위", bg=BG).grid(row=0, column=4, padx=4)
        self.sc_pri = ttk.Combobox(form, values=["high", "normal", "low"],
                                    width=8, state="readonly")
        self.sc_pri.set("normal")
        self.sc_pri.grid(row=0, column=5, padx=4)

        tk.Label(form, text="설명", bg=BG).grid(row=1, column=0, padx=4,
                                                 pady=(8, 0))
        self.sc_desc = tk.Entry(form, width=70)
        self.sc_desc.grid(row=1, column=1, columnspan=4, padx=4,
                          pady=(8, 0), sticky="we")
        ttk.Button(form, text="추가", style="Primary.TButton",
                   command=self.add_schedule).grid(row=1, column=5,
                                                    padx=4, pady=(8, 0),
                                                    sticky="we")

        list_frame = tk.Frame(frame, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("id", "done", "date", "priority", "title", "description")
        headers = ("ID", "완료", "날짜", "우선순위", "제목", "설명")
        widths = (40, 60, 100, 90, 220, 400)
        self.sc_tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            self.sc_tree.heading(c, text=h)
            self.sc_tree.column(c, width=w, anchor="w")
        self.sc_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.sc_tree.yview)
        sb.pack(side="right", fill="y")
        self.sc_tree.configure(yscrollcommand=sb.set)

        toolbar = tk.Frame(frame, bg=BG)
        toolbar.pack(fill="x", padx=20, pady=(0, 12))
        ttk.Button(toolbar, text="완료 체크 토글",
                   command=self.toggle_schedule).pack(side="left", padx=4)
        ttk.Button(toolbar, text="선택 삭제",
                   command=self.delete_schedule).pack(side="right")

    def add_schedule(self):
        title = self.sc_title.get().strip()
        if not title:
            messagebox.showwarning("입력 필요", "제목을 입력해주세요.")
            return
        self.db.add_schedule(
            self.sc_date.get(), title,
            self.sc_desc.get(), self.sc_pri.get()
        )
        self.sc_title.delete(0, "end")
        self.sc_desc.delete(0, "end")
        self.refresh_schedule()
        self.refresh_dashboard()

    def toggle_schedule(self):
        sel = self.sc_tree.selection()
        if not sel:
            return
        sid = self.sc_tree.item(sel[0])["values"][0]
        current = self.sc_tree.item(sel[0])["values"][1] == "✅"
        self.db.toggle_schedule(sid, not current)
        self.refresh_schedule()
        self.refresh_dashboard()

    def delete_schedule(self):
        sel = self.sc_tree.selection()
        if not sel:
            return
        sid = self.sc_tree.item(sel[0])["values"][0]
        self.db.delete_schedule(sid)
        self.refresh_schedule()
        self.refresh_dashboard()

    def refresh_schedule(self):
        for i in self.sc_tree.get_children():
            self.sc_tree.delete(i)
        for s in self.db.get_schedules():
            self.sc_tree.insert("", "end", values=(
                s["id"], "✅" if s["done"] else "⬜",
                s["date"], s["priority"],
                s["title"], s["description"] or ""
            ))

    # ========== 공통 ==========
    def refresh_all(self):
        self.refresh_ledger()
        self.refresh_deposit()
        self.refresh_stock()
        self.refresh_asset()
        self.refresh_schedule()
        self.refresh_dashboard()


if __name__ == "__main__":
    app = AssetManagerApp()
    app.mainloop()
