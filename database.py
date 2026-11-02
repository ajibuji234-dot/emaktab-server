import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "emaktab.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                frequency TEXT DEFAULT 'daily',
                is_active INTEGER DEFAULT 1,
                last_run TEXT,
                last_status TEXT DEFAULT 'Kutilmoqda',
                last_message TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                account_login TEXT,
                account_name TEXT,
                status TEXT NOT NULL,
                message TEXT,
                executed_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Standart sozlamalarni kiritish
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('schedule_time', '08:30')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('schedule_time_second', '18:00')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_run_enabled', '1')")
        conn.commit()

def get_accounts(active_only=False):
    with get_connection() as conn:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM accounts WHERE is_active = 1 ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM accounts ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_account(account_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_account(full_name, login, password, frequency='daily'):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO accounts (full_name, login, password, frequency, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (full_name.strip(), login.strip(), password.strip(), frequency, now))
        conn.commit()
        return cursor.lastrowid

def update_account(account_id, full_name, login, password=None, frequency='daily'):
    with get_connection() as conn:
        cursor = conn.cursor()
        if password and password.strip():
            cursor.execute("""
                UPDATE accounts 
                SET full_name = ?, login = ?, password = ?, frequency = ?
                WHERE id = ?
            """, (full_name.strip(), login.strip(), password.strip(), frequency, account_id))
        else:
            cursor.execute("""
                UPDATE accounts 
                SET full_name = ?, login = ?, frequency = ?
                WHERE id = ?
            """, (full_name.strip(), login.strip(), frequency, account_id))
        conn.commit()

def delete_account(account_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        cursor.execute("DELETE FROM logs WHERE account_id = ?", (account_id,))
        conn.commit()

def toggle_account_status(account_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET is_active = 1 - is_active WHERE id = ?", (account_id,))
        conn.commit()

def update_account_stats(account_id, status, message):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if status == 'success':
            cursor.execute("""
                UPDATE accounts 
                SET last_run = ?, last_status = 'Muvaffaqiyatli', last_message = ?, success_count = success_count + 1
                WHERE id = ?
            """, (now, message, account_id))
        else:
            cursor.execute("""
                UPDATE accounts 
                SET last_run = ?, last_status = 'Xatolik', last_message = ?, failure_count = failure_count + 1
                WHERE id = ?
            """, (now, message, account_id))
        conn.commit()

def add_log(account_id, account_login, account_name, status, message):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO logs (account_id, account_login, account_name, status, message, executed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (account_id, account_login, account_name, status, message, now))
        conn.commit()

def get_logs(limit=100):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

def clear_logs():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")
        conn.commit()

def get_stats():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        total_accounts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE is_active = 1")
        active_accounts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM logs WHERE status = 'success'")
        total_success = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM logs WHERE status = 'error'")
        total_errors = cursor.fetchone()[0]
        
        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "total_success": total_success,
            "total_errors": total_errors
        }

def get_settings():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in cursor.fetchall()}

def update_setting(key, value):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
