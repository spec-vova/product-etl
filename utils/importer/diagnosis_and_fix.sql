-- DIAGNOSIS: ETL Results Analysis
-- The products are in the database but have incorrect foreign key relationships

-- 1. Verify the issue: Products with orphaned collection references
SELECT 
    COUNT(*) as total_products,
    COUNT(CASE WHEN pc.id IS NULL THEN 1 END) as orphaned_products,
    COUNT(CASE WHEN pc.id IS NOT NULL THEN 1 END) as linked_products
FROM product p
LEFT JOIN product_collection pc ON pc.id = p.product_attributes_raw_collection_id;

-- 2. Show sample of orphaned products with their supposed collection info
SELECT 
    p.product_collection_sku,
    p.product_collection_master_code,
    p.product_attributes_raw_collection_id,
    'No matching collection found' as issue
FROM product p
LEFT JOIN product_collection pc ON pc.id = p.product_attributes_raw_collection_id
WHERE pc.id IS NULL
LIMIT 10;

-- 3. Check if collections exist with matching master codes
SELECT 
    p.product_collection_master_code as product_master_code,
    pc.master_code as collection_master_code,
    COUNT(p.id) as product_count,
    pc.id as collection_id
FROM product p
LEFT JOIN product_collection pc ON pc.master_code = p.product_collection_master_code
WHERE p.product_collection_master_code IS NOT NULL
GROUP BY p.product_collection_master_code, pc.master_code, pc.id
ORDER BY product_count DESC
LIMIT 10;

-- 4. SOLUTION: Update products to link to correct collections by master_code
-- This query will fix the foreign key relationships
/*
UPDATE product 
SET product_attributes_raw_collection_id = pc.id
FROM product_collection pc 
WHERE product.product_collection_master_code = pc.master_code
  AND product.product_collection_master_code IS NOT NULL
  AND pc.master_code IS NOT NULL;
*/

-- 5. Verification query to run after the fix
/*
SELECT 
    COUNT(*) as total_products,
    COUNT(CASE WHEN pc.id IS NULL THEN 1 END) as orphaned_products,
    COUNT(CASE WHEN pc.id IS NOT NULL THEN 1 END) as linked_products
FROM product p
LEFT JOIN product_collection pc ON pc.id = p.product_attributes_raw_collection_id;
*/

-- 6. Sample query to verify products are properly linked after fix
/*
SELECT 
    p.product_collection_sku,
    p.product_selling_price,
    p.inventory,
    pc.master_code,
    pc.product_collection_sku as collection_sku
FROM product p
JOIN product_collection pc ON pc.id = p.product_attributes_raw_collection_id
WHERE p.product_collection_sku LIKE '66862c-%'
ORDER BY p.product_collection_sku
LIMIT 10;
*/