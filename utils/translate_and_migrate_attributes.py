# -*- coding: utf-8 -*-
import sys
import os
import uuid
from dotenv import load_dotenv
import psycopg2
from google.cloud import translate_v2 as translate


# Для Windows-консоли установить кодировку UTF-8
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')
    
# ===== Настройки =====
load_dotenv()
DB_CONFIG = {
    "host": "localhost",
    "port": "5433",
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}
GOOGLE_CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# ===== Базовые функции подключения =====
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# ===== 1. Автосоздание таблиц =====
def create_translation_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS public.custom_attributes_keys_translations (
        id uuid NOT NULL DEFAULT gen_random_uuid(),
        attr_key text NOT NULL,
        lang_code varchar(10) NOT NULL,
        value text NOT NULL,
        CONSTRAINT custom_attributes_keys_translations_pkey PRIMARY KEY (id),
        CONSTRAINT unique_key_lang UNIQUE (attr_key, lang_code)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS public.custom_attributes_values_translations (
        id uuid NOT NULL DEFAULT gen_random_uuid(),
        attr_key text NOT NULL,
        attr_value text NOT NULL,
        lang_code varchar(10) NOT NULL,
        value text NOT NULL,
        CONSTRAINT custom_attributes_values_translations_pkey PRIMARY KEY (id),
        CONSTRAINT unique_value_lang UNIQUE (attr_key, attr_value, lang_code)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

# ===== 2. Собрать уникальные ключи/значения =====
def get_unique_keys_and_values():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT attr_key FROM custom_attributes_parsed")
    keys = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT DISTINCT attr_key, attr_value FROM custom_attributes_parsed")
    values = cur.fetchall()
    cur.close()
    conn.close()
    return keys, values

# ===== 3. Проверка, есть ли перевод =====
def translation_exists(table, attr_key, attr_value=None):
    conn = get_connection()
    cur = conn.cursor()
    if table == "keys":
        cur.execute("""
            SELECT 1 FROM custom_attributes_keys_translations
            WHERE attr_key = %s AND lang_code = 'en'
        """, (attr_key,))
    else:
        cur.execute("""
            SELECT 1 FROM custom_attributes_values_translations
            WHERE attr_key = %s AND attr_value = %s AND lang_code = 'en'
        """, (attr_key, attr_value))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

# ===== 4. Вставка перевода =====
def insert_key_translation(attr_key, value_en):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO custom_attributes_keys_translations (id, attr_key, lang_code, value)
        VALUES (%s, %s, 'en', %s)
        ON CONFLICT (attr_key, lang_code) DO NOTHING
    """, (str(uuid.uuid4()), attr_key, value_en))
    conn.commit()
    cur.close()
    conn.close()

def insert_value_translation(attr_key, attr_value, value_en):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO custom_attributes_values_translations (id, attr_key, attr_value, lang_code, value)
        VALUES (%s, %s, %s, 'en', %s)
        ON CONFLICT (attr_key, attr_value, lang_code) DO NOTHING
    """, (str(uuid.uuid4()), attr_key, attr_value, value_en))
    conn.commit()
    cur.close()
    conn.close()

# ===== 5. Перевод через Google Translate =====
def google_translate(text, target_lang="en"):
    if not text or text.strip() == "":
        return ""
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language=target_lang)
    return result["translatedText"]

# ===== 6. Основной цикл =====
def main():
    print("Создаём таблицы переводов (если ещё не созданы)...")
    create_translation_tables()
    print("ОК!\nСобираем уникальные ключи и значения...")
    keys, values = get_unique_keys_and_values()
    print(f"Уникальных ключей: {len(keys)}, уникальных пар ключ-значение: {len(values)}\n")

    print("Переводим ключи...")
    for key in keys:
        if translation_exists("keys", key):
            print(f"[SKIP] Key '{key}' уже переведён.")
            continue
        translated = google_translate(key)
        insert_key_translation(key, translated)
        print(f"[OK] {key} → {translated}")

    print("\nПереводим значения...")
    for attr_key, attr_value in values:
        if translation_exists("values", attr_key, attr_value):
            print(f"[SKIP] Value '{attr_key}: {attr_value}' уже переведено.")
            continue
        translated = google_translate(attr_value)
        insert_value_translation(attr_key, attr_value, translated)
        print(f"[OK] {attr_key}: {attr_value} → {translated}")

    print("\nВсё готово! Переводы ключей и значений занесены в базу.")

if __name__ == "__main__":
    main()
