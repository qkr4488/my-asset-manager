"""
database.py - SQLite 데이터베이스 관리 모듈
가계부 앱의 모든 데이터를 저장하고 관리합니다.
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path


def get_db_path():
    """데이터베이스 파일 경로를 반환합니다.
    사용자 홈 폴더에 저장하여 .exe로 빌드한 후에도 데이터가 유지되도록 합니다.
    """
    home = Path.home()
    app_dir = home / "MyAssetManager"
    app_dir.mkdir(exist_ok=True)
    return str(app_dir / "asset_manager.db")


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """모든 테이블을 생성합니다."""
        conn = self.get_connection()
        c = conn.cursor()

        # 수입/지출 거래내역
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,        -- 'income' 또는 'expense'
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 적금/예금
        c.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                deposit_type TEXT NOT NULL,    -- '적금' 또는 '예금'
                principal REAL NOT NULL,        -- 원금(예금) 또는 월 납입액(적금)
                interest_rate REAL NOT NULL,    -- 연이율 (%)
                period_months INTEGER NOT NULL, -- 기간(개월)
                compound_period INTEGER DEFAULT 12,  -- 연 복리 횟수
                start_date TEXT NOT NULL,
                tax_rate REAL DEFAULT 15.4,    -- 이자소득세율 (%)
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 보유 주식
        c.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                current_price REAL DEFAULT 0,
                currency TEXT DEFAULT 'KRW',
                last_updated TEXT,
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 기타 자산 (현금, 부동산 등)
        c.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,    -- '현금', '부동산', '암호화폐', '기타'
                value REAL NOT NULL,
                memo TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 일정/목표
        c.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'normal',  -- 'high', 'normal', 'low'
                done INTEGER DEFAULT 0,           -- 0: 미완료, 1: 완료
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
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
            INSERT INTO stocks (ticker, name, quantity, avg_price, current_price, currency, memo)
            VALUES (?,?,?,?,?,?,?)
        """, (ticker, name, quantity, avg_price, avg_price, currency, memo))
        conn.commit()
        conn.close()

    def get_stocks(self):
        conn = self.get_connection()
        rows = conn.execute("SELECT * FROM stocks ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_stock_price(self, sid, current_price):
        conn = self.get_connection()
        conn.execute(
            "UPDATE stocks SET current_price=?, last_updated=? WHERE id=?",
            (current_price, datetime.now().isoformat(timespec="seconds"), sid)
        )
        conn.commit()
        conn.close()

    def delete_stock(self, sid):
        conn = self.get_connection()
        conn.execute("DELETE FROM stocks WHERE id=?", (sid,))
        conn.commit()
        conn.close()

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

    # ===== 일정 =====
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
