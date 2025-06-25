# Details Translator with Database Integration

This utility extracts, processes, and translates product details from HTML content stored in the database. It performs the following steps:

1. Extracts image links from HTML content
2. Downloads images (if not already present)
3. Performs OCR on images to extract text
4. Translates extracted text from Chinese to English
5. Extracts logistics information from translated text
6. Stores results back in the database

## Requirements

- Python 3.7+
- PostgreSQL database
- Tesseract OCR installed
- OpenAI API key

## Installation

1. Install required Python packages:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables:

```
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASS=your_database_password
DB_PORT=your_database_port
OPENAI_API_KEY=your_openai_api_key
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Usage

Run the orchestrator with various options:

```bash
python run_orchestrator.py [options]
```

### Options

- `--dry-run`: Run in dry-run mode (no database changes)
- `--limit N`: Limit the number of products to process (0 = no limit)
- `--skip-download`: Skip image downloading step
- `--skip-ocr`: Skip OCR processing step
- `--skip-translation`: Skip translation step
- `--skip-logistics`: Skip logistics extraction step
- `--product-id ID`: Process only a specific product ID
- `--collection-id ID`: Process only products from a specific collection ID
- `--images-folder PATH`: Path to the folder where images will be stored
- `--tesseract-path PATH`: Path to the Tesseract OCR executable

### Examples

```bash
# Run in dry-run mode
python run_orchestrator.py --dry-run

# Process only 5 products
python run_orchestrator.py --limit 5

# Skip image downloading and OCR
python run_orchestrator.py --skip-download --skip-ocr

# Process a specific product
python run_orchestrator.py --product-id "12345678-1234-1234-1234-123456789012"

# Specify custom paths
python run_orchestrator.py --images-folder "D:\product_images" --tesseract-path "D:\Tesseract-OCR\tesseract.exe"
```

## Database Schema

The script interacts with the following database tables:

- `product`: Contains product information
- `product_collection`: Contains product collection information and HTML details
- `product_translations`: Stores translated product descriptions
- `product_custom_attributes`: Stores custom attributes including logistics information

## Error Handling

The script includes error handling for:

- Database connection issues
- Image download failures
- OCR processing errors
- Translation failures
- Logistics extraction errors

Errors are logged to the console, and the script will continue processing other products when possible.

## Dry Run Mode

In dry-run mode, the script performs all processing steps but does not commit changes to the database. This is useful for testing and validation.