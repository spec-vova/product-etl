import os
from pathlib import Path
import pytesseract
from PIL import Image
import pandas as pd
from tqdm import tqdm
import sys

# === Путь до Tesseract ===
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# === UTF-8 консоль для Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# === Настройки ===
IMAGES_FOLDER = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\images"
OUTPUT_CSV = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\ocr_results.csv"
BASE_IMAGE_URL = "file:///" + IMAGES_FOLDER.replace("\\", "/")

print(f"🔍 Сканируем изображения в папке: {IMAGES_FOLDER}")

# === Список всех изображений ===
image_files = []
for root, _, files in os.walk(IMAGES_FOLDER):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_files.append(Path(root) / file)

print(f"📸 Найдено {len(image_files)} изображений")

# === Подготовка CSV ===
header_written = os.path.exists(OUTPUT_CSV)

# === OCR ===
for img_path in tqdm(image_files):
    try:
        product_id = img_path.parent.name
        filename = img_path.name
        image_index = int(filename.split('.')[0])
        full_url = "file:///" + str(img_path).replace("\\", "/")

        print(f"➡️ Распознаем: {img_path}")
        img = Image.open(img_path)
        ocr_data = pytesseract.image_to_data(img, lang='chi_sim', output_type=pytesseract.Output.DICT)

        image_results = []

        for i, text in enumerate(ocr_data['text']):
            text_clean = text.strip()
            if text_clean:
                print(f"   ⤷ [{i}] '{text_clean}'")
                image_results.append({
                    'product_id': product_id,
                    'image_file': filename,
                    'image_url': full_url,
                    'image_index': image_index,
                    'ocr_index': i,
                    'text': text_clean
                })

        if image_results:
            df = pd.DataFrame(image_results)
            df.to_csv(OUTPUT_CSV, mode='a', header=not header_written, index=False, encoding='utf-8-sig')
            header_written = True

    except Exception as e:
        print(f"[!] Ошибка при обработке {img_path}: {e}")

print(f"✅ Готово. Все результаты записаны в файл: {OUTPUT_CSV}")
