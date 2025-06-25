import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import sys

# === UTF-8 консоль для Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')


# Конфиг подключения к базе
PG_CONN = "host=localhost dbname=yourdb user=youruser password=yourpassword"

raw_excel_path = 'RAW_WXW/Raw Data.xlsx'
mapping_csv_path = 'vol - Sheet8.csv'

# 1. Загружаем mapping
df_map = pd.read_csv(mapping_csv_path, encoding='utf-8')
mapping = {}
for _, row in df_map.iterrows():
    raw_col = str(row['Raw Column']).strip()
    table = str(row['Table']).strip()
    column = str(row['Field']).strip()
    dtype = str(row['Type']).strip() if 'Type' in row else 'text'
    mapping[raw_col] = {'table': table, 'column': column, 'type': dtype}

# 2. Читаем Excel
raw_df = pd.read_excel(raw_excel_path, sheet_name=0)

# --- Подключение к базе ---
conn = psycopg2.connect(PG_CONN)
cur = conn.cursor()

# --- 3. Коллекция (master-строка) ---
collection_row = raw_df.iloc[0]
collection_data = {}
for raw_col, value in collection_row.items():
    if raw_col in mapping and mapping[raw_col]['table'] == 'product_collection':
        db_col = mapping[raw_col]['column']
        collection_data[db_col] = value

# TODO: UPSERT коллекции по master_code или другому уникальному полю
# cur.execute("INSERT INTO ... ON CONFLICT ... DO UPDATE ...", ...)

# --- 4. Вариации (products) ---
products = []
for idx, row in raw_df.iterrows():
    if idx == 0:
        continue
    product_data = {}
    for raw_col, value in row.items():
        if raw_col in mapping and mapping[raw_col]['table'] == 'product':
            db_col = mapping[raw_col]['column']
            product_data[db_col] = value
    # Добавляем связь с коллекцией
    product_data['product_collection_master_code'] = collection_data.get('master_code')
    products.append(product_data)

# TODO: Batch insert продуктов через execute_values или по одному (UPSERT)
# execute_values(cur, "...", [tuple(...)])

# --- 5. Переводы, атрибуты, связи ---
# Для каждой строки и каждого поля, если mapping[raw_col]['table'].endswith('_translations'):
#   - Собираем структуру перевода
#   - Вставляем в *_translations, связываем с product_id/collection_id

conn.commit()
cur.close()
conn.close()