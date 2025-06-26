import psycopg2
import uuid
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "port": os.getenv("DB_PORT", "5433"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

def insert_missing_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # Example: Insert missing web page details for collections
        # First, find collections without details
        cur.execute("""
        SELECT pc.id, pc.master_code
        FROM product_collection pc
        LEFT JOIN product_collection_details_html pcdh ON pc.id = pcdh.product_collection_id
        WHERE pcdh.details_html_id IS NULL
        LIMIT 5
        """)
        
        collections_without_details = cur.fetchall()
        
        for collection_id, master_code in collections_without_details:
            # Create sample HTML details
            details_html_content = f"<h1>Product Details for {master_code}</h1><p>Sample product description and specifications.</p>"
            
            # Insert into details_html table
            details_id = str(uuid.uuid4())
            details_html_ref_id = str(uuid.uuid4())
            
            # First insert HTML content into details_html_translations
            cur.execute("""
            INSERT INTO details_html_translations (id, details_html_id, lang_id, field_name, value)
            VALUES (%s, %s, %s, %s, %s)
            """, (details_html_ref_id, details_id, "365d96e3-9f08-4d2e-bf17-18a26a5072f7", "details_html", details_html_content))
            
            # Then insert into details_html table
            cur.execute("""
            INSERT INTO details_html (id, details_html)
            VALUES (%s, %s)
            """, (details_id, details_html_ref_id))
            
            # Link to product collection
            link_id = str(uuid.uuid4())
            cur.execute("""
            INSERT INTO product_collection_details_html (id, product_collection_id, details_html_id)
            VALUES (%s, %s, %s)
            """, (link_id, collection_id, details_id))
            
            print(f"Inserted details for collection: {master_code}")
        
        conn.commit()
        print("Missing data insertion completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error inserting missing data: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    insert_missing_data()