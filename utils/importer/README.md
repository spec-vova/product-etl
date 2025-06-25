# ETL Script for Furnithai

This ETL (Extract, Transform, Load) script is designed to import product data from CSV files into the Furnithai database.

## Overview

The script performs the following operations:

1. Reads a CSV file containing product data
2. Maps the CSV columns to database tables and fields according to a mapping configuration
3. Processes product collections (master rows) and their variations
4. Handles translations, custom attributes, and product images
5. Inserts or updates data in the database using UPSERT operations

## Files

- `ETL.py`: The main ETL script
- `map.csv`: Configuration file that maps CSV columns to database tables and fields

## Installation

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Ensure your `.env` file contains the correct database credentials:
   ```
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASS=your_database_password
   DB_PORT=5433  # Default port, change if needed
   ```

2. Test the ETL process before running it:
   ```
   python test_etl.py
   ```
   This will validate the utility functions and check if the CSV and mapping files can be read correctly.

3. Run the ETL script using one of the following methods:

   ### Using the Batch File (Windows)
   Simply double-click the `run_etl.bat` file or run it from the command prompt:
   ```
   run_etl.bat
   ```
   This will display a menu with options to:
   - Install dependencies
   - Run tests
   - Run ETL with dry-run (no database changes)
   - Run ETL (with database changes)

   ### Direct Execution
   ```
   python ETL.py
   ```

   ### Using the Command-Line Interface
   ```
   python run_etl.py [options]
   ```

   Available options:
   - `--csv PATH`: Specify a custom path to the CSV file
   - `--mapping PATH`: Specify a custom path to the mapping CSV file
   - `--dry-run`: Perform a dry run without committing changes to the database

   Examples:
   ```
   # Run with default settings
   python run_etl.py
   
   # Run with a custom CSV file
   python run_etl.py --csv "path/to/your/data.csv"
   
   # Run with a custom mapping file and in dry-run mode
   python run_etl.py --mapping "path/to/your/mapping.csv" --dry-run
   ```

## Mapping Configuration

The `map.csv` file defines how CSV columns map to database tables and fields. Each row contains:

- `raw_input_field`: The column name in the CSV file
- `db_table`: The target database table
- `field`: The target field in the database table
- Additional configuration parameters (optional)

## Data Processing

- **Product Collections**: The first row in the CSV is treated as the master product collection
- **Product Variations**: Subsequent rows are treated as variations of the master product
- **Custom Attributes**: Parsed from the 'Custom Attributes' column
- **Images**: URLs are extracted from array-like strings

## Error Handling

The script uses transaction management to ensure data integrity. If an error occurs during processing, all changes are rolled back.