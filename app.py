"""
BOM Extraction Web Application
Flask app for uploading PDFs and extracting BOM data
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import PyPDF2
import openai
import pandas as pd
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}


class BOMExtractor:
    """Extract structured BOM data from PDFs using LLMs"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("API key not found. Set OPENAI_API_KEY in .env file")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from PDF"""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text += f"\n--- Page {page_num} ---\n"
                text += page.extract_text()
        return text
    
    def extract_bom_data(self, pdf_path: str, bom_type: str = "simple") -> Dict[str, Any]:
        """
        Extract BOM data from PDF
        
        Args:
            pdf_path: Path to PDF file
            bom_type: Type of BOM - "engineering" or "simple"
        
        Returns:
            Dictionary with extracted BOM items
        """
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        
        # Define schema based on BOM type
        if bom_type == "engineering":
            schema = {
                "item_number": "Line item number (e.g., '1', '2')",
                "quantity": "Quantity needed",
                "substitution_code": "Substitution code (S column, e.g., 6, 10)",
                "manufacturer": "Manufacturer name",
                "part_number": "Manufacturer part number",
                "description": "Component description",
                "reference_designator": "Reference designator (REF column, e.g., 'C1, C2', 'U1')",
                "package": "Package type if specified (e.g., '0603', 'SOIC8')"
            }
        else:  # simple
            schema = {
                "category": "Category (e.g., STRUCTURE, ELECTRONICS, OTHER)",
                "where": "Source/location",
                "item": "Item description",
                "quantity": "Quantity",
                "unit_price": "Unit price",
                "total": "Total cost"
            }
        
        # Create prompt
        prompt = f"""
Extract ALL BOM (Bill of Materials) line items from this document.

Document contains a BOM table with these expected fields:
{json.dumps(schema, indent=2)}

CRITICAL INSTRUCTIONS:
1. Extract EVERY line item - do not skip any rows
2. Preserve exact values from the document
3. If a field is empty or not present, use null
4. Return ONLY valid JSON with no markdown formatting
5. For engineering BOMs: Pay attention to substitution codes and reference designators
6. For cost BOMs: Ensure calculations match (quantity × unit_price = total)

Return format:
{{
  "document_title": "extracted title if present",
  "bom_type": "{bom_type}",
  "total_items": <count>,
  "items": [
    {{"field1": "value1", "field2": "value2", ...}},
    ...
  ]
}}

Document text:
{text}
"""
        
        # Call LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise BOM data extraction expert. Extract data exactly as it appears."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        return result


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the upload page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and BOM extraction"""
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    # Get BOM type from form
    bom_type = request.form.get('bom_type', 'simple')
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract BOM data
        extractor = BOMExtractor()
        bom_data = extractor.extract_bom_data(filepath, bom_type)
        
        # Save outputs
        base_name = os.path.splitext(filename)[0]
        json_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{base_name}.json')
        csv_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{base_name}.csv')
        
        # Save JSON
        with open(json_path, 'w') as f:
            json.dump(bom_data, f, indent=2)
        
        # Save CSV
        df = pd.DataFrame(bom_data['items'])
        df.to_csv(csv_path, index=False)
        
        # Return results
        return jsonify({
            'success': True,
            'data': bom_data,
            'files': {
                'json': f'{base_name}.json',
                'csv': f'{base_name}.csv'
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filetype>/<filename>')
def download_file(filetype, filename):
    """Download extracted files"""
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    mimetype = 'application/json' if filetype == 'json' else 'text/csv'
    return send_file(filepath, mimetype=mimetype, as_attachment=True)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)