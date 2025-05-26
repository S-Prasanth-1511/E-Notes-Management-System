# E-Notes Management System

A web-based platform that empowers students and educators to upload, manage, and intelligently retrieve academic notes. The system features a semantic search engine powered by NLP techniques, enhancing user experience through relevant and context-aware search results.

## 🔍 Features
- User registration and secure login (students/faculty)
- Upload notes with titles, categories, and attachments (PDFs/images)
- Browse all uploaded notes with filtering options
- Advanced semantic search using NLP (TF-IDF + Cosine Similarity)
- Feedback system for search effectiveness
- Responsive and intuitive user interface

## 🎯 Objectives
- Centralized platform for digital academic content
- Fast and relevant information retrieval
- Environmentally friendly by reducing paper-based note sharing
- Accessible from any device, anytime
- Secure and role-based access for users

## 🛠️ Tech Stack

### 🔧 Frontend
- HTML, CSS
- Jinja2 Templating
- Bootstrap (for responsive design)

### ⚙️ Backend
- Python (Flask)
- Flask-Login (for session/authentication management)
- MySQL (for data storage)

### 🤖 NLP/Machine Learning
- **NLTK**: Tokenization, Lemmatization, Preprocessing
- **Scikit-learn**: TF-IDF Vectorization, Cosine Similarity

## 🚀 Getting Started

### ✅ Prerequisites
- Python 3.x
- MySQL server
- pip (Python package manager)

### 📦 Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/e-notes-management.git
   cd e-notes-management
2. **Install Dependencies**

bash
Copy
Edit
pip install -r requirements.txt

3. **Database Setup**

Create a MySQL database (e.g., enotes_db)

Import the provided schema.sql file

Update config.py with your DB credentials

4. **Run the Application**

bash
Copy
Edit
python app.py
Access the app at http://localhost:5000

**Folder Structure**
e-notes-management/
├── app.py
├── templates/
│   ├── login.html
│   ├── upload.html
│   ├── search.html
│   └── results.html
├── static/
│   ├── css/
│   └── uploads/
├── config.py
├── models.py
├── nlp_engine.py
├── requirements.txt
└── schema.sql
