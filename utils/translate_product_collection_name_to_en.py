import os
from dotenv import load_dotenv
import psycopg2
import uuid
import time
from google.cloud import translate_v2 as translate
import sys

if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

# Твои значения lang_id — меняй если понадобится
ZH_LANG_ID = '365d96e3-9f08-4d2e-bf17-18a26a5072f7'
EN_LANG_ID = 'ff5ad46b-1f8f-4443-98a8-23674ca0d484'
FIELD_NAME = 'product_collection_name'

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_collections_without_english():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT pct.product_id, pct.value
        FROM product_collection_translations pct
        WHERE pct.lang_id = %s
          AND pct.field_name = %s
          AND NOT EXISTS (
              SELECT 1 FROM product_collection_translations pct2
              WHERE pct2.product_id = pct.product_id AND pct2.lang_id = %s AND pct2.field_name = %s
          )
    """, (ZH_LANG_ID, FIELD_NAME, EN_LANG_ID, FIELD_NAME))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def insert_english_name(product_id, name_en):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO product_collection_translations (id, product_id, lang_id, field_name, value)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (str(uuid.uuid4()), product_id, EN_LANG_ID, FIELD_NAME, name_en))
    conn.commit()
    cur.close()
    conn.close()

def google_translate(text, target_lang="en"):
    if not text or text.strip() == "":
        return ""
    translate_client = translate.Client()
    for _ in range(3):
        try:
            result = translate_client.translate(text, target_language=target_lang)
            return result["translatedText"]
        except Exception as e:
            print(f"Google Translate error: {e}. Retrying...")
            time.sleep(2)
    return text

def main():
    rows = get_collections_without_english()
    print(f"Need to translate {len(rows)} collection names...")
    for product_id, name_original in rows:
        name_en = google_translate(name_original)
        insert_english_name(product_id, name_en)
        print(f"[OK] {name_original} --> {name_en}")

if __name__ == "__main__":
    main()
