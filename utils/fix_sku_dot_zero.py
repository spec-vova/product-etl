#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления проблемы с .0 в конце SKU коллекций.
Удаляет .0 из SKU в базе данных и переименовывает соответствующие папки.
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
LOG_FILE = IMAGES_FOLDER / 'fix_sku_log.txt'

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def get_skus_with_dot_zero(cursor):
    """Получить все SKU с .0 в конце"""
    cursor.execute("""
        SELECT DISTINCT product_collection_sku 
        FROM product_collection 
        WHERE product_collection_sku LIKE '%.0'
        ORDER BY product_collection_sku;
    """)
    return [row['product_collection_sku'] for row in cursor.fetchall()]

def fix_sku_in_database(cursor, old_sku, new_sku):
    """Исправить SKU в базе данных"""
    try:
        # Обновляем product_collection
        cursor.execute("""
            UPDATE product_collection 
            SET product_collection_sku = %s 
            WHERE product_collection_sku = %s;
        """, (new_sku, old_sku))
        pc_updated = cursor.rowcount
        
        # Обновляем product_collection_images
        cursor.execute("""
            UPDATE product_collection_images 
            SET collection_sku = %s 
            WHERE collection_sku = %s;
        """, (new_sku, old_sku))
        pci_updated = cursor.rowcount
        
        # Обновляем url_local в product_collection_images
        cursor.execute("""
            UPDATE product_collection_images 
            SET url_local = REPLACE(url_local, %s, %s)
            WHERE collection_sku = %s;
        """, (old_sku, new_sku, new_sku))
        url_updated = cursor.rowcount
        
        log(f"[БД] {old_sku} -> {new_sku}: product_collection={pc_updated}, images={pci_updated}, urls={url_updated}")
        return True
        
    except Exception as e:
        log(f"[БД] Ошибка при обновлении {old_sku}: {e}")
        return False

def rename_folder(old_sku, new_sku):
    """Переименовать папку с изображениями"""
    old_folder = IMAGES_FOLDER / old_sku
    new_folder = IMAGES_FOLDER / new_sku
    
    if old_folder.exists():
        if new_folder.exists():
            log(f"[ПАПКА] Целевая папка {new_sku} уже существует, пропускаем")
            return False
        
        try:
            old_folder.rename(new_folder)
            log(f"[ПАПКА] Переименовано: {old_sku} -> {new_sku}")
            return True
        except Exception as e:
            log(f"[ПАПКА] Ошибка переименования {old_sku}: {e}")
            return False
    else:
        log(f"[ПАПКА] Папка {old_sku} не найдена")
        return False

def main():
    log("=== Начало исправления SKU с .0 ===")
    
    # Очищаем лог
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        host=DB_HOST, port=DB_PORT
    )
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Получаем все SKU с .0
        skus_with_dot_zero = get_skus_with_dot_zero(cursor)
        log(f"Найдено {len(skus_with_dot_zero)} SKU с .0 в конце")
        
        if not skus_with_dot_zero:
            log("Нет SKU для исправления")
            return
        
        # Показываем план действий
        log("\nПлан исправления:")
        for old_sku in skus_with_dot_zero:
            new_sku = old_sku.rstrip('.0')
            log(f"  {old_sku} -> {new_sku}")
        
        # Подтверждение
        response = input("\nПродолжить исправление? (y/N): ")
        if response.lower() != 'y':
            log("Операция отменена пользователем")
            return
        
        # Выполняем исправления
        success_count = 0
        for old_sku in skus_with_dot_zero:
            new_sku = old_sku.rstrip('.0')
            
            log(f"\n--- Обработка {old_sku} ---")
            
            # Исправляем в БД
            db_success = fix_sku_in_database(cursor, old_sku, new_sku)
            
            # Переименовываем папку
            folder_success = rename_folder(old_sku, new_sku)
            
            if db_success:
                success_count += 1
                # Коммитим изменения для каждого SKU
                conn.commit()
                log(f"[УСПЕХ] {old_sku} исправлен")
            else:
                # Откатываем изменения при ошибке
                conn.rollback()
                log(f"[ОШИБКА] {old_sku} не исправлен")
        
        log(f"\n=== Завершено: {success_count}/{len(skus_with_dot_zero)} SKU исправлено ===")
        
    except Exception as e:
        log(f"Критическая ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    main()