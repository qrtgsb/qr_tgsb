from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from db import search_employees_by_name, link_telegram_id, get_employee_by_id
from location import request_location
from loader import dp
from aiogram.dispatcher.filters import Text


class AuthStates(StatesGroup):
    waiting_for_name = State()

def register(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "authorize")
    async def authorize_handler(callback_query: types.CallbackQuery):
        await callback_query.message.answer("Введите часть вашего имени для поиска:")
        await AuthStates.waiting_for_name.set()

    @dp.message_handler(state=AuthStates.waiting_for_name)
    async def search_employee(message: types.Message, state: FSMContext):
        matches = search_employees_by_name(message.text)
        if not matches:
            await message.answer("Сотрудник не найден. Попробуйте снова.")
            return


        keyboard = types.InlineKeyboardMarkup()
        for emp_id, full_name in matches:
            keyboard.add(types.InlineKeyboardButton(full_name, callback_data=f"select_{emp_id}"))
        await message.answer("Выберите себя из списка:", reply_markup=keyboard)

@dp.callback_query_handler(Text(startswith="select_"))
async def confirm_selection(callback: types.CallbackQuery):
    emp_id = callback.data.replace("select_", "")
    user_id = callback.from_user.id

    link_telegram_id(emp_id, user_id)
    employee = get_employee_by_id(emp_id)

    if not employee:
        await callback.message.answer("⚠️ Ошибка: сотрудник не найден в базе.")
        return

    full_name = employee[3]  # если full_name — 4-й столбец

    await callback.message.edit_reply_markup()
    await callback.message.answer(f"✅ Вы успешно авторизованы как {full_name}.")

    # ⬇️ Сразу предлагаем отправить геолокацию
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton(text="📍 Отправить геолокацию", request_location=True))

    await callback.message.answer("Пожалуйста, отправьте свою геолокацию для отметки входа:", reply_markup=keyboard)
это был auth.py
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

def mark_attendance(emp_id, lat, lon):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO attendance (emp_id, timestamp, latitude, longitude)
        VALUES (?, ?, ?, ?)
    """, (emp_id, timestamp, lat, lon))
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


def get_today_attendance():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT a.timestamp, a.latitude, a.longitude, e.full_name
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
            "full_name": row[3]
        }
        for row in rows
    ]

# ✅ Геопроверка: расстояние между точками
def is_within_radius(user_location, center_location, radius_meters=500):
    distance = geodesic(user_location, center_location).meters
    return distance <= radius_meters
это db.pu
from aiogram import types
from aiogram.dispatcher import FSMContext
from states import LocationStates
from db import (
    search_employees_by_name,
    update_employee_telegram_id,
    get_employee_by_telegram_id,
    mark_attendance,
    is_within_radius
)
from config import ADMIN_ID

OFFICE_LOCATION = (43.270355, 68.285416)  # координаты офиса

def register(dp):
    @dp.message_handler(state=LocationStates.waiting_for_employee_search)
    async def handle_name_search(message: types.Message, state: FSMContext):
        query = message.text.strip()
        matches = search_employees_by_name(query)

        if not matches:
            await message.answer("❌ Сотрудники не найдены. Попробуйте ещё раз.")
            return

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for emp_id, full_name in matches:
            keyboard.add(types.KeyboardButton(full_name))

        await state.update_data(matches={full_name: emp_id for emp_id, full_name in matches})
        await message.answer("Выберите себя из списка:", reply_markup=keyboard)
        await LocationStates.waiting_for_employee_selection.set()

    @dp.message_handler(state=LocationStates.waiting_for_employee_selection)
    async def handle_employee_selection(message: types.Message, state: FSMContext):
        def normalize(text):
            return text.strip().lower().replace("ё", "е")

        selected_name = normalize(message.text)
        data = await state.get_data()
        raw_matches = data.get("matches", {})

        matches = {normalize(name): emp_id for name, emp_id in raw_matches.items()}
        emp_id = matches.get(selected_name)

        if not emp_id:
            await message.answer("❌ Имя не распознано. Введите имя или фамилию заново:")
            await LocationStates.waiting_for_employee_search.set()
            return

        update_employee_telegram_id(emp_id, message.from_user.id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton("📍 Отправить геолокацию", request_location=True)
        keyboard.add(button)
        await LocationStates.waiting_for_location.set()
        await message.answer("✅ Вы успешно авторизованы. Теперь отправьте геолокацию для отметки входа:", reply_markup=keyboard)

    @dp.message_handler(content_types=[types.ContentType.LOCATION, types.ContentType.VENUE], state=LocationStates.waiting_for_location)
    async def handle_location(message: types.Message, state: FSMContext):
        location = message.location or (message.venue.location if message.venue else None)

        if not location:
            await message.answer("❌ Геолокация не получена. Убедитесь, что GPS включён и повторите попытку.")
            return

        user_id = message.from_user.id
        employee = get_employee_by_telegram_id(user_id)

        emp_id = employee[0] if employee else f"UNKNOWN_{user_id}"
        full_name = employee[1] if employee else f"Неизвестный ({user_id})"
        user_location = (location.latitude, location.longitude)

        within_zone = is_within_radius(user_location, OFFICE_LOCATION)

        # ✅ сохраняем отметку независимо от зоны
        mark_attendance(emp_id, *user_location)

        if within_zone:
            await message.answer("✅ Отметка входа сохранена.")
            await state.finish()
        else:
            # ❌ Вне зоны — предлагаем повторную отправку
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button = types.KeyboardButton("📍 Повторно отправить геолокацию", request_location=True)
            keyboard.add(button)

            await message.answer(
                "⚠️ Вы вне допустимой зоны (500 м).\n"
                "📡 Убедитесь, что GPS включён и вы находитесь рядом с офисом.\n\n"
                "🔁 Вы можете повторно отправить геолокацию:",
                reply_markup=keyboard
            )
            # FSM остаётся в ожидании геолокации это location handler 
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN
import start
import auth
import location
from db import init_db
import admin
import location_handler
import admin_panel

# 🔧 Фейковый HTTP-сервер для Render (чтобы не падал из-за отсутствия порта)
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("✅ Бот работает".encode("utf-8"))

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ✅ Лог старта
print("✅ Бот запускается на Render...")

# 🔧 Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

init_db()

# 🔧 Регистрация хендлеров
start.register(dp)
auth.register(dp)
location_handler.register(dp)
admin_panel.register(dp)

# 🛡️ Защита от падения
if __name__ == "__main__":
    try:
        print("🚀 Бот начинает слушать Telegram...")
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
