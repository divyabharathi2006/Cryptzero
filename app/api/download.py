from pathlib import Path

from flask import Blueprint, jsonify, send_file

from app import get_job

download_bp = Blueprint('download', __name__)


@download_bp.route('/api/jobs/<job_id>/download', methods=['GET'])
def download(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error_code': 'INVALID_FILE', 'message': 'Unknown job.'}), 404

    output_path = job.get('output_path')
    if not output_path or not Path(output_path).exists():
        return jsonify({'success': False, 'error_code': 'PROCESSING_ERROR', 'message': 'No output file available for this job.'}), 404

    return send_file(output_path, as_attachment=True, download_name=Path(output_path).name)
