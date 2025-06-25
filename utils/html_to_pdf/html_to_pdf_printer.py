import pandas as pd
import pdfkit
import os
import sys
import re

if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

INPUT_CSV = 'utils\\html_to_pdf\\html.csv'
OUTPUT_CSV = 'utils\\html_to_pdf\\output.csv'
OUTPUT_FOLDER = 'utils\\html_to_pdf\\pdf_output'

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name.strip())[:100]

# Опции PDFKit
options = {
    'enable-local-file-access': None
}

df = pd.read_csv(INPUT_CSV)
pdf_paths = []

for _, row in df.iterrows():
    product_name = clean_filename(str(row['name']))
    html_content = str(row['details_html'])

    output_file = os.path.join(OUTPUT_FOLDER, f"{product_name}.pdf")

    try:
        pdfkit.from_string(html_content, output_file, options=options)
        pdf_paths.append(output_file)
    except Exception as e:
        print(f"Ошибка: {e}")
        pdf_paths.append("")

df['pdf_file'] = pdf_paths
df.to_csv(OUTPUT_CSV, index=False)

print(f"✅ Готово! CSV с путями PDF: {OUTPUT_CSV}")