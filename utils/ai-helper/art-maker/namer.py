import csv
import openai
import os
import time
import sys

if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')
    

key = 

client = openai.OpenAI(api_key= key)

INPUT_CSV = "X:\\DATA_STORAGE\\Furnithai\\utils\\ai-helper\\art-maker\\input_products.csv"
OUTPUT_CSV = "X:\\DATA_STORAGE\\Furnithai\\utils\\ai-helper\\art-maker\\output_products_with_gpt.csv"

def generate_name_and_sku(category, product_collection, attributes):
    prompt = (
        f"You are an expert merchandiser for a furniture retailer. "
        f"Given the product category: \"{category}\", collection: \"{product_collection}\", and attributes: \"{attributes}\", "
        f"1. Suggest a short, natural English product  name (max 7 words), name should starting with product definition for example: Curtains, brown, lengh: **, high: **, style:.\n"
        f"2. Invent a SKU/article code (6-12 alphanumeric chars, hinting at category or collection).\n"
        f"Return as:\nName: ...\nSKU: ..."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        result = response.choices[0].message.content.strip()
        name_line = next((l for l in result.splitlines() if l.startswith("Name:")), "")
        sku_line = next((l for l in result.splitlines() if l.startswith("SKU:")), "")
        name = name_line.replace("Name:", "").strip()
        sku = sku_line.replace("SKU:", "").strip()
        return name, sku
    except Exception as e:
        print(f"Error: {e}")
        return "", ""

def main():
    with open(INPUT_CSV, newline='', encoding='utf-8') as infile, \
         open(OUTPUT_CSV, "w", newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        rows = list(reader)
        header = rows[0]
        header += ["normalized_name", "sku"]
        writer = csv.writer(outfile)
        writer.writerow(header)
        for row in rows[1:]:
            category = row[1]
            collection = row[2]
            attributes = row[3]
            print(f"Processing: {category} / {collection} / {attributes}".encode("utf-8", errors="replace").decode("utf-8"))
            name, sku = generate_name_and_sku(category, collection, attributes)
            row += [name, sku]
            writer.writerow(row)
            time.sleep(1.2)  # чтобы не словить лимиты

if __name__ == "__main__":
    main()