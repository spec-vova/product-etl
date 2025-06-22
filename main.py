import csv
from parse_custom_attributes import parse_custom_attributes

INPUT_CSV = 'custom_attributes_raw.csv'   # Файл должен содержать столбец "id" и "custom_attributes_raw"
OUTPUT_JSON = 'parsed_attributes.json'    # Временно — просто для отладки

parsed_results = []

with open(INPUT_CSV, mode='r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        parsed = parse_custom_attributes(row['custom_attributes_raw'])
        parsed_results.append({
            "id": row['id'],
            "parsed_attributes": parsed
        })

# Пример вывода в файл (временно)
import json
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(parsed_results, f, ensure_ascii=False, indent=2)

print("✅ Parsed", len(parsed_results), "rows.")
