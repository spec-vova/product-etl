# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
import uuid
from dotenv import load_dotenv
import re

# === UTF-8 консоль для Windows ===
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

# File paths - can be overridden by environment variables
RAW_CSV_PATH = os.getenv('RAW_CSV_PATH', 'x:\\DATA_STORAGE\\Furnithai\\RAW_WXW\\latest_Raw Data.csv')
MAPPING_CSV_PATH = os.getenv('MAPPING_CSV_PATH', 'x:\\DATA_STORAGE\\Furnithai\\utils\\importer\\map.csv')
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

# Helper functions
def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

def clean_string(s):
    """Clean and normalize string values"""
    if not isinstance(s, str):
        return s
    return s.strip()

def convert_numpy_types(value):
    """Convert numpy types to Python native types"""
    if isinstance(value, np.integer):
        return int(value)
    elif isinstance(value, np.floating):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif pd.isna(value):
        return None
    return value

def parse_array(array_str):
    """Parse array strings like '[url1, url2, url3]' into Python lists"""
    if not array_str or not isinstance(array_str, str):
        return []
    
    # Extract URLs using regex
    urls = re.findall(r'https?://[^\s,\]]+', array_str)
    return urls

def parse_attributes(attr_str):
    """Parse custom attributes string into key-value pairs"""
    if not attr_str or not isinstance(attr_str, str):
        return []
    
    result = []
    # Split by dash and then by colon
    for pair in attr_str.split('-'):
        if not pair.strip():
            continue
        # Check for sub-pairs separated by semicolon
        subpairs = pair.split(';')
        for subpair in subpairs:
            if ':' in subpair:
                k, v = subpair.split(':', 1)
                result.append((k.strip(), v.strip()))
    return result

def main():
    print("Starting ETL process...")
    
    if DRY_RUN:
        print("DRY RUN MODE: No changes will be committed to the database")
    
    # 1. Load mapping configuration
    print("Loading mapping configuration...")
    df_map = pd.read_csv(MAPPING_CSV_PATH, encoding='utf-8')
    mapping = {}
    for _, row in df_map.iterrows():
        raw_col = str(row['raw_input_field']).strip()
        table = str(row['db_table']).strip()
        column = str(row['field']).strip() if not pd.isna(row['field']) else ""
        mapping[raw_col] = {'table': table, 'column': column}
    
    # 2. Read CSV data
    print(f"Reading data from {RAW_CSV_PATH}...")
    raw_df = pd.read_csv(RAW_CSV_PATH, sep=';', encoding='utf-8')
    
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get default language ID (assuming 'en' is the default language)
    cur.execute("""
    SELECT id FROM lang WHERE lang_code = 'en'
    """)
    default_lang_id_result = cur.fetchone()
    if default_lang_id_result:
        default_lang_id = default_lang_id_result[0]
    else:
        # If 'en' language doesn't exist, create it
        default_lang_id = generate_uuid()
        cur.execute("""
        INSERT INTO lang (id, lang_code)
        VALUES (%s, %s)
        """, (default_lang_id, 'en'))
        conn.commit()
    
    try:
        # 3. Process product collections (master rows)
        print("Processing product collections...")
        
        # Get unique master codes to process each collection
        unique_master_codes = raw_df['Master Code'].dropna().unique()
        print(f"Found {len(unique_master_codes)} unique master codes to process")
        
        for master_code in unique_master_codes:
            # Get the first row for this master code as the collection template
            master_rows = raw_df[raw_df['Master Code'] == master_code]
            if master_rows.empty:
                continue
                
            row = master_rows.iloc[0]  # Use first row as template
            collection_data = {}
            collection_id = generate_uuid()
            
            # Extract collection data
            for col in raw_df.columns:
                if col in mapping and mapping[col]['table'] == 'product_collection' and mapping[col]['column']:
                    db_col = mapping[col]['column']
                    value = convert_numpy_types(row[col])
                    
                    # Special handling for arrays
                    if db_col == 'product_collection_img_array':
                        value = parse_array(value)
                    
                    collection_data[db_col] = value
            
            # Add collection ID
            collection_data['id'] = collection_id
            master_code = collection_data.get('master_code')
            collection_sku = collection_data.get('product_collection_sku', '')
            
            # Generate UUID for product_collection_name
            product_name_id = generate_uuid()
            collection_data['product_collection_name'] = product_name_id
            
            # Insert collection first to ensure it exists before linking
            if master_code:
                columns = list(collection_data.keys())
                values = [collection_data[col] for col in columns]
                
                # Check if collection exists first
                cur.execute("""
                SELECT id FROM product_collection 
                WHERE master_code = %s
                """, (master_code,))
                
                existing_collection = cur.fetchone()
                
                if existing_collection:
                    # Update existing collection
                    collection_id = existing_collection[0]
                    update_cols = [col for col in columns if col != 'id' and col != 'master_code']
                    
                    if update_cols:
                        update_query = f"""
                        UPDATE product_collection SET 
                        {', '.join([f"{col} = %s" for col in update_cols])}
                        WHERE id = %s
                        """
                        
                        update_values = [collection_data[col] for col in update_cols]
                        update_values.append(collection_id)
                        
                        cur.execute(update_query, update_values)
                else:
                    # Insert new collection
                    query = f"""
                    INSERT INTO product_collection ({', '.join(columns)})
                    VALUES ({', '.join(['%s'] * len(columns))})
                    RETURNING id
                    """
                    
                    cur.execute(query, values)
                    collection_id = cur.fetchone()[0]
                
                print(f"Inserted/Updated collection with master_code: {master_code}, ID: {collection_id}")
                
                # Process product images array after collection is inserted
                product_images = row.get('Product Image')
                if product_images and isinstance(product_images, str):
                    # Create array of image URLs
                    image_urls = [url.strip() for url in product_images.split(',') if url.strip()]
                    
                    if image_urls:
                        # Insert into product_collection_img_array
                        img_array_id = generate_uuid()
                        cur.execute("""
                        INSERT INTO product_collection_img_array 
                        (id, product_collection_img_array)
                        VALUES (%s, %s)
                        RETURNING id
                        """, (img_array_id, image_urls))
                        
                        img_array_db_id = cur.fetchone()[0]
                        
                        # Link to product_collection
                        # Check if link already exists
                        cur.execute("""
                        SELECT id FROM product_collection_product_collection_img_array 
                        WHERE product_collection_id = %s AND product_collection_img_array = %s
                        """, (collection_id, img_array_db_id))
                        
                        existing_link = cur.fetchone()
                        
                        if not existing_link:
                            # Create new link
                            link_id = generate_uuid()
                            cur.execute("""
                            INSERT INTO product_collection_product_collection_img_array 
                            (id, product_collection_id, product_collection_img_array)
                            VALUES (%s, %s, %s)
                            """, (link_id, collection_id, img_array_db_id))
                
                # Process collection translations
                for col in raw_df.columns:
                    if col in mapping and mapping[col]['table'] == 'product_collection_translations':
                        value = clean_string(row[col])
                        if value:
                            trans_id = generate_uuid()
                            # Chinese language ID - should be configurable
                            lang_id = "365d96e3-9f08-4d2e-bf17-18a26a5072f7"
                            field_name = "product_collection_name"
                            
                            # Check if translation exists
                            cur.execute("""
                            SELECT id FROM product_collection_translations 
                            WHERE product_id = %s AND lang_id = %s AND field_name = %s
                            """, (collection_id, lang_id, field_name))
                            
                            existing_trans = cur.fetchone()
                            
                            if existing_trans:
                                # Update existing translation
                                cur.execute("""
                                UPDATE product_collection_translations 
                                SET value = %s
                                WHERE id = %s
                                """, (value, existing_trans[0]))
                            else:
                                # Insert new translation
                                cur.execute("""
                                INSERT INTO product_collection_translations 
                                (id, product_id, lang_id, field_name, value)
                                VALUES (%s, %s, %s, %s, %s)
                                """, (trans_id, collection_id, lang_id, field_name, value))
                    
                    print(f"Inserted/Updated collection with master_code: {master_code}, ID: {collection_id}")
                    
                    # Process collection translations
                    for col in raw_df.columns:
                        if col in mapping and mapping[col]['table'] == 'product_collection_translations':
                            value = clean_string(row[col])
                            if value:
                                trans_id = generate_uuid()
                                # Chinese language ID - should be configurable
                                lang_id = "365d96e3-9f08-4d2e-bf17-18a26a5072f7"
                                field_name = "product_collection_name"
                                
                                # Check if translation exists
                                cur.execute("""
                                SELECT id FROM product_collection_translations 
                                WHERE product_id = %s AND lang_id = %s AND field_name = %s
                                """, (collection_id, lang_id, field_name))
                                
                                existing_trans = cur.fetchone()
                                
                                if existing_trans:
                                    # Update existing translation
                                    cur.execute("""
                                    UPDATE product_collection_translations 
                                    SET value = %s
                                    WHERE id = %s
                                    """, (value, existing_trans[0]))
                                else:
                                    # Insert new translation
                                    cur.execute("""
                                    INSERT INTO product_collection_translations 
                                    (id, product_id, lang_id, field_name, value)
                                    VALUES (%s, %s, %s, %s, %s)
                                    """, (trans_id, collection_id, lang_id, field_name, value))
                    
                    # Process category
                    category_name = row.get('Category Name')
                    if category_name and isinstance(category_name, str):
                        # First check if category exists by name
                        cur.execute("""
                        SELECT ct.category_id 
                        FROM category_translations ct
                        WHERE ct.value = %s AND ct.lang_id = %s AND ct.field_name = %s
                        """, (category_name, "365d96e3-9f08-4d2e-bf17-18a26a5072f7", "category_name"))
                        
                        category_result = cur.fetchone()
                        category_id = None
                        
                        if category_result:
                            # Category exists, use its ID
                            category_id = category_result[0]
                            print(f"Found existing category: {category_name}, ID: {category_id}")
                        else:
                            # Create new category using existing translation as temporary placeholder
                            category_id = generate_uuid()
                            trans_id = generate_uuid()
                            # Use existing translation as placeholder to avoid FK constraint
                            placeholder_trans_id = "646b58d9-de22-4459-b4f1-8302e8d64c7d"
                            
                            # Step 1: Insert into category table with existing translation as placeholder
                            cur.execute("""
                            INSERT INTO category (id, category_name)
                            VALUES (%s, %s)
                            """, (category_id, placeholder_trans_id))
                            
                            # Step 2: Insert the real category translation
                            cur.execute("""
                            INSERT INTO category_translations 
                            (id, category_id, lang_id, field_name, value)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (trans_id, category_id, "365d96e3-9f08-4d2e-bf17-18a26a5072f7", "category_name", category_name))
                            
                            # Step 3: Update category to point to the real translation
                            cur.execute("""
                            UPDATE category SET category_name = %s WHERE id = %s
                            """, (trans_id, category_id))
                            
                            print(f"Created new category: {category_name}, ID: {category_id}")
                        
                        # Link category to collection
                        if category_id:
                            # Check if link already exists
                            cur.execute("""
                            SELECT id FROM product_collection_category 
                            WHERE product_collection_id = %s AND category_id = %s
                            """, (collection_id, category_id))
                            
                            existing_link = cur.fetchone()
                            
                            if not existing_link:
                                # Create new link
                                link_id = generate_uuid()
                                cur.execute("""
                                INSERT INTO product_collection_category 
                                (id, product_collection_id, category_id)
                                VALUES (%s, %s, %s)
                                """, (link_id, collection_id, category_id))
                    
                    # Process custom attributes
                    custom_attrs = row.get('Custom Attributes')
                    if custom_attrs and isinstance(custom_attrs, str):
                        attrs_id = generate_uuid()
                        cur.execute("""
                        INSERT INTO custom_attributes_raw 
                        (id, custom_attributes_raw)
                        VALUES (%s, %s)
                        RETURNING id
                        """, (attrs_id, custom_attrs))
                        
                        attrs_collection_id = cur.fetchone()[0]
                        
                        # Link attributes to collection using the linking table
                        link_id = generate_uuid()
                        cur.execute("""
                        INSERT INTO product_collection_custom_attributes_raw
                        (id, product_collection_id, custom_attributes_raw_id)
                        VALUES (%s, %s, %s)
                        """, (link_id, collection_id, attrs_collection_id))
                        
                    # Process web page details
                    web_page_details = row.get('Web Page Details')
                    if web_page_details and isinstance(web_page_details, str):
                        # Step 1: Create IDs
                        trans_id = generate_uuid()
                        details_html_id = generate_uuid()
                        lang_id = "365d96e3-9f08-4d2e-bf17-18a26a5072f7"  # Chinese language ID
                        field_name = "details_html"
                        
                        # Step 2: Use existing translation as temporary placeholder
                        # Get an existing translation ID to use as placeholder
                        cur.execute("""
                        SELECT id FROM details_html_translations LIMIT 1
                        """)
                        placeholder_result = cur.fetchone()
                        
                        if placeholder_result:
                            placeholder_trans_id = placeholder_result[0]
                        else:
                            # If no existing translations, create a minimal one first
                            placeholder_trans_id = generate_uuid()
                            placeholder_html_id = generate_uuid()
                            
                            # Insert placeholder details_html record
                            cur.execute("""
                            INSERT INTO details_html (id, details_html)
                            VALUES (%s, %s)
                            """, (placeholder_html_id, placeholder_trans_id))
                            
                            # Insert placeholder translation
                            cur.execute("""
                            INSERT INTO details_html_translations 
                            (id, details_html_id, lang_id, field_name, value)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (placeholder_trans_id, placeholder_html_id, lang_id, "placeholder", "placeholder"))
                        
                        # Step 3: Insert details_html record with placeholder
                        cur.execute("""
                        INSERT INTO details_html (id, details_html)
                        VALUES (%s, %s)
                        RETURNING id
                        """, (details_html_id, placeholder_trans_id))
                        
                        details_html_db_id = cur.fetchone()[0]
                        
                        # Step 4: Insert actual translation
                        cur.execute("""
                        INSERT INTO details_html_translations 
                        (id, details_html_id, lang_id, field_name, value)
                        VALUES (%s, %s, %s, %s, %s)
                        """, (trans_id, details_html_db_id, lang_id, field_name, web_page_details))
                        
                        # Step 5: Update details_html to point to actual translation
                        cur.execute("""
                        UPDATE details_html SET details_html = %s WHERE id = %s
                        """, (trans_id, details_html_db_id))
                        
                        print(f"Inserted web page details for collection {collection_id}")
                        
                        # Link details to collection
                        # Check if link already exists
                        cur.execute("""
                        SELECT id FROM product_collection_details_html 
                        WHERE product_collection_id = %s AND details_html_id = %s
                        """, (collection_id, details_html_db_id))
                        
                        existing_link = cur.fetchone()
                        
                        if not existing_link:
                            # Create new link
                            link_id = generate_uuid()
                            cur.execute("""
                            INSERT INTO product_collection_details_html 
                            (id, product_collection_id, details_html_id)
                            VALUES (%s, %s, %s)
                            """, (link_id, collection_id, details_html_db_id))
                
                # Process video URL
                video_url = row.get('Video')
                if video_url and isinstance(video_url, str):
                    # Update collection with video URL
                    cur.execute("""
                    UPDATE product_collection 
                    SET video = %s
                    WHERE id = %s
                    """, (video_url, collection_id))
                
                # Process product variations for this specific master code
                print(f"Processing product variations for master code: {master_code}")
                
                # Filter variations that belong to this master code
                master_variations = raw_df[raw_df['Master Code'] == master_code]
                
                for var_idx, var_row in master_variations.iterrows():
                    # Skip the first row (master row) for this master code
                    if var_idx == master_variations.index[0]:
                        continue  # Skip the master row we just processed
                    
                    product_data = {}
                    product_id = generate_uuid()
                    
                    # Extract product data
                    for col in raw_df.columns:
                        if col in mapping and mapping[col]['table'] == 'product' and mapping[col]['column']:
                            db_col = mapping[col]['column']
                            value = clean_string(convert_numpy_types(var_row[col]))
                            if value:  # Only update if value is not empty
                                # Handle numeric values with comma decimal separator
                                if db_col in ['product_selling_price'] and isinstance(value, str):
                                    value = value.replace(',', '.')
                                product_data[db_col] = value
                    
                    # Add product ID and required fields
                    product_data['id'] = product_id
                    
                    # Link product to collection using master_code
                    # Extract master code from the current row to find the correct collection
                    row_master_code = var_row.get('Master Code')
                    if row_master_code:
                        # Find the collection ID for this master code
                        cur.execute("""
                        SELECT id FROM product_collection 
                        WHERE master_code = %s
                        """, (row_master_code,))
                        
                        collection_result = cur.fetchone()
                        if collection_result:
                            # Use the actual collection ID instead of random UUID
                            product_data['product_attributes_raw_collection_id'] = collection_result[0]
                        else:
                            # Fallback: use the collection_id from the master row processing
                            product_data['product_attributes_raw_collection_id'] = collection_id
                    else:
                        # Fallback: use the collection_id from the master row processing
                        product_data['product_attributes_raw_collection_id'] = collection_id
                    
                    # Store master code for easier querying
                    if row_master_code:
                        product_data['product_collection_master_code'] = row_master_code
                    
                    # Extract SKU code
                    sku_code = var_row.get('SKU Code')
                    if sku_code:
                        product_data['product_collection_sku'] = sku_code
                    
                    # Inherit fields from parent collection
                    if row_master_code:
                        cur.execute("""
                        SELECT product_collection_url, product_collection_image, images 
                        FROM product_collection 
                        WHERE master_code = %s
                        """, (row_master_code,))
                        
                        collection_fields = cur.fetchone()
                        if collection_fields:
                            # Inherit collection fields into product
                            if collection_fields[0]:  # product_collection_url
                                product_data['product_collection_url'] = collection_fields[0]
                            if collection_fields[1]:  # product_collection_image
                                product_data['product_collection_image'] = collection_fields[1]
                            if collection_fields[2]:  # images array
                                product_data['images'] = collection_fields[2]
                    
                    # Insert product
                    if product_data and 'product_collection_sku' in product_data:
                        sku = product_data['product_collection_sku']
                        
                        # Check if product exists
                        cur.execute("""
                        SELECT id FROM product 
                        WHERE product_collection_sku = %s
                        """, (sku,))
                        
                        existing_product = cur.fetchone()
                        
                        if existing_product:
                            # Update existing product
                            update_cols = [col for col in product_data.keys() if col != 'id' and col != 'product_collection_sku']
                            
                            if update_cols:
                                update_query = f"""
                                UPDATE product SET 
                                {', '.join([f"{col} = %s" for col in update_cols])}
                                WHERE product_collection_sku = %s
                                """
                                
                                update_values = [product_data[col] for col in update_cols]
                                update_values.append(sku)
                                
                                cur.execute(update_query, update_values)
                        else:
                            # Insert new product
                            columns = list(product_data.keys())
                            values = [product_data[col] for col in columns]
                            
                            query = f"""
                            INSERT INTO product ({', '.join(columns)})
                            VALUES ({', '.join(['%s'] * len(columns))})
                            """
                            
                            cur.execute(query, values)
                        
                        print(f"Inserted/Updated product with SKU: {sku_code}")
                        
                        # Process Sku Attribute if available
                        sku_attr = var_row.get('Sku Attribute')
                        if sku_attr and isinstance(sku_attr, str):
                            # Store product attributes in product_attributes_raw_collection
                            attrs_id = generate_uuid()
                            cur.execute("""
                            INSERT INTO product_attributes_raw_collection 
                            (id, product_attributes_collection)
                            VALUES (%s, %s)
                            RETURNING id
                            """, (attrs_id, sku_attr))
                            
                            attrs_collection_id = cur.fetchone()[0]
                            
                            # Link attributes to product
                            cur.execute("""
                            UPDATE product 
                            SET product_attributes_raw_collection_id = %s
                            WHERE id = %s
                            """, (attrs_collection_id, product_id))
        
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
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()