import os
from pathlib import Path
import pytesseract
from PIL import Image
import pandas as pd
from tqdm import tqdm
import sys

if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# === Настройки ===
IMAGES_FOLDER = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\images"
OUTPUT_CSV = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\ocr_results.csv"

# === Список всех изображений ===
image_files = []
for root, _, files in os.walk(IMAGES_FOLDER):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_files.append(Path(root) / file)

# === OCR ===
results = []
for img_path in tqdm(image_files):
    try:
        product_id = img_path.parent.name
        filename = img_path.name
        image_index = int(filename.split('.')[0])

        img = Image.open(img_path)
        ocr_data = pytesseract.image_to_data(img, lang='chi_sim', output_type=pytesseract.Output.DICT)

        for i, text in enumerate(ocr_data['text']):
            text_clean = text.strip()
            if text_clean:
                results.append({
                    'product_id': product_id,
                    'image_file': filename,
                    'image_index': image_index,
                    'ocr_index': i,
                    'text': text_clean
                })
    except Exception as e:
        print(f"[!] Error {img_path}: {e}")

# === Сохраняем результат ===
pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"✅ Done and saved here {OUTPUT_CSV}")
