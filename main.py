from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Update
from config import BOT_TOKEN

import start
import auth
import location
from db import init_db
import admin
import location_handler
import admin_panel

# 🌐 Webhook настройки
WEBHOOK_HOST = "https://qr-tgsb.onrender.com"  # ← твой Render-домен
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 10000

# ✅ Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# 🔧 Установка текущего контекста
Bot.set_current(bot)
Dispatcher.set_current(dp)

# 🔧 Инициализация базы данных и хендлеров
init_db()
start.register(dp)
auth.register(dp)
location_handler.register(dp)
admin_panel.register(dp)

# 📩 Обработка входящих обновлений от Telegram
async def handle_webhook(request):
    try:
        data = await request.json()
        update = Update.to_object(data)
        await dp.process_update(update)
    except Exception as e:
        print(f"❌ Ошибка обработки обновления: {e}")
    return web.Response()

# 👋 Health check для Render
async def handle_root(request):
    return web.Response(text="✅ Бот работает и слушает Telegram")

# 🚀 При старте приложения
async def on_startup(app):
    print(f"📡 Установка webhook на {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook установлен")

# 🛑 При завершении приложения
async def on_shutdown(app):
    print("❌ Отключение webhook...")
    await bot.delete_webhook()
    await bot.session.close()

# 🌐 Создание aiohttp-приложения
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.router.add_get("/", handle_root)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# 🧠 Запуск сервера
if __name__ == "__main__":
    print("🚀 Бот запускается через aiohttp...")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
