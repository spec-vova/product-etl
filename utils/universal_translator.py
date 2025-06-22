# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
import psycopg2
import uuid
import time
from google.cloud import translate_v2 as translate

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

def get_lang_id(lang_code):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id FROM lang WHERE lang_code = %s", (lang_code,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def google_translate(text, source_lang, target_lang):
    if not text or text.strip() == "":
        return ""
    translate_client = translate.Client()
    for _ in range(3):
        try:
            result = translate_client.translate(
                text,
                source_language=source_lang,
                target_language=target_lang
            )
            return result["translatedText"]
        except Exception as e:
            print(f"Google Translate error: {e}. Retrying...")
            time.sleep(2)
    return text

def get_rows_to_translate(table, field, orig_lang_id, target_lang_id):
    # Проверим есть ли field_name
    field_name_clause = ""
    # Если в таблице есть field_name - ищем только нужное поле
    if field != 'value':
        field_name_clause = f"AND field_name = '{field}'"
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(f'''
        SELECT t.id, t.{field}
        FROM {table} t
        WHERE t.lang_id = %s
          {field_name_clause}
          AND NOT EXISTS (
              SELECT 1 FROM {table} t2
              WHERE t2.id != t.id
                AND t2.lang_id = %s
                AND t2.{field} = t.{field}
                {field_name_clause}
          )
    ''', (orig_lang_id, target_lang_id))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def insert_translation(table, row_id, field, value_en, target_lang_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    # Узнать, есть ли поле field_name
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name='field_name'", (table,))
    has_field_name = cur.fetchone() is not None
    # Узнать, какое *_id поле связывает с сущностью (кроме lang_id и id)
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name LIKE '%%_id' AND column_name != 'lang_id' AND column_name != 'id'", (table,))
    entity_id_field = cur.fetchone()
    entity_id_value = None
    if entity_id_field:
        entity_id_field = entity_id_field[0]
        cur.execute(f"SELECT {entity_id_field} FROM {table} WHERE id=%s", (row_id,))
        entity_id_value = cur.fetchone()[0]
    if has_field_name and entity_id_field:
        cur.execute(f"SELECT field_name FROM {table} WHERE id=%s", (row_id,))
        field_name = cur.fetchone()[0]
        cur.execute(
            f"INSERT INTO {table} (id, {entity_id_field}, lang_id, field_name, {field}) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (str(uuid.uuid4()), entity_id_value, target_lang_id, field_name, value_en)
        )
    elif has_field_name:
        cur.execute(f"SELECT field_name FROM {table} WHERE id=%s", (row_id,))
        field_name = cur.fetchone()[0]
        cur.execute(
            f"INSERT INTO {table} (id, lang_id, field_name, {field}) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (str(uuid.uuid4()), target_lang_id, field_name, value_en)
        )
    elif entity_id_field:
        cur.execute(
            f"INSERT INTO {table} (id, {entity_id_field}, lang_id, {field}) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (str(uuid.uuid4()), entity_id_value, target_lang_id, value_en)
        )
    else:
        cur.execute(
            f"INSERT INTO {table} (id, lang_id, {field}) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (str(uuid.uuid4()), target_lang_id, value_en)
        )
    conn.commit()
    cur.close()
    conn.close()


def main():
    # --- настройки ---
    table = 'category_translations'         # Название таблицы
    field = 'value'                        # Имя поля, которое нужно переводить
    source_lang = 'zh'                     # Исходный язык (двухбуквенный код)
    target_lang = 'en'                     # Язык для перевода (двухбуквенный код)
    # ---------------
    orig_lang_id = get_lang_id(source_lang)
    target_lang_id = get_lang_id(target_lang)
    rows = get_rows_to_translate(table, field, orig_lang_id, target_lang_id)
    print(f"Need to translate {len(rows)} items...")
    for row_id, value_orig in rows:
        value_en = google_translate(value_orig, source_lang, target_lang)
        insert_translation(table, row_id, field, value_en, target_lang_id)
        print(f"[OK] {value_orig} → {value_en}")

if __name__ == "__main__":
    import sys
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        sys.stdout.reconfigure(encoding='utf-8')
    main()
