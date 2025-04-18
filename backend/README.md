# Hindi Voter ID Data Extractor - Backend

This is the backend service for the Hindi Voter ID Data Extractor application. It provides OCR capabilities to extract information from Hindi voter ID cards in PDF format.

## Prerequisites

1. Python 3.8 or higher
2. Tesseract OCR with Hindi language support
3. Poppler (for pdf2image)

## Installation

### 1. Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
sudo apt-get install -y tesseract-ocr-hin
sudo apt-get install -y poppler-utils
```

#### macOS:
```bash
brew install tesseract
brew install tesseract-lang
brew install poppler
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`.

## API Endpoints

### POST /upload
Uploads and processes a PDF file containing Hindi voter ID information.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (PDF file)

**Response:**
```json
[
  {
    "name": "नाम",
    "gender": "पुरुष",
    "age": "25",
    "voter_id": "ABC1234567"
  }
]
```

## Directory Structure

- `uploads/`: Temporary storage for uploaded PDF files
- `data/`: Storage for extracted JSON data
- `app.py`: Main Flask application
- `ocr_utils.py`: OCR processing utilities