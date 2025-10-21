import sqlite3
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

DATABASE = 'quiz.db'
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
    """Get database connection with WAL mode"""
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    """Initialize database schema and import questions"""
    conn = get_db()
    
    # Create tables
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            programme_code TEXT NOT NULL,
            programme_name TEXT NOT NULL,
            question TEXT NOT NULL,
            option_A TEXT NOT NULL,
            option_B TEXT NOT NULL,
            option_C TEXT NOT NULL,
            option_D TEXT NOT NULL,
            answer TEXT NOT NULL,
            answer_text TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS rotation_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            programme_code TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            times_used INTEGER DEFAULT 0,
            FOREIGN KEY (question_id) REFERENCES questions(id),
            UNIQUE(programme_code, position)
        );
        
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pin TEXT NOT NULL,
            phone TEXT NOT NULL,
            consent INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER DEFAULT 22,
            percent REAL NOT NULL,
            is_winner INTEGER DEFAULT 0,
            gift_given INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (participant_id) REFERENCES participants(id)
        );
        
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            FOREIGN KEY (attempt_id) REFERENCES attempts(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_rotation_prog ON rotation_queue(programme_code);
        CREATE INDEX IF NOT EXISTS idx_attempts_winner ON attempts(is_winner);
    ''')
    
    # Check if questions already loaded
    count = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
    if count == 0:
        print("Importing questions from CSV...")
        import_questions()
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def import_questions():
    """Import questions from CSV file"""
    conn = get_db()
    csv_path = 'attached_assets/Exhibition Questions Demo - brac_exhibition_quiz_220_questions_1761025867146.csv'
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute('''
                INSERT INTO questions (programme_code, programme_name, question, 
                                      option_A, option_B, option_C, option_D, answer, answer_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row['programme_code'], row['programme_name'], row['question'],
                  row['option_A'], row['option_B'], row['option_C'], row['option_D'],
                  row['answer'], row['answer_text']))
    
    conn.commit()
    
    # Initialize rotation queues
    initialize_rotation_queues()
    print(f"Imported questions and initialized rotation queues")

def initialize_rotation_queues():
    """Initialize rotation queues for each programme"""
    conn = get_db()
    
    # Get all programmes
    programmes = conn.execute('SELECT DISTINCT programme_code FROM questions ORDER BY programme_code').fetchall()
    
    for prog in programmes:
        prog_code = prog['programme_code']
        
        # Get all question IDs for this programme
        questions = conn.execute(
            'SELECT id FROM questions WHERE programme_code = ? ORDER BY RANDOM()',
            (prog_code,)
        ).fetchall()
        
        # Insert into rotation queue
        for idx, q in enumerate(questions):
            conn.execute('''
                INSERT OR IGNORE INTO rotation_queue (programme_code, question_id, position, times_used)
                VALUES (?, ?, ?, 0)
            ''', (prog_code, q['id'], idx))
    
    conn.commit()

def get_next_question_for_programme(programme_code):
    """Get next question from rotation queue (least used)"""
    conn = get_db()
    
    # Find the question with minimum times_used, prefer lower position on tie
    result = conn.execute('''
        SELECT question_id, times_used, position
        FROM rotation_queue
        WHERE programme_code = ?
        ORDER BY times_used ASC, position ASC
        LIMIT 1
    ''', (programme_code,)).fetchone()
    
    if result:
        question_id = result['question_id']
        # Increment usage counter
        conn.execute('''
            UPDATE rotation_queue 
            SET times_used = times_used + 1
            WHERE programme_code = ? AND question_id = ?
        ''', (programme_code, question_id))
        conn.commit()
        
        # Return the full question
        question = conn.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()
        return dict(question)
    
    return None

@app.route('/')
def index():
    """Landing page with sign-in form"""
    session.clear()
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    """Handle participant sign-in and start quiz"""
    name = request.form.get('name', '').strip()
    pin = request.form.get('pin', '').strip()
    phone = request.form.get('phone', '').strip()
    
    # Validate all required fields and PIN format (exactly 6 digits)
    if not all([name, pin, phone]) or not (pin.isdigit() and len(pin) == 6):
        print(f"Validation failed - name:{name}, pin:{pin}, phone:{phone}")
        return redirect('/')
    
    # Create participant record
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO participants (name, pin, phone, consent) VALUES (?, ?, ?, ?)',
        (name, pin, phone, 1)
    )
    participant_id = cursor.lastrowid
    conn.commit()
    
    # Store in session
    session['participant_id'] = participant_id
    session['name'] = name
    session.modified = True  # Force session save
    
    print(f"Session set: participant_id={participant_id}, name={name}")
    
    return redirect('/quiz')

@app.route('/quiz')
def quiz():
    """Display 22-question quiz (one per programme)"""
    print(f"Quiz route - session contents: {dict(session)}")
    if 'participant_id' not in session:
        print("No participant_id in session - redirecting to home")
        return redirect('/')
    
    conn = get_db()
    
    # Get all programmes (should be 22)
    programmes = conn.execute(
        'SELECT DISTINCT programme_code, programme_name FROM questions ORDER BY programme_code'
    ).fetchall()
    
    # Get one question per programme using rotation queue
    questions = []
    for prog in programmes:
        q = get_next_question_for_programme(prog['programme_code'])
        if q:
            # Format for template
            q['options'] = [q['option_A'], q['option_B'], q['option_C'], q['option_D']]
            questions.append(q)
    
    # Store question IDs in session for grading
    session['question_ids'] = [q['id'] for q in questions]
    
    return render_template('quiz.html', items=questions)

@app.route('/submit', methods=['POST'])
def submit():
    """Grade quiz and save results"""
    if 'participant_id' not in session or 'question_ids' not in session:
        return redirect('/')
    
    participant_id = session['participant_id']
    question_ids = session['question_ids']
    
    conn = get_db()
    
    # Create attempt record
    cursor = conn.execute(
        'INSERT INTO attempts (participant_id, score, total_questions, percent, is_winner) VALUES (?, 0, 22, 0, 0)',
        (participant_id,)
    )
    attempt_id = cursor.lastrowid
    
    # Grade responses
    score = 0
    for qid in question_ids:
        selected = request.form.get(str(qid), '').strip()
        
        # Get correct answer
        question = conn.execute('SELECT answer FROM questions WHERE id = ?', (qid,)).fetchone()
        is_correct = 1 if (question and selected == question['answer']) else 0
        score += is_correct
        
        # Save response
        conn.execute(
            'INSERT INTO responses (attempt_id, question_id, selected_answer, is_correct) VALUES (?, ?, ?, ?)',
            (attempt_id, qid, selected, is_correct)
        )
    
    # Calculate percentage and winner status
    percent = (score / 22) * 100
    is_winner = 1 if percent >= 70 else 0
    
    # Update attempt
    conn.execute(
        'UPDATE attempts SET score = ?, percent = ?, is_winner = ? WHERE id = ?',
        (score, percent, is_winner, attempt_id)
    )
    
    conn.commit()
    
    # Store attempt_id for result page
    session['attempt_id'] = attempt_id
    
    return redirect('/result')

@app.route('/result')
def result():
    """Display quiz results"""
    if 'attempt_id' not in session:
        return redirect('/')
    
    attempt_id = session['attempt_id']
    conn = get_db()
    
    attempt = conn.execute(
        'SELECT * FROM attempts WHERE id = ?', (attempt_id,)
    ).fetchone()
    
    if not attempt:
        return redirect('/')
    
    data = {
        'score': attempt['score'],
        'percent': attempt['percent'],
        'is_winner': attempt['is_winner']
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
    """Admin dashboard with winner list"""
    conn = get_db()
    
    # Get all attempts with participant info
    attempts = conn.execute('''
        SELECT a.*, p.name, p.pin, p.phone
        FROM attempts a
        JOIN participants p ON a.participant_id = p.id
        ORDER BY a.created_at DESC
    ''').fetchall()
    
    # Get statistics
    total_attempts = len(attempts)
    total_winners = conn.execute('SELECT COUNT(*) FROM attempts WHERE is_winner = 1').fetchone()[0]
    avg_score = conn.execute('SELECT AVG(score) FROM attempts').fetchone()[0] or 0
    
    stats = {
        'total_attempts': total_attempts,
        'total_winners': total_winners,
        'avg_score': round(avg_score, 1)
    }
    
    return render_template('admin.html', attempts=attempts, stats=stats)

@app.route('/admin/mark_gift/<int:attempt_id>', methods=['POST'])
@admin_required
def mark_gift(attempt_id):
    """Mark gift as given"""
    csrf_token = request.form.get('csrf_token')
    if not verify_csrf_token(csrf_token):
        abort(403)
    
    conn = get_db()
    conn.execute('UPDATE attempts SET gift_given = 1 WHERE id = ?', (attempt_id,))
    conn.commit()
    return redirect('/admin')

@app.route('/admin/export')
@admin_required
def export_csv():
    """Export winners to CSV"""
    conn = get_db()
    
    winners = conn.execute('''
        SELECT p.name, p.pin, p.phone, a.score, a.percent, a.created_at, a.gift_given
        FROM attempts a
        JOIN participants p ON a.participant_id = p.id
        WHERE a.is_winner = 1
        ORDER BY a.created_at DESC
    ''').fetchall()
    
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
        "name": "BRAC Exhibition Quiz",
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

if __name__ == '__main__':
    # Initialize database on first run
    if not os.path.exists(DATABASE):
        init_db()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
