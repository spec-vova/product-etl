import pandas as pd
import psycopg2
import uuid
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# === UTF-8 консоль для Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": os.getenv("DB_PORT", "5433"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

def migrate_from_custom_attributes(conn):
    """Миграция атрибутов из custom_attributes_raw в product_attributes_raw_collection"""
    cursor = conn.cursor()
    created_count = 0
    updated_count = 0
    
    try:
        print("Начинаем миграцию из custom_attributes_raw...")
        
        # Получаем все продукты, которые ссылаются на custom_attributes_raw
        cursor.execute("""
            SELECT DISTINCT p.product_attributes_raw_collection_id, car.custom_attributes_raw
            FROM product p
            JOIN custom_attributes_raw car ON p.product_attributes_raw_collection_id = car.id
            WHERE p.product_attributes_raw_collection_id NOT IN (
                SELECT id FROM product_attributes_raw_collection
            )
        """)
        
        attributes_to_migrate = cursor.fetchall()
        print(f"Найдено {len(attributes_to_migrate)} уникальных атрибутов для миграции")
        
        for attr_id, attr_content in attributes_to_migrate:
            # Создаем новую запись в product_attributes_raw_collection с тем же ID
            cursor.execute("""
                INSERT INTO product_attributes_raw_collection 
                (id, product_attributes_collection, created_on, modified_on)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (attr_id, attr_content, datetime.now(), datetime.now()))
            
            if cursor.rowcount > 0:
                created_count += 1
            
            if created_count % 100 == 0 and created_count > 0:
                print(f"Создано {created_count} записей...")
        
        # Теперь проверяем, сколько продуктов теперь правильно связаны
        cursor.execute("""
            SELECT COUNT(*) FROM product p
            JOIN product_attributes_raw_collection parc ON p.product_attributes_raw_collection_id = parc.id
        """)
        linked_count = cursor.fetchone()[0]
        
        conn.commit()
        print(f"\nСоздано новых записей атрибутов: {created_count}")
        print(f"Продуктов теперь правильно связано: {linked_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при миграции: {e}")
        raise
    finally:
        cursor.close()

def create_missing_attributes_from_existing_data(conn):
    """Создает недостающие атрибуты на основе существующих данных продуктов"""
    cursor = conn.cursor()
    created_count = 0
    
    try:
        print("\nСоздаем недостающие атрибуты для продуктов без связей...")
        
        # Находим продукты без правильных связей с атрибутами
        cursor.execute("""
            SELECT p.id, p.product_collection_sku, p.product_attributes_raw_collection_id
            FROM product p
            WHERE p.product_attributes_raw_collection_id IS NOT NULL
            AND p.product_attributes_raw_collection_id NOT IN (
                SELECT id FROM product_attributes_raw_collection
            )
            LIMIT 1000
        """)
        
        products_without_attrs = cursor.fetchall()
        print(f"Найдено {len(products_without_attrs)} продуктов без правильных атрибутов")
        
        for product_id, sku, old_attr_id in products_without_attrs:
            # Создаем базовые атрибуты на основе SKU
            basic_attributes = f"SKU:{sku}"
            
            # Проверяем, существует ли уже запись с такими атрибутами
            cursor.execute("""
                SELECT id FROM product_attributes_raw_collection 
                WHERE product_attributes_collection = %s
            """, (basic_attributes,))
            existing = cursor.fetchone()
            
            if existing:
                # Используем существующую запись
                new_attr_id = existing[0]
            else:
                # Создаем новую запись с тем же ID, что был у продукта
                cursor.execute("""
                    INSERT INTO product_attributes_raw_collection 
                    (id, product_attributes_collection, created_on, modified_on)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (old_attr_id, basic_attributes, datetime.now(), datetime.now()))
                
                if cursor.rowcount > 0:
                    created_count += 1
                    new_attr_id = old_attr_id
                else:
                    # Если конфликт ID, создаем новый
                    new_attr_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO product_attributes_raw_collection 
                        (id, product_attributes_collection, created_on, modified_on)
                        VALUES (%s, %s, %s, %s)
                    """, (new_attr_id, basic_attributes, datetime.now(), datetime.now()))
                    created_count += 1
                    
                    # Обновляем ссылку в продукте
                    cursor.execute("""
                        UPDATE product 
                        SET product_attributes_raw_collection_id = %s, modified_on = %s
                        WHERE id = %s
                    """, (new_attr_id, datetime.now(), product_id))
            
            if created_count % 100 == 0 and created_count > 0:
                print(f"Создано {created_count} записей...")
        
        conn.commit()
        print(f"Создано дополнительных записей атрибутов: {created_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании недостающих атрибутов: {e}")
        raise
    finally:
        cursor.close()

def verify_migration(conn):
    """Проверяет результаты миграции"""
    cursor = conn.cursor()
    
    try:
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM product")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM product p 
            JOIN product_attributes_raw_collection parc 
            ON p.product_attributes_raw_collection_id = parc.id
        """)
        products_with_valid_attrs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM product_attributes_raw_collection")
        total_attributes = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM product 
            WHERE product_attributes_raw_collection_id IS NOT NULL
        """)
        products_with_attr_ids = cursor.fetchone()[0]
        
        print("\n=== РЕЗУЛЬТАТЫ МИГРАЦИИ ===")
        print(f"Всего продуктов: {total_products}")
        print(f"Продуктов с правильными ссылками на атрибуты: {products_with_valid_attrs}")
        print(f"Продуктов с ID атрибутов: {products_with_attr_ids}")
        print(f"Всего записей атрибутов: {total_attributes}")
        
        if products_with_valid_attrs == total_products:
            print("✅ Все продукты имеют правильные ссылки на атрибуты")
        else:
            invalid_count = total_products - products_with_valid_attrs
            print(f"❌ {invalid_count} продуктов имеют неправильные ссылки")
        
        # Показываем примеры
        cursor.execute("""
            SELECT p.product_collection_sku, parc.product_attributes_collection
            FROM product p 
            JOIN product_attributes_raw_collection parc 
            ON p.product_attributes_raw_collection_id = parc.id
            LIMIT 3
        """)
        examples = cursor.fetchall()
        
        if examples:
            print("\nПримеры правильно связанных атрибутов:")
            for sku, attrs in examples:
                print(f"  SKU: {sku} -> {attrs[:100]}...")
        
        # Показываем продукты с неправильными ссылками
        cursor.execute("""
            SELECT COUNT(*) FROM product p
            WHERE p.product_attributes_raw_collection_id IS NOT NULL
            AND p.product_attributes_raw_collection_id NOT IN (
                SELECT id FROM product_attributes_raw_collection
            )
        """)
        invalid_links = cursor.fetchone()[0]
        
        if invalid_links > 0:
            print(f"\n⚠️  {invalid_links} продуктов ссылаются на несуществующие атрибуты")
        
    except Exception as e:
        print(f"Ошибка при проверке: {e}")
    finally:
        cursor.close()

def main():
    """Основная функция миграции"""
    print("Начинаем миграцию атрибутов продуктов...")
    
    # Подключаемся к базе данных
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Подключение к базе данных установлено")
        
        # Сначала мигрируем из custom_attributes_raw
        migrate_from_custom_attributes(conn)
        
        # Затем создаем недостающие атрибуты
        create_missing_attributes_from_existing_data(conn)
        
        # Проверяем результаты
        verify_migration(conn)
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            print("\nСоединение с базой данных закрыто")

if __name__ == "__main__":
    main()