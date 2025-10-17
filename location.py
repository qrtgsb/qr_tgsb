from aiogram import types
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from loader import dp
from states import LocationStates
from config import TARGET_LOCATION, LOCATION_RADIUS_KM
from db import get_employee_by_telegram_id, mark_attendance
from geo import haversine
import time
from config import ADMIN_ID


# Хранилище времени запуска /start
user_timestamps = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_timestamps[user_id] = time.time()

    employee = get_employee_by_telegram_id(user_id)
    if employee:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton("📍 Отправить геолокацию", request_location=True)
        keyboard.add(button)
        await LocationStates.waiting_for_location.set()
        await message.answer("Пожалуйста, отправьте свою геолокацию для отметки входа:", reply_markup=keyboard)
    else:
        await message.answer("❌ Вы не зарегистрированы. Обратитесь к администратору.")

@dp.message_handler(content_types=types.ContentType.LOCATION, state=LocationStates.waiting_for_location)
async def location_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    employee = get_employee_by_telegram_id(user_id)

    if not employee:
        await message.answer("❌ Сотрудник не найден. Отметка невозможна.")
        await state.finish()
        return

    lat = message.location.latitude
    lon = message.location.longitude
    accuracy = getattr(message.location, "horizontal_accuracy", None)

    # ✅ Проверка точности GPS
    if accuracy is None:
        await message.answer("❌ Геолокация не содержит точности. Включите GPS и попробуйте снова.")
        await state.finish()
        return

    if accuracy > 500:  # ← ТВОЙ ЛИМИТ
        await message.answer(f"❌ Геолокация слишком неточная ({accuracy:.1f} м). Вход не засчитан.")
        await state.finish()
        return

    # ✅ Проверка времени отклика (лимит 60 секунд)
    sent_at = user_timestamps.get(user_id, 0)
    now = time.time()
    if now - sent_at > 60:
        await message.answer("❌ Геолокация отправлена слишком поздно после запуска. Вход не засчитан.")
        await state.finish()
        return

    # ✅ Проверка расстояния до объекта
    target_lat, target_lon = TARGET_LOCATION
    distance = haversine(lat, lon, target_lat, target_lon)

    if distance > LOCATION_RADIUS_KM:
        await message.answer(f"❌ Вы находитесь слишком далеко от объекта ({distance:.1f} км). Вход не засчитан.", reply_markup=ReplyKeyboardRemove())
        await state.finish()
        return

    # ✅ Всё прошло — засчитываем вход
    mark_attendance(employee[0], lat, lon)

    # 📤 Отправка отчёта админу
    full_name = employee[3]  # если ФИО — 4-й столбец
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    report = (
        f"📥 Вход сотрудника:\n"
        f"👤 {full_name}\n"
        f"🕒 {timestamp}\n"
        f"📍 Координаты: {lat:.5f}, {lon:.5f}\n"
        f"🎯 Точность: {accuracy:.1f} м\n"
        f"📏 Расстояние: {distance:.2f} км"
    )

    await message.answer(
        f"✅ Вход засчитан. Точность: {accuracy:.1f} м, расстояние: {distance:.1f} км",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.bot.send_message(ADMIN_ID, report)
    await state.finish()

# Вспомогательная функция — можно вызывать из других мест
async def request_location(message: types.Message, employee):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("📍 Отправить геолокацию", request_location=True)
    keyboard.add(button)
    await LocationStates.waiting_for_location.set()
    await message.answer("Пожалуйста, отправьте свою геолокацию для отметки входа:", reply_markup=keyboard)

from aiogram import types
from aiogram.dispatcher import FSMContext
from states import LocationStates
from db import get_employee_by_full_name, update_employee_telegram_id, get_employee_by_telegram_id, mark_attendance
from config import ADMIN_ID

def register(dp):
    @dp.message_handler(state=LocationStates.waiting_for_employee)
    async def handle_employee_selection(message: types.Message, state: FSMContext):
        full_name = message.text.strip()
        employee = get_employee_by_full_name(full_name)

        if not employee:
            await message.answer("❌ Сотрудник не найден. Попробуйте ещё раз.")
            return

        update_employee_telegram_id(employee[0], message.from_user.id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton("📍 Отправить геолокацию", request_location=True)
        keyboard.add(button)
        await LocationStates.waiting_for_location.set()
        await message.answer("✅ Выбран сотрудник. Теперь отправьте геолокацию:", reply_markup=keyboard)

    @dp.message_handler(content_types=types.ContentType.LOCATION, state=LocationStates.waiting_for_location)
    async def handle_location(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        employee = get_employee_by_telegram_id(user_id)

        if not employee and user_id != ADMIN_ID:
            await message.answer("❌ Сотрудник не найден. Отметка невозможна.")
            await state.finish()
            return

        emp_id = employee[0] if employee else "ADMIN"
        lat = message.location.latitude
        lon = message.location.longitude

        mark_attendance(emp_id, lat, lon)
        await message.answer("✅ Отметка входа сохранена.")
        await state.finish()

