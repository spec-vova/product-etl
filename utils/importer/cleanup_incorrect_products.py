#!/usr/bin/env python3
"""
Cleanup script to remove incorrectly processed products from the database.
This script removes products that were created with random UUIDs instead of proper collection links.

Run this before executing the corrected ETL.py to ensure clean data.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create database connection using environment variables."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5433'),
            database=os.getenv('DB_NAME', 'furnithai_products'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS', '')
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def cleanup_incorrect_products():
    """Remove products with incorrect collection links."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Starting cleanup of incorrectly linked products...")
        
        # Find products with product_attributes_raw_collection_id that don't exist in product_collection
        cur.execute("""
        SELECT p.id, p.product_collection_sku, p.product_attributes_raw_collection_id
        FROM product p
        LEFT JOIN product_collection pc ON p.product_attributes_raw_collection_id = pc.id
        WHERE pc.id IS NULL
        AND p.product_attributes_raw_collection_id IS NOT NULL
        """)
        
        incorrect_products = cur.fetchall()
        
        if not incorrect_products:
            print("No incorrectly linked products found.")
            return True
        
        print(f"Found {len(incorrect_products)} incorrectly linked products.")
        
        # Show some examples
        print("\nExamples of incorrect products:")
        for i, product in enumerate(incorrect_products[:5]):
            print(f"  {i+1}. SKU: {product['product_collection_sku']}, "
                  f"Invalid Collection ID: {product['product_attributes_raw_collection_id']}")
        
        if len(incorrect_products) > 5:
            print(f"  ... and {len(incorrect_products) - 5} more")
        
        # Ask for confirmation
        response = input(f"\nDo you want to delete these {len(incorrect_products)} incorrect products? (y/N): ")
        
        if response.lower() != 'y':
            print("Cleanup cancelled.")
            return False
        
        # Delete incorrect products
        product_ids = [p['id'] for p in incorrect_products]
        
        # Delete in batches to avoid memory issues
        batch_size = 100
        deleted_count = 0
        
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]
            
            # Delete related records first (if tables exist)
            try:
                cur.execute("""
                DELETE FROM product_translations 
                WHERE product_id = ANY(%s)
                """, (batch,))
                print(f"Deleted product_translations for batch {i//batch_size + 1}")
            except errors.UndefinedTable:
                print("Table product_translations does not exist, skipping...")
                conn.rollback()  # Rollback the failed transaction
                cur = conn.cursor(cursor_factory=RealDictCursor)  # Get new cursor
            except Exception as e:
                print(f"Error deleting from product_translations: {e}")
                conn.rollback()
                cur = conn.cursor(cursor_factory=RealDictCursor)
            
            try:
                cur.execute("""
                DELETE FROM product_custom_attributes 
                WHERE product_id = ANY(%s)
                """, (batch,))
                print(f"Deleted product_custom_attributes for batch {i//batch_size + 1}")
            except errors.UndefinedTable:
                print("Table product_custom_attributes does not exist, skipping...")
                conn.rollback()
                cur = conn.cursor(cursor_factory=RealDictCursor)
            except Exception as e:
                print(f"Error deleting from product_custom_attributes: {e}")
                conn.rollback()
                cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Delete the products
            cur.execute("""
            DELETE FROM product 
            WHERE id = ANY(%s::uuid[])
            """, (batch,))
            
            deleted_count += len(batch)
            print(f"Deleted {deleted_count}/{len(product_ids)} products...")
            conn.commit()  # Commit after each successful batch
        
        # Also clean up orphaned custom_attributes_raw records
        print("\nCleaning up orphaned custom attributes...")
        cur.execute("""
        DELETE FROM custom_attributes_raw car
        WHERE NOT EXISTS (
            SELECT 1 FROM product p 
            WHERE p.product_attributes_raw_collection_id = car.id
        )
        AND NOT EXISTS (
            SELECT 1 FROM product_collection_custom_attributes_raw pccar 
            WHERE pccar.custom_attributes_raw_id = car.id
        )
        """)
        
        orphaned_attrs = cur.rowcount
        print(f"Deleted {orphaned_attrs} orphaned custom attributes.")
        conn.commit()  # Commit the orphaned attributes cleanup
        
        print(f"\nCleanup completed successfully!")
        print(f"- Deleted {deleted_count} incorrect products")
        print(f"- Deleted {orphaned_attrs} orphaned custom attributes")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error during cleanup: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def verify_cleanup():
    """Verify that cleanup was successful."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Check for remaining incorrect products
        cur.execute("""
        SELECT COUNT(*) as count
        FROM product p
        LEFT JOIN product_collection pc ON p.product_attributes_raw_collection_id = pc.id
        WHERE pc.id IS NULL
        AND p.product_attributes_raw_collection_id IS NOT NULL
        """)
        
        remaining = cur.fetchone()[0]
        
        if remaining == 0:
            print("\n✅ Verification successful: No incorrectly linked products remain.")
        else:
            print(f"\n⚠️  Warning: {remaining} incorrectly linked products still exist.")
        
        # Show current product count
        cur.execute("SELECT COUNT(*) FROM product")
        total_products = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM product_collection")
        total_collections = cur.fetchone()[0]
        
        print(f"\nCurrent database state:")
        print(f"- Total products: {total_products}")
        print(f"- Total collections: {total_collections}")
        
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Product Cleanup Script")
    print("=" * 50)
    
    if cleanup_incorrect_products():
        verify_cleanup()
        print("\nYou can now run the corrected ETL.py script.")
    else:
        print("\nCleanup failed or was cancelled.")