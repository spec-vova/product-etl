-- SQL Script to add 'created_on' and 'modified_on' fields to all tables
-- This script adds timestamp fields with appropriate defaults and triggers

-- =============================================================================
-- STEP 1: Add created_on and modified_on columns to all tables
-- =============================================================================

-- Add timestamp fields to 'product' table
ALTER TABLE product 
ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add timestamp fields to 'product_collection' table
ALTER TABLE product_collection 
ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add timestamp fields to 'product_translations' table
ALTER TABLE product_translations 
ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add timestamp fields to 'product_custom_attributes' table
ALTER TABLE product_custom_attributes 
ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add timestamp fields to 'product_collection_img_array' table
ALTER TABLE product_collection_img_array 
ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add timestamp fields to 'lang' table
ALTER TABLE lang 
ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add timestamp fields to 'product_collection_translations' table (if exists)
ALTER TABLE product_collection_translations 
ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add timestamp fields to 'product_collection_custom_attributes' table (if exists)
ALTER TABLE product_collection_custom_attributes 
ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- =============================================================================
-- STEP 2: Create function to automatically update modified_on timestamp
-- =============================================================================

CREATE OR REPLACE FUNCTION update_modified_on_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_on = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =============================================================================
-- STEP 3: Create triggers to automatically update modified_on on UPDATE
-- =============================================================================

-- Trigger for 'product' table
DROP TRIGGER IF EXISTS update_product_modified_on ON product;
CREATE TRIGGER update_product_modified_on
    BEFORE UPDATE ON product
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_on_column();

-- Trigger for 'product_collection' table
DROP TRIGGER IF EXISTS update_product_collection_modified_on ON product_collection;
CREATE TRIGGER update_product_collection_modified_on
    BEFORE UPDATE ON product_collection
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_on_column();

-- Trigger for 'product_translations' table
DROP TRIGGER IF EXISTS update_product_translations_modified_on ON product_translations;
CREATE TRIGGER update_product_translations_modified_on
    BEFORE UPDATE ON product_translations
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_on_column();

-- Trigger for 'product_custom_attributes' table
DROP TRIGGER IF EXISTS update_product_custom_attributes_modified_on ON product_custom_attributes;
CREATE TRIGGER update_product_custom_attributes_modified_on
    BEFORE UPDATE ON product_custom_attributes
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_on_column();

-- Trigger for 'product_collection_img_array' table
DROP TRIGGER IF EXISTS update_product_collection_img_array_modified_on ON product_collection_img_array;
CREATE TRIGGER update_product_collection_img_array_modified_on
    BEFORE UPDATE ON product_collection_img_array
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_on_column();

-- Trigger for 'lang' table
DROP TRIGGER IF EXISTS update_lang_modified_on ON lang;
CREATE TRIGGER update_lang_modified_on
    BEFORE UPDATE ON lang
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_on_column();

-- Trigger for 'product_collection_translations' table (if exists)
DROP TRIGGER IF EXISTS update_product_collection_translations_modified_on ON product_collection_translations;
CREATE TRIGGER update_product_collection_translations_modified_on
    BEFORE UPDATE ON product_collection_translations
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_on_column();

-- Trigger for 'product_collection_custom_attributes' table (if exists)
DROP TRIGGER IF EXISTS update_product_collection_custom_attributes_modified_on ON product_collection_custom_attributes;
CREATE TRIGGER update_product_collection_custom_attributes_modified_on
    BEFORE UPDATE ON product_collection_custom_attributes
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_on_column();

-- =============================================================================
-- STEP 4: Update existing records to set created_on to current timestamp
-- (Optional - only if you want to set timestamps for existing data)
-- =============================================================================

-- Uncomment the following lines if you want to update existing records:
-- UPDATE product SET created_on = CURRENT_TIMESTAMP WHERE created_on IS NULL;
-- UPDATE product_collection SET created_on = CURRENT_TIMESTAMP WHERE created_on IS NULL;
-- UPDATE product_translations SET created_on = CURRENT_TIMESTAMP WHERE created_on IS NULL;
-- UPDATE product_custom_attributes SET created_on = CURRENT_TIMESTAMP WHERE created_on IS NULL;
-- UPDATE product_collection_img_array SET created_on = CURRENT_TIMESTAMP WHERE created_on IS NULL;
-- UPDATE lang SET created_on = CURRENT_TIMESTAMP WHERE created_on IS NULL;
-- UPDATE product_collection_translations SET created_on = CURRENT_TIMESTAMP WHERE created_on IS NULL;
-- UPDATE product_collection_custom_attributes SET created_on = CURRENT_TIMESTAMP WHERE created_on IS NULL;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check if columns were added successfully
SELECT 
    table_name,
    column_name,
    data_type,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
    AND column_name IN ('created_on', 'modified_on')
ORDER BY table_name, column_name;

-- Check triggers
SELECT 
    trigger_name,
    event_object_table,
    action_timing,
    event_manipulation
FROM information_schema.triggers 
WHERE trigger_schema = 'public' 
    AND trigger_name LIKE '%modified_on%'
ORDER BY event_object_table;