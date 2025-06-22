# /etl/custom_attributes.py

from sqlalchemy import create_engine, text
import re

# Пример подключения — замени на свои значения
DATABASE_URL = "postgresql+psycopg2://username:password@localhost:5432/dbname"

def parse_custom_attributes(raw_string):
    """Парсит строку атрибутов в словарь"""
    pairs = raw_string.strip().split('-')
    attributes = {}
    for pair in pairs:
        if ':' in pair:
            key, value = pair.split(':', 1)
            attributes[key.strip()] = value.strip()
    return attributes

def extract_all_raw_attributes():
    """Извлекает строки из таблицы custom_attributes_raw"""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, custom_attributes_raw FROM custom_attributes_raw"))
        return result.fetchall()

def insert_into_target_table(data):
    """Сохраняет разобранные данные в новую таблицу (например, custom_attributes_parsed)"""
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        for row_id, raw_text in data:
            parsed = parse_custom_attributes(raw_text)
            for key, value in parsed.items():
                conn.execute(
                    text("""
                        INSERT INTO custom_attributes_parsed (raw_id, attr_key, attr_value)
                        VALUES (:raw_id, :attr_key, :attr_value)
                    """),
                    {"raw_id": row_id, "attr_key": key, "attr_value": value}
                )

def run():
    raw_data = extract_all_raw_attributes()
    insert_into_target_table(raw_data)
