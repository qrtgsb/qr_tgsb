# admin.py

ADMINS = {
    6561816231: "MED",       # ← ты
    1234567890: "Тестовый админ",  # ← не сотрудник, но имеет доступ
}

def is_admin(user_id):
    return user_id in ADMINS
