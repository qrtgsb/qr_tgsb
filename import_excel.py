import pandas as pd
from db import conn

def import_employees_from_excel(path="employees.xlsx"):
    try:
        df = pd.read_excel(path)
        if not all(col in df.columns for col in ["emp_id", "full_name", "position"]):
            print("❌ Excel-файл не содержит нужные столбцы: emp_id, full_name, position.")
            return
        df.to_sql("employees", conn, if_exists="replace", index=False)
        print("✅ Сотрудники успешно импортированы из Excel.")
    except Exception as e:
        print(f"❌ Ошибка при импорте: {e}")

if __name__ == "__main__":
    import_employees_from_excel()
