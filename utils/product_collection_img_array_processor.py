import os
import sys
import time
import csv
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === UTF-8 консоль для Windows ===
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5433))
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

IMAGES_FOLDER = Path(r"X:\DATA_STORAGE\Furnithai\pictures")
LOG_FILE = IMAGES_FOLDER / 'import_log.txt'
PROGRESS_CSV = IMAGES_FOLDER / 'import_progress.csv'
HEADERS = {"User-Agent": "Mozilla/5.0"}


def parse_img_array(img_array):
    if isinstance(img_array, list):
        return img_array
    if not img_array:
        return []
    s = img_array.strip('{}').replace('"', '')
    return [u.strip() for u in s.split(',') if u.strip()]


def download_image(url, save_path):
    try:
        r = requests.get(url, timeout=20, headers=HEADERS)
        r.raise_for_status()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(r.content)
        return True, None
    except Exception as e:
        return False, str(e)


def log(msg):
    print(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')


def load_progress():
    seen = set()
    if PROGRESS_CSV.exists():
        with open(PROGRESS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'] == 'success':
                    seen.add((row['collection_sku'], row['url']))
    else:
        # write header
        with open(PROGRESS_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['collection_sku','url','local_path','status','error'])
    return seen


def append_progress(collection_sku, url, local_path, status, error=''):
    with open(PROGRESS_CSV, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([collection_sku, url, str(local_path), status, error])


def main():
    IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    seen = load_progress()

    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT
            pc.product_collection_sku       AS collection_sku,
            pc.master_code,
            img_tbl.product_collection_img_array
        FROM product_collection pc
        JOIN product_collection_product_collection_img_array link_tbl
            ON link_tbl.product_collection_id = pc.id
        JOIN product_collection_img_array img_tbl
            ON img_tbl.id = link_tbl.product_collection_img_array;
    """)
    rows = cursor.fetchall()

    for row in tqdm(rows, desc='Collections'):
        collection_sku = row['collection_sku']
        master_code = row.get('master_code') or ''
        urls = parse_img_array(row['product_collection_img_array'])
        if not urls:
            log(f"[{collection_sku}] Нет фотографий.")
            continue

        local_paths = []
        for idx, url in enumerate(urls, start=1):
            if (collection_sku, url) in seen:
                log(f"[{collection_sku}] [SKIP] Уже загружено URL: {url}")
                continue

            ext = os.path.splitext(url)[1].split('?')[0] or '.jpg'
            filename = f"{collection_sku}_{idx}{ext}"
            save_path = IMAGES_FOLDER / collection_sku / filename

            ok, err = download_image(url, save_path)
            if ok:
                log(f"[{collection_sku}] [{filename}] Загружено.")
                append_progress(collection_sku, url, save_path, 'success')
            else:
                log(f"[{collection_sku}] [{filename}] Ошибка: {err}")
                append_progress(collection_sku, url, save_path, 'failed', err)
            time.sleep(1)

            # записать в БД
            cursor.execute(
                """
                INSERT INTO product_collection_images
                    (collection_sku, collection_master_code, image_index, url_original, url_local)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (collection_sku, master_code, idx, url, str(save_path))
            )
            local_paths.append(str(save_path))

        # обновить массив локальных путей в коллекции
        if local_paths:
            cursor.execute(
                """
                UPDATE product_collection
                SET images = %s
                WHERE product_collection_sku = %s;
                """,
                (local_paths, collection_sku)
            )

    conn.commit()
    cursor.close()
    conn.close()
    log('Процесс завершён.')

if __name__ == '__main__':
    main()
