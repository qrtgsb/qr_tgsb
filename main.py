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
        self.wfile.write(b"✅ Бот работает")

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ✅ Лог старта
print("✅ Бот запускается на Render...")

# 🔧 Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp =
