# -*- coding: utf-8 -*-
import os
import psycopg2
import uuid
import time
from dotenv import load_dotenv
from google.cloud import translate_v2 as translate

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

def get_all_products():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, product_attributes_raw_collection_id FROM product WHERE product_attributes_raw_collection_id IS NOT NULL
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows  # [(product_id, collection_id)]

def get_collection_attrs(collection_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT product_attributes_collection FROM product_attributes_raw_collection WHERE id = %s", (collection_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def parse_attributes(attr_str):
    result = []
    if not attr_str:
        return result
    for pair in attr_str.split('-'):
        if not pair.strip():
            continue
        # под-пары через ';' если есть
        subpairs = pair.split(';')
        for subpair in subpairs:
            if ':' in subpair:
                k, v = subpair.split(':', 1)
                result.append((k.strip(), v.strip()))
    return result

def get_or_create_key(conn, attr_key):
    cur = conn.cursor()
    cur.execute("SELECT id FROM product_attribute_keys WHERE attr_key=%s", (attr_key,))
    row = cur.fetchone()
    if row:
        return row[0]
    key_id = str(uuid.uuid4())
    cur.execute("INSERT INTO product_attribute_keys (id, attr_key) VALUES (%s, %s)", (key_id, attr_key))
    conn.commit()
    return key_id

def get_or_create_value(conn, key_id, attr_value):
    cur = conn.cursor()
    cur.execute("SELECT id FROM product_attribute_values WHERE attr_key_id=%s AND attr_value=%s", (key_id, attr_value))
    row = cur.fetchone()
    if row:
        return row[0]
    value_id = str(uuid.uuid4())
    cur.execute("INSERT INTO product_attribute_values (id, attr_key_id, attr_value) VALUES (%s, %s, %s)", (value_id, key_id, attr_value))
    conn.commit()
    return value_id

def link_product_value(conn, product_id, value_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM product_attribute_product WHERE product_id=%s AND attr_value_id=%s", (product_id, value_id))
    if not cur.fetchone():
        cur.execute("INSERT INTO product_attribute_product (id, product_id, attr_value_id) VALUES (%s, %s, %s)", (str(uuid.uuid4()), product_id, value_id))
        conn.commit()

def get_untranslated_keys(conn, lang_code):
    cur = conn.cursor()
    cur.execute("""
        SELECT k.id, k.attr_key FROM product_attribute_keys k
        LEFT JOIN product_attribute_key_translations t ON t.attr_key_id = k.id AND t.lang_code = %s
        WHERE t.id IS NULL
    """, (lang_code,))
    return cur.fetchall()

def get_untranslated_values(conn, lang_code):
    cur = conn.cursor()
    cur.execute("""
        SELECT v.id, v.attr_value FROM product_attribute_values v
        LEFT JOIN product_attribute_value_translations t ON t.attr_value_id = v.id AND t.lang_code = %s
        WHERE t.id IS NULL
    """, (lang_code,))
    return cur.fetchall()

def insert_key_translation(conn, key_id, lang_code, translation):
    cur = conn.cursor()
    cur.execute("INSERT INTO product_attribute_key_translations (id, attr_key_id, lang_code, value) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (str(uuid.uuid4()), key_id, lang_code, translation))
    conn.commit()

def insert_value_translation(conn, value_id, lang_code, translation):
    cur = conn.cursor()
    cur.execute("INSERT INTO product_attribute_value_translations (id, attr_value_id, lang_code, value) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (str(uuid.uuid4()), value_id, lang_code, translation))
    conn.commit()

def google_translate(text, source_lang, target_lang):
    if not text or text.strip() == "":
        return ""
    translate_client = translate.Client()
    for _ in range(3):
        try:
            result = translate_client.translate(text, source_language=source_lang, target_language=target_lang)
            return result["translatedText"]
        except Exception as e:
            print(f"Google Translate error: {e}. Retrying...")
            time.sleep(2)
    return text

def main():
    source_lang = 'zh'    # исходный язык атрибутов
    target_lang = 'en'    # целевой язык перевода
    conn = psycopg2.connect(**DB_CONFIG)

    # 1. Парсим продукты и строим уникальный справочник
    products = get_all_products()
    print(f"Found {len(products)} products.")
    for product_id, collection_id in products:
        attr_str = get_collection_attrs(collection_id)
        if not attr_str:
            continue
        pairs = parse_attributes(attr_str)
        for key, value in pairs:
            key_id = get_or_create_key(conn, key)
            value_id = get_or_create_value(conn, key_id, value)
            link_product_value(conn, product_id, value_id)
            print(f"{product_id} | {key} : {value}")

    # 2. Переводим только то, что ещё не переведено (batch)
    keys_to_translate = get_untranslated_keys(conn, target_lang)
    print(f"Untranslated keys: {len(keys_to_translate)}")
    for key_id, attr_key in keys_to_translate:
        trans = google_translate(attr_key, source_lang, target_lang)
        insert_key_translation(conn, key_id, target_lang, trans)
        print(f"Key: {attr_key} → {trans}")

    values_to_translate = get_untranslated_values(conn, target_lang)
    print(f"Untranslated values: {len(values_to_translate)}")
    for value_id, attr_value in values_to_translate:
        trans = google_translate(attr_value, source_lang, target_lang)
        insert_value_translation(conn, value_id, target_lang, trans)
        print(f"Value: {attr_value} → {trans}")

    conn.close()

if __name__ == "__main__":
    import sys
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        sys.stdout.reconfigure(encoding='utf-8')
    main()
