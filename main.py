from dotenv import load_dotenv
import os
import sys

# Для Windows-консоли установить кодировку UTF-8
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    
from utils.custom_attributes_parser import (
    get_custom_attributes_rows,
    parse_custom_attributes,
    insert_parsed_attributes,
    link_with_product_collections
)

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": "5433",
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

def main():
    rows = get_custom_attributes_rows(DB_CONFIG)
    for raw_id, raw_str in rows:
        attrs = parse_custom_attributes(raw_str)
        if not attrs:
            continue
        parsed_ids = insert_parsed_attributes(DB_CONFIG, raw_id, attrs)
        link_with_product_collections(DB_CONFIG, raw_id, parsed_ids)
        print(f"Processed raw_id: {raw_id}, parsed_ids: {parsed_ids}")

if __name__ == "__main__":
    main()