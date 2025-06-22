import psycopg2
import uuid

def get_custom_attributes_rows(db_config):
    """Чтение всех строк из custom_attributes_raw"""
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("SELECT id, custom_attributes_raw FROM custom_attributes_raw")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def parse_custom_attributes(raw_string):
    """Парсинг строки 'ключ:значение-ключ2:знач2' в dict"""
    if not raw_string:
        return {}
    result = {}
    for pair in raw_string.split('-'):
        if ':' in pair:
            key, value = pair.split(':', 1)
            result[key.strip()] = value.strip()
    return result

def insert_parsed_attributes(db_config, raw_id, attributes):
    """Вставляет каждую пару в custom_attributes_parsed"""
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    ids = []
    for k, v in attributes.items():
        parsed_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO custom_attributes_parsed (id, raw_id, attr_key, attr_value)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (parsed_id, raw_id, k, v)
        )
        ids.append(cur.fetchone()[0])
    conn.commit()
    cur.close()
    conn.close()
    return ids

def link_with_product_collections(db_config, raw_id, parsed_ids):
    """
    Связывает custom_attributes_parsed с product_collection через product_collection_custom_attributes_raw и product_collection_custom_attributes_parsed
    """
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    # Находим все коллекции, связанные с этим raw_id
    cur.execute(
        """
        SELECT product_collection_id FROM product_collection_custom_attributes_raw
        WHERE custom_attributes_raw_id = %s
        """,
        (raw_id,)
    )
    rows = cur.fetchall()
    product_collection_ids = [r[0] for r in rows]
    for collection_id in product_collection_ids:
        for parsed_id in parsed_ids:
            link_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO product_collection_custom_attributes_parsed (id, product_collection_id, custom_attributes_parsed_id)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (link_id, collection_id, parsed_id)
            )
    conn.commit()
    cur.close()
    conn.close()
