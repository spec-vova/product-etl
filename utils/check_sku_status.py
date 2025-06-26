#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки состояния SKU с .0 в базе данных и файловой системе.
Используется для диагностики до и после исправления.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === UTF-8 консоль для Windows ===
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5433))
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

IMAGES_FOLDER = Path(r"X:\DATA_STORAGE\Furnithai\pictures")

def check_database_status(cursor):
    """Проверить состояние SKU в базе данных"""
    print("=== СОСТОЯНИЕ БАЗЫ ДАННЫХ ===")
    
    # SKU с .0 в product_collection
    cursor.execute("""
        SELECT product_collection_sku 
        FROM product_collection 
        WHERE product_collection_sku LIKE '%.0'
        ORDER BY product_collection_sku;
    """)
    pc_with_dot_zero = cursor.fetchall()
    
    print(f"SKU с .0 в product_collection: {len(pc_with_dot_zero)}")
    for row in pc_with_dot_zero:
        print(f"  - {row['product_collection_sku']}")
    
    # SKU с .0 в product_collection_images
    cursor.execute("""
        SELECT DISTINCT collection_sku 
        FROM product_collection_images 
        WHERE collection_sku LIKE '%.0'
        ORDER BY collection_sku;
    """)
    pci_with_dot_zero = cursor.fetchall()
    
    print(f"\nSKU с .0 в product_collection_images: {len(pci_with_dot_zero)}")
    for row in pci_with_dot_zero:
        print(f"  - {row['collection_sku']}")
    
    # URL с .0 в путях
    cursor.execute("""
        SELECT DISTINCT collection_sku, COUNT(*) as image_count
        FROM product_collection_images 
        WHERE url_local LIKE '%.0%'
        GROUP BY collection_sku
        ORDER BY collection_sku;
    """)
    urls_with_dot_zero = cursor.fetchall()
    
    print(f"\nSKU с .0 в url_local: {len(urls_with_dot_zero)}")
    for row in urls_with_dot_zero:
        print(f"  - {row['collection_sku']}: {row['image_count']} изображений")

def check_filesystem_status():
    """Проверить состояние папок в файловой системе"""
    print("\n=== СОСТОЯНИЕ ФАЙЛОВОЙ СИСТЕМЫ ===")
    
    if not IMAGES_FOLDER.exists():
        print(f"Папка {IMAGES_FOLDER} не существует")
        return
    
    # Найти папки с .0
    folders_with_dot_zero = []
    for item in IMAGES_FOLDER.iterdir():
        if item.is_dir() and item.name.endswith('.0'):
            folders_with_dot_zero.append(item.name)
    
    print(f"Папки с .0: {len(folders_with_dot_zero)}")
    for folder in sorted(folders_with_dot_zero):
        folder_path = IMAGES_FOLDER / folder
        image_count = len(list(folder_path.glob('*.*')))
        print(f"  - {folder}: {image_count} файлов")
    
    # Проверить, есть ли дублирующиеся папки (с .0 и без)
    print("\n=== ПРОВЕРКА ДУБЛИРУЮЩИХСЯ ПАПОК ===")
    duplicates_found = False
    for folder in folders_with_dot_zero:
        clean_name = folder.rstrip('.0')
        clean_folder = IMAGES_FOLDER / clean_name
        if clean_folder.exists():
            print(f"ДУБЛИКАТ: {folder} и {clean_name} существуют одновременно")
            duplicates_found = True
    
    if not duplicates_found:
        print("Дублирующихся папок не найдено")

def check_consistency(cursor):
    """Проверить согласованность между БД и файловой системой"""
    print("\n=== ПРОВЕРКА СОГЛАСОВАННОСТИ ===")
    
    # Получить все SKU из БД
    cursor.execute("""
        SELECT DISTINCT collection_sku 
        FROM product_collection_images 
        ORDER BY collection_sku;
    """)
    db_skus = {row['collection_sku'] for row in cursor.fetchall()}
    
    # Получить все папки из файловой системы
    if IMAGES_FOLDER.exists():
        fs_folders = {item.name for item in IMAGES_FOLDER.iterdir() if item.is_dir()}
    else:
        fs_folders = set()
    
    # SKU в БД, но нет папки
    missing_folders = db_skus - fs_folders
    if missing_folders:
        print(f"SKU в БД без папок ({len(missing_folders)}):")
        for sku in sorted(missing_folders):
            print(f"  - {sku}")
    
    # Папки есть, но нет в БД
    missing_db = fs_folders - db_skus
    if missing_db:
        print(f"\nПапки без записей в БД ({len(missing_db)}):")
        for folder in sorted(missing_db):
            print(f"  - {folder}")
    
    if not missing_folders and not missing_db:
        print("Все SKU согласованы между БД и файловой системой")

def main():
    print("=== ПРОВЕРКА СОСТОЯНИЯ SKU ===")
    
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        host=DB_HOST, port=DB_PORT
    )
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        check_database_status(cursor)
        check_filesystem_status()
        check_consistency(cursor)
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()