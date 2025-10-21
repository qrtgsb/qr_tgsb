from aiogram import types
from loader import dp
from db import get_today_attendance
from io import BytesIO
import datetime
from aiogram.types import InputFile
from openpyxl import Workbook
from geopy.distance import distance  # добавь в зависимости: pip install geopy

# Координаты рабочего места (Туркестан)
WORK_LAT = 43.270355
WORK_LON = 68.285416
WORK_LOCATION = (WORK_LAT, WORK_LON)

def register(dp):
    @dp.message_handler(commands=['admin'])
    async def admin_panel(message: types.Message):
        if message.from_user.id != 6561816231:
            await message.answer("❌ Доступ запрещён.")
            return

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("📊 Отчёт за сегодня", callback_data="report_today"))
        keyboard.add(types.InlineKeyboardButton("📤 Скачать статистику (Excel)", callback_data="export_today"))
        await message.answer("🔧 Админ-панель:", reply_markup=keyboard)

    @dp.callback_query_handler(lambda c: c.data == "export_today")
    async def handle_export_today(callback_query: types.CallbackQuery):
        entries = get_today_attendance()
        if not entries:
            await callback_query.message.answer("📭 Сегодня ещё никто не отметился.")
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Отчёт"

        # Заголовки
        ws.append(["ФИО", "Время", "Локация (≤500м)", "Опоздание после 08:30", "Статус"])

        for emp in entries:
            raw_ts = emp.get('timestamp')

            # Преобразуем timestamp в datetime
            try:
                if isinstance(raw_ts, str):
                    dt = datetime.datetime.strptime(raw_ts, "%Y-%m-%d %H:%M:%S")
                elif isinstance(raw_ts, (int, float)):
                    dt = datetime.datetime.fromtimestamp(raw_ts)
                else:
                    dt = datetime.datetime.now()
            except Exception:
                dt = datetime.datetime.now()

            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")

            # Получаем координаты сотрудника
            lat = emp.get('latitude')
            lon = emp.get('longitude')

            # Локация и статус
            if lat is None or lon is None:
                location_status = "Не отправлено"
                status = "Локация не отправлена"
                late_status = "—"
            else:
                actual_location = (lat, lon)
                meters = distance(actual_location, WORK_LOCATION).meters
                location_ok = meters <= 500
                location_status = "В рабочем месте" if location_ok else "Вне рабочего места"

                # Опоздание
                is_late = dt.time() > datetime.time(8, 30)
                late_status = "Да" if is_late else "Нет"

                # Статус
                if not location_ok:
                    status = "Вне рабочего места"
                elif is_late:
                    status = "Опоздал"
                else:
                    status = "Прибыл вовремя"

            ws.append([
                emp['full_name'],
                formatted_time,
                location_status,
                late_status,
                status
            ])

        file = BytesIO()
        wb.save(file)
        file.seek(0)

        document = InputFile(file, "Отчет_за_сегодня.xlsx")

        await callback_query.message.answer_document(
            document=document,
            caption="📤 Вот Excel-отчёт за сегодня"
        )
