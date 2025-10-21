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
            # FSM остаётся в ожидании геолокации
