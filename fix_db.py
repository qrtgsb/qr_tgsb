import sqlite3

conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE employees ADD COLUMN telegram_id INTEGER")
    conn.commit()
    print("✅ Столбец telegram_id добавлен.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Ошибка: {e}")

conn.close()
