import os
import sys
import time
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
HEADERS = {"User-Agent": "Mozilla/5.0"}


def parse_img_array(img_array):
    if isinstance(img_array, list):
        # Фильтруем только URL из массива, игнорируя числовые параметры
        urls = []
        for item in img_array:
            item_str = str(item).strip()
            # Очищаем от лишних символов в начале
            item_str = item_str.lstrip('["')
            # Проверяем, что это URL (начинается с http/https)
            if item_str.startswith(('http://', 'https://')):
                urls.append(item_str)
        return urls
    if not img_array:
        return []
    s = img_array.strip('{}').replace('"', '')
    items = [u.strip() for u in s.split(',') if u.strip()]
    # Фильтруем только URL из строкового массива
    urls = []
    for item in items:
        item = item.lstrip('["')
        if item.startswith(('http://', 'https://')):
            urls.append(item)
    return urls


def download_image(url, save_path):
    try:
        r = requests.get(url, timeout=20, headers=HEADERS)
        r.raise_for_status()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(r.content)
        return True, None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False, '404 Not Found'
        return False, str(e)
    except Exception as e:
        return False, str(e)


def log(msg):
    print(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')





def get_collections_without_images(cursor):
    """Получить коллекции, у которых нет обработанных изображений в БД"""
    cursor.execute("""
        SELECT
            pc.product_collection_sku       AS collection_sku,
            pc.master_code,
            img_tbl.product_collection_img_array
        FROM product_collection pc
        JOIN product_collection_product_collection_img_array link_tbl
            ON link_tbl.product_collection_id = pc.id
        JOIN product_collection_img_array img_tbl
            ON img_tbl.id = link_tbl.product_collection_img_array
        LEFT JOIN product_collection_images pci
            ON pci.collection_sku = pc.product_collection_sku
        WHERE pci.collection_sku IS NULL;
    """)
    return cursor.fetchall()


def get_processed_urls_from_db(cursor, collection_sku):
    """Получить уже обработанные URL для конкретной коллекции из БД"""
    cursor.execute("""
        SELECT url_original
        FROM product_collection_images
        WHERE collection_sku = %s;
    """, (collection_sku,))
    return {row['url_original'] for row in cursor.fetchall()}


def main():
    IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Получаем только коллекции без обработанных изображений
    rows = get_collections_without_images(cursor)
    log(f"Найдено {len(rows)} коллекций без обработанных изображений.")

    for row in tqdm(rows, desc='Collections'):
        collection_sku = row['collection_sku']
        master_code = row.get('master_code') or ''
        urls = parse_img_array(row['product_collection_img_array'])
        if not urls:
            log(f"[{collection_sku}] Нет фотографий.")
            continue

        # Получаем уже обработанные URL для этой коллекции из БД
        processed_urls = get_processed_urls_from_db(cursor, collection_sku)
        
        local_paths = []
        for idx, url in enumerate(urls, start=1):
            if url in processed_urls:
                continue  # Пропускаем без логирования

            ext = os.path.splitext(url)[1].split('?')[0] or '.jpg'
            filename = f"{collection_sku}_{idx}{ext}"
            save_path = IMAGES_FOLDER / collection_sku / filename

            ok, err = download_image(url, save_path)
            if ok:
                log(f"[{collection_sku}] [{filename}] Загружено.")
                # Записываем в БД только при успешной загрузке
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
            else:
                if err == '404 Not Found':
                    log(f"[{collection_sku}] [{filename}] Ошибка 404: Файл не найден по URL: {url}")
                else:
                    log(f"[{collection_sku}] [{filename}] Ошибка загрузки: {err}")
            
            time.sleep(0.5) # Снижаем задержку



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
