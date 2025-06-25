# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# === UTF-8 консоль для Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Set dry run mode for ETL
os.environ['DRY_RUN'] = 'true'

# Import ETL functions after setting environment variables
from ETL import parse_array, parse_attributes, clean_string

def test_parse_array():
    """Test the parse_array function"""
    test_cases = [
        ('[https://example.com/1.jpg, https://example.com/2.jpg]', 2),
        ('https://example.com/single.jpg', 1),
        ('', 0),
        (None, 0),
        (123, 0)  # Non-string input
    ]
    
    for input_val, expected_count in test_cases:
        result = parse_array(input_val)
        assert len(result) == expected_count, f"Expected {expected_count} items, got {len(result)} for input: {input_val}"
    
    print("✅ parse_array tests passed")

def test_parse_attributes():
    """Test the parse_attributes function"""
    test_cases = [
        ('品牌:NEXTUXURY AVENUE/丽舍大道-外套材质:混纺-图案:几何图案', 3),
        ('key1:value1', 1),
        ('key1:value1;key2:value2', 2),
        ('', 0),
        (None, 0),
        (123, 0)  # Non-string input
    ]
    
    for input_val, expected_count in test_cases:
        result = parse_attributes(input_val)
        assert len(result) == expected_count, f"Expected {expected_count} pairs, got {len(result)} for input: {input_val}"
    
    print("✅ parse_attributes tests passed")

def test_clean_string():
    """Test the clean_string function"""
    test_cases = [
        ('  test  ', 'test'),
        ('test', 'test'),
        ('', ''),
        (None, None),
        (123, 123)  # Non-string input
    ]
    
    for input_val, expected in test_cases:
        result = clean_string(input_val)
        assert result == expected, f"Expected '{expected}', got '{result}' for input: {input_val}"
    
    print("✅ clean_string tests passed")

def test_csv_reading():
    """Test reading the CSV file"""
    try:
        # Get the CSV path from environment or use default
        csv_path = os.getenv('RAW_CSV_PATH', 'x:\\DATA_STORAGE\\Furnithai\\RAW_WXW\\_Raw Data.csv')
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        print(f"✅ Successfully read CSV file with {len(df)} rows and {len(df.columns)} columns")
        print(f"Column names: {', '.join(df.columns[:5])}...")
        return True
    except Exception as e:
        print(f"❌ Failed to read CSV file: {e}")
        return False

def test_mapping_reading():
    """Test reading the mapping file"""
    try:
        # Get the mapping path from environment or use default
        mapping_path = os.getenv('MAPPING_CSV_PATH', 'x:\\DATA_STORAGE\\Furnithai\\utils\\importer\\map.csv')
        df = pd.read_csv(mapping_path, encoding='utf-8')
        print(f"✅ Successfully read mapping file with {len(df)} rows")
        return True
    except Exception as e:
        print(f"❌ Failed to read mapping file: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("Running ETL validation tests...\n")
    
    # Test utility functions
    test_parse_array()
    test_parse_attributes()
    test_clean_string()
    
    # Test file reading
    csv_ok = test_csv_reading()
    mapping_ok = test_mapping_reading()
    
    print("\nTest summary:")
    if csv_ok and mapping_ok:
        print("✅ All tests passed! The ETL process should work correctly.")
        print("\nYou can now run the ETL process with:")
        print("  python run_etl.py --dry-run  # To test without making changes")
        print("  python run_etl.py  # To run the actual import")
    else:
        print("❌ Some tests failed. Please fix the issues before running the ETL process.")

if __name__ == "__main__":
    run_tests()