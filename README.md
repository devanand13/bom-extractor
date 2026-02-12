# BOM Extractor - Local Setup

Extract structured data from Bill of Materials PDFs using AI.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

### 1. Clone or Download Project
```bash
# Create project folder
mkdir bom-extractor
cd bom-extractor

# Copy all project files here
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=sk-your-api-key-here
FLASK_ENV=development
```

### 5. Create Directory Structure
```bash
mkdir -p templates static/css static/js uploads outputs
```

### 6. Add Files

Make sure you have these files in the correct locations:
```
bom-extractor/
├── app.py
├── requirements.txt
├── .env
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── uploads/
└── outputs/
```

## Run the Application
```bash
# Make sure virtual environment is activated
python app.py
```

Open your browser and go to: **http://localhost:3000**

## Usage

1. Upload a PDF file (Bill of Materials)
2. Select BOM type (Simple or Engineering)
3. Click "Extract BOM Data"
4. Download results as JSON or CSV
