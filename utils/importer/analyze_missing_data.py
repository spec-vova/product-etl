import psycopg2
from dotenv import load_dotenv
import os
import psycopg2

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

def analyze_missing_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Check for products without categories
    cur.execute("""
    SELECT p.id, p.product_collection_sku 
    FROM product p
    LEFT JOIN product_collection pc ON p.product_attributes_raw_collection_id = pc.id
    LEFT JOIN product_collection_category pcc ON pc.id = pcc.product_collection_id
    WHERE pcc.category_id IS NULL
    """)
    
    products_without_categories = cur.fetchall()
    print(f"Products without categories: {len(products_without_categories)}")
    
    # Check for collections without details
    cur.execute("""
    SELECT pc.id, pc.master_code
    FROM product_collection pc
    LEFT JOIN product_collection_details_html pcdh ON pc.id = pcdh.product_collection_id
    WHERE pcdh.details_html_id IS NULL
    """)
    
    collections_without_details = cur.fetchall()
    print(f"Collections without details: {len(collections_without_details)}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    analyze_missing_data()