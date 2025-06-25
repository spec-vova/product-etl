# -*- coding: utf-8 -*-
import os
import sys
import argparse
from ETL import main as run_etl

# === UTF-8 консоль для Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='Run ETL process for Furnithai')
    parser.add_argument('--csv', type=str, help='Path to the CSV file (default: RAW_WXW/_Raw Data.csv)')
    parser.add_argument('--mapping', type=str, help='Path to the mapping CSV file (default: utils/importer/map.csv)')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without committing changes to the database')
    
    args = parser.parse_args()
    
    # Override default paths if provided
    if args.csv:
        os.environ['RAW_CSV_PATH'] = args.csv
    if args.mapping:
        os.environ['MAPPING_CSV_PATH'] = args.mapping
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'
    
    # Run the ETL process
    run_etl()

if __name__ == "__main__":
    main()