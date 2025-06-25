import pandas as pd
import os
import sys

# === UTF-8 консоль для Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')


# Путь к файлам
raw_excel_path = 'RAW_WXW/Raw Data.xlsx'
mapping_csv_path = 'map.csv'

# Читаем mapping
df_map = pd.read_csv(mapping_csv_path, encoding='utf-8')
mapping = {}
for _, row in df_map.iterrows():
    raw_col = str(row['Raw Column']).strip()
    table = str(row['Table']).strip()
    column = str(row['Field']).strip()
    dtype = str(row['Type']).strip() if 'Type' in row else 'text'
    mapping[raw_col] = {'table': table, 'column': column, 'type': dtype}

# Читаем Excel
raw_df = pd.read_excel(raw_excel_path, sheet_name=0)
print(raw_df.columns)