import psycopg2
import psycopg2.extras
import csv
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, jsonify, make_response, abort
from functools import wraps
import os
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', secrets.token_hex(32))
# Configure session for iframe/preview environment
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allows cookies in iframe redirects
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session

# Disable caching to ensure CSS/JS updates are loaded immediately
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

DATABASE_URL = os.environ.get('DATABASE_URL')
ADMIN_PIN = os.environ.get('ADMIN_PIN', '2025')

def generate_csrf_token():
    """Generate CSRF token for session"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def verify_csrf_token(token):
    """Verify CSRF token matches session"""
    return token and session.get('csrf_token') == token

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_csrf_token():
    """Make CSRF token available to all templates"""
    return dict(csrf_token=generate_csrf_token)

def get_db():
    """Get database connection"""
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def init_db():
    """Initialize database with single quiz_records table"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Drop old tables if they exist
    cursor.execute('''
        DROP TABLE IF EXISTS responses CASCADE;
        DROP TABLE IF EXISTS attempts CASCADE;
        DROP TABLE IF EXISTS participants CASCADE;
        DROP TABLE IF EXISTS questions CASCADE;
        DROP TABLE IF EXISTS quiz_records CASCADE;
    ''')
    
    # Create single table with all quiz data
    cursor.execute('''
        CREATE TABLE quiz_records (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            percent REAL NOT NULL,
            weighted_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Database initialized successfully!")

def capitalize_first_letter(text):
    """Capitalize the first letter of a string if it's not already capitalized"""
    if not text:
        return text
    return text[0].upper() + text[1:] if text else text

def load_questions_from_csv(language='en'):
    """Load questions from CSV file based on language (not stored in database)"""
    import re
    
    # Use different CSV files based on language
    if language == 'bn':
        csv_path = 'questions_bangla.csv'
        # Fallback to English if Bangla CSV doesn't exist
        if not os.path.exists(csv_path):
            print(f"Bangla CSV not found, falling back to English")
            csv_path = 'questions_english.csv'
    else:
        csv_path = 'questions_english.csv'
    
    questions = []
    
    # Weight mapping: Easy=0.5, Medium=0.75, Hard=1.5 (total 10 marks for 2+4+4 distribution)
    # Handle both uppercase and lowercase difficulty values
    weight_mapping = {
        'Easy': 0.5, 'easy': 0.5,
        'Medium': 0.75, 'medium': 0.75,
        'Hard': 1.5, 'hard': 1.5
    }
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Keep the actual question text with programme names
            question_text = row['question']
            
            # Clean up extra spaces and punctuation
            question_text = re.sub(r'\s+', ' ', question_text).strip()
            question_text = re.sub(r'\s+([?.!,])', r'\1', question_text)
            
            # Capitalize first letter
            question_text = capitalize_first_letter(question_text)
            
            # Capitalize options
            option_a = capitalize_first_letter(row['option_A'].strip())
            option_b = capitalize_first_letter(row['option_B'].strip())
            option_c = capitalize_first_letter(row['option_C'].strip())
            option_d = capitalize_first_letter(row['option_D'].strip())
            
            # Apply custom weight based on difficulty level
            difficulty = row['difficulty']
            custom_weight = weight_mapping.get(difficulty, 1.0)
            
            questions.append({
                'programme_code': row['programme_code'],
                'programme_name': row['programme_name'],
                'difficulty': difficulty,
                'weight': custom_weight,  # Use custom weight instead of CSV weight
                'question': question_text,
                'option_A': option_a,
                'option_B': option_b,
                'option_C': option_c,
                'option_D': option_d,
                'answer': row['answer_letter'],
                'answer_text': row['answer_text']
            })
    
    return questions

def select_weighted_random_questions(num_questions=10, language='en'):
    """Select random questions with difficulty-based weighting
    
    Target distribution for 10 questions:
    - Easy (weight 0.5): 2 questions (20%) = 1.0 marks
    - Medium (weight 0.75): 4 questions (40%) = 3.0 marks
    - Hard (weight 1.5): 4 questions (40%) = 6.0 marks
    Total: 10.0 marks
    """
    import random
    
    # Load all questions from CSV based on language
    all_questions = load_questions_from_csv(language)
    
    # Target distribution
    target_easy = 2
    target_medium = 4
    target_hard = 4
    
    # Separate questions by difficulty (handle both uppercase and lowercase)
    easy_questions = [q for q in all_questions if q['difficulty'].lower() == 'easy']
    medium_questions = [q for q in all_questions if q['difficulty'].lower() == 'medium']
    hard_questions = [q for q in all_questions if q['difficulty'].lower() == 'hard']
    
    # Select random questions from each difficulty
    selected_questions = []
    selected_questions.extend(random.sample(easy_questions, min(target_easy, len(easy_questions))))
    selected_questions.extend(random.sample(medium_questions, min(target_medium, len(medium_questions))))
    selected_questions.extend(random.sample(hard_questions, min(target_hard, len(hard_questions))))
    
    # Shuffle the selected questions so difficulty levels are mixed
    random.shuffle(selected_questions)
    
    # Add an index to each question for tracking
    for idx, q in enumerate(selected_questions):
        q['idx'] = idx
    
    # Debug: Print distribution summary
    easy_count = len([q for q in selected_questions if q['difficulty'] == 'Easy'])
    medium_count = len([q for q in selected_questions if q['difficulty'] == 'Medium'])
    hard_count = len([q for q in selected_questions if q['difficulty'] == 'Hard'])
    print(f"Question distribution: Easy={easy_count}, Medium={medium_count}, Hard={hard_count}")
    
    return selected_questions

@app.route('/')
def index():
    """Landing page with sign-in form"""
    session.clear()
    return render_template('index.html')

def count_player_attempts(email=None):
    """Count how many times a player has attempted the quiz"""
    conn = get_db()
    cursor = conn.cursor()
    
    if email:
        cursor.execute('SELECT COUNT(*) as count FROM quiz_records WHERE email = %s', (email,))
    else:
        cursor.close()
        conn.close()
        return 0
    
    result = cursor.fetchone()
    count = result['count'] if result else 0
    
    cursor.close()
    conn.close()
    return count

MAX_ATTEMPTS = 3

@app.route('/start', methods=['POST'])
def start():
    """Handle participant registration and start quiz"""
    form_type = request.form.get('form_type', '').strip()
    language = request.form.get('language', 'en').strip()
    
    # Store language preference in session
    session['language'] = language
    
    if form_type == 'register':
        # Registration: name and email required
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        
        # Validate required fields
        if not all([name, email]):
            print(f"Validation failed - name:{name}, email:{email}")
            return redirect('/')
        
        # Check attempt limit for email users
        attempts = count_player_attempts(email=email)
        if attempts >= MAX_ATTEMPTS:
            error_msg = 'আপনি ইতিমধ্যে ৩ বার খেলেছেন' if language == 'bn' else 'You have already played 3 times'
            return render_template('index.html', error=error_msg, error_lang=language)
        
    else:
        # Invalid form type
        return redirect('/')
    
    print(f"Starting quiz for: name={name}, email={email}, language={language}")
    
    # Get 10 random questions with weighted distribution
    questions = select_weighted_random_questions(10, language)
    
    # Format for template
    for q in questions:
        q['options'] = [q['option_A'], q['option_B'], q['option_C'], q['option_D']]
    
    print(f"Selected {len(questions)} questions for quiz")
    
    # Render quiz page directly (pass participant data through form)
    return render_template('quiz.html', 
                         items=questions, 
                         participant_name=name,
                         participant_email=email)

@app.route('/submit', methods=['POST'])
def submit():
    """Grade quiz and save results to single database table"""
    # Get participant data from form (not session to avoid cookie issues)
    name = request.form.get('participant_name', '').strip() or None
    email = request.form.get('participant_email', '').strip().lower() or None
    
    # Load all questions to match against submissions
    all_questions = load_questions_from_csv()
    
    # Grade responses with weighted scoring
    weighted_score = 0.0
    total_questions = 10
    
    # Check each submitted answer against the CSV questions
    for i in range(total_questions):
        question_text = request.form.get(f'question_{i}', '').strip()
        selected = request.form.get(f'answer_{i}', '').strip()
        
        # Find matching question in CSV
        for q in all_questions:
            if q['question'] == question_text:
                is_correct = (selected == q['answer'])
                if is_correct:
                    weighted_score += q['weight']
                break
    
    # Calculate percentage based on weighted score
    # Total possible weighted marks: 2 Easy (0.5×2=1.0) + 4 Medium (0.75×4=3.0) + 4 Hard (1.5×4=6.0) = 10.0
    total_weighted_marks = 10.0
    weighted_percent = (weighted_score / total_weighted_marks) * 100
    
    # Save single record to database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO quiz_records (name, email, percent, weighted_score) VALUES (%s, %s, %s, %s)',
        (name, email, weighted_percent, weighted_score)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Quiz saved: name={name}, email={email}, weighted_score={weighted_score:.1f}/10.0, weighted_percent={weighted_percent:.2f}%")
    
    # Render result page directly
    display_name = name if name else "Participant"
    
    data = {
        'name': display_name,
        'weighted_score': round(weighted_score, 1),
        'total_weighted': total_weighted_marks,
        'percent': round(weighted_percent, 2),
        'weighted_percent': round(weighted_percent, 2),
        'is_winner': 1 if weighted_score >= 7.0 else 0  # For result page display only
    }
    
    return render_template('result.html', data=data)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not verify_csrf_token(csrf_token):
            abort(403)
        
        pin = request.form.get('admin_pin', '')
        if pin == ADMIN_PIN:
            session['admin_authenticated'] = True
            return redirect('/admin')
        else:
            return render_template('admin_login.html', error='Invalid PIN')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    return redirect('/')

@app.route('/admin')
@admin_required
def admin():
    """Admin dashboard with quiz records"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all quiz records
    cursor.execute('SELECT * FROM quiz_records ORDER BY created_at DESC')
    records = cursor.fetchall()
    
    # Get statistics
    total_attempts = len(records)
    # Count winners (weighted_score >= 7.0)
    total_winners = sum(1 for r in records if r.get('weighted_score', 0) >= 7.0)
    cursor.execute('SELECT AVG(weighted_score) FROM quiz_records')
    avg_weighted_row = cursor.fetchone()
    avg_weighted = avg_weighted_row['avg'] if avg_weighted_row and avg_weighted_row['avg'] else 0
    
    cursor.close()
    conn.close()
    
    stats = {
        'total_attempts': total_attempts,
        'total_winners': total_winners,
        'avg_weighted_score': round(float(avg_weighted), 1)
    }
    
    return render_template('admin.html', attempts=records, stats=stats)


@app.route('/admin/export')
@admin_required
def export_csv():
    """Export all quiz records to CSV"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, email, weighted_score, percent, created_at
        FROM quiz_records
        ORDER BY created_at DESC
    ''')
    records = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Create CSV
    output = "Name,Email,Weighted Score,Percentage,Date\n"
    for r in records:
        output += f'"{r["name"]}",{r["email"]},{r["weighted_score"]:.1f},{r["percent"]:.2f}%,{r["created_at"]}\n'
    
    response = make_response(output)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=quiz_records.csv'
    return response

@app.route('/leaderboard')
def leaderboard():
    """Leaderboard page showing top scores"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get top 10 scores (best score per player, identified by email)
    # For players with multiple attempts, show their best score
    # Calculate percentage directly from score: score/10 * 100 = score * 10
    cursor.execute('''
        SELECT 
            COALESCE(name, 'Participant') as display_name,
            email,
            MAX(COALESCE(weighted_score, 0)) as best_score,
            MAX(COALESCE(weighted_score, 0)) * 10 as best_percent
        FROM quiz_records 
        GROUP BY COALESCE(name, 'Participant'), email
        ORDER BY best_score DESC NULLS LAST
        LIMIT 10
    ''')
    
    top_players = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Get language from session for translations
    language = session.get('language', 'en')
    
    return render_template('leaderboard.html', players=top_players, lang=language)

@app.route('/manifest.json')
def manifest():
    """PWA manifest"""
    return jsonify({
        "name": "BRAC Innovation Exhibition Quiz",
        "short_name": "BRAC Quiz",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#e31837",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    })

# Initialize database on startup (check if tables exist)
def check_database():
    """Check if database tables exist, create them if not"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'quiz_records')")
        exists = cursor.fetchone()['exists']
        cursor.close()
        conn.close()
        if not exists:
            init_db()
    except Exception as e:
        print(f"Database check failed: {e}. Attempting to initialize...")
        init_db()

check_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
