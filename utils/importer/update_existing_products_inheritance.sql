-- Update existing products to inherit fields from their parent collections
-- This script will populate the newly added inherited fields for existing products

UPDATE product 
SET 
    product_collection_url = pc.product_collection_url,
    product_collection_image = pc.product_collection_image,
    images = pc.images
FROM product_collection pc
WHERE product.product_collection_master_code = pc.master_code
  AND (product.product_collection_url IS NULL 
       OR product.product_collection_image IS NULL 
       OR product.images IS NULL);

-- Show summary of updated records
SELECT 
    COUNT(*) as total_products_updated,
    COUNT(CASE WHEN product_collection_url IS NOT NULL THEN 1 END) as products_with_url,
    COUNT(CASE WHEN product_collection_image IS NOT NULL THEN 1 END) as products_with_image,
    COUNT(CASE WHEN images IS NOT NULL THEN 1 END) as products_with_images_array
FROM product 
WHERE product_collection_master_code IS NOT NULL;