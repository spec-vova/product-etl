#!/usr/bin/env python3
"""
Script to verify product collections data integrity and relationships
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

def verify_product_collections():
    """Comprehensive verification of product collections"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("=== PRODUCT COLLECTIONS VERIFICATION ===")
        print()
        
        # 1. Basic collection statistics
        print("1. COLLECTION STATISTICS:")
        cur.execute("SELECT COUNT(*) FROM product_collection;")
        total_collections = cur.fetchone()[0]
        print(f"   Total collections: {total_collections}")
        
        cur.execute("SELECT COUNT(DISTINCT master_code) FROM product_collection WHERE master_code IS NOT NULL;")
        unique_master_codes = cur.fetchone()[0]
        print(f"   Unique master codes: {unique_master_codes}")
        
        cur.execute("SELECT COUNT(*) FROM product_collection WHERE master_code IS NULL;")
        null_master_codes = cur.fetchone()[0]
        print(f"   Collections without master code: {null_master_codes}")
        print()
        
        # 2. Collection data completeness
        print("2. DATA COMPLETENESS:")
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(master_code) as has_master_code,
                COUNT(product_collection_sku) as has_sku,
                COUNT(product_collection_name) as has_name_id,
                COUNT(product_collection_image) as has_image,
                COUNT(inventory) as has_inventory
            FROM product_collection;
        """)
        result = cur.fetchone()
        print(f"   Total collections: {result[0]}")
        print(f"   With master code: {result[1]} ({result[1]/result[0]*100:.1f}%)")
        print(f"   With SKU: {result[2]} ({result[2]/result[0]*100:.1f}%)")
        print(f"   With name ID: {result[3]} ({result[3]/result[0]*100:.1f}%)")
        print(f"   With image: {result[4]} ({result[4]/result[0]*100:.1f}%)")
        print(f"   With inventory: {result[5]} ({result[5]/result[0]*100:.1f}%)")
        print()
        
        # 3. Sample collections with full data
        print("3. SAMPLE COLLECTIONS:")
        cur.execute("""
            SELECT 
                master_code,
                product_collection_sku,
                inventory,
                CASE WHEN product_collection_image IS NOT NULL THEN 'Yes' ELSE 'No' END as has_image,
                CASE WHEN video IS NOT NULL THEN 'Yes' ELSE 'No' END as has_video
            FROM product_collection
            WHERE master_code IS NOT NULL
            ORDER BY master_code
            LIMIT 10;
        """)
        results = cur.fetchall()
        if results:
            print("   Master Code | Collection SKU         | Inventory | Image | Video")
            print("   " + "-" * 70)
            for row in results:
                master_code = row[0] or 'NULL'
                sku = row[1] or 'NULL'
                inventory = str(row[2]) if row[2] is not None else 'NULL'
                has_image = row[3]
                has_video = row[4]
                print(f"   {master_code:<11} | {sku:<22} | {inventory:<9} | {has_image:<5} | {has_video}")
        print()
        
        # 4. Collections with translations
        print("4. COLLECTION TRANSLATIONS:")
        cur.execute("""
            SELECT COUNT(DISTINCT pc.id) as collections_with_translations
            FROM product_collection pc
            JOIN product_collection_translations pct ON pct.product_id = pc.id;
        """)
        result = cur.fetchone()
        collections_with_translations = result[0]
        print(f"   Collections with translations: {collections_with_translations}")
        
        cur.execute("""
            SELECT 
                pct.field_name,
                COUNT(*) as translation_count
            FROM product_collection_translations pct
            GROUP BY pct.field_name
            ORDER BY translation_count DESC;
        """)
        results = cur.fetchall()
        if results:
            print("   Translation fields:")
            for row in results:
                field_name = row[0]
                count = row[1]
                print(f"     {field_name}: {count} translations")
        print()
        
        # 5. Collections with images
        print("5. COLLECTION IMAGES:")
        cur.execute("""
            SELECT COUNT(DISTINCT pc.id) as collections_with_img_arrays
            FROM product_collection pc
            JOIN product_collection_product_collection_img_array pcpcia ON pcpcia.product_collection_id = pc.id;
        """)
        result = cur.fetchone()
        collections_with_images = result[0]
        print(f"   Collections with image arrays: {collections_with_images}")
        
        cur.execute("SELECT COUNT(*) FROM product_collection_img_array;")
        total_img_arrays = cur.fetchone()[0]
        print(f"   Total image arrays: {total_img_arrays}")
        print()
        
        # 6. Collections with categories
        print("6. COLLECTION CATEGORIES:")
        cur.execute("""
            SELECT COUNT(DISTINCT pc.id) as collections_with_categories
            FROM product_collection pc
            JOIN product_collection_category pcc ON pcc.product_collection_id = pc.id;
        """)
        result = cur.fetchone()
        collections_with_categories = result[0]
        print(f"   Collections with categories: {collections_with_categories}")
        print()
        
        # 7. Collections with custom attributes
        print("7. COLLECTION CUSTOM ATTRIBUTES:")
        cur.execute("""
            SELECT COUNT(DISTINCT pc.id) as collections_with_raw_attrs
            FROM product_collection pc
            JOIN product_collection_custom_attributes_raw pccar ON pccar.product_collection_id = pc.id;
        """)
        result = cur.fetchone()
        collections_with_raw_attrs = result[0]
        print(f"   Collections with raw attributes: {collections_with_raw_attrs}")
        
        cur.execute("""
            SELECT COUNT(DISTINCT pc.id) as collections_with_parsed_attrs
            FROM product_collection pc
            JOIN product_collection_custom_attributes_parsed pccap ON pccap.product_collection_id = pc.id;
        """)
        result = cur.fetchone()
        collections_with_parsed_attrs = result[0]
        print(f"   Collections with parsed attributes: {collections_with_parsed_attrs}")
        print()
        
        # 8. Product-Collection relationship analysis
        print("8. PRODUCT-COLLECTION RELATIONSHIPS:")
        cur.execute("""
            SELECT 
                pc.master_code,
                COUNT(p.id) as product_count,
                pc.inventory as collection_inventory
            FROM product_collection pc
            LEFT JOIN product p ON p.product_collection_master_code = pc.master_code
            WHERE pc.master_code IS NOT NULL
            GROUP BY pc.master_code, pc.inventory
            ORDER BY product_count DESC
            LIMIT 10;
        """)
        results = cur.fetchall()
        if results:
            print("   Master Code | Products | Collection Inventory")
            print("   " + "-" * 45)
            for row in results:
                master_code = row[0]
                product_count = row[1]
                collection_inventory = str(row[2]) if row[2] is not None else 'NULL'
                print(f"   {master_code:<11} | {product_count:<8} | {collection_inventory}")
        print()
        
        # 9. Orphaned collections (no products)
        print("9. ORPHANED COLLECTIONS:")
        cur.execute("""
            SELECT COUNT(*) as orphaned_collections
            FROM product_collection pc
            LEFT JOIN product p ON p.product_collection_master_code = pc.master_code
            WHERE p.id IS NULL AND pc.master_code IS NOT NULL;
        """)
        result = cur.fetchone()
        orphaned_collections = result[0]
        print(f"   Collections without products: {orphaned_collections}")
        
        if orphaned_collections > 0:
            cur.execute("""
                SELECT pc.master_code, pc.product_collection_sku
                FROM product_collection pc
                LEFT JOIN product p ON p.product_collection_master_code = pc.master_code
                WHERE p.id IS NULL AND pc.master_code IS NOT NULL
                LIMIT 5;
            """)
            results = cur.fetchall()
            print("   Sample orphaned collections:")
            for row in results:
                master_code = row[0]
                sku = row[1] or 'NULL'
                print(f"     {master_code} (SKU: {sku})")
        print()
        
        cur.close()
        conn.close()
        
        print("=== COLLECTION VERIFICATION COMPLETE ===")
        
    except Exception as e:
        print(f"Error during collection verification: {e}")
        return False
    
    return True

if __name__ == "__main__":
    verify_product_collections()