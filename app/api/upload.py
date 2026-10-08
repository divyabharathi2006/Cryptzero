import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from app import create_job_record, get_job, update_job
from app.core.detector import analyze_file
from app.security.validation import sanitize_filename, validate_file_upload

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    file_obj = request.files.get('file')
    if file_obj is None:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'No file was provided.'}), 400

    filename = sanitize_filename(file_obj.filename)
    is_valid, msg = validate_file_upload(file_obj, filename)
    if not is_valid:
        return jsonify({'success': False, 'error_code': msg, 'message': msg}), 400

    job_id = uuid.uuid4().hex
    jobs_root = Path(current_app.config['JOBS_ROOT'])
    job_dir = jobs_root / job_id
    input_dir = job_dir / 'input'
    input_dir.mkdir(parents=True, exist_ok=True)

    target = input_dir / filename
    file_obj.save(target)

    analysis = analyze_file(str(target))
    create_job_record(
        job_id=job_id,
        filename=filename,
        size=target.stat().st_size,
        detected_format=analysis.get('detected_format', 'UNKNOWN'),
        encryption_type=analysis.get('encryption_type', 'NONE'),
        status='uploaded'
    )
    update_job(job_id, input_path=str(target), file_type=analysis.get('mime_type', 'application/octet-stream'), metadata=str(analysis))

    return jsonify({
        'success': True,
        'job_id': job_id,
        'status': 'uploaded',
        'analysis': analysis,
        'message': 'File accepted for analysis.'
    })
