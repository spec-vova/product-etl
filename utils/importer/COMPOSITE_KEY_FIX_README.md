# Composite Key Issue Fix

## Problem Identified

A critical issue was discovered in the ETL process where **composite keys were being saved into single fields** instead of properly linking products to their collections. This resulted in:

1. **Random UUIDs**: Products were assigned random `product_attributes_raw_collection_id` values instead of linking to actual collections
2. **Incorrect Relationships**: Products were not properly associated with their parent collections
3. **Data Integrity Issues**: Starting from row 4688, new products had broken relationships
4. **Performance Problems**: Queries couldn't efficiently join products with their collections

## Root Cause

The issue was in the `ETL.py` file where:

```python
# INCORRECT CODE (before fix):
product_data['product_attributes_raw_collection_id'] = generate_uuid()  # Random UUID!

# Also, ALL rows were processed as variations for EVERY master row:
for var_idx, var_row in raw_df.iterrows():  # Wrong: processes all rows
    if var_idx == 0:
        continue  # Only skips first row, not master row for each group
```

## Solution Implemented

### 1. Fixed Product-Collection Linking

Replaced random UUID generation with proper collection lookup:

```python
# CORRECTED CODE:
# Link product to collection using master_code
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
```

### 2. Fixed Variation Processing Logic

Changed from processing all rows to only processing variations of the same master code:

```python
# CORRECTED CODE:
# Filter variations that belong to this master code
master_variations = raw_df[raw_df['Master Code'] == master_code]

for var_idx, var_row in master_variations.iterrows():
    # Skip if this is the master row (first occurrence of this master code)
    if var_idx == idx:
        continue  # Skip the master row we just processed
```

## Files Modified

### 1. `ETL.py` - Main Fix
- Fixed product-collection linking logic
- Fixed variation processing to only handle same master code
- Added proper master code storage in products

### 2. `cleanup_incorrect_products.py` - Data Cleanup
- Identifies products with broken collection links
- Safely removes incorrectly processed products
- Cleans up orphaned custom attributes
- Provides verification of cleanup success

### 3. `cleanup_incorrect_products.bat` - Easy Execution
- Batch file for easy cleanup script execution

## How to Fix Your Database

### Step 1: Backup Your Database
```bash
pg_dump -h localhost -p 5433 -U speci furnithai > backup_before_fix.sql
```

### Step 2: Run Cleanup Script
```bash
# Option 1: Use batch file
cleanup_incorrect_products.bat

# Option 2: Run Python directly
python cleanup_incorrect_products.py
```

### Step 3: Re-run ETL with Fixed Code
```bash
# The ETL.py file is now fixed, run it again
python ETL.py
```

### Step 4: Verify Results
```sql
-- Check that products are properly linked to collections
SELECT 
    p.product_collection_sku,
    p.product_attributes_raw_collection_id,
    pc.master_code,
    pc.product_collection_name
FROM product p
JOIN product_collection pc ON p.product_attributes_raw_collection_id = pc.id
LIMIT 10;

-- Count products per collection
SELECT 
    pc.master_code,
    pc.product_collection_name,
    COUNT(p.id) as product_count
FROM product_collection pc
LEFT JOIN product p ON pc.id = p.product_attributes_raw_collection_id
GROUP BY pc.id, pc.master_code, pc.product_collection_name
ORDER BY product_count DESC;
```

## What the Fix Accomplishes

### ✅ Proper Data Relationships
- Products are now correctly linked to their parent collections
- Master codes properly group related products
- Foreign key relationships are maintained

### ✅ Improved Performance
- Queries can efficiently join products with collections
- Indexes can be used effectively
- Reduced data redundancy

### ✅ Data Integrity
- No more orphaned products with random UUIDs
- Consistent master code handling
- Proper variation grouping

### ✅ Maintainable Code
- Clear logic for product-collection relationships
- Proper error handling and fallbacks
- Better debugging output

## Prevention for Future

### 1. Add Database Constraints
```sql
-- Add foreign key constraint to prevent orphaned products
ALTER TABLE product 
ADD CONSTRAINT fk_product_collection 
FOREIGN KEY (product_attributes_raw_collection_id) 
REFERENCES product_collection(id);
```

### 2. Add Validation in ETL
- Validate that collection exists before creating products
- Add logging for relationship creation
- Implement data quality checks

### 3. Regular Data Audits
```sql
-- Query to check for orphaned products
SELECT COUNT(*) as orphaned_products
FROM product p
LEFT JOIN product_collection pc ON p.product_attributes_raw_collection_id = pc.id
WHERE pc.id IS NULL;
```

## Testing

After applying the fix:

1. **Relationship Test**: Verify all products link to valid collections
2. **Master Code Test**: Ensure products group correctly by master code
3. **Variation Test**: Check that variations belong to correct collections
4. **Performance Test**: Measure query performance improvements

## Support

If you encounter issues:

1. Check database connection settings in `.env`
2. Verify backup was created before cleanup
3. Review cleanup script output for errors
4. Check ETL logs for processing details

The fix ensures your product data maintains proper relationships and can be queried efficiently for your furniture catalog system.