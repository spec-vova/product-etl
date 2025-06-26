# Product Inheritance System

This system allows products to inherit specific fields from their parent product collections, ensuring data consistency and reducing redundancy.

## 🎯 Overview

Products now automatically inherit the following fields from their parent `product_collection`:
- `product_collection_url` - URL of the collection page
- `product_collection_image` - Main collection image
- `images` - Array of collection images

## 📋 Implementation Details

### Database Schema Changes

Three new columns have been added to the `product` table:

```sql
ALTER TABLE product 
ADD COLUMN IF NOT EXISTS product_collection_url text,
ADD COLUMN IF NOT EXISTS product_collection_image text,
ADD COLUMN IF NOT EXISTS images text[];
```

### ETL Process Enhancement

The ETL process has been updated to automatically populate these inherited fields when creating or updating products. The inheritance happens during product processing:

```python
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
```

## 🚀 Migration Process

### For New Installations

1. Run the schema migration:
   ```bash
   psql -d your_database -f add_inherited_fields.sql
   ```

2. The ETL process will automatically handle inheritance for new products.

### For Existing Installations

#### Option 1: Automated Migration (Recommended)

**Windows:**
```bash
run_migration.bat
```

**Linux/Mac:**
```bash
python migrate_product_inheritance.py
```

#### Option 2: Manual Migration

1. **Add columns to product table:**
   ```bash
   psql -d your_database -f add_inherited_fields.sql
   ```

2. **Update existing products:**
   ```bash
   psql -d your_database -f update_existing_products_inheritance.sql
   ```

## 📊 Verification

After migration, verify the inheritance is working:

```sql
-- Check inheritance statistics
SELECT 
    COUNT(*) as total_products,
    COUNT(CASE WHEN product_collection_url IS NOT NULL THEN 1 END) as products_with_url,
    COUNT(CASE WHEN product_collection_image IS NOT NULL THEN 1 END) as products_with_image,
    COUNT(CASE WHEN images IS NOT NULL THEN 1 END) as products_with_images_array
FROM product 
WHERE product_collection_master_code IS NOT NULL;

-- Verify inheritance accuracy (sample)
SELECT 
    p.product_collection_sku,
    p.product_collection_master_code,
    p.product_collection_url = pc.product_collection_url as url_inherited_correctly,
    p.product_collection_image = pc.product_collection_image as image_inherited_correctly
FROM product p
JOIN product_collection pc ON p.product_collection_master_code = pc.master_code
LIMIT 10;
```

## 🔧 Benefits

### Data Consistency
- Products automatically reflect their collection's visual and URL information
- Eliminates manual data entry errors
- Ensures uniform presentation across product variants

### Performance
- Reduces JOIN operations in queries
- Enables direct access to collection data from product records
- Improves query performance for product listings

### Maintenance
- Automatic inheritance during ETL process
- No manual intervention required for new products
- Centralized collection data management

## 📝 Usage Examples

### Query Products with Collection Data

```sql
-- Get products with their inherited collection information
SELECT 
    product_collection_sku,
    product_collection_url,
    product_collection_image,
    array_length(images, 1) as image_count
FROM product 
WHERE product_collection_url IS NOT NULL
ORDER BY created_on DESC
LIMIT 20;
```

### Find Products Missing Inheritance

```sql
-- Identify products that should have inherited data but don't
SELECT 
    p.product_collection_sku,
    p.product_collection_master_code,
    pc.product_collection_url IS NOT NULL as collection_has_url,
    p.product_collection_url IS NOT NULL as product_has_url
FROM product p
JOIN product_collection pc ON p.product_collection_master_code = pc.master_code
WHERE pc.product_collection_url IS NOT NULL 
  AND p.product_collection_url IS NULL;
```

## ⚠️ Important Notes

1. **Backup First**: Always backup your database before running migrations
2. **Test Environment**: Test the migration in a development environment first
3. **Data Validation**: Verify inheritance accuracy after migration
4. **Performance**: Large datasets may require extended processing time

## 🐛 Troubleshooting

### Common Issues

1. **Missing master_code**: Products without `product_collection_master_code` won't inherit data
2. **Orphaned products**: Products referencing non-existent collections
3. **Null collection data**: Collections without the required fields

### Solutions

```sql
-- Find products without master_code
SELECT COUNT(*) FROM product WHERE product_collection_master_code IS NULL;

-- Find orphaned products
SELECT p.product_collection_sku, p.product_collection_master_code
FROM product p
LEFT JOIN product_collection pc ON p.product_collection_master_code = pc.master_code
WHERE p.product_collection_master_code IS NOT NULL 
  AND pc.id IS NULL;

-- Find collections with missing data
SELECT master_code, 
       product_collection_url IS NULL as missing_url,
       product_collection_image IS NULL as missing_image,
       images IS NULL as missing_images
FROM product_collection
WHERE product_collection_url IS NULL 
   OR product_collection_image IS NULL 
   OR images IS NULL;
```

## 🔄 Future Enhancements

- Real-time inheritance updates when collection data changes
- Configurable inheritance rules
- Inheritance validation triggers
- Automated inheritance repair tools

---

*For technical support or questions about the inheritance system, refer to the main ETL documentation or contact the development team.*