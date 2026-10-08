from flask import Blueprint, jsonify, request

from app import get_job, update_job
from app.core.registry import resolve_handler

unlock_bp = Blueprint('unlock', __name__)


@unlock_bp.route('/api/files/unlock', methods=['POST'])
def unlock_file():
    payload = request.get_json(silent=True) or request.form
    if not isinstance(payload, dict):
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'The request body was invalid.'}), 400

    job_id = payload.get('job_id')
    credential = payload.get('credential')

    if not job_id or not credential:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'Job ID and credential are required.'}), 400

    job = get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'Unknown job.'}), 404

    handler = resolve_handler(job.get('detected_format', 'UNKNOWN'))
    result = handler.decrypt(job.get('input_path'), credential, job_id)

    if not result.get('success'):
        update_job(job_id, status='failed', error_code=result.get('error_code', 'PROCESSING_ERROR'))
        return jsonify({'success': False, 'error_code': result.get('error_code', 'PROCESSING_ERROR'), 'message': result.get('message', 'Unlock failed.')})

    update_job(job_id, status='completed', output_path=result.get('output_path'), error_code=None)
    return jsonify({'success': True, 'job_id': job_id, 'status': 'completed', 'result': result})
