# retry_failed_downloads.py

import os
import time
import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup

# === Настройки ===
FAILED_CSV = r"failed_downloads.csv"          # файл с ошибками первой загрузки
ORIGINAL_CSV = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\html.csv"  # путь к исходному CSV
IMAGES_FOLDER = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\images"  # папка для сохранения
HEADERS = {"User-Agent": "Mozilla/5.0"}

# === Загрузка исходного файла ===
df = pd.read_csv(ORIGINAL_CSV)

# === Функция парсинга HTML (повтор из основного скрипта) ===
def extract_img_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    return [img.get('src') for img in soup.find_all('img') if img.get('src')]

# === Сопоставление всех изображений ===
df['image_urls'] = df['details_html'].apply(extract_img_links)
df = df[df['image_urls'].map(len) > 0].reset_index(drop=True)

# === Плоская таблица: все возможные картинки с путями ===
all_images = []
for _, row in df.iterrows():
    for i, url in enumerate(row['image_urls']):
        all_images.append({
            'product_id': row['product_id'],
            'image_index': i,
            'image_url': url,
            'local_path': os.path.join(IMAGES_FOLDER, row['product_id'], f"{i:02d}.jpg")
        })

all_df = pd.DataFrame(all_images)

# === Фильтруем только те, которых реально не хватает ===
def is_missing(path):
    return not Path(path).exists()

missing_df = all_df[all_df['local_path'].apply(is_missing)].reset_index(drop=True)
print(f"Найдено отсутствующих файлов: {len(missing_df)}")

# === Загрузка с паузой ===
def download_image(url, save_path):
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        r.raise_for_status()
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"[!] Ошибка: {e}")
        return False

failed = []

for _, row in tqdm(missing_df.iterrows(), total=len(missing_df)):
    success = download_image(row['image_url'], row['local_path'])
    if not success:
        failed.append(row)
    time.sleep(2)  # пауза между запросами

# Сохраняем неудачные попытки
if failed:
    pd.DataFrame(failed).to_csv("failed_downloads_retry.csv", index=False)
    print(f"[!] Не удалось загрузить: {len(failed)}")
else:
    print("✅ Все недостающие картинки успешно загружены.")
