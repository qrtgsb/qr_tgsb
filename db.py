import sqlite3
from datetime import datetime
from geopy.distance import geodesic

DB_PATH = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            telegram_id INTEGER UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            latitude REAL,
            longitude REAL
        )
    """)

    # ✅ Добавляем колонку status, если её нет
    try:
        cursor.execute("ALTER TABLE attendance ADD COLUMN status TEXT")
    except sqlite3.OperationalError:
        pass  # колонка уже есть

    conn.commit()
    conn.close()

def get_employee_by_telegram_id(telegram_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, full_name FROM employees WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_employee_telegram_id(emp_id, telegram_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET telegram_id = ? WHERE emp_id = ?", (telegram_id, emp_id))
    conn.commit()
    conn.close()

def reset_all_telegram_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET telegram_id = NULL")
    conn.commit()
    conn.close()

def search_employees_by_name(name_query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, full_name FROM employees WHERE full_name LIKE ?", (f"%{name_query}%",))
    results = cursor.fetchall()
    conn.close()
    return results

def link_telegram_id(emp_id, tg_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET telegram_id = ? WHERE emp_id = ?", (tg_id, emp_id))
    conn.commit()
    conn.close()

# ✅ Теперь принимает статус
def mark_attendance(emp_id, lat, lon, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO attendance (emp_id, timestamp, latitude, longitude, status)
        VALUES (?, ?, ?, ?, ?)
    """, (emp_id, timestamp, lat, lon, status))
    conn.commit()
    conn.close()

def get_all_employees():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM employees")
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]

def get_employee_by_full_name(full_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, full_name FROM employees WHERE full_name = ?", (full_name,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_employee_name_by_id(emp_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM employees WHERE emp_id = ?", (emp_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_employee_by_name_like(name_query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, full_name FROM employees WHERE full_name LIKE ?", (f"%{name_query}%",))
    results = cursor.fetchall()
    conn.close()
    return [{"emp_id": row[0], "full_name": row[1]} for row in results]

def get_employee_by_id(emp_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, full_name, telegram_id FROM employees WHERE emp_id = ?", (emp_id,))
    result = cursor.fetchone()
    conn.close()
    return result

# ✅ Теперь возвращает status
def get_today_attendance():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT a.timestamp, a.latitude, a.longitude, a.status, e.full_name
        FROM attendance a
        JOIN employees e ON a.emp_id = e.emp_id
        WHERE DATE(a.timestamp) = ?
        ORDER BY a.timestamp ASC
    """, (today,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "timestamp": row[0],
            "latitude": row[1],
            "longitude": row[2],
            "status": row[3],
            "full_name": row[4]
        }
        for row in rows
    ]

# ✅ Геопроверка: расстояние между точками
def is_within_radius(user_location, center_location, radius_meters=500):
    distance = geodesic(user_location, center_location).meters
    return distance <= radius_meters
