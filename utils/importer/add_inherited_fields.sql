-- Add inherited fields from product_collection to product table
-- These fields will be populated from the parent collection during ETL process

ALTER TABLE product 
ADD COLUMN IF NOT EXISTS product_collection_url text,
ADD COLUMN IF NOT EXISTS product_collection_image text,
ADD COLUMN IF NOT EXISTS images text[];

-- Add comments to document the purpose of these fields
COMMENT ON COLUMN product.product_collection_url IS 'Inherited from parent product_collection.product_collection_url';
COMMENT ON COLUMN product.product_collection_image IS 'Inherited from parent product_collection.product_collection_image';
COMMENT ON COLUMN product.images IS 'Inherited from parent product_collection.images array';

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_product_collection_url ON product(product_collection_url);
CREATE INDEX IF NOT EXISTS idx_product_collection_image ON product(product_collection_image);