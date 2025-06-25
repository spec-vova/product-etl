-- Dynamic SQL Script to add 'created_on' and 'modified_on' fields to ALL tables
-- This script automatically detects all tables and adds timestamp fields

-- =============================================================================
-- STEP 1: Create function to automatically update modified_on timestamp
-- =============================================================================

CREATE OR REPLACE FUNCTION update_modified_on_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_on = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =============================================================================
-- STEP 2: Dynamic script to add timestamp fields to ALL tables
-- =============================================================================

DO $$
DECLARE
    table_record RECORD;
    sql_statement TEXT;
BEGIN
    -- Loop through all tables in the public schema
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    LOOP
        -- Add created_on column if it doesn't exist
        sql_statement := format('
            ALTER TABLE %I 
            ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        ', table_record.table_name);
        
        EXECUTE sql_statement;
        RAISE NOTICE 'Added created_on column to table: %', table_record.table_name;
        
        -- Add modified_on column if it doesn't exist
        sql_statement := format('
            ALTER TABLE %I 
            ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        ', table_record.table_name);
        
        EXECUTE sql_statement;
        RAISE NOTICE 'Added modified_on column to table: %', table_record.table_name;
        
    END LOOP;
END
$$;

-- =============================================================================
-- STEP 3: Dynamic script to create triggers for ALL tables
-- =============================================================================

DO $$
DECLARE
    table_record RECORD;
    trigger_name TEXT;
    sql_statement TEXT;
BEGIN
    -- Loop through all tables in the public schema
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    LOOP
        -- Create trigger name
        trigger_name := format('update_%s_modified_on', table_record.table_name);
        
        -- Drop existing trigger if it exists
        sql_statement := format('DROP TRIGGER IF EXISTS %I ON %I', trigger_name, table_record.table_name);
        EXECUTE sql_statement;
        
        -- Create new trigger
        sql_statement := format('
            CREATE TRIGGER %I
                BEFORE UPDATE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION update_modified_on_column()
        ', trigger_name, table_record.table_name);
        
        EXECUTE sql_statement;
        RAISE NOTICE 'Created trigger % for table: %', trigger_name, table_record.table_name;
        
    END LOOP;
END
$$;

-- =============================================================================
-- STEP 4: Optional - Update existing records with current timestamp
-- =============================================================================

DO $$
DECLARE
    table_record RECORD;
    sql_statement TEXT;
    updated_count INTEGER;
BEGIN
    -- Loop through all tables in the public schema
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    LOOP
        -- Update created_on for existing records where it's NULL
        sql_statement := format('
            UPDATE %I 
            SET created_on = CURRENT_TIMESTAMP 
            WHERE created_on IS NULL
        ', table_record.table_name);
        
        EXECUTE sql_statement;
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        
        IF updated_count > 0 THEN
            RAISE NOTICE 'Updated % existing records in table: %', updated_count, table_record.table_name;
        END IF;
        
    END LOOP;
END
$$;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Show all tables with their timestamp columns
SELECT 
    t.table_name,
    CASE WHEN c_created.column_name IS NOT NULL THEN 'YES' ELSE 'NO' END as has_created_on,
    CASE WHEN c_modified.column_name IS NOT NULL THEN 'YES' ELSE 'NO' END as has_modified_on,
    c_created.column_default as created_on_default,
    c_modified.column_default as modified_on_default
FROM information_schema.tables t
LEFT JOIN information_schema.columns c_created 
    ON t.table_name = c_created.table_name 
    AND t.table_schema = c_created.table_schema 
    AND c_created.column_name = 'created_on'
LEFT JOIN information_schema.columns c_modified 
    ON t.table_name = c_modified.table_name 
    AND t.table_schema = c_modified.table_schema 
    AND c_modified.column_name = 'modified_on'
WHERE t.table_schema = 'public' 
    AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name;

-- Show all triggers created
SELECT 
    trigger_name,
    event_object_table as table_name,
    action_timing,
    event_manipulation
FROM information_schema.triggers 
WHERE trigger_schema = 'public' 
    AND trigger_name LIKE '%modified_on%'
ORDER BY event_object_table;

-- Show sample data with timestamps from each table
DO $$
DECLARE
    table_record RECORD;
    sql_statement TEXT;
    result_record RECORD;
BEGIN
    RAISE NOTICE 'SAMPLE DATA WITH TIMESTAMPS:';
    RAISE NOTICE '================================';
    
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    LOOP
        sql_statement := format('
            SELECT COUNT(*) as total_records,
                   MIN(created_on) as earliest_created,
                   MAX(created_on) as latest_created,
                   MAX(modified_on) as latest_modified
            FROM %I
        ', table_record.table_name);
        
        BEGIN
            FOR result_record IN EXECUTE sql_statement LOOP
                RAISE NOTICE 'Table: % | Records: % | Earliest: % | Latest Created: % | Latest Modified: %', 
                    table_record.table_name, 
                    result_record.total_records,
                    result_record.earliest_created,
                    result_record.latest_created,
                    result_record.latest_modified;
            END LOOP;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Table: % | Error querying table: %', table_record.table_name, SQLERRM;
        END;
        
    END LOOP;
END
$$;