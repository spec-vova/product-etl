# -*- coding: utf-8 -*-
import os
import sys
import psycopg2
from dotenv import load_dotenv
import openai
import pytesseract
from PIL import Image

# === UTF-8 console for Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection"""
    print("\n=== Testing Database Connection ===")
    
    # Database configuration
    db_config = {
        "host": "localhost",
        "port": os.getenv("DB_PORT", "5433"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASS")
    }
    
    # Check if required environment variables are set
    missing_vars = []
    for key, value in db_config.items():
        if key != "host" and (value is None or value.strip() == ""):
            missing_vars.append(key)
    
    if missing_vars:
        print("[!] Missing database configuration variables:")
        for var in missing_vars:
            print(f"  - {var.upper()}")
        print("Please set these variables in your .env file.")
        return False
    
    # Try to connect to the database
    try:
        print(f"Connecting to PostgreSQL database '{db_config['dbname']}' on {db_config['host']}:{db_config['port']}...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"Connection successful! PostgreSQL version: {version}")
        
        # Check if required tables exist
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND 
              table_name IN ('product', 'product_collection', 'product_translations', 'product_custom_attributes')
        """)
        tables = cursor.fetchall()
        tables = [t[0] for t in tables]
        
        required_tables = ['product', 'product_collection', 'product_translations', 'product_custom_attributes']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print("[!] Missing required tables:")
            for table in missing_tables:
                print(f"  - {table}")
            print("Please ensure these tables exist in your database.")
        else:
            print("All required tables found!")
        
        # Check if there are products with HTML details
        cursor.execute("""
        SELECT COUNT(*) 
        FROM product p
        JOIN product_collection pc ON p.product_collection_id = pc.id
        WHERE pc.details_html IS NOT NULL AND pc.details_html != ''
        """)
        product_count = cursor.fetchone()[0]
        print(f"Found {product_count} products with HTML details")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[!] Database connection error: {e}")
        return False

def test_tesseract():
    """Test Tesseract OCR installation"""
    print("\n=== Testing Tesseract OCR ===")
    
    tesseract_cmd = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    print(f"Tesseract path: {tesseract_cmd}")
    
    if not os.path.exists(tesseract_cmd):
        print(f"[!] Tesseract executable not found at: {tesseract_cmd}")
        print("Please install Tesseract OCR or set the correct path in your .env file.")
        return False
    
    # Set Tesseract path
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    try:
        # Get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract version: {version}")
        print("Tesseract OCR is properly configured!")
        return True
    except Exception as e:
        print(f"[!] Tesseract error: {e}")
        return False

def test_openai_api():
    """Test OpenAI API key"""
    print("\n=== Testing OpenAI API ===")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[!] OPENAI_API_KEY not found in .env file")
        print("Please set your OpenAI API key in the .env file.")
        return False
    
    # Set OpenAI API key
    openai.api_key = api_key
    
    try:
        # Test API connection with a simple request
        print("Testing API connection...")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=5
        )
        print("OpenAI API connection successful!")
        return True
    except Exception as e:
        print(f"[!] OpenAI API error: {e}")
        return False

def test_images_folder():
    """Test images folder"""
    print("\n=== Testing Images Folder ===")
    
    images_folder = os.getenv("IMAGES_FOLDER", os.path.join(os.path.dirname(__file__), "images"))
    print(f"Images folder: {images_folder}")
    
    if not os.path.exists(images_folder):
        print(f"Creating images folder: {images_folder}")
        try:
            os.makedirs(images_folder, exist_ok=True)
            print("Images folder created successfully!")
        except Exception as e:
            print(f"[!] Error creating images folder: {e}")
            return False
    else:
        print("Images folder exists!")
    
    return True

def main():
    print("=== Details Translator Environment Test ===")
    print("Testing environment setup...\n")
    
    # Test database connection
    db_ok = test_database_connection()
    
    # Test Tesseract OCR
    tesseract_ok = test_tesseract()
    
    # Test OpenAI API
    openai_ok = test_openai_api()
    
    # Test images folder
    images_ok = test_images_folder()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Database connection: {'✓' if db_ok else '✗'}")
    print(f"Tesseract OCR: {'✓' if tesseract_ok else '✗'}")
    print(f"OpenAI API: {'✓' if openai_ok else '✗'}")
    print(f"Images folder: {'✓' if images_ok else '✗'}")
    
    if db_ok and tesseract_ok and openai_ok and images_ok:
        print("\nAll tests passed! You're ready to run the details translator.")
        print("Run 'python run_orchestrator.py --help' for usage information.")
    else:
        print("\nSome tests failed. Please fix the issues before running the details translator.")

if __name__ == "__main__":
    main()