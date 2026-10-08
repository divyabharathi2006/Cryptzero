from flask import Blueprint, jsonify

from app import get_job, update_job

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_info(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'Unknown job.'}), 404
    return jsonify({'success': True, 'job': job})


@jobs_bp.route('/api/jobs/<job_id>/progress', methods=['GET'])
def job_progress(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'Unknown job.'}), 404
    progress = 100 if job.get('status') == 'completed' else 60
    return jsonify({'success': True, 'job_id': job_id, 'status': job.get('status'), 'progress': progress})


@jobs_bp.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    update_job(job_id, status='deleted')
    return jsonify({'success': True, 'job_id': job_id, 'status': 'deleted'})
