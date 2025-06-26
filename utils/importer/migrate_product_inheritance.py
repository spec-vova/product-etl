#!/usr/bin/env python3
"""
Migration script to add inherited fields from product_collection to product table
and update existing products with inherited values.

This script:
1. Adds new columns to product table if they don't exist
2. Updates existing products to inherit values from their parent collections
3. Provides detailed reporting of changes
"""

import os
import sys
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

def check_columns_exist(cur):
    """Check if the inherited columns already exist in product table"""
    cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'product' 
    AND column_name IN ('product_collection_url', 'product_collection_image', 'images')
    """)
    
    existing_columns = [row[0] for row in cur.fetchall()]
    return existing_columns

def add_inherited_columns(cur):
    """Add inherited columns to product table"""
    print("Adding inherited columns to product table...")
    
    cur.execute("""
    ALTER TABLE product 
    ADD COLUMN IF NOT EXISTS product_collection_url text,
    ADD COLUMN IF NOT EXISTS product_collection_image text,
    ADD COLUMN IF NOT EXISTS images text[];
    """)
    
    # Add comments
    cur.execute("""
    COMMENT ON COLUMN product.product_collection_url IS 'Inherited from parent product_collection.product_collection_url';
    COMMENT ON COLUMN product.product_collection_image IS 'Inherited from parent product_collection.product_collection_image';
    COMMENT ON COLUMN product.images IS 'Inherited from parent product_collection.images array';
    """)
    
    # Create indexes
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_product_collection_url ON product(product_collection_url);
    CREATE INDEX IF NOT EXISTS idx_product_collection_image ON product(product_collection_image);
    """)
    
    print("✅ Columns and indexes created successfully")

def get_migration_stats(cur):
    """Get statistics before migration"""
    cur.execute("""
    SELECT 
        COUNT(*) as total_products,
        COUNT(CASE WHEN product_collection_master_code IS NOT NULL THEN 1 END) as products_with_master_code,
        COUNT(CASE WHEN product_collection_url IS NOT NULL THEN 1 END) as products_with_url,
        COUNT(CASE WHEN product_collection_image IS NOT NULL THEN 1 END) as products_with_image,
        COUNT(CASE WHEN images IS NOT NULL THEN 1 END) as products_with_images
    FROM product
    """)
    
    return cur.fetchone()

def update_inherited_fields(cur):
    """Update existing products with inherited values from collections"""
    print("Updating existing products with inherited values...")
    
    # Get stats before update
    before_stats = get_migration_stats(cur)
    
    # Perform the update
    cur.execute("""
    UPDATE product 
    SET 
        product_collection_url = pc.product_collection_url,
        product_collection_image = pc.product_collection_image,
        images = pc.images
    FROM product_collection pc
    WHERE product.product_collection_master_code = pc.master_code
      AND (product.product_collection_url IS NULL 
           OR product.product_collection_image IS NULL 
           OR product.images IS NULL)
    """)
    
    updated_count = cur.rowcount
    
    # Get stats after update
    after_stats = get_migration_stats(cur)
    
    print(f"\n📊 Migration Results:")
    print(f"   Products updated: {updated_count}")
    print(f"   Total products: {after_stats[0]}")
    print(f"   Products with master_code: {after_stats[1]}")
    print(f"   Products with URL: {before_stats[2]} → {after_stats[2]}")
    print(f"   Products with image: {before_stats[3]} → {after_stats[3]}")
    print(f"   Products with images array: {before_stats[4]} → {after_stats[4]}")
    
    return updated_count

def verify_inheritance(cur):
    """Verify that inheritance is working correctly"""
    print("\n🔍 Verifying inheritance...")
    
    cur.execute("""
    SELECT 
        p.product_collection_sku,
        p.product_collection_master_code,
        p.product_collection_url,
        pc.product_collection_url as collection_url,
        CASE WHEN p.product_collection_url = pc.product_collection_url THEN '✅' ELSE '❌' END as url_match
    FROM product p
    JOIN product_collection pc ON p.product_collection_master_code = pc.master_code
    WHERE p.product_collection_url IS NOT NULL
    LIMIT 5
    """)
    
    results = cur.fetchall()
    if results:
        print("   Sample verification (first 5 products):")
        for row in results:
            print(f"   SKU: {row[0]}, Master: {row[1]}, URL Match: {row[4]}")
    else:
        print("   No products found with inherited URLs")

def main():
    """Main migration function"""
    print("🚀 Starting Product Inheritance Migration")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Use transactions
        cur = conn.cursor()
        
        # Check existing columns
        existing_columns = check_columns_exist(cur)
        print(f"Existing inherited columns: {existing_columns}")
        
        # Add columns if needed
        add_inherited_columns(cur)
        
        # Update existing products
        updated_count = update_inherited_fields(cur)
        
        # Verify results
        verify_inheritance(cur)
        
        # Commit changes
        conn.commit()
        print(f"\n✅ Migration completed successfully!")
        print(f"   {updated_count} products updated with inherited fields")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
        
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()