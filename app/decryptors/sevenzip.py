import os
from pathlib import Path

import py7zr

from app.decryptors.base import FileDecryptor


class SevenZipDecryptor(FileDecryptor):
    name = 'sevenzip'

    def detect(self, file_path):
        return Path(file_path).suffix.lower() == '.7z'

    def analyze(self, file_path):
        return {'success': True, 'name': '7Z', 'encrypted': True, 'requires_password': True}

    def decrypt(self, file_path, credential, job_id):
        if not file_path or not os.path.exists(file_path):
            return {'success': False, 'error_code': 'INVALID_FILE', 'message': 'Input file missing.'}

        try:
            base_dir = Path(file_path).resolve().parent.parent / 'jobs' / job_id
            output_dir = base_dir / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)

            with py7zr.SevenZipFile(file_path, mode='r', password=credential) as z:
                z.extractall(path=str(output_dir))

            if not any(output_dir.iterdir()):
                return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied 7Z password is incorrect.'}

            return {'success': True, 'output_path': str(output_dir), 'job_id': job_id, 'message': '7Z archive successfully extracted.'}
        except Exception as exc:
            message = str(exc).lower()
            if 'password' in message or 'wrong' in message:
                return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied 7Z password is incorrect.'}
            return {'success': False, 'error_code': 'PROCESSING_ERROR', 'message': f'Unable to decrypt 7Z archive: {exc}'}

    def validate(self, output_path):
        return os.path.isdir(output_path) and len(os.listdir(output_path)) > 0
