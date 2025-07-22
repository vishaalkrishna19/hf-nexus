# 📊 HappyFox Nexus - Rule-Based Resume Parser & AI Shortlister

> **Transforming complex hiring processes into streamlined and intelligent workflows**

HappyFox Nexus serves as the central point of connection between resumes, data, and recruiters. Built with a hybrid architecture combining high-speed rule-based parsing enhanced with NLP and POS tagging for rapid extraction, and Google Gemini API for intelligent candidate ranking and qualitative analysis.

## 🚀 Key Features

### 🧠 Advanced Rule-Based Parsing with NLP & POS Tagging
- **High-Speed Processing**: Sophisticated rule-based engine powered by spaCy and NLTK for fast and accurate data extraction
- **NLP Enhancement**: Named Entity Recognition (NER) for identifying entities like PERSON names and GPE locations
- **POS Tagging Intelligence**: Part-of-Speech tagging to understand context and identify patterns (e.g., project descriptions through nouns and action verbs)
- **Multi-Format Support**: Processes PDF, DOCX, and image files seamlessly

### 📄 Comprehensive Data Extraction
- **Personal Information**: Name, email, phone number validation using regex patterns
- **Professional Profiles**: LinkedIn and GitHub URL extraction with profile crawling
- **Educational Background**: Degrees, institutions, marks, and CGPA calculation
- **Experience Details**: Internships, projects, and tech stack identification
- **Achievements & Skills**: Awards recognition and programming language detection

### 🔍 OCR Fallback Technology
- **Tesseract Integration**: Advanced OCR engine for text extraction from scanned documents and images
- **Image Processing**: Handles resumes in image formats with high accuracy

### 🤖 AI-Powered Intelligent Ranking
- **Gemini API Integration**: Uses Google's Gemini API for sophisticated candidate ranking
- **Role-Specific Analysis**: Tailored evaluation for Frontend, Backend, and Full Stack positions
- **Detailed Scoring**: Comprehensive score breakdown across multiple criteria
- **Company Fit Assessment**: Analyzes candidates specifically for HappyFox requirements

### 🐙 GitHub Profile Analysis
- **Repository Crawling**: Analyzes public repositories, languages, and coding activity
- **Contribution Insights**: Evaluates GitHub contribution patterns and activity levels
- **Technical Skills Validation**: Cross-references claimed skills with actual code repositories


### 📊 Advanced Data Management
- **Excel Export**: Comprehensive data export with 18+ fields including scores and analysis
- **Responsive UI/UX**: Modern interface with dark/light mode toggle



## 🛠️ Technology Stack

### Backend (Django)
| Library | Purpose |
|---------|---------|
| Django | Core web framework for backend API |
| djangorestframework | Robust REST API toolkit |
| django-cors-headers | Cross-Origin Resource Sharing handling |
| spacy / nltk | **NLP for NER, POS tagging, and tokenization** |
| PyPDF2 / python-docx | PDF and DOCX file processing |
| pytesseract / Pillow | OCR engine for image-to-text extraction |
| google-generativeai | Google Gemini API Python SDK |
| beautifulsoup4 / requests | Web scraping and HTTP requests |
| openpyxl | Excel file generation |

### Frontend (React)
| Library | Purpose |
|---------|---------|
| React | Core UI library |
| react-router-dom | Client-side routing |
| Vite | Modern frontend build tool |
| axios | HTTP client for API requests |
| sass-embedded | SASS/SCSS compilation |
| react-hot-toast | User-friendly notifications |

## 📁 Project Structure

```
nexus/
├── backend/
│   ├── api/                    # Main Django app
│   │   ├── extractors/         # Modular data extraction logic
│   │   │   ├── name_extractor.py
│   │   │   ├── details_extractor.py
│   │   │   ├── linkedin_extractor.py
│   │   │   ├── github_crawler.py
│   │   │   ├── education_extractor.py
│   │   │   ├── internship_extractor.py
│   │   │   ├── project_details.py
│   │   │   ├── achievements_extractor.py
│   │   │   └── language_extractor.py
│   │   ├── utils/              # Utility scripts
│   │   ├── resume_parser.py    # Core parsing orchestrator
│   │   ├── ranker.py          # Gemini-based ranking logic
│   │   └── views.py           # API endpoint views
│   └── myproject/             # Django configuration
└── frontend/                  # React application
    └── src/
        ├── components/
        ├── pages/
        └── utils/
```

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.8+ and pip
- Node.js 16+ and npm
- Git
- Google Gemini API key

### Backend Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd nexus/backend
```

2. **Create and activate virtual environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Install spaCy model (Essential for NLP)**
```bash
python -m spacy download en_core_web_sm
```

5. **Configure environment variables**
Create a `.env` file in `backend/myproject/`:
```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
DEBUG=True
SECRET_KEY="your-secret-key"
```

6. **Run database migrations**
```bash
python manage.py migrate
```

7. **Start the Django server**
```bash
python manage.py runserver
```
Backend API available at `http://127.0.0.1:8000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd ../frontend
```

2. **Install Node.js dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```
Frontend application available at `http://localhost:5173`

## 📖 Usage Guide

### End-User Workflow

1. **Upload Resumes**: Navigate to home page and drag-and-drop or select resume files (PDF/DOCX/Images)
2. **Automatic Parsing**: System processes resumes using rule-based NLP extraction
3. **Shortlist Candidates**: Filter by skills, CGPA, experience, and other criteria
4. **AI Ranking**: Paste job description to get AI-powered candidate rankings with detailed analysis
5. **Export Data**: Download comprehensive Excel reports at any stage
6. **Track Progress**: Use Kanban board to manage interview stages

### Developer Workflow

#### Adding New Extractors
To parse additional fields (e.g., certifications):

```python
# Create certification_extractor.py in api/extractors/
import re
import spacy

def extract_certifications(text):
    # Use NLP and regex patterns
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    
    # Your extraction logic here
    certifications = []
    return certifications
```

Then integrate in `resume_parser.py`:
```python
from extractors.certification_extractor import extract_certifications

# In parsing workflow
certifications = extract_certifications(resume_text)
```

## 🔗 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/shortlist-candidates/` | Filter candidates by criteria |
| POST | `/api/rank-resumes/` | AI-powered candidate ranking |
| GET | `/api/github-details/` | Fetch GitHub profile analysis |
| POST | `/api/export-excel/` | Export candidate data to Excel |

### Example API Usage

**Shortlist Candidates:**
```json
POST /api/shortlist-candidates/
{
  "candidates": [
    {"name": "John Doe", "skills": ["Python", "React"], "cgpa": 8.7}
  ],
  "criteria": {
    "skills": ["Python", "Django"],
    "min_cgpa": 8.5
  }
}
```

**Rank Candidates:**
```json
POST /api/rank-resumes/
{
  "candidates": [
    {"name": "John Doe", "skills": ["Python", "React"]}
  ],
  "job_description": "Looking for Senior Python Developer with Django and AWS experience..."
}
```

## 🎯 Rule-Based Parsing Architecture

### NLP & POS Tagging Implementation

The core strength of HappyFox Nexus lies in its sophisticated rule-based parsing engine:

#### Named Entity Recognition (NER)
- **spaCy Integration**: Uses pre-trained models for entity identification
- **PERSON Recognition**: Accurately extracts candidate names
- **GPE Detection**: Identifies locations and geographical entities

#### Part-of-Speech (POS) Tagging
- **Context Understanding**: Identifies nouns, verbs, and adjectives
- **Pattern Recognition**: Detects project descriptions through noun-verb patterns
- **Semantic Analysis**: Understands document structure and content hierarchy

#### Extraction Modules
Each extractor module combines rule-based patterns with NLP:
- **Regex Patterns**: For structured data like emails and phone numbers
- **Keyword Matching**: For section identification and content extraction
- **NLP Enhancement**: For context-aware parsing and validation

## 📸 Screenshots

### Screenshot 1: Resume Parsing Dashboard
*[Include a screenshot showing the main dashboard with uploaded resumes and extracted data in a table format, highlighting the parsed information like names, emails, skills, etc.]*

### Screenshot 2: AI-Powered Ranking Interface
*[Include a screenshot of the ranking page showing the job description input field and the ranked candidates table with scores and detailed analysis]*




---

**Project by Vishaal Krishna**