import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

from config import Config
from app.core.registry import get_capabilities
from app.security.headers import add_security_headers
from app.security.validation import ensure_storage_dirs

DB_PATH = str(Path(__file__).resolve().parent.parent / 'cryptzero.db')


def get_db_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn


def ensure_db_schema():
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS archives (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            original_name TEXT,
            stored_name TEXT,
            safe_path TEXT,
            size INTEGER,
            entries INTEGER,
            encrypted INTEGER,
            status TEXT,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            archive_id TEXT,
            user_id TEXT,
            method TEXT,
            status TEXT,
            original_filename TEXT,
            size INTEGER,
            detected_format TEXT,
            encryption_type TEXT,
            created_at TEXT,
            expires_at TEXT,
            processing_duration REAL,
            error_code TEXT,
            output_path TEXT,
            input_path TEXT,
            file_type TEXT,
            credential_hash TEXT,
            metadata TEXT,
            attempts INTEGER DEFAULT 0,
            total_candidates INTEGER DEFAULT 0,
            password TEXT,
            progress REAL DEFAULT 0,
            search_space TEXT,
            result TEXT,
            started_at TEXT,
            ended_at TEXT,
            elapsed_seconds REAL DEFAULT 0,
            notes TEXT
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            created_at TEXT
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY,
            job_id TEXT,
            archive_name TEXT,
            method TEXT,
            started_at TEXT,
            ended_at TEXT,
            attempts INTEGER,
            result TEXT,
            duration REAL,
            password_saved INTEGER DEFAULT 0
        )
        '''
    )
    conn.commit()
    conn.close()


def create_job_record(job_id=None, archive_id=None, user_id=None, method='wordlist', status='queued', **legacy_fields):
    if job_id is None:
        job_id = uuid.uuid4().hex
    if user_id is None:
        user_id = 'legacy'
    if archive_id is None:
        archive_id = job_id

    now = datetime.utcnow().isoformat()
    expires = (datetime.utcnow() + timedelta(minutes=Config.TEMP_EXPIRATION_MINUTES)).isoformat()
    row = {
        'job_id': job_id,
        'archive_id': archive_id,
        'user_id': user_id,
        'method': method,
        'status': status,
        'original_filename': legacy_fields.get('filename'),
        'size': legacy_fields.get('size'),
        'detected_format': legacy_fields.get('detected_format'),
        'encryption_type': legacy_fields.get('encryption_type'),
        'created_at': now,
        'expires_at': expires,
        'processing_duration': 0.0,
        'error_code': legacy_fields.get('error_code'),
        'output_path': legacy_fields.get('output_path', ''),
        'input_path': legacy_fields.get('input_path', ''),
        'file_type': legacy_fields.get('file_type', 'file'),
        'credential_hash': '',
        'metadata': legacy_fields.get('metadata', '{}'),
        'attempts': 0,
        'total_candidates': 0,
        'password': None,
        'progress': 0.0,
        'search_space': '',
        'result': legacy_fields.get('result', ''),
        'started_at': now,
        'ended_at': None,
        'elapsed_seconds': 0.0,
        'notes': '',
    }

    conn = get_db_connection()
    conn.execute(
        '''
        INSERT INTO jobs (
            job_id, archive_id, user_id, method, status,
            original_filename, size, detected_format, encryption_type,
            created_at, expires_at, processing_duration, error_code, output_path,
            input_path, file_type, credential_hash, metadata,
            attempts, total_candidates, password, progress, search_space,
            result, started_at, ended_at, elapsed_seconds, notes
        ) VALUES (
            :job_id, :archive_id, :user_id, :method, :status,
            :original_filename, :size, :detected_format, :encryption_type,
            :created_at, :expires_at, :processing_duration, :error_code, :output_path,
            :input_path, :file_type, :credential_hash, :metadata,
            :attempts, :total_candidates, :password, :progress, :search_space,
            :result, :started_at, :ended_at, :elapsed_seconds, :notes
        )
        ''',
        row,
    )
    conn.commit()
    conn.close()
    return job_id


def update_job(job_id, **fields):
    if not fields:
        return
    conn = get_db_connection()
    assignments = ', '.join(f'{key} = ?' for key in fields.keys())
    values = list(fields.values()) + [job_id]
    conn.execute(f'UPDATE jobs SET {assignments} WHERE job_id = ?', values)
    conn.commit()
    conn.close()


def get_job(job_id):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_jobs(user_id=None, limit=50):
    conn = get_db_connection()
    if user_id:
        rows = conn.execute('SELECT * FROM jobs WHERE user_id = ? ORDER BY started_at DESC LIMIT ?', (user_id, limit)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM jobs ORDER BY started_at DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_archive(archive_id):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM archives WHERE id = ?', (archive_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_archives(user_id=None, limit=50):
    conn = get_db_connection()
    if user_id:
        rows = conn.execute('SELECT * FROM archives WHERE user_id = ? ORDER BY created_at DESC LIMIT ?', (user_id, limit)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM archives ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_history(user_id=None, limit=50):
    conn = get_db_connection()
    if user_id:
        rows = conn.execute('SELECT * FROM history WHERE job_id IN (SELECT job_id FROM jobs WHERE user_id = ?) ORDER BY started_at DESC LIMIT ?', (user_id, limit)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM history ORDER BY started_at DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def auth_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            session['user_id'] = 'anonymous'
            session['username'] = 'anonymous'
        return view(*args, **kwargs)

    return wrapped


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE
    app.config['UPLOAD_FOLDER'] = str(Config.STORAGE_ROOT / 'uploads')
    app.config['JOBS_ROOT'] = str(Config.JOBS_ROOT)
    app.config['EXTRACTED_ROOT'] = str(Config.STORAGE_ROOT / 'extracted')
    app.secret_key = Config.SECRET_KEY
    ensure_storage_dirs(app)
    ensure_db_schema()

    @app.before_request
    def ensure_local_session():
        if 'user_id' not in session:
            session['user_id'] = 'anonymous'
            session['username'] = 'anonymous'

    @app.after_request
    def set_security_headers(response):
        return add_security_headers(response)

    @app.route('/')
    def index():
        return render_template('dashboard.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/api/health')
    def health():
        return jsonify({'success': True, 'status': 'healthy', 'capabilities': get_capabilities()})

    @app.route('/api/formats')
    def formats():
        return jsonify({'success': True, 'formats': get_capabilities()['formats']})

    @app.route('/api/capabilities')
    def capabilities():
        return jsonify(get_capabilities())

    @app.route('/api/auth/register', methods=['POST'])
    def register_user():
        payload = request.get_json(silent=True) or {}
        username = (payload.get('username') or '').strip()
        password = payload.get('password') or ''
        if not username or not password:
            return jsonify({'success': False, 'error_code': 'INVALID_INPUT', 'message': 'Username and password are required.'}), 400

        from werkzeug.security import generate_password_hash

        conn = get_db_connection()
        exists = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if exists:
            conn.close()
            return jsonify({'success': False, 'error_code': 'USER_EXISTS', 'message': 'User already exists.'}), 409

        user_id = uuid.uuid4().hex
        conn.execute('INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)', (user_id, username, generate_password_hash(password), datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'User registered.'})

    @app.route('/api/auth/login', methods=['POST'])
    def login_user():
        payload = request.get_json(silent=True) or {}
        username = (payload.get('username') or '').strip()
        password = payload.get('password') or ''

        from werkzeug.security import check_password_hash

        conn = get_db_connection()
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if not row or not check_password_hash(row['password_hash'], password):
            return jsonify({'success': False, 'error_code': 'INVALID_CREDENTIALS', 'message': 'Invalid username or password.'}), 401

        session['user_id'] = row['id']
        session['username'] = row['username']
        return jsonify({'success': True, 'message': 'Login successful.', 'user': {'id': row['id'], 'username': row['username']}})

    @app.route('/api/auth/logout', methods=['POST'])
    def logout_user():
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out.'})

    from app.api.upload import upload_bp
    from app.api.analyze import analyze_bp
    from app.api.unlock import unlock_bp
    from app.api.jobs import jobs_bp
    from app.routes.api import api_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(analyze_bp)
    app.register_blueprint(unlock_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(api_bp)

    return app
