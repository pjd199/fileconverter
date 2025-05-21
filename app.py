# app.py
import os
import zipfile
import io
from flask import Flask, request, render_template, send_file
from pdf2image import convert_from_bytes
from PIL import Image

app = Flask(__name__)

# IMPORTANT: For AWS Lambda, you need to ensure 'poppler-utils' is available.
# This usually means creating a Lambda Layer with the poppler binaries.
# If poppler is not found, pdf2image will raise an error.
# You might need to specify the path to poppler's bin directory if it's not in PATH.
# Example: POPPLER_PATH = "/opt/bin" # If using a Lambda Layer
# If you set POPPLER_PATH, pass it to convert_from_bytes:
# images = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)

@app.route('/')
def index():
    """
    Renders the main page with the PDF upload form.
    """
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_pdf():
    """
    Handles the PDF file upload, converts it to JPG(s),
    and returns the result (single JPG or a ZIP file of JPGs).
    """
    if 'pdfFile' not in request.files:
        return "No PDF file part in the request", 400

    pdf_file = request.files['pdfFile']
    if pdf_file.filename == '':
        return "No selected file", 400

    if pdf_file and pdf_file.filename.lower().endswith('.pdf'):
        try:
            pdf_bytes = pdf_file.read()

            # Convert PDF to images. Each page becomes a PIL Image object.
            # You can adjust dpi for quality, e.g., dpi=200
            images = convert_from_bytes(pdf_bytes, dpi=150)

            if not images:
                return "Could not convert PDF to images. Ensure PDF is valid.", 500

            if len(images) == 1:
                # Single-page PDF: Return a single JPG
                img_byte_arr = io.BytesIO()
                images[0].save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr.seek(0)
                return send_file(img_byte_arr, mimetype='image/jpeg', as_attachment=True, download_name='converted_page_1.jpg')
            else:
                # Multi-page PDF: Create a ZIP file of JPGs
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zf:
                    for i, img in enumerate(images):
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG', quality=85)
                        img_byte_arr.seek(0)
                        zf.writestr(f'page_{i+1}.jpg', img_byte_arr.getvalue())
                zip_buffer.seek(0)
                return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='converted_pages.zip')

        except Exception as e:
            # Log the error for debugging
            print(f"Error during PDF conversion: {e}")
            return f"An error occurred during conversion: {e}", 500
    else:
        return "Invalid file type. Please upload a PDF.", 400

# This is for local development. For Lambda, use the wsgi_lambda handler.
if __name__ == '__main__':
    app.run(debug=True, port=5000)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF to JPG Converter</title>
    <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
    <link href="[https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap)" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f3f4f6; /* Light gray background */
        }
        .container {
            max-width: 600px;
        }
        .card {
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }
        .file-input-label {
            cursor: pointer;
            border: 2px dashed #d1d5db; /* Gray dashed border */
            border-radius: 8px;
            padding: 1.5rem;
            transition: all 0.2s ease-in-out;
        }
        .file-input-label:hover {
            border-color: #9ca3af; /* Darker gray on hover */
            background-color: #f9fafb; /* Lighter background on hover */
        }
        .file-input-label input[type="file"] {
            display: none;
        }
        .upload-button {
            background-color: #4f46e5; /* Indigo */
            color: white;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            transition: background-color 0.2s ease-in-out;
        }
        .upload-button:hover {
            background-color: #4338ca; /* Darker indigo on hover */
        }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="container mx-auto p-6 card">
        <h1 class="text-3xl font-bold text-center text-gray-800 mb-6">
            Welcome to PDF to JPG Converter!
        </h1>
        <p class="text-center text-gray-600 mb-8">
            Easily convert your PDF files into high-quality JPG images.
            Single-page PDFs will be returned as one JPG, while multi-page PDFs will be zipped into a single file containing all the converted JPGs.
        </p>

        <form action="/convert" method="post" enctype="multipart/form-data" class="space-y-6">
            <div class="flex items-center justify-center">
                <label for="pdfFile" class="file-input-label flex flex-col items-center justify-center w-full text-gray-500">
                    <svg class="w-12 h-12 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                    </svg>
                    <span class="font-medium text-gray-600">Drag and drop your PDF here or click to select</span>
                    <input type="file" id="pdfFile" name="pdfFile" accept=".pdf" required onchange="updateFileName(this)">
                </label>
            </div>
            <div id="fileNameDisplay" class="text-center text-sm text-gray-700 mt-2"></div>

            <div class="text-center">
                <button type="submit" class="upload-button inline-flex items-center justify-center font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
                    Convert PDF
                </button>
            </div>
        </form>
    </div>

    <script>
        function updateFileName(input) {
            const fileNameDisplay = document.getElementById('fileNameDisplay');
            if (input.files.length > 0) {
                fileNameDisplay.textContent = `Selected file: ${input.files[0].name}`;
            } else {
                fileNameDisplay.textContent = '';
            }
        }
    </script>
</body>
</html>
```python
# lambda_function.py
# This file is the entry point for AWS Lambda.
# It uses 'wsgi_lambda' to wrap the Flask application.

from wsgi_lambda import LambdaResponse, WsgiLambda
from app import app # Import your Flask app instance

# Initialize the WsgiLambda handler with your Flask app
# The 'app' object from app.py is the WSGI application.
lambda_handler = WsgiLambda(app)

# You can optionally define a direct handler function for testing or specific integrations
# def handler(event, context):
#     # This function will be called by AWS Lambda
#     # The WsgiLambda instance handles the actual WSGI request/response conversion
#     return lambda_handler(event, context)

