from flask import Flask, request, g, render_template, session, redirect, url_for
import logging
import json
from datetime import datetime
import socket
import os
import sqlite3
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure rotating file handler
file_handler = RotatingFileHandler(
    'logs/app.log', maxBytes=1024 * 1024 * 5, backupCount=3)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'))
logger.addHandler(file_handler)

# SQLite setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'monitor.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            method TEXT,
            path TEXT,
            status_code INTEGER,
            ip TEXT,
            user_agent TEXT,
            referer TEXT,
            headers_json TEXT,
            query_json TEXT,
            body TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ip TEXT,
            user_agent TEXT,
            answers_json TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


@app.before_request
def comprehensive_logging():
    """Capture comprehensive request information safely"""
    g.start_time = datetime.now()

    # Get ALL headers safely
    all_headers = dict(request.headers)

    # Enhanced request info with safe attribute access
    request_info = {
        'timestamp': g.start_time.isoformat(),

        # Request basics
        'method': request.method,
        'url': request.url,
        'full_path': request.full_path,
        'path': request.path,
        'query_params': dict(request.args),
        'form_data': dict(request.form) if request.form else None,

        # All headers
        'headers': all_headers,
        'header_count': len(all_headers),

        # Network info
        'remote_addr': request.remote_addr,
        'client_ip': get_client_ip(),
        'server_name': request.server[0] if request.server else None,
        'server_port': request.server[1] if request.server else None,
        'scheme': request.scheme,
        'is_secure': request.is_secure,

        # Content info (safe access)
        'content_type': getattr(request, 'content_type', None),
        'content_length': getattr(request, 'content_length', None),
        'mimetype': getattr(request, 'mimetype', None),
        'is_json': getattr(request, 'is_json', False),

        # Browser/Client fingerprinting
        'user_agent_info': parse_user_agent(),

        # Environment info
        'environ_keys': list(request.environ.keys()),
        'wsgi_version': request.environ.get('wsgi.version'),
        'server_software': request.environ.get('SERVER_SOFTWARE'),

        # Additional Flask properties (safe access)
        'base_url': getattr(request, 'base_url', None),
        'url_root': getattr(request, 'url_root', None),
        'blueprint': getattr(request, 'blueprint', None),
    }

    # Add JSON body if present and safe to access
    try:
        if hasattr(request, 'is_json') and request.is_json:
            request_info['json_body'] = request.get_json()
    except Exception as e:
        request_info['json_body'] = f'Could not parse JSON: {str(e)}'

    # Add specific WSGI environ variables that might be interesting
    interesting_environ = [
        'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'HTTP_X_FORWARDED_PROTO',
        'HTTP_CF_RAY', 'HTTP_CF_CONNECTING_IP', 'HTTP_CF_IPCOUNTRY',
        'HTTP_CF_VISITOR', 'HTTP_CF_RAY', 'HTTP_CF_CONNECTING_IP',
        'REMOTE_HOST', 'REMOTE_USER', 'AUTH_TYPE',
        'REQUEST_METHOD', 'SCRIPT_NAME', 'PATH_INFO',
        'QUERY_STRING', 'CONTENT_TYPE', 'CONTENT_LENGTH',
        'SERVER_NAME', 'SERVER_PORT', 'SERVER_PROTOCOL',
        'HTTP_HOST', 'HTTP_USER_AGENT', 'HTTP_REFERER',
        'HTTP_COOKIE', 'HTTP_AUTHORIZATION', 'HTTP_ACCEPT',
        'HTTP_ACCEPT_LANGUAGE', 'HTTP_ACCEPT_ENCODING',
        'HTTP_CONNECTION', 'HTTP_CACHE_CONTROL', 'HTTP_PRAGMA',
        'HTTP_UPGRADE_INSECURE_REQUESTS', 'HTTP_SEC_FETCH_DEST',
        'HTTP_SEC_FETCH_MODE', 'HTTP_SEC_FETCH_SITE', 'HTTP_SEC_FETCH_USER',
        'HTTP_SEC_CH_UA', 'HTTP_SEC_CH_UA_MOBILE', 'HTTP_SEC_CH_UA_PLATFORM',
        'HTTP_DNT', 'HTTP_ACCEPT_DATETIME', 'HTTP_IF_MODIFIED_SINCE',
        'HTTP_IF_NONE_MATCH', 'HTTP_IF_RANGE', 'HTTP_RANGE',
        'HTTP_X_REQUESTED_WITH', 'HTTP_X_CSRF_TOKEN', 'HTTP_X_API_KEY',
        'HTTP_X_AUTH_TOKEN', 'HTTP_X_SESSION_ID', 'HTTP_X_REQUEST_ID',
        'HTTP_X_CORRELATION_ID', 'HTTP_X_TRACE_ID', 'HTTP_X_SPAN_ID',
        'HTTP_X_FORWARDED_HOST', 'HTTP_X_FORWARDED_PORT', 'HTTP_X_FORWARDED_SERVER',
        'HTTP_X_ORIGINAL_URL', 'HTTP_X_REWRITE_URL', 'HTTP_X_HTTP_METHOD_OVERRIDE',
        'HTTP_X_HTTP_VERSION', 'HTTP_X_HTTPS', 'HTTP_X_SCHEME',
        'HTTP_X_FORWARDED_SSL', 'HTTP_X_FORWARDED_PROTO', 'HTTP_X_FORWARDED_FOR',
        'HTTP_X_CLUSTER_CLIENT_IP', 'HTTP_X_CLIENT_IP', 'HTTP_X_REAL_IP',
        'HTTP_X_ORIGINAL_FORWARDED_FOR', 'HTTP_X_FORWARDED', 'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED_HOST', 'HTTP_X_FORWARDED_SERVER',
        'HTTP_X_FORWARDED_PORT', 'HTTP_X_ORIGINAL_URL', 'HTTP_X_REWRITE_URL',
        'HTTP_X_HTTP_METHOD_OVERRIDE', 'HTTP_X_HTTP_VERSION', 'HTTP_X_HTTPS',
        'HTTP_X_SCHEME', 'HTTP_X_FORWARDED_SSL', 'HTTP_X_FORWARDED_PROTO',
        'HTTP_X_FORWARDED_FOR', 'HTTP_X_CLUSTER_CLIENT_IP', 'HTTP_X_CLIENT_IP',
        'HTTP_X_REAL_IP', 'HTTP_X_ORIGINAL_FORWARDED_FOR', 'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED_HOST',
        'HTTP_X_FORWARDED_SERVER', 'HTTP_X_FORWARDED_PORT', 'HTTP_X_ORIGINAL_URL',
        'HTTP_X_REWRITE_URL', 'HTTP_X_HTTP_METHOD_OVERRIDE', 'HTTP_X_HTTP_VERSION',
        'HTTP_X_HTTPS', 'HTTP_X_SCHEME', 'HTTP_X_FORWARDED_SSL', 'HTTP_X_FORWARDED_PROTO'
    ]

    environ_data = {}
    for key in interesting_environ:
        value = request.environ.get(key)
        if value:
            environ_data[key] = value

    # Add all HTTP headers from environ (comprehensive approach)
    http_headers = {}
    for key, value in request.environ.items():
        if key.startswith('HTTP_'):
            # Convert HTTP_HEADER_NAME to Header-Name format
            header_name = key[5:].replace('_', '-').title()
            http_headers[header_name] = value

    request_info['environ_data'] = environ_data
    request_info['http_headers_from_environ'] = http_headers
    request_info['all_environ_keys'] = list(request.environ.keys())

    # Add request data if present
    try:
        if request.data:
            request_info['raw_data'] = request.data.decode(
                'utf-8', errors='replace')
    except Exception as e:
        request_info['raw_data'] = f'Could not decode raw data: {str(e)}'

    # Add files if present
    if request.files:
        files_info = {}
        for key, file in request.files.items():
            files_info[key] = {
                'filename': file.filename,
                'content_type': file.content_type,
                'content_length': file.content_length
            }
        request_info['files'] = files_info

    logger.info(
        f"COMPREHENSIVE REQUEST: {json.dumps(request_info, indent=2, default=str)}")


@app.after_request
def log_to_db(response):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        headers_json = json.dumps(dict(request.headers), default=str)
        query_json = json.dumps(dict(request.args), default=str)
        try:
            body_text = request.get_data(cache=False, as_text=True)
        except Exception:
            body_text = None
        cur.execute(
            """
            INSERT INTO request_logs (
                timestamp, method, path, status_code, ip, user_agent, referer, headers_json, query_json, body
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                request.method,
                request.path,
                response.status_code,
                request.remote_addr,
                request.headers.get('User-Agent'),
                request.headers.get('Referer'),
                headers_json,
                query_json,
                body_text,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception(f"Failed to persist request log: {e}")
    return response


def get_client_ip():
    """Get real client IP from various headers"""
    # Check common proxy headers
    for header in ['HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP']:
        ip = request.environ.get(header)
        if ip:
            return ip.split(',')[0].strip()
    return request.remote_addr


def parse_user_agent():
    """Extract more info from User-Agent"""
    ua = request.headers.get('User-Agent', '')

    info = {
        'raw': ua,
        'is_mobile': any(mobile in ua.lower() for mobile in ['mobile', 'android', 'iphone', 'ipad']),
        'is_bot': any(bot in ua.lower() for bot in ['bot', 'crawler', 'spider', 'scraper']),
    }

    # Basic browser detection
    if 'Chrome' in ua:
        info['browser'] = 'Chrome'
    elif 'Firefox' in ua:
        info['browser'] = 'Firefox'
    elif 'Safari' in ua and 'Chrome' not in ua:
        info['browser'] = 'Safari'
    elif 'Edge' in ua:
        info['browser'] = 'Edge'
    else:
        info['browser'] = 'Unknown'

    return info


@app.route('/')
def home():
    return render_template('index.html')


def get_quiz_questions():
    # Humorous, privacy-satire questions that DO NOT ask for real secrets
    # Stored in session for this demo (not persisted)
    return [
        {
            'id': 'q1',
            'prompt': "What's your favorite thing to post online?",
            'type': 'radio',
            'options': [
                "My super-secret cookie recipe",
                "My childhood nickname for a pet rock",
                "My favorite fictional password (definitely not a real one)",
                "My high score in a 1998 arcade game",
            ],
        },
        {
            'id': 'q2',
            'prompt': "What's your favorite address type to currently live on?",
            'type': 'radio',
            'options': ["Street", "Road", "Lane", "None of the above"],
        },
        {
            'id': 'q3',
            'prompt': "Complete the sentence: 'Security questions should be...'",
            'type': 'radio',
            'options': [
                "Replaced by multi-factor auth",
                "So vague even future-me is confused",
                "Multiple-choice with only 'None of the above'",
                "A trap for oversharing (but not today!)",
            ],
        },
        {
            'id': 'q4',
            'prompt': "In a parallel universe, your 'favorite password' is... ",
            'type': 'radio',
            'options': ["swordfish", "password1234-but-ironic", "correcthorsebatterystaple-ish", "******"],
        },
        {
            'id': 'q5',
            'prompt': "How would you respond to: 'What is your mother's maiden name?'",
            'type': 'radio',
            'options': [
                "Politely decline and enable 2FA",
                "Answer: 'Maiden? She was always a boss'",
                "Use a password manager's generated answer",
                "Redirect to a security awareness talk",
            ],
        },
        {
            'id': 'q6',
            'prompt': "Pick a superhero to guard your privacy",
            'type': 'radio',
            'options': ["Captain Obfuscation", "The Redactor", "Null Pointer", "Agent 404"],
        },
    ]


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'GET':
        # Always refresh questions so code changes are reflected immediately
        session['quiz_questions'] = get_quiz_questions()
        return render_template('quiz.html', questions=session['quiz_questions'])

    # POST: collect answers
    answers = {}
    for question in session.get('quiz_questions', []):
        qid = question['id']
        answers[qid] = request.form.get(qid)

    # Persist submission
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO quiz_submissions (timestamp, ip, user_agent, answers_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                request.remote_addr,
                request.headers.get('User-Agent'),
                json.dumps(answers, default=str),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception(f"Failed to persist quiz submission: {e}")

    session['quiz_answers'] = answers
    return redirect(url_for('quiz_results'))


@app.route('/quiz/reset')
def quiz_reset():
    session.pop('quiz_questions', None)
    session.pop('quiz_answers', None)
    return redirect(url_for('quiz'))


@app.route('/quiz/results')
def quiz_results():
    questions = session.get('quiz_questions', [])
    answers = session.get('quiz_answers', {})
    profile = determine_animal_profile(answers)
    return render_template('results.html', questions=questions, answers=answers, profile=profile)


def determine_animal_profile(answers: dict) -> dict:
    """Return a fun, BuzzFeed-style animal profile based on answers.
    Uses a simple deterministic hash so the same answers yield the same animal.
    """
    # Build a stable seed from answers
    concat = "|".join(f"{k}:{v}" for k, v in sorted(answers.items()))
    seed = sum(ord(c) for c in concat) % 1000

    animal_profiles = [
        {
            'name': 'Red Panda',
            'emoji': '🦝',
            'tagline': "Cozy, curious, and criminally cute",
            'description': "You thrive on vibes and soft blankets. Youre a gentle introvert who still knows how to steal the spotlight  mostly with snacks.",
            'traits': ['Cozy-core', 'Snack-forward', 'Camera-ready'],
        },
        {
            'name': 'Otter',
            'emoji': '🦦',
            'tagline': "Play first, plan… eventually",
            'description': "Youre collaborative, chaotic-good, and find joy in little things (like holding hands and river slides).",
            'traits': ['Playful', 'Social', 'Inventive'],
        },
        {
            'name': 'Quokka',
            'emoji': '🦘',
            'tagline': "A smile with legs",
            'description': "Your optimism is contagious and slightly suspicious. People feel safer just by standing near you.",
            'traits': ['Optimistic', 'Disarming', 'Unflappable'],
        },
        {
            'name': 'Axolotl',
            'emoji': '🦎',
            'tagline': "Soft chaos scientist",
            'description': "Youre adaptable, adorable, and unbothered. If vibes were a PhD, youd be tenured.",
            'traits': ['Adaptive', 'Serene', 'Mysteriously wise'],
        },
        {
            'name': 'Corgi',
            'emoji': '🐶',
            'tagline': "Short king energy",
            'description': "You lead with enthusiasm and snack diplomacy. Your calendar is 50% walks, 50% parties.",
            'traits': ['Loyal', 'Upbeat', 'Snack-positive'],
        },
        {
            'name': 'Penguin',
            'emoji': '🐧',
            'tagline': "Formalwear, informal chaos",
            'description': "Youre elegant under pressure and hilarious on land. Teamwork is your superpower.",
            'traits': ['Graceful', 'Team-first', 'Resilient'],
        },
    ]

    idx = seed % len(animal_profiles)
    return animal_profiles[idx]


@app.route('/api/test', methods=['GET', 'POST', 'PUT'])
def api_test():
    """Test endpoint for different request types"""
    if request.method == 'POST':
        return {"received_json": request.get_json(), "form": dict(request.form)}
    return {"method": request.method, "headers_count": len(request.headers)}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)
