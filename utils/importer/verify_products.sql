-- SQL queries to verify ETL results and check product data

-- 1. Check total number of products inserted
SELECT COUNT(*) as total_products FROM product;

-- 2. Check products with their collections
SELECT 
    p.id,
    p.product_collection_sku,
    p.product_selling_price,
    p.inventory,
    pc.master_code,
    pc.name as collection_name
FROM product p
LEFT JOIN product_collection pc ON pc.id = p.product_attributes_raw_collection_id
ORDER BY p.product_collection_sku
LIMIT 20;

-- 3. Check specific SKU patterns from the ETL log
SELECT 
    product_collection_sku,
    product_selling_price,
    inventory,
    created_at
FROM product 
WHERE product_collection_sku LIKE '66862c-%' 
   OR product_collection_sku LIKE '74e760-%'
   OR product_collection_sku LIKE 'b09cc8-%'
ORDER BY product_collection_sku;

-- 4. Check product collections
SELECT 
    id,
    master_code,
    name,
    created_at
FROM product_collection
ORDER BY created_at DESC;

-- 5. Check for any products without proper foreign key relationships
SELECT 
    p.id,
    p.product_collection_sku,
    p.product_attributes_raw_collection_id,
    CASE 
        WHEN pc.id IS NULL THEN 'Missing collection reference'
        ELSE 'OK'
    END as status
FROM product p
LEFT JOIN product_collection pc ON pc.id = p.product_attributes_raw_collection_id
WHERE pc.id IS NULL;

-- 6. Check recent insertions (last hour)
SELECT 
    COUNT(*) as recent_products,
    MIN(created_at) as first_insert,
    MAX(created_at) as last_insert
FROM product 
WHERE created_at >= NOW() - INTERVAL '1 hour';

-- 7. Sample of actual product data
SELECT 
    product_collection_sku,
    product_selling_price,
    inventory,
    weight,
    long,
    width,
    high
FROM product 
WHERE product_collection_sku IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;