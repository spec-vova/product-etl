# Furnithai ETL (Extract, Transform, Load) System

A comprehensive data import system designed to process product data from CSV files into the Furnithai PostgreSQL database with support for multiple product collections, translations, and complex data relationships.

## 🚀 Features

- **Multi-Collection Processing**: Handles multiple unique product collections from a single CSV file
- **Data Type Safety**: Automatic conversion of NumPy data types to PostgreSQL-compatible formats
- **Foreign Key Management**: Intelligent handling of circular dependencies between tables
- **Translation Support**: Multi-language content processing for product collections and categories
- **Image Array Processing**: Extraction and processing of product image URLs
- **Custom Attributes**: Parsing and storage of product-specific attributes
- **Transaction Safety**: Full rollback capability on errors to ensure data integrity
- **Dry Run Mode**: Test imports without making database changes

## 📁 Project Structure

```
utils/importer/
├── ETL.py                    # Main ETL processing script
├── run_etl.py               # Command-line interface
├── run_etl.bat              # Windows batch file for easy execution
├── test_etl.py              # Unit tests and validation
├── map.csv                  # Column mapping configuration
├── requirements.txt         # Python dependencies
└── README.md               # This documentation
```

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Access to Furnithai database schema

### Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create a `.env` file in the project root with your database credentials:
   ```env
   DB_NAME=furnithai_database
   DB_USER=your_username
   DB_PASS=your_password
   DB_PORT=5433
   RAW_CSV_PATH=path/to/your/data.csv
   MAPPING_CSV_PATH=utils/importer/map.csv
   DRY_RUN=false
   ```

## 🚦 Usage

### Quick Start (Windows)

Double-click `run_etl.bat` for an interactive menu with options to:
- Install dependencies
- Run validation tests
- Execute dry-run (preview changes)
- Run full ETL process

### Command Line Interface

```bash
# Basic execution
python run_etl.py

# Custom CSV file
python run_etl.py --csv "path/to/custom_data.csv"

# Dry run mode (no database changes)
python run_etl.py --dry-run

# Custom mapping configuration
python run_etl.py --mapping "path/to/custom_mapping.csv"
```

### Direct Script Execution

```bash
# Run ETL directly
python ETL.py

# Run tests first
python test_etl.py
```

## 📊 Data Processing Flow

### 1. Data Extraction
- Reads CSV file using pandas
- Identifies unique `master_code` entries for collections
- Converts NumPy data types to Python native types

### 2. Data Transformation
- **Product Collections**: Each unique `master_code` creates a collection
- **Product Variations**: All rows with the same `master_code` become product variants
- **Categories**: Extracted and linked to collections with translation support
- **Custom Attributes**: Parsed from structured text format
- **Image Arrays**: URLs extracted from array-like strings

### 3. Data Loading
- **UPSERT Operations**: Updates existing records or inserts new ones
- **Foreign Key Resolution**: Handles circular dependencies intelligently
- **Translation Management**: Creates multilingual content entries
- **Transaction Safety**: All-or-nothing approach with rollback on errors

## 🗺️ Mapping Configuration

The `map.csv` file defines the relationship between CSV columns and database schema:

| Column | Description |
|--------|-------------|
| `raw_input_field` | CSV column name |
| `db_table` | Target database table |
| `field` | Target database column |

### Supported Tables
- `product_collection` - Main product collection data
- `product_collection_translations` - Multilingual collection names
- `product` - Individual product variants
- `category` - Product categories
- `category_translations` - Multilingual category names
- `details_html` - Product detail pages
- `details_html_translations` - Multilingual HTML content

## 🔧 Advanced Features

### Custom Attributes Processing
Parses structured attribute strings into key-value pairs for flexible product specifications.

### Image Array Handling
Extracts multiple image URLs from array-formatted strings and creates proper database relationships.

### Translation Management
Automatically creates translation entries for multilingual content with proper foreign key relationships.

### Error Recovery
Comprehensive error handling with detailed logging and automatic transaction rollback.

## 🧪 Testing

```bash
# Run all tests
python test_etl.py

# Validate CSV and mapping files
python -c "from ETL import *; print('Configuration valid')"
```

## 📝 Logging

The ETL process provides detailed console output including:
- Processing progress for each collection
- Database operation results
- Error messages with context
- Transaction status updates

## ⚠️ Important Notes

- **Backup First**: Always backup your database before running ETL operations
- **Test Mode**: Use `--dry-run` to preview changes before committing
- **Data Validation**: Ensure CSV data quality before processing
- **Performance**: Large datasets may require extended processing time

## 🐛 Troubleshooting

### Common Issues

1. **Foreign Key Violations**: Ensure all referenced data exists or use the built-in dependency resolution
2. **Data Type Errors**: The system automatically converts NumPy types, but verify data formats
3. **Memory Issues**: For very large CSV files, consider processing in batches
4. **Connection Errors**: Verify database credentials and network connectivity

### Getting Help

Check the console output for detailed error messages and stack traces. Most issues are related to:
- Database connectivity
- Data format inconsistencies
- Missing required fields

## 🔄 Recent Improvements

- ✅ Fixed circular foreign key dependencies
- ✅ Added support for multiple product collections per CSV
- ✅ Implemented NumPy data type conversion
- ✅ Enhanced error handling and logging
- ✅ Improved transaction management

---

*For technical support or feature requests, please refer to the project documentation or contact the development team.*