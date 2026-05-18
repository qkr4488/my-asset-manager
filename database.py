"""
database.py - SQLite 데이터베이스 관리 모듈
"""
import sqlite3
import os
from datetime import datetime, date, timedelta
from pathlib import Path


def get_db_path():
    home = Path.home()
    app_dir = home / "MyAssetManager"
    app_dir.mkdir(exist_ok=True)
    return str(app_dir / "asset_manager.db")


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        self.init_database()
        self.migrate()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                deposit_type TEXT NOT NULL,
                principal REAL NOT NULL,
                interest_rate REAL NOT NULL,
                period_months INTEGER NOT NULL,
                compound_period INTEGER DEFAULT 12,
                start_date TEXT NOT NULL,
                tax_rate REAL DEFAULT 15.4,
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                current_price REAL DEFAULT 0,
                currency TEXT DEFAULT 'KRW',
                price_source TEXT DEFAULT 'manual',
                use_manual INTEGER DEFAULT 0,
                last_updated TEXT,
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                value REAL NOT NULL,
                memo TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'normal',
                done INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ===== 신규: 주식 매매 기록 =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS stock_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                name TEXT,
                trade_type TEXT NOT NULL,   -- 'buy' or 'sell'
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                fees REAL DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ===== 신규: 장기 목표 =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT '기타',
                target_date TEXT,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                color TEXT DEFAULT '#5cb85c',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ===== 신규: 습관 (갓생살기) =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon TEXT DEFAULT '✅',
                target_frequency TEXT DEFAULT 'daily',
                color TEXT DEFAULT '#5cb85c',
                active INTEGER DEFAULT 1,
                points INTEGER DEFAULT 10,
                category TEXT DEFAULT '일반',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                UNIQUE(habit_id, date)
            )
        """)

        conn.commit()
        conn.close()

    def migrate(self):
        """기존 DB에 새 컬럼이 없으면 추가합니다."""
        conn = self.get_connection()
        try:
            # stocks 테이블에 신규 컬럼 추가 (기존 DB 호환)
            cols = [r[1] for r in conn.execute("PRAGMA table_info(stocks)").fetchall()]
            if "price_source" not in cols:
                conn.execute("ALTER TABLE stocks ADD COLUMN price_source TEXT DEFAULT 'manual'")
            if "use_manual" not in cols:
                conn.execute("ALTER TABLE stocks ADD COLUMN use_manual INTEGER DEFAULT 0")
            conn.commit()
        except Exception as e:
            print(f"[migrate] {e}")
        finally:
            conn.close()

    # ===== 거래내역 =====
    def add_transaction(self, date, type_, category, amount, memo=""):
        conn = self.get_connection()
        conn.execute(
            "INSERT INTO transactions (date, type, category, amount, memo) VALUES (?,?,?,?,?)",
            (date, type_, category, amount, memo)
        )
        conn.commit()
        conn.close()

    def get_transactions(self, start_date=None, end_date=None):
        conn = self.get_connection()
        q = "SELECT * FROM transactions"
        params = []
        if start_date and end_date:
            q += " WHERE date BETWEEN ? AND ?"
            params = [start_date, end_date]
        q += " ORDER BY date DESC, id DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_transaction(self, tid):
        conn = self.get_connection()
        conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
        conn.commit()
        conn.close()

    def get_monthly_summary(self, year, month):
        conn = self.get_connection()
        prefix = f"{year:04d}-{month:02d}"
        rows = conn.execute(
            "SELECT type, SUM(amount) as total FROM transactions WHERE date LIKE ? GROUP BY type",
            (prefix + "%",)
        ).fetchall()
        conn.close()
        result = {"income": 0, "expense": 0}
        for r in rows:
            result[r["type"]] = r["total"] or 0
        return result

    # ===== 적금/예금 =====
    def add_deposit(self, name, deposit_type, principal, interest_rate,
                    period_months, start_date, tax_rate=15.4, compound_period=12, memo=""):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO deposits (name, deposit_type, principal, interest_rate,
                                  period_months, compound_period, start_date, tax_rate, memo)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (name, deposit_type, principal, interest_rate, period_months,
              compound_period, start_date, tax_rate, memo))
        conn.commit()
        conn.close()

    def get_deposits(self):
        conn = self.get_connection()
        rows = conn.execute("SELECT * FROM deposits ORDER BY start_date DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_deposit(self, did):
        conn = self.get_connection()
        conn.execute("DELETE FROM deposits WHERE id=?", (did,))
        conn.commit()
        conn.close()

    # ===== 주식 =====
    def add_stock(self, ticker, name, quantity, avg_price, currency="KRW", memo=""):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO stocks (ticker, name, quantity, avg_price, current_price,
                                currency, price_source, memo)
            VALUES (?,?,?,?,?,?,?,?)
        """, (ticker, name, quantity, avg_price, avg_price, currency, "manual", memo))
        conn.commit()
        conn.close()

    def get_stocks(self):
        conn = self.get_connection()
        rows = conn.execute("SELECT * FROM stocks ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_stock_price(self, sid, current_price, source="api", currency=None):
        conn = self.get_connection()
        if currency:
            conn.execute(
                "UPDATE stocks SET current_price=?, price_source=?, currency=?, last_updated=? WHERE id=?",
                (current_price, source, currency,
                 datetime.now().isoformat(timespec="seconds"), sid)
            )
        else:
            conn.execute(
                "UPDATE stocks SET current_price=?, price_source=?, last_updated=? WHERE id=?",
                (current_price, source,
                 datetime.now().isoformat(timespec="seconds"), sid)
            )
        conn.commit()
        conn.close()

    def toggle_stock_manual(self, sid, manual):
        conn = self.get_connection()
        conn.execute("UPDATE stocks SET use_manual=? WHERE id=?", (1 if manual else 0, sid))
        conn.commit()
        conn.close()

    def delete_stock(self, sid):
        conn = self.get_connection()
        conn.execute("DELETE FROM stocks WHERE id=?", (sid,))
        conn.commit()
        conn.close()

    # ===== 주식 매매 기록 =====
    def add_stock_trade(self, date, ticker, name, trade_type, quantity, price,
                         fees=0, realized_pnl=0, memo=""):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO stock_trades (date, ticker, name, trade_type, quantity,
                                       price, fees, realized_pnl, memo)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (date, ticker, name, trade_type, quantity, price, fees, realized_pnl, memo))
        conn.commit()
        conn.close()

    def get_stock_trades(self, year=None):
        conn = self.get_connection()
        if year:
            rows = conn.execute(
                "SELECT * FROM stock_trades WHERE date LIKE ? ORDER BY date DESC, id DESC",
                (f"{year}%",)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM stock_trades ORDER BY date DESC, id DESC"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_stock_trade(self, tid):
        conn = self.get_connection()
        conn.execute("DELETE FROM stock_trades WHERE id=?", (tid,))
        conn.commit()
        conn.close()

    def get_avg_buy_price(self, ticker):
        """해당 티커의 평균 매수가(매수만 집계)와 보유 수량을 반환"""
        conn = self.get_connection()
        rows = conn.execute(
            "SELECT trade_type, quantity, price FROM stock_trades WHERE ticker=? ORDER BY date, id",
            (ticker,)
        ).fetchall()
        conn.close()
        total_qty = 0.0
        total_cost = 0.0
        for r in rows:
            if r["trade_type"] == "buy":
                total_cost += r["quantity"] * r["price"]
                total_qty += r["quantity"]
            else:
                # 매도: 평균매수가로 차감
                if total_qty > 0:
                    avg = total_cost / total_qty
                    total_cost -= avg * r["quantity"]
                    total_qty -= r["quantity"]
        if total_qty <= 0:
            return 0.0, 0.0
        return total_cost / total_qty, total_qty

    def get_trade_summary(self, year=None):
        """실현손익 합계"""
        conn = self.get_connection()
        if year:
            row = conn.execute(
                "SELECT SUM(realized_pnl) as total FROM stock_trades WHERE trade_type='sell' AND date LIKE ?",
                (f"{year}%",)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT SUM(realized_pnl) as total FROM stock_trades WHERE trade_type='sell'"
            ).fetchone()
        conn.close()
        return row["total"] or 0

    # ===== 기타 자산 =====
    def add_asset(self, name, asset_type, value, memo=""):
        conn = self.get_connection()
        conn.execute(
            "INSERT INTO assets (name, asset_type, value, memo) VALUES (?,?,?,?)",
            (name, asset_type, value, memo)
        )
        conn.commit()
        conn.close()

    def get_assets(self):
        conn = self.get_connection()
        rows = conn.execute("SELECT * FROM assets ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_asset(self, aid, value):
        conn = self.get_connection()
        conn.execute(
            "UPDATE assets SET value=?, updated_at=? WHERE id=?",
            (value, datetime.now().isoformat(timespec="seconds"), aid)
        )
        conn.commit()
        conn.close()

    def delete_asset(self, aid):
        conn = self.get_connection()
        conn.execute("DELETE FROM assets WHERE id=?", (aid,))
        conn.commit()
        conn.close()

    # ===== 일정 (To-Do) =====
    def add_schedule(self, date, title, description="", priority="normal"):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO schedules (date, title, description, priority)
            VALUES (?,?,?,?)
        """, (date, title, description, priority))
        conn.commit()
        conn.close()

    def get_schedules(self, date=None):
        conn = self.get_connection()
        if date:
            rows = conn.execute(
                "SELECT * FROM schedules WHERE date=? ORDER BY priority, id",
                (date,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM schedules ORDER BY date DESC, priority, id"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def toggle_schedule(self, sid, done):
        conn = self.get_connection()
        conn.execute("UPDATE schedules SET done=? WHERE id=?", (1 if done else 0, sid))
        conn.commit()
        conn.close()

    def delete_schedule(self, sid):
        conn = self.get_connection()
        conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
        conn.commit()
        conn.close()

    # ===== 장기 목표 =====
    def add_goal(self, title, description="", category="기타",
                 target_date=None, color="#5cb85c"):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO goals (title, description, category, target_date, color)
            VALUES (?,?,?,?,?)
        """, (title, description, category, target_date, color))
        conn.commit()
        conn.close()

    def get_goals(self, status=None):
        conn = self.get_connection()
        if status:
            rows = conn.execute(
                "SELECT * FROM goals WHERE status=? ORDER BY id DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM goals ORDER BY status, id DESC"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_goal_progress(self, gid, progress):
        conn = self.get_connection()
        progress = max(0, min(100, int(progress)))
        status = "completed" if progress >= 100 else "active"
        conn.execute(
            "UPDATE goals SET progress=?, status=? WHERE id=?",
            (progress, status, gid)
        )
        conn.commit()
        conn.close()

    def delete_goal(self, gid):
        conn = self.get_connection()
        conn.execute("DELETE FROM goals WHERE id=?", (gid,))
        conn.commit()
        conn.close()

    # ===== 습관 =====
    def add_habit(self, name, icon="✅", color="#5cb85c", points=10,
                  category="일반", target_frequency="daily"):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO habits (name, icon, color, points, category, target_frequency)
            VALUES (?,?,?,?,?,?)
        """, (name, icon, color, points, category, target_frequency))
        conn.commit()
        conn.close()

    def get_habits(self, active_only=True):
        conn = self.get_connection()
        if active_only:
            rows = conn.execute(
                "SELECT * FROM habits WHERE active=1 ORDER BY id"
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM habits ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_habit(self, hid):
        conn = self.get_connection()
        conn.execute("DELETE FROM habits WHERE id=?", (hid,))
        conn.execute("DELETE FROM habit_logs WHERE habit_id=?", (hid,))
        conn.commit()
        conn.close()

    def toggle_habit_log(self, habit_id, date_str):
        """체크 토글, 결과(현재 체크 여부) 반환"""
        conn = self.get_connection()
        existing = conn.execute(
            "SELECT id FROM habit_logs WHERE habit_id=? AND date=?",
            (habit_id, date_str)
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM habit_logs WHERE id=?", (existing["id"],))
            checked = False
        else:
            conn.execute(
                "INSERT INTO habit_logs (habit_id, date) VALUES (?,?)",
                (habit_id, date_str)
            )
            checked = True
        conn.commit()
        conn.close()
        return checked

    def get_habit_logs(self, habit_id, days=30):
        """최근 N일치 로그 (집합)"""
        conn = self.get_connection()
        cutoff = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT date FROM habit_logs WHERE habit_id=? AND date>=?",
            (habit_id, cutoff)
        ).fetchall()
        conn.close()
        return set(r["date"] for r in rows)

    def calculate_streak(self, habit_id):
        """현재 연속 일수"""
        logs = self.get_habit_logs(habit_id, days=365)
        if not logs:
            return 0
        streak = 0
        d = date.today()
        # 오늘 체크 안 했으면 어제부터 카운트
        if d.strftime("%Y-%m-%d") not in logs:
            d -= timedelta(days=1)
        while d.strftime("%Y-%m-%d") in logs:
            streak += 1
            d -= timedelta(days=1)
        return streak

    def get_today_points(self, date_str=None):
        """오늘 획득 포인트"""
        date_str = date_str or date.today().strftime("%Y-%m-%d")
        conn = self.get_connection()
        row = conn.execute("""
            SELECT SUM(h.points) as total
            FROM habit_logs l JOIN habits h ON l.habit_id = h.id
            WHERE l.date=?
        """, (date_str,)).fetchone()
        conn.close()
        return row["total"] or 0

    def get_total_points(self):
        conn = self.get_connection()
        row = conn.execute("""
            SELECT SUM(h.points) as total
            FROM habit_logs l JOIN habits h ON l.habit_id = h.id
        """).fetchone()
        conn.close()
        return row["total"] or 0
        conn = self.get_connection()
        conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
        conn.commit()
        conn.close()
