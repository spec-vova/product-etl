# -*- coding: utf-8 -*-
import os
import sys
import argparse
from dotenv import load_dotenv

# === UTF-8 console for Windows ===
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Run the Details Translator ETL process with database integration')
    
    parser.add_argument('--dry-run', action='store_true', 
                        help='Run in dry-run mode (no database changes)')
    
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit the number of products to process (0 = no limit)')
    
    parser.add_argument('--skip-download', action='store_true',
                        help='Skip image downloading step')
    
    parser.add_argument('--skip-ocr', action='store_true',
                        help='Skip OCR processing step')
    
    parser.add_argument('--skip-translation', action='store_true',
                        help='Skip translation step')
    
    parser.add_argument('--skip-logistics', action='store_true',
                        help='Skip logistics extraction step')
    
    parser.add_argument('--product-id', type=str,
                        help='Process only a specific product ID')
    
    parser.add_argument('--collection-id', type=str,
                        help='Process only products from a specific collection ID')
    
    parser.add_argument('--images-folder', type=str,
                        help='Path to the folder where images will be stored')
    
    parser.add_argument('--tesseract-path', type=str,
                        help='Path to the Tesseract OCR executable')
    
    args = parser.parse_args()
    
    # Set environment variables based on arguments
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'
    else:
        os.environ['DRY_RUN'] = 'false'
    
    if args.limit > 0:
        os.environ['PROCESS_LIMIT'] = str(args.limit)
    
    if args.skip_download:
        os.environ['SKIP_DOWNLOAD'] = 'true'
    
    if args.skip_ocr:
        os.environ['SKIP_OCR'] = 'true'
    
    if args.skip_translation:
        os.environ['SKIP_TRANSLATION'] = 'true'
    
    if args.skip_logistics:
        os.environ['SKIP_LOGISTICS'] = 'true'
    
    if args.product_id:
        os.environ['PRODUCT_ID'] = args.product_id
    
    if args.collection_id:
        os.environ['COLLECTION_ID'] = args.collection_id
    
    if args.images_folder:
        os.environ['IMAGES_FOLDER'] = args.images_folder
    
    if args.tesseract_path:
        os.environ['TESSERACT_CMD'] = args.tesseract_path
    
    # Import and run the orchestrator
    from db_orchestrator import main as run_orchestrator
    run_orchestrator()

if __name__ == "__main__":
    main()