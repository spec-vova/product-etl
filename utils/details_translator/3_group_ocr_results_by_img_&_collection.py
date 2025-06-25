import pandas as pd
from pathlib import Path
import os
import sys

# === UTF-8 консоль для Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# === Настройки ===
INPUT_CSV = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\ocr_results.csv"
OUTPUT_DIR = r"X:\\DATA_STORAGE\\Furnithai\\utils\\details_translator\\3_grouped_by_product"

# === Загрузка данных ===
df = pd.read_csv(INPUT_CSV)

# === Убедимся, что нужные колонки есть ===
required_columns = {
    'product_id', 'image_filename', 'text_found_on_image',
    'index_of_image_in_product'
}
assert required_columns.issubset(df.columns), f"Не найдены нужные колонки: {required_columns - set(df.columns)}"

# === Подготовка данных ===
df = df.dropna(subset=['index_of_image_in_product'])
df['image_index'] = df['index_of_image_in_product'].astype(int)

# === Группировка текста по картинке ===
grouped = df.groupby(['product_id', 'image_index'], as_index=False).agg({
    'text_found_on_image': lambda x: ' '.join(str(t).strip() for t in x if str(t).strip())
})

# === Сохраняем по одному файлу на коллекцию ===
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

product_ids = grouped['product_id'].unique()
print(f"🔍 Обнаружено {len(product_ids)} уникальных коллекций")

for product_id in product_ids:
    group_df = grouped[grouped['product_id'] == product_id]
    if group_df.empty:
        print(f"⚠️ Пропущено: {product_id} (нет текста)")
        continue
    output_path = Path(OUTPUT_DIR) / f"{product_id}.csv"
    group_df[['product_id', 'image_index', 'text_found_on_image']].to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ Сохранено: {output_path} ({len(group_df)} строк)")
