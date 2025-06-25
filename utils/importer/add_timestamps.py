#!/usr/bin/env python3
"""
Script to add 'created_on' and 'modified_on' timestamp fields to all database tables
This script connects to the PostgreSQL database and executes the timestamp addition queries
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
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

def execute_sql_file(cursor, file_path):
    """Execute SQL commands from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
            cursor.execute(sql_content)
        return True
    except Exception as e:
        print(f"Error executing SQL file {file_path}: {e}")
        return False

def add_timestamp_fields_manual():
    """Add timestamp fields to known tables manually"""
    
    # Known tables from the codebase analysis
    tables = [
        'product',
        'product_collection', 
        'product_translations',
        'product_custom_attributes',
        'product_collection_img_array',
        'lang',
        'product_collection_translations',
        'product_collection_custom_attributes'
    ]
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Connected successfully!")
        
        # Step 1: Create the update function
        print("\n=== Creating update function ===")
        create_function_sql = """
        CREATE OR REPLACE FUNCTION update_modified_on_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.modified_on = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        
        cur.execute(create_function_sql)
        print("✓ Created update_modified_on_column() function")
        
        # Step 2: Add columns to each table
        print("\n=== Adding timestamp columns ===")
        for table in tables:
            try:
                # Add created_on column
                add_created_sql = f"""
                ALTER TABLE {table} 
                ADD COLUMN IF NOT EXISTS created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                """
                cur.execute(add_created_sql)
                
                # Add modified_on column  
                add_modified_sql = f"""
                ALTER TABLE {table} 
                ADD COLUMN IF NOT EXISTS modified_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                """
                cur.execute(add_modified_sql)
                
                print(f"✓ Added timestamp columns to {table}")
                
            except psycopg2.Error as e:
                if "does not exist" in str(e):
                    print(f"⚠ Table {table} does not exist, skipping...")
                else:
                    print(f"✗ Error adding columns to {table}: {e}")
        
        # Step 3: Create triggers
        print("\n=== Creating triggers ===")
        for table in tables:
            try:
                trigger_name = f"update_{table}_modified_on"
                
                # Drop existing trigger
                drop_trigger_sql = f"DROP TRIGGER IF EXISTS {trigger_name} ON {table};"
                cur.execute(drop_trigger_sql)
                
                # Create new trigger
                create_trigger_sql = f"""
                CREATE TRIGGER {trigger_name}
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_modified_on_column();
                """
                cur.execute(create_trigger_sql)
                
                print(f"✓ Created trigger for {table}")
                
            except psycopg2.Error as e:
                if "does not exist" in str(e):
                    print(f"⚠ Table {table} does not exist, skipping trigger...")
                else:
                    print(f"✗ Error creating trigger for {table}: {e}")
        
        # Step 4: Verification
        print("\n=== Verification ===")
        
        # Check columns
        cur.execute("""
        SELECT 
            table_name,
            column_name,
            data_type,
            column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
            AND column_name IN ('created_on', 'modified_on')
        ORDER BY table_name, column_name;
        """)
        
        columns_result = cur.fetchall()
        if columns_result:
            print("\nTimestamp columns added:")
            for row in columns_result:
                print(f"  {row[0]}.{row[1]} ({row[2]}) - Default: {row[3]}")
        else:
            print("⚠ No timestamp columns found")
        
        # Check triggers
        cur.execute("""
        SELECT 
            trigger_name,
            event_object_table,
            action_timing,
            event_manipulation
        FROM information_schema.triggers 
        WHERE trigger_schema = 'public' 
            AND trigger_name LIKE '%modified_on%'
        ORDER BY event_object_table;
        """)
        
        triggers_result = cur.fetchall()
        if triggers_result:
            print("\nTriggers created:")
            for row in triggers_result:
                print(f"  {row[1]}: {row[0]} ({row[2]} {row[3]})")
        else:
            print("⚠ No triggers found")
        
        # Show table counts
        print("\n=== Table Statistics ===")
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"  {table}: {count} records")
            except psycopg2.Error:
                print(f"  {table}: Table does not exist")
        
        print("\n✅ Timestamp fields addition completed successfully!")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            print("Database connection closed.")
    
    return True

def add_timestamp_fields_dynamic():
    """Add timestamp fields to ALL tables dynamically"""
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Connected successfully!")
        
        # Execute the dynamic SQL file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(script_dir, 'add_timestamp_fields_dynamic.sql')
        
        if os.path.exists(sql_file_path):
            print(f"Executing dynamic SQL script: {sql_file_path}")
            if execute_sql_file(cur, sql_file_path):
                print("✅ Dynamic timestamp fields addition completed successfully!")
            else:
                print("✗ Failed to execute dynamic SQL script")
                return False
        else:
            print(f"✗ SQL file not found: {sql_file_path}")
            return False
            
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            print("Database connection closed.")
    
    return True

def main():
    """Main function"""
    print("=== Add Timestamp Fields to Database Tables ===")
    print("This script will add 'created_on' and 'modified_on' fields to all tables.")
    print()
    
    # Check if environment variables are set
    required_env_vars = ['DB_NAME', 'DB_USER', 'DB_PASS']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"✗ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment.")
        return False
    
    print("Choose an option:")
    print("1. Add timestamp fields to known tables only (manual)")
    print("2. Add timestamp fields to ALL tables dynamically (recommended)")
    print()
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == '1':
        return add_timestamp_fields_manual()
    elif choice == '2':
        return add_timestamp_fields_dynamic()
    else:
        print("Invalid choice. Please run the script again and choose 1 or 2.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)