from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdf2image
import pytesseract
import cv2
import numpy as np
from pathlib import Path
import tempfile
import os
import re
import time
import logging  # Add this line
import gc

app = FastAPI()

# Configure CORS to allow the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Tesseract with the correct Windows path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    """Preprocess the image for better OCR results."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.fastNlMeansDenoising(binary)
    return denoised

def extract_text_from_pdf(pdf_path: str):
    """Extract structured data from PDF using OCR."""
    extracted_data = []
    images = []
    
    try:
        images = pdf2image.convert_from_path(pdf_path, dpi=400)
        for page_num, image in enumerate(images):
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            if opencv_image.ndim == 3 and opencv_image.shape[2] == 4:
                opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_BGRA2BGR)
            
            processed_img = preprocess_image(opencv_image)
            ocr_text = pytesseract.image_to_string(processed_img, lang='hin+eng')
            logger.info(f"OCR text from page {page_num}: {ocr_text}")
            
            lines = ocr_text.split('\n')
            record = {}
            for line in lines:
                line = line.strip()
                if not line:
                    if record and all(key in record for key in ['name', 'age', 'house_number']):
                        extracted_data.append(record)
                        record = {}
                    continue
                
                section_match = re.search(r'अनुभाग संख्या एवं नाम\s*:\s*(\d+-\w+[\w\s]+)', ocr_text, re.MULTILINE)
                if section_match and 'section_number' not in record:
                    section = section_match.group(1).strip()
                    record['section_number'] = section.split('-')[0].strip()
                    record['section_name'] = '-'.join(section.split('-')[1:]).strip()

                polling_match = re.search(r'निवाचन क्षेत्र की संख्या एवं नाम\s*:\s*(\d+\s*-\s*[\w\s()]+)', ocr_text, re.MULTILINE)
                if polling_match and 'polling_station_number' not in record:
                    polling = polling_match.group(1).strip()
                    record['polling_station_number'] = polling.split('-')[0].strip()
                    record['polling_station_name'] = '-'.join(polling.split('-')[1:]).strip()

                name_match = re.search(r'निर्वाचक का नाम\s*:\s*([^\n]+)', line)
                if name_match:
                    full_name = name_match.group(1).strip()
                    name_parts = full_name.split()
                    record['name'] = full_name
                    record['surname'] = name_parts[-1] if name_parts else ''
                    continue
                
                age_match = re.search(r'उम्र\s*:\s*(\d+)', line)
                if age_match:
                    record['age'] = int(age_match.group(1))
                    continue
                
                house_number_match = re.search(r'मकान संख्या\s*:\s*(\d+)', line)
                if house_number_match:
                    record['house_number'] = house_number_match.group(1).strip()
                    continue
                
                spouse_or_parent_match = re.search(r'(पिता का नाम|पति का नाम)\s*:\s*([^\n]+)', line)
                if spouse_or_parent_match:
                    record['spouse_or_parent_name'] = spouse_or_parent_match.group(2).strip()
                    continue
                
                gender_match = re.search(r'लिंग\s*:\s*(पुरुष|महिला)', line)
                if gender_match:
                    record['gender'] = gender_match.group(1)
                    continue
                
                tag_match = re.search(r'\|?\s*(\d+\s*\|?\s*[A-Za-z0-9]+)', line)
                if tag_match and 'tag_number' not in record:
                    record['tag_number'] = tag_match.group(1).strip().replace('|', '').strip()
            
            if record and all(key in record for key in ['name', 'age', 'house_number']):
                extracted_data.append(record)
                logger.info(f"Matched data on page {page_num}: {record}")
            else:
                logger.warning(f"No match found on page {page_num} with OCR text: {ocr_text}")
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        for image in images:
            if hasattr(image, 'close'):
                image.close()
        gc.collect()
    
    return extracted_data

@app.post("/api/extract")
async def extract_data(file: UploadFile):
    if not file.filename.endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={"detail": "Only PDF files are allowed"}
        )
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        extracted_data = extract_text_from_pdf(temp_path)
        
        if not extracted_data:
            return JSONResponse(
                status_code=422,
                content={"detail": "No data could be extracted from the PDF"}
            )
        
        return JSONResponse(content=extracted_data)
    
    except Exception as e:
        logger.error(f"Error in extract_data: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"An error occurred: {str(e)}"}
        )
    
    finally:
        if temp_path and os.path.exists(temp_path):
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    time.sleep(1 + attempt * 0.5)
                    os.unlink(temp_path)
                    logger.info(f"Deleted temp file: {temp_path} after {attempt + 1} attempt(s)")
                    break
                except PermissionError as e:
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed to delete {temp_path}: {str(e)}")
                    if attempt == max_attempts - 1:
                        logger.error(f"Failed to delete temp file after {max_attempts} attempts: {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error deleting {temp_path}: {str(e)}")
                    break

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

@app.get("/test-cors")
async def test_cors():
    logger.info("Testing CORS endpoint")
    return {"message": "CORS test successful"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)