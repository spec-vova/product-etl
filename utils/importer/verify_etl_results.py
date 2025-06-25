#!/usr/bin/env python3
"""
Script to verify ETL results by running SQL queries against the database
"""

import os
import psycopg2
from dotenv import load_dotenv

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

def run_verification_queries():
    """Run verification queries and display results"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("=== ETL VERIFICATION RESULTS ===")
        print()
        
        # Query 1: Total products
        print("1. TOTAL PRODUCTS:")
        cur.execute("SELECT COUNT(*) as total_products FROM product;")
        result = cur.fetchone()
        print(f"   Total products in database: {result[0]}")
        print()
        
        # Query 2: Products by master code
        print("2. PRODUCTS BY MASTER CODE:")
        cur.execute("""
            SELECT 
                product_collection_master_code,
                COUNT(*) as product_count
            FROM product 
            WHERE product_collection_master_code IS NOT NULL
            GROUP BY product_collection_master_code
            ORDER BY product_count DESC
            LIMIT 10;
        """)
        results = cur.fetchall()
        if results:
            print("   Master Code | Product Count")
            print("   " + "-" * 30)
            for row in results:
                master_code = row[0] or 'NULL'
                count = row[1]
                print(f"   {master_code:<11} | {count}")
        else:
            print("   No products with master codes found!")
        print()
        
        # Query 3: Sample SKUs from ETL log
        print("3. SAMPLE PRODUCTS BY SKU PATTERN:")
        cur.execute("""
            SELECT 
                product_collection_sku,
                product_selling_price,
                inventory
            FROM product 
            WHERE product_collection_sku LIKE '66862c-%' 
               OR product_collection_sku LIKE '74e760-%'
               OR product_collection_sku LIKE 'b09cc8-%'
            ORDER BY product_collection_sku
            LIMIT 10;
        """)
        results = cur.fetchall()
        if results:
            print("   SKU                    | Price  | Inventory")
            print("   " + "-" * 45)
            for row in results:
                sku = row[0] or 'NULL'
                price = row[1] or 'NULL'
                inventory = row[2] or 'NULL'
                print(f"   {sku:<22} | {price:<6} | {inventory}")
        else:
            print("   No products found with expected SKU patterns!")
        print()
        
        # Query 4: Product collections
        print("4. PRODUCT COLLECTIONS:")
        cur.execute("""
            SELECT 
                master_code,
                product_collection_sku,
                product_collection_name
            FROM product_collection
            ORDER BY master_code
            LIMIT 10;
        """)
        results = cur.fetchall()
        if results:
            print("   Master Code | Collection SKU         | Name ID")
            print("   " + "-" * 60)
            for row in results:
                master_code = row[0] or 'NULL'
                collection_sku = row[1] or 'NULL'
                name_id = str(row[2])[:8] + '...' if row[2] else 'NULL'
                print(f"   {master_code:<11} | {collection_sku:<22} | {name_id}")
        else:
            print("   No product collections found!")
        print()
        
        # Query 5: Check for orphaned products
        print("5. ORPHANED PRODUCTS (missing collection reference):")
        cur.execute("""
            SELECT COUNT(*)
            FROM product p
            LEFT JOIN product_collection pc ON pc.id = p.product_attributes_raw_collection_id
            WHERE pc.id IS NULL;
        """)
        result = cur.fetchone()
        orphaned_count = result[0]
        print(f"   Products without valid collection reference: {orphaned_count}")
        print()
        
        # Query 6: Sample products
        print("6. SAMPLE PRODUCTS:")
        cur.execute("""
            SELECT 
                product_collection_sku,
                product_selling_price,
                inventory,
                product_collection_master_code
            FROM product 
            WHERE product_collection_sku IS NOT NULL
            ORDER BY product_collection_sku
            LIMIT 10;
        """)
        results = cur.fetchall()
        if results:
            print("   SKU                    | Price  | Inventory | Master Code")
            print("   " + "-" * 65)
            for row in results:
                sku = row[0] or 'NULL'
                price = row[1] or 'NULL'
                inventory = row[2] or 'NULL'
                master_code = row[3] or 'NULL'
                print(f"   {sku:<22} | {price:<6} | {inventory:<9} | {master_code}")
        else:
            print("   No products with SKUs found!")
        print()
        
        cur.close()
        conn.close()
        
        print("=== VERIFICATION COMPLETE ===")
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_verification_queries()