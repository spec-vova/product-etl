import pandas as pd
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys

if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# === Настройки ===
INPUT_CSV = 'utils\\html_to_pdf\\html_shorter.csv'
OUTPUT_DIR = Path("utils\\html_to_pdf\\pdf_outputs")
OUTPUT_CSV = "utils\\html_to_pdf\\output_with_pdf.csv"

# === Подготовка папки ===
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === Загрузка данных ===
df = pd.read_csv(INPUT_CSV, delimiter=";")
pdf_paths = []

# === Рендеринг PDF ===
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 8000})  # Высота большая

    for idx, row in df.iterrows():
        product_id = row[0]
        product_name = str(row[1]).strip().replace(" ", "_").replace("/", "_")
        html_content = row[2]

        # Сохраняем временный HTML
        html_path = OUTPUT_DIR / f"{product_name}.html"
        html_path.write_text(html_content, encoding="utf-8")

        # Загружаем HTML в браузер
        page.goto(f"file://{html_path.resolve()}")
        page.emulate_media(media="screen")

        height_px = page.evaluate("() => document.body.scrollHeight")
        height_mm = f"{height_px * 0.264583}mm"  # px → mm

        pdf_path = OUTPUT_DIR / f"{product_name}.pdf"
        page.pdf(
            path=str(pdf_path),
            print_background=True,
            width="210mm",  # A4 ширина
            height=height_mm
        )
        pdf_paths.append(str(pdf_path))

    browser.close()

# === Добавляем колонку и сохраняем CSV ===
df["pdf_path"] = pdf_paths
df.to_csv(OUTPUT_CSV, index=False)
print(f"Saved to {OUTPUT_CSV}")
