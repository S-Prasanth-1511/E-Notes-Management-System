from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import os

from models import db, User, Note, SearchFeedback

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np
import nltk
import string
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet, stopwords
from nltk import pos_tag

import re
from markupsafe import Markup, escape


def highlight_text(text, keywords):
    escaped_text = escape(text)
    keywords = sorted(set(keywords), key=len, reverse=True)
    pattern = re.compile(r'(' + '|'.join(re.escape(k) for k in keywords) + r')', re.IGNORECASE)
    highlighted = pattern.sub(r'<span class="highlight">\1</span>', escaped_text)
    return Markup(highlighted)

# NLTK setup
nltk.data.path.append('./nltk_data')
for resource in ['punkt', 'wordnet', 'omw-1.4', 'averaged_perceptron_tagger', 'stopwords']:
    try:
        nltk.data.find(resource)
    except LookupError:
        nltk.download(resource, download_dir='./nltk_data')

lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'docx'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
@login_required
def index():
    notes = Note.query.all()
    return render_template('home.html', notes=notes)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and (user.password==password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        content = request.form['content']
        file = request.files['file']

        filename = None
        filetype = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filetype = file.content_type
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_note = Note(title=title, category=category, content=content,
                        filename=filename, filetype=filetype, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()

        flash('Note uploaded successfully!')
        return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/note/<int:note_id>')
@login_required
def view_note(note_id):
    note = Note.query.get_or_404(note_id)
    query = request.args.get('q')
    return render_template('view_note.html', note=note, query=query)

# --- Text Preprocessing ---

def get_wordnet_pos(tag):
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    return wordnet.NOUN

def preprocess_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in stopwords.words('english')]
    pos_tags = pos_tag(tokens)
    lemmatized = [lemmatizer.lemmatize(token, get_wordnet_pos(tag)) for token, tag in pos_tags]
    return ' '.join(lemmatized)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    search_query = request.args.get('q')
    results = []
    query_terms = []

    def expand_query_terms(terms):
        expanded = set()
        for term in terms:
            expanded.add(term)
            for syn in wordnet.synsets(term):
                for lemma in syn.lemmas():
                    expanded.add(lemma.name().replace('_', ' ').lower())
        return list(expanded)

    def highlight_text(text, terms):
        # Escape terms for regex, join as OR group
        pattern = re.compile(r'(' + '|'.join(re.escape(term) for term in terms) + r')', re.I)
        # Replace matches with span highlight tag
        highlighted = pattern.sub(r'<mark>\1</mark>', text)
        return Markup(highlighted)  # mark safe for Jinja2

    if search_query:
        notes = Note.query.all()

        processed_query = preprocess_text(search_query)
        raw_terms = search_query.lower().split()
        query_terms = expand_query_terms(raw_terms)

        corpus = [preprocess_text(note.title + " " + note.content) for note in notes]

        if corpus:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(corpus + [processed_query])
            similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

            for i, note in enumerate(notes):
                note.similarity_score = similarities[i]
                note_words = (note.title + " " + note.content).lower().split()

                for qterm in query_terms:
                    if any(word.startswith(qterm) for word in note_words):
                        note.similarity_score += 0.2
                    if note.title.lower().startswith(qterm):
                        note.similarity_score += 0.3

            sorted_notes = sorted(notes, key=lambda x: x.similarity_score, reverse=True)
            results = [note for note in sorted_notes if note.similarity_score > 0]

            # Add highlight fields for rendering
            for note in results:
                note.highlighted_content = highlight_text(note.content, query_terms)
                note.highlighted_title = highlight_text(note.title, query_terms)
        else:
            results = []

    # Feedback handling remains the same
    if request.method == 'POST':
        feedback_text = request.form.get('feedback')
        if feedback_text:
            existing = SearchFeedback.query.filter_by(user_id=current_user.id, query=search_query).first()
            if existing:
                existing.feedback = feedback_text
            else:
                db.session.add(SearchFeedback(user_id=current_user.id, query=search_query, feedback=feedback_text))
            db.session.commit()
            flash('Feedback submitted!')

    feedback_entry = SearchFeedback.query.filter_by(user_id=current_user.id, query=search_query).first()
    return render_template('search.html', notes=results, query=search_query, feedback=feedback_entry)


@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.get_json()
    query = data.get('query')
    feedback_text = data.get('feedback')

    if not query or not feedback_text:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    existing = SearchFeedback.query.filter_by(user_id=current_user.id, query=query).first()
    if existing:
        return jsonify({'status': 'error', 'message': 'Feedback already submitted'}), 400

    feedback_entry = SearchFeedback(user_id=current_user.id, query=query, feedback=feedback_text)
    db.session.add(feedback_entry)
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route('/bookmarks')
@login_required
def bookmarks():
    return render_template('bookmarks.html')

@app.route('/get_note_preview')
def get_note_preview():
    note_id = request.args.get('note_id')
    note = Note.query.get(note_id)
    if note:
        return jsonify({'content': note.content})
    return jsonify({'content': 'Note not found'}), 404

# Create tables if not exist
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
