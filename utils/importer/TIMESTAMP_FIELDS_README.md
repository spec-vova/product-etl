# Database Timestamp Fields Addition

This directory contains scripts to add `created_on` and `modified_on` timestamp fields to all database tables, along with automatic update triggers.

## 📁 Files Overview

### Core Scripts
- **`add_timestamps.py`** - Main Python script with interactive options
- **`add_timestamps.bat`** - Windows batch file for easy execution
- **`add_timestamp_fields.sql`** - Manual SQL script for known tables
- **`add_timestamp_fields_dynamic.sql`** - Dynamic SQL script for all tables

## 🚀 Quick Start

### Option 1: Run Python Script (Recommended)
```bash
# Navigate to the importer directory
cd x:\DATA_STORAGE\Furnithai\utils\importer

# Run the interactive script
python add_timestamps.py
```

### Option 2: Run Batch File (Windows)
```bash
# Double-click or run from command line
add_timestamps.bat
```

### Option 3: Execute SQL Directly
```sql
-- For all tables dynamically
\i add_timestamp_fields_dynamic.sql

-- Or for known tables only
\i add_timestamp_fields.sql
```

## 🔧 What These Scripts Do

### 1. Add Timestamp Columns
- **`created_on`**: Timestamp when record was created (default: CURRENT_TIMESTAMP)
- **`modified_on`**: Timestamp when record was last updated (default: CURRENT_TIMESTAMP)

### 2. Create Update Function
```sql
CREATE OR REPLACE FUNCTION update_modified_on_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_on = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

### 3. Create Automatic Triggers
- Automatically updates `modified_on` field whenever a record is updated
- One trigger per table: `update_{table_name}_modified_on`

### 4. Verification
- Lists all tables with timestamp columns
- Shows all created triggers
- Displays sample data with timestamps

## 📊 Benefits

### Data Auditing
- Track when records were created
- Monitor when records were last modified
- Essential for data governance and compliance

### Performance Monitoring
- Identify recently updated data
- Optimize queries with timestamp-based filtering
- Monitor ETL process timing

### Debugging & Troubleshooting
- Trace data modification patterns
- Identify stale or outdated records
- Debug ETL pipeline issues

## 🛡️ Safety Features

### Non-Destructive
- Uses `ADD COLUMN IF NOT EXISTS` to prevent errors
- Existing data remains unchanged
- Can be run multiple times safely

### Rollback Support
```sql
-- To remove timestamp fields (if needed)
ALTER TABLE table_name DROP COLUMN IF EXISTS created_on;
ALTER TABLE table_name DROP COLUMN IF EXISTS modified_on;
DROP TRIGGER IF EXISTS update_table_name_modified_on ON table_name;
```

## 📈 Code Quality & Maintainability Enhancements

### 1. Database Schema Management

#### Current State Analysis
- ✅ **ETL Pipeline**: Well-structured with proper error handling
- ✅ **Data Validation**: Good use of cleaning functions
- ✅ **Foreign Key Relationships**: Properly implemented
- ⚠️ **Missing**: Timestamp tracking for audit trails

#### Recommendations

**A. Implement Database Versioning**
```sql
-- Create schema version table
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Track schema changes
INSERT INTO schema_version (version, description) 
VALUES ('1.1.0', 'Added timestamp fields to all tables');
```

**B. Add Data Quality Constraints**
```sql
-- Ensure created_on is never in the future
ALTER TABLE product ADD CONSTRAINT check_created_on_not_future 
CHECK (created_on <= CURRENT_TIMESTAMP);

-- Ensure modified_on >= created_on
ALTER TABLE product ADD CONSTRAINT check_modified_after_created 
CHECK (modified_on >= created_on);
```

### 2. ETL Pipeline Improvements

#### Current ETL Analysis
- ✅ **Error Handling**: Good exception management
- ✅ **Data Cleaning**: Proper string and array parsing
- ✅ **UUID Generation**: Consistent ID management
- ⚠️ **Missing**: Incremental updates and change tracking

#### Recommendations

**A. Implement Change Detection**
```python
# Add to ETL.py
def detect_changes(new_data, existing_data):
    """Detect if record has changed"""
    for key, value in new_data.items():
        if key in existing_data and existing_data[key] != value:
            return True
    return False

# Use in ETL process
if existing_record:
    if detect_changes(new_record, existing_record):
        # Update record - trigger will set modified_on
        update_record(new_record)
    else:
        # Skip update - no changes detected
        continue
```

**B. Add ETL Logging Table**
```sql
CREATE TABLE etl_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    process_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) CHECK (status IN ('running', 'completed', 'failed')),
    records_processed INTEGER,
    records_inserted INTEGER,
    records_updated INTEGER,
    error_message TEXT
);
```

### 3. Performance Optimizations

**A. Add Indexes for Timestamp Queries**
```sql
-- Index for recent records queries
CREATE INDEX CONCURRENTLY idx_product_created_on ON product(created_on DESC);
CREATE INDEX CONCURRENTLY idx_product_modified_on ON product(modified_on DESC);

-- Composite index for ETL queries
CREATE INDEX CONCURRENTLY idx_product_master_code_modified 
ON product(product_collection_master_code, modified_on DESC);
```

**B. Partitioning for Large Tables**
```sql
-- Example: Partition product table by creation date
CREATE TABLE product_partitioned (
    LIKE product INCLUDING ALL
) PARTITION BY RANGE (created_on);

-- Create monthly partitions
CREATE TABLE product_2024_01 PARTITION OF product_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 4. Monitoring & Alerting

**A. Data Freshness Monitoring**
```sql
-- Query to check data freshness
SELECT 
    table_name,
    MAX(modified_on) as last_update,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(modified_on)))/3600 as hours_since_update
FROM (
    SELECT 'product' as table_name, modified_on FROM product
    UNION ALL
    SELECT 'product_collection' as table_name, modified_on FROM product_collection
) t
GROUP BY table_name;
```

**B. ETL Performance Monitoring**
```python
# Add to ETL monitoring
def monitor_etl_performance():
    """Monitor ETL performance metrics"""
    metrics = {
        'records_per_second': calculate_throughput(),
        'error_rate': calculate_error_rate(),
        'data_freshness': check_data_freshness(),
        'foreign_key_violations': check_orphaned_records()
    }
    
    # Send alerts if thresholds exceeded
    if metrics['error_rate'] > 0.05:  # 5% error rate
        send_alert(f"High ETL error rate: {metrics['error_rate']}")
```

### 5. Code Organization Improvements

**A. Configuration Management**
```python
# config.py
class ETLConfig:
    def __init__(self):
        self.db_config = self._load_db_config()
        self.file_paths = self._load_file_paths()
        self.processing_options = self._load_processing_options()
    
    def _load_db_config(self):
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5433")),
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASS")
        }
```

**B. Modular ETL Components**
```python
# etl_components.py
class DataExtractor:
    def extract_from_csv(self, file_path): pass
    def extract_from_api(self, endpoint): pass

class DataTransformer:
    def clean_data(self, data): pass
    def validate_data(self, data): pass
    def transform_data(self, data): pass

class DataLoader:
    def load_to_database(self, data): pass
    def handle_conflicts(self, conflicts): pass
```

## 🔍 Usage Examples

### Query Recent Changes
```sql
-- Find all products modified in the last 24 hours
SELECT product_collection_sku, modified_on
FROM product 
WHERE modified_on > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY modified_on DESC;

-- Find products created today
SELECT COUNT(*) as new_products_today
FROM product 
WHERE created_on::date = CURRENT_DATE;
```

### ETL Monitoring Queries
```sql
-- Check for stale data (not updated in 7 days)
SELECT 
    table_name,
    COUNT(*) as stale_records
FROM (
    SELECT 'product' as table_name FROM product 
    WHERE modified_on < CURRENT_TIMESTAMP - INTERVAL '7 days'
    UNION ALL
    SELECT 'product_collection' as table_name FROM product_collection 
    WHERE modified_on < CURRENT_TIMESTAMP - INTERVAL '7 days'
) t
GROUP BY table_name;
```

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Ensure user has ALTER TABLE privileges
   GRANT ALTER ON ALL TABLES IN SCHEMA public TO your_user;
   ```

2. **Trigger Creation Failed**
   ```sql
   -- Check if function exists
   SELECT proname FROM pg_proc WHERE proname = 'update_modified_on_column';
   ```

3. **Column Already Exists**
   - Scripts use `IF NOT EXISTS` - safe to re-run
   - Check existing columns: `\d table_name`

### Verification Commands
```sql
-- Check all timestamp columns
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE column_name IN ('created_on', 'modified_on')
ORDER BY table_name;

-- Check all triggers
SELECT trigger_name, event_object_table 
FROM information_schema.triggers 
WHERE trigger_name LIKE '%modified_on%';
```

## 📝 Next Steps

1. **Run the timestamp addition scripts**
2. **Update ETL processes** to leverage timestamp fields
3. **Implement monitoring queries** for data freshness
4. **Add performance indexes** for timestamp-based queries
5. **Consider implementing** the suggested code quality improvements

---

*This enhancement adds robust timestamp tracking to your database schema, providing the foundation for better data auditing, performance monitoring, and ETL pipeline management.*