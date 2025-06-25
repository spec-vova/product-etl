import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import os
import sys
import time

# === UTF-8 консоль для Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# === Загрузка переменных окружения ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# === Проверка зависимости ===
try:
    import openai
except ImportError:
    print("[!] Библиотека openai не установлена. Установи: pip install openai")
    sys.exit(1)

# === Проверка ключа ===
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("[!] Не найден ключ OPENAI_API_KEY в .env файле")
    sys.exit(1)

# === Пути ===
INPUT_DIR = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\3_grouped_by_product"
OUTPUT_DIR = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\4_translated_by_product"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# === Функция перевода на новом API ===
def translate_text(text):
    if not text.strip():
        return ""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional translator specialized in product descriptions for furniture and home decor."},
                {"role": "user", "content": f"Translate the following Chinese text to English. It comes from product descriptions of furniture and home decor: {text}"}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[!] Ошибка перевода '{text}': {e}")
        return ""

# === Обработка файлов ===
input_files = list(Path(INPUT_DIR).glob("*.csv"))
print(f"🔍 Найдено файлов для перевода: {len(input_files)}")

for file_path in input_files:
    print(f"➡️ Обрабатываем: {file_path.name}")
    df = pd.read_csv(file_path)
    df['translated_text'] = df['text_found_on_image'].fillna('').map(translate_text)
    out_path = Path(OUTPUT_DIR) / file_path.name
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"✅ Сохранено: {out_path}")
    time.sleep(1)
