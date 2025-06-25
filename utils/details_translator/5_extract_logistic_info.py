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

try:
    import openai
except ImportError:
    print("[!] Библиотека openai не установлена. Установи: pip install openai")
    sys.exit(1)

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("[!] Не найден ключ OPENAI_API_KEY в .env")
    sys.exit(1)

# === Пути ===
INPUT_DIR = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\4_translated_by_product"
OUTPUT_DIR = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\5_extracted_logistics"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# === Новые поля ===
logistic_fields = [
    "packaging_features",
    "dimensions_cm",
    "volumetric_weight_kg",
    "actual_weight_kg",
    "logistics_notes"
]

# === Подготовка запроса к GPT ===
def extract_logistics_info(text):
    if not text.strip():
        return ["" for _ in logistic_fields]
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a logistics expert for international furniture shipments. Based on the provided product description, extract only logistics-relevant information and fill out the following fields: Packaging features, Dimensions in cm (HxLxW), Volumetric weight (kg), Actual weight (kg), and Logistics notes."},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
        )
        result = response.choices[0].message.content.strip().split("\n")
        values = [line.split(":", 1)[-1].strip() if ":" in line else "" for line in result]
        return (values + [""] * len(logistic_fields))[:len(logistic_fields)]
    except Exception as e:
        print(f"[!] Ошибка обработки: {e}")
        return ["" for _ in logistic_fields]

# === Обработка файлов ===
input_files = list(Path(INPUT_DIR).glob("*.csv"))
print(f"🔍 Найдено файлов: {len(input_files)}")

for file_path in input_files:
    print(f"➡️ Обрабатываем: {file_path.name}")
    df = pd.read_csv(file_path)
    full_text = " ".join(df['translated_text'].fillna('').astype(str).tolist())
    extracted = extract_logistics_info(full_text)

    info_dict = {"product_id": file_path.stem}
    info_dict.update(dict(zip(logistic_fields, extracted)))

    out_df = pd.DataFrame([info_dict])
    out_path = Path(OUTPUT_DIR) / file_path.name
    out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"✅ Сохранено: {out_path}")
    time.sleep(1)
