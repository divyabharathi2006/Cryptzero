from pathlib import Path

from flask import Blueprint, jsonify, request

from app import get_job, update_job
from app.core.detector import analyze_file

analyze_bp = Blueprint('analyze', __name__)


@analyze_bp.route('/api/files/analyze', methods=['POST'])
def analyze():
    payload = request.get_json(silent=True) or request.form
    job_id = payload.get('job_id') if isinstance(payload, dict) else None

    if not job_id:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'Job ID is required.'}), 400

    job = get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'Unknown job.'}), 404

    input_path = job.get('input_path')
    if not input_path or not Path(input_path).exists():
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'Input file not found.'}), 404

    analysis = analyze_file(input_path)
    update_job(job_id, detected_format=analysis.get('detected_format', 'UNKNOWN'), encryption_type=analysis.get('encryption_type', 'NONE'), status='analyzed', metadata=str(analysis))
    return jsonify({'success': True, 'job_id': job_id, 'status': 'analyzed', 'analysis': analysis})
