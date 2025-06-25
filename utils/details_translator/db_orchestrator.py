# -*- coding: utf-8 -*-
import os
import sys
import psycopg2
from psycopg2.extras import execute_values
import uuid
from dotenv import load_dotenv
import re
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
import openai

# === UTF-8 console for Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": os.getenv("DB_PORT", "5433"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

# Paths
IMAGES_FOLDER = os.getenv("IMAGES_FOLDER", os.path.join(os.path.dirname(__file__), "images"))
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("[!] OPENAI_API_KEY not found in .env file")
    sys.exit(1)

# Logistics fields to extract
logistic_fields = [
    "packaging_features",
    "dimensions_cm",
    "volumetric_weight_kg",
    "actual_weight_kg",
    "logistics_notes"
]

# HTTP Headers
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Helper functions
def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

def extract_img_links(html):
    """Extract image links from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    return [img.get('src') for img in soup.find_all('img') if img.get('src')]

def is_missing(path):
    """Check if a file is missing"""
    return not Path(path).exists()

def download_image(url, save_path):
    """Download an image from URL"""
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        r.raise_for_status()
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"[!] Error downloading image: {e}")
        return False

def perform_ocr(img_path):
    """Perform OCR on an image"""
    try:
        img = Image.open(img_path)
        ocr_data = pytesseract.image_to_data(img, lang='chi_sim', output_type=pytesseract.Output.DICT)
        
        text_results = []
        for i, text in enumerate(ocr_data['text']):
            text_clean = text.strip()
            if text_clean:
                text_results.append(text_clean)
        
        return " ".join(text_results)
    except Exception as e:
        print(f"[!] OCR error: {e}")
        return ""

def translate_text(text):
    """Translate text using OpenAI"""
    if not text.strip():
        return ""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional translator specialized in product descriptions for furniture and home decor."},
                {"role": "user", "content": f"Translate the following Chinese text to English. It comes from product descriptions of furniture and home decor: {text}"}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[!] Translation error: {e}")
        return ""

def extract_logistics_info(text):
    """Extract logistics information using OpenAI"""
    if not text.strip():
        return {field: "" for field in logistic_fields}
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a logistics expert for international furniture shipments. Based on the provided product description, extract only logistics-relevant information and fill out the following fields: Packaging features, Dimensions in cm (HxLxW), Volumetric weight (kg), Actual weight (kg), and Logistics notes."},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
        )
        result = response.choices[0].message.content.strip().split("\n")
        values = [line.split(":", 1)[-1].strip() if ":" in line else "" for line in result]
        return dict(zip(logistic_fields, (values + [""] * len(logistic_fields))[:len(logistic_fields)]))
    except Exception as e:
        print(f"[!] Logistics extraction error: {e}")
        return {field: "" for field in logistic_fields}

# Main process functions
def get_products_with_html_details(conn):
    """Get products with HTML details from database"""
    cursor = conn.cursor()
    try:
        query = """
        SELECT p.id, pc.id as collection_id, p.sku, pc.details_html 
        FROM product p
        JOIN product_collection pc ON p.product_collection_id = pc.id
        WHERE pc.details_html IS NOT NULL AND pc.details_html != ''
        """
        
        # Apply filters if specified
        params = []
        
        # Filter by product ID
        product_id = os.getenv('PRODUCT_ID')
        if product_id:
            query += " AND p.id = %s"
            params.append(product_id)
        
        # Filter by collection ID
        collection_id = os.getenv('COLLECTION_ID')
        if collection_id:
            query += " AND pc.id = %s"
            params.append(collection_id)
        
        # Apply limit if specified
        limit = os.getenv('PROCESS_LIMIT')
        if limit and limit.isdigit() and int(limit) > 0:
            query += " LIMIT %s"
            params.append(int(limit))
        
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        print(f"[!] Database query error: {e}")
        return []
    finally:
        cursor.close()

def process_product_details(conn, product_id, collection_id, sku, html_details):
    """Process product details through the entire pipeline"""
    print(f"\n=== Processing product {sku} (ID: {product_id}) ===")
    
    # 1. Extract images from HTML
    image_urls = extract_img_links(html_details)
    if not image_urls:
        print(f"No images found for product {sku}")
        return
    
    print(f"Found {len(image_urls)} images")
    
    # 2. Download images (if not skipped)
    skip_download = os.getenv('SKIP_DOWNLOAD', 'false').lower() == 'true'
    image_paths = []
    
    if not skip_download:
        product_images_folder = os.path.join(IMAGES_FOLDER, product_id)
        Path(product_images_folder).mkdir(parents=True, exist_ok=True)
        
        for i, url in enumerate(image_urls):
            local_path = os.path.join(product_images_folder, f"{i:02d}.jpg")
            if is_missing(local_path):
                print(f"Downloading image {i+1}/{len(image_urls)}")
                if download_image(url, local_path):
                    image_paths.append(local_path)
                time.sleep(1)  # Avoid rate limiting
            else:
                image_paths.append(local_path)
    else:
        print("Skipping image download (--skip-download flag is set)")
        # Still need to collect existing image paths
        product_images_folder = os.path.join(IMAGES_FOLDER, product_id)
        for i in range(len(image_urls)):
            local_path = os.path.join(product_images_folder, f"{i:02d}.jpg")
            if not is_missing(local_path):
                image_paths.append(local_path)
    
    # 3. Perform OCR on images (if not skipped)
    skip_ocr = os.getenv('SKIP_OCR', 'false').lower() == 'true'
    combined_text = ""
    
    if not skip_ocr and image_paths:
        print("Performing OCR on images...")
        ocr_results = []
        for img_path in image_paths:
            text = perform_ocr(img_path)
            if text:
                ocr_results.append(text)
        
        combined_text = " ".join(ocr_results)
        if not combined_text:
            print(f"No text extracted from images for product {sku}")
            return
    else:
        if skip_ocr:
            print("Skipping OCR processing (--skip-ocr flag is set)")
            # Try to get existing OCR results from database
            cursor = conn.cursor()
            try:
                cursor.execute("""
                SELECT value FROM product_custom_attributes 
                WHERE product_id = %s AND attribute_name = 'ocr_text'
                """, (product_id,))
                result = cursor.fetchone()
                if result:
                    combined_text = result[0]
                    print("Using existing OCR text from database")
                else:
                    print("No existing OCR text found in database")
                    return
            except Exception as e:
                print(f"[!] Error retrieving OCR text: {e}")
                return
            finally:
                cursor.close()
        elif not image_paths:
            print("No images available for OCR processing")
            return
    
    # 4. Translate text (if not skipped)
    skip_translation = os.getenv('SKIP_TRANSLATION', 'false').lower() == 'true'
    translated_text = ""
    
    if not skip_translation and combined_text:
        print("Translating extracted text...")
        translated_text = translate_text(combined_text)
        if not translated_text:
            print(f"Translation failed for product {sku}")
            return
    else:
        if skip_translation:
            print("Skipping translation (--skip-translation flag is set)")
            # Try to get existing translation from database
            cursor = conn.cursor()
            try:
                # English language ID - should be configurable
                lang_id = "c1d8b146-e1a3-4e4e-a77e-3f7a0f3f9606"  # Assuming this is English
                cursor.execute("""
                SELECT value FROM product_translations 
                WHERE product_id = %s AND lang_id = %s AND field_name = 'product_description'
                """, (product_id, lang_id))
                result = cursor.fetchone()
                if result:
                    translated_text = result[0]
                    print("Using existing translation from database")
                else:
                    print("No existing translation found in database")
                    return
            except Exception as e:
                print(f"[!] Error retrieving translation: {e}")
                return
            finally:
                cursor.close()
        elif not combined_text:
            print("No text available for translation")
            return
    
    # 5. Extract logistics information (if not skipped)
    skip_logistics = os.getenv('SKIP_LOGISTICS', 'false').lower() == 'true'
    logistics_info = {}
    
    if not skip_logistics and translated_text:
        print("Extracting logistics information...")
        logistics_info = extract_logistics_info(translated_text)
    else:
        if skip_logistics:
            print("Skipping logistics extraction (--skip-logistics flag is set)")
            # Use empty logistics info
            logistics_info = {field: "" for field in logistic_fields}
        elif not translated_text:
            print("No translated text available for logistics extraction")
            return
    
    # 6. Store results in database
    print("Storing results in database...")
    store_results_in_db(conn, product_id, collection_id, translated_text, logistics_info, combined_text)

def store_results_in_db(conn, product_id, collection_id, translated_text, logistics_info, ocr_text=""):
    """Store processing results in database"""
    cursor = conn.cursor()
    try:
        # Store translated description
        trans_id = generate_uuid()
        # English language ID - should be configurable
        lang_id = "c1d8b146-e1a3-4e4e-a77e-3f7a0f3f9606"  # Assuming this is English
        field_name = "product_description"
        
        cursor.execute("""
        INSERT INTO product_translations 
        (id, product_id, lang_id, field_name, value)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (product_id, lang_id, field_name) DO UPDATE 
        SET value = EXCLUDED.value
        """, (trans_id, product_id, lang_id, field_name, translated_text))
        
        # Store OCR text for future reference if available
        if ocr_text:
            ocr_attr_id = generate_uuid()
            cursor.execute("""
            INSERT INTO product_custom_attributes 
            (id, product_id, attribute_name, value)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_id, attribute_name) DO UPDATE 
            SET value = EXCLUDED.value
            """, (ocr_attr_id, product_id, "ocr_text", ocr_text))
        
        # Store logistics information
        for field, value in logistics_info.items():
            if value:
                # Create or update custom attribute
                attr_id = generate_uuid()
                cursor.execute("""
                INSERT INTO product_custom_attributes 
                (id, product_id, attribute_name, value)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_id, attribute_name) DO UPDATE 
                SET value = EXCLUDED.value
                """, (attr_id, product_id, field, value))
        
        print("Database update successful")
    except Exception as e:
        print(f"[!] Database update error: {e}")
    finally:
        cursor.close()

def main():
    print("Starting Details Translator ETL process...")
    
    if DRY_RUN:
        print("DRY RUN MODE: No changes will be committed to the database")
    
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        # Get products with HTML details
        products = get_products_with_html_details(conn)
        print(f"Found {len(products)} products with HTML details")
        
        # Process each product
        for product in products:
            product_id, collection_id, sku, html_details = product
            process_product_details(conn, product_id, collection_id, sku, html_details)
            time.sleep(1)  # Avoid rate limiting
        
        # Commit all changes (unless in dry run mode)
        if not DRY_RUN:
            conn.commit()
            print("ETL process completed successfully! All changes committed.")
        else:
            conn.rollback()
            print("Dry run completed successfully! No changes were committed.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during ETL process: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()