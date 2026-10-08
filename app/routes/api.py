import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, session

from app import auth_required, create_job_record, get_archive, get_history, get_job, list_archives, list_jobs, update_job
from app.services.zip_analyzer import analyze_zip_archive
from app.services.recovery_engine import RecoveryEngine
from app.services.verifier import verify_password
from app.services.extractor import safe_extract_zip

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/archive/upload', methods=['POST'])
@auth_required
def upload_archive():
    file_obj = request.files.get('file')
    if file_obj is None:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'No archive file uploaded.'}), 400

    filename = file_obj.filename or 'archive.zip'
    ext = Path(filename).suffix.lower()
    if ext not in {'.zip', '.rar'}:
        return jsonify({'success': False, 'error_code': 'INVALID_EXTENSION', 'message': 'Only .zip and .rar files are accepted.'}), 400

    safe_name = uuid.uuid4().hex + ext
    upload_root = Path(current_app.config['UPLOAD_FOLDER'])
    upload_root.mkdir(parents=True, exist_ok=True)
    stored_path = upload_root / safe_name
    file_obj.save(stored_path)

    analysis = analyze_zip_archive(str(stored_path))
    archive_id = uuid.uuid4().hex
    conn = __import__('app', fromlist=['get_db_connection']).get_db_connection()
    conn.execute(
        '''
        INSERT INTO archives (id, user_id, original_name, stored_name, safe_path, size, entries, encrypted, status, metadata, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            archive_id,
            session['user_id'],
            filename,
            safe_name,
            str(stored_path),
            analysis.get('size', 0),
            analysis.get('entries', 0),
            1 if analysis.get('encrypted') else 0,
            'analyzed',
            json.dumps(analysis),
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'archive_id': archive_id, 'analysis': analysis})


@api_bp.route('/api/archive/<archive_id>', methods=['GET'])
@auth_required
def get_archive_info(archive_id):
    archive = get_archive(archive_id)
    if not archive:
        return jsonify({'success': False, 'error_code': 'NOT_FOUND', 'message': 'Archive not found.'}), 404
    if archive.get('user_id') != session['user_id']:
        return jsonify({'success': False, 'error_code': 'FORBIDDEN', 'message': 'Access denied.'}), 403
    return jsonify({'success': True, 'archive': archive})


@api_bp.route('/api/archive/<archive_id>', methods=['DELETE'])
@auth_required
def delete_archive(archive_id):
    archive = get_archive(archive_id)
    if not archive:
        return jsonify({'success': False, 'error_code': 'NOT_FOUND', 'message': 'Archive not found.'}), 404
    if archive.get('user_id') != session['user_id']:
        return jsonify({'success': False, 'error_code': 'FORBIDDEN', 'message': 'Access denied.'}), 403

    try:
        if os.path.exists(archive['safe_path']):
            os.remove(archive['safe_path'])
    except Exception:
        pass

    conn = __import__('app', fromlist=['get_db_connection']).get_db_connection()
    conn.execute('DELETE FROM archives WHERE id = ?', (archive_id,))
    conn.execute('DELETE FROM jobs WHERE archive_id = ?', (archive_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Archive deleted.'})


@api_bp.route('/api/recovery/start', methods=['POST'])
@auth_required
def start_recovery():
    payload = request.get_json(silent=True) or {}
    archive_id = payload.get('archive_id')
    method = payload.get('method', 'wordlist')
    options = payload.get('options', {}) or {}

    archive = get_archive(archive_id)
    if not archive:
        return jsonify({'success': False, 'error_code': 'NOT_FOUND', 'message': 'Archive not found.'}), 404
    if archive.get('user_id') != session['user_id']:
        return jsonify({'success': False, 'error_code': 'FORBIDDEN', 'message': 'Access denied.'}), 403

    job_id = create_job_record(
        archive_id=archive_id,
        user_id=session['user_id'],
        method=method,
        status='queued',
    )
    engine = RecoveryEngine(job_id, archive_id, method, options)
    engine.start_background()
    return jsonify({'success': True, 'job_id': job_id, 'status': 'started'})


@api_bp.route('/api/recovery/<job_id>/status', methods=['GET'])
@auth_required
def recovery_status(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error_code': 'NOT_FOUND', 'message': 'Job not found.'}), 404
    if job.get('user_id') != session['user_id']:
        return jsonify({'success': False, 'error_code': 'FORBIDDEN', 'message': 'Access denied.'}), 403
    return jsonify({'success': True, 'job': job})


@api_bp.route('/api/recovery/<job_id>/pause', methods=['POST'])
@auth_required
def pause_recovery(job_id):
    update_job(job_id, status='paused')
    return jsonify({'success': True, 'message': 'Recovery paused.'})


@api_bp.route('/api/recovery/<job_id>/resume', methods=['POST'])
@auth_required
def resume_recovery(job_id):
    update_job(job_id, status='running')
    return jsonify({'success': True, 'message': 'Recovery resumed.'})


@api_bp.route('/api/recovery/<job_id>/cancel', methods=['POST'])
@auth_required
def cancel_recovery(job_id):
    update_job(job_id, status='cancelled')
    return jsonify({'success': True, 'message': 'Recovery cancelled.'})


@api_bp.route('/api/recovery/<job_id>/verify', methods=['POST'])
@auth_required
def verify_recovery(job_id):
    payload = request.get_json(silent=True) or {}
    candidate = payload.get('candidate')
    if not candidate:
        return jsonify({'success': False, 'error_code': 'INVALID_INPUT', 'message': 'Candidate password is required.'}), 400

    job = get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error_code': 'NOT_FOUND', 'message': 'Job not found.'}), 404
    archive = get_archive(job['archive_id'])
    if not archive:
        return jsonify({'success': False, 'error_code': 'NOT_FOUND', 'message': 'Archive not found.'}), 404
    if archive.get('user_id') != session['user_id']:
        return jsonify({'success': False, 'error_code': 'FORBIDDEN', 'message': 'Access denied.'}), 403

    ok, detail = verify_password(archive['safe_path'], candidate)
    return jsonify({'success': ok, 'password_valid': ok, 'detail': detail})


@api_bp.route('/api/archive/<archive_id>/extract', methods=['POST'])
@auth_required
def extract_archive(archive_id):
    archive = get_archive(archive_id)
    if not archive:
        return jsonify({'success': False, 'error_code': 'NOT_FOUND', 'message': 'Archive not found.'}), 404
    if archive.get('user_id') != session['user_id']:
        return jsonify({'success': False, 'error_code': 'FORBIDDEN', 'message': 'Access denied.'}), 403

    payload = request.get_json(silent=True) or {}
    password = payload.get('password')
    result = safe_extract_zip(archive['safe_path'], password)
    return jsonify(result)


@api_bp.route('/api/archives', methods=['GET'])
@auth_required
def list_user_archives():
    return jsonify({'success': True, 'archives': list_archives(session['user_id'])})


@api_bp.route('/api/jobs', methods=['GET'])
@auth_required
def list_user_jobs():
    return jsonify({'success': True, 'jobs': list_jobs(session['user_id'])})


@api_bp.route('/api/history', methods=['GET'])
@auth_required
def history():
    return jsonify({'success': True, 'history': get_history(session['user_id'])})
