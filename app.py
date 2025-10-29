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
            name TEXT NOT NULL,
            pin TEXT NOT NULL,
            phone TEXT NOT NULL,
            score INTEGER NOT NULL,
            percent REAL NOT NULL,
            is_winner INTEGER DEFAULT 0,
            gift_given INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    cursor.execute('CREATE INDEX idx_winner ON quiz_records(is_winner);')
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Database initialized successfully!")

def capitalize_first_letter(text):
    """Capitalize the first letter of a string if it's not already capitalized"""
    if not text:
        return text
    return text[0].upper() + text[1:] if text else text

def load_questions_from_csv():
    """Load questions from CSV file (not stored in database)"""
    import re
    csv_path = 'attached_assets/Untitled spreadsheet - QuestionBank_1761118191656.csv'
    questions = []
    
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
            
            questions.append({
                'programme_code': row['programme_code'],
                'programme_name': row['programme_name'],
                'difficulty': row['difficulty'],
                'weight': float(row['weight']),
                'question': question_text,
                'option_A': option_a,
                'option_B': option_b,
                'option_C': option_c,
                'option_D': option_d,
                'answer': row['answer_letter'],
                'answer_text': row['answer_text']
            })
    
    return questions

def select_weighted_random_questions(num_questions=10):
    """Select random questions with difficulty-based weighting
    
    Target distribution for 10 questions:
    - Easy (weight 1.0): 3 questions (30%)
    - Medium (weight 1.5): 3 questions (30%)
    - Hard (weight 2.0): 4 questions (40%)
    """
    import random
    
    # Load all questions from CSV
    all_questions = load_questions_from_csv()
    
    # Target distribution
    target_easy = 3
    target_medium = 3
    target_hard = 4
    
    # Separate questions by difficulty
    easy_questions = [q for q in all_questions if q['difficulty'] == 'Easy']
    medium_questions = [q for q in all_questions if q['difficulty'] == 'Medium']
    hard_questions = [q for q in all_questions if q['difficulty'] == 'Hard']
    
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
    
    return selected_questions

@app.route('/')
def index():
    """Landing page with sign-in form"""
    session.clear()
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    """Handle participant sign-in and start quiz"""
    form_type = request.form.get('form_type', '').strip()
    
    if form_type == 'have_pin':
        # Have PIN: only PIN field required
        pin = request.form.get('pin', '').strip()
        
        # Validate PIN format (exactly 6 digits)
        if not (pin.isdigit() and len(pin) == 6):
            print(f"Validation failed - invalid PIN: {pin}")
            return redirect('/')
        
        # Generate placeholder name and phone for PIN users
        name = f"Player-{pin}"
        phone = f"PIN{pin}"
        
    elif form_type == 'no_pin':
        # Don't Have PIN: name and phone required
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validate required fields
        if not all([name, phone]):
            print(f"Validation failed - name:{name}, phone:{phone}")
            return redirect('/')
        
        # Generate random 6-digit PIN for users without PIN
        import random
        pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
    else:
        # Invalid form type
        return redirect('/')
    
    print(f"Starting quiz for: name={name}, pin={pin}, form_type={form_type}")
    
    # Get 10 random questions with weighted distribution
    questions = select_weighted_random_questions(10)
    
    # Format for template
    for q in questions:
        q['options'] = [q['option_A'], q['option_B'], q['option_C'], q['option_D']]
    
    print(f"Selected {len(questions)} questions for quiz")
    
    # Render quiz page directly (pass participant data through form)
    return render_template('quiz.html', 
                         items=questions, 
                         participant_name=name,
                         participant_pin=pin,
                         participant_phone=phone)

@app.route('/submit', methods=['POST'])
def submit():
    """Grade quiz and save results to single database table"""
    # Get participant data from form (not session to avoid cookie issues)
    name = request.form.get('participant_name', 'Unknown').strip()
    pin = request.form.get('participant_pin', '000000').strip()
    phone = request.form.get('participant_phone', 'N/A').strip()
    
    # Load all questions to match against submissions
    all_questions = load_questions_from_csv()
    
    # Grade responses with weighted scoring
    score = 0
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
                    score += 1
                    weighted_score += q['weight']
                break
    
    # Calculate percentage and winner status (70% = 7/10)
    percent = (score / total_questions) * 100
    is_winner = 1 if score >= 7 else 0
    
    # Save single record to database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO quiz_records (name, pin, phone, score, percent, is_winner) VALUES (%s, %s, %s, %s, %s, %s)',
        (name, pin, phone, score, percent, is_winner)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Quiz saved: name={name}, score={score}/{total_questions}, percent={percent:.2f}%, winner={is_winner}")
    
    # Calculate total possible weighted marks (3 Easy + 3 Medium + 4 Hard)
    # Easy (1.0) × 3 = 3.0, Medium (1.5) × 3 = 4.5, Hard (2.0) × 4 = 8.0
    total_weighted_marks = 15.5
    
    # Render result page directly
    data = {
        'name': name,
        'score': score,
        'total': total_questions,
        'weighted_score': round(weighted_score, 1),
        'total_weighted': total_weighted_marks,
        'percent': round(percent, 2),
        'is_winner': is_winner
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
    cursor.execute('SELECT COUNT(*) FROM quiz_records WHERE is_winner = 1')
    total_winners = cursor.fetchone()['count']
    cursor.execute('SELECT AVG(score) FROM quiz_records')
    avg_score_row = cursor.fetchone()
    avg_score = avg_score_row['avg'] if avg_score_row and avg_score_row['avg'] else 0
    
    cursor.close()
    conn.close()
    
    stats = {
        'total_attempts': total_attempts,
        'total_winners': total_winners,
        'avg_score': round(float(avg_score), 1)
    }
    
    return render_template('admin.html', attempts=records, stats=stats)

@app.route('/admin/mark_gift/<int:record_id>', methods=['POST'])
@admin_required
def mark_gift(record_id):
    """Mark gift as given"""
    csrf_token = request.form.get('csrf_token')
    if not verify_csrf_token(csrf_token):
        abort(403)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE quiz_records SET gift_given = 1 WHERE id = %s', (record_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin')

@app.route('/admin/export')
@admin_required
def export_csv():
    """Export winners to CSV"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, pin, phone, score, percent, created_at, gift_given
        FROM quiz_records
        WHERE is_winner = 1
        ORDER BY created_at DESC
    ''')
    winners = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Create CSV
    output = "Name,PIN,Phone,Score,Percentage,Date,Gift Given\n"
    for w in winners:
        # Mask phone number (show only last 4 digits)
        masked_phone = '****' + w['phone'][-4:] if len(w['phone']) >= 4 else w['phone']
        gift_status = 'Yes' if w['gift_given'] else 'No'
        output += f'"{w["name"]}",{w["pin"]},{masked_phone},{w["score"]},{w["percent"]:.2f}%,{w["created_at"]},{gift_status}\n'
    
    response = make_response(output)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=winners.csv'
    return response

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
