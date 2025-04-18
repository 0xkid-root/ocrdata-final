from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import magic
from pydantic import ValidationError
from ocr_utils import process_pdf, PDFProcessingError
from models import ProcessingResponse

app = Flask(__name__)
CORS(app)

# Create necessary directories
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
ALLOWED_MIME_TYPES = ['application/pdf']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

def validate_file(file):
    """Validate uploaded file"""
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    if size > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 10MB limit")
    file.seek(0)
    
    # Check file type
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError("Invalid file type. Only PDF files are allowed")

@app.route("/upload", methods=["POST"])
def upload_pdf():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        try:
            validate_file(file)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Save and process file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        
        try:
            extracted_data = process_pdf(file_path)
            response = ProcessingResponse(
                status="success",
                data=extracted_data,
                message="PDF processed successfully"
            )
            return jsonify(response.model_dump())
        except PDFProcessingError as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "details": e.details
            }), 422
        finally:
            # Clean up
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "status": "error",
        "error": "File too large",
        "message": "The file size exceeds the maximum limit of 10MB"
    }), 413

if __name__ == "__main__":
    app.run(debug=True, port=5000)