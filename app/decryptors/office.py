import os
from pathlib import Path

import pyzipper

from app.decryptors.base import FileDecryptor


class OfficeDecryptor(FileDecryptor):
    name = 'office'

    def detect(self, file_path):
        return Path(file_path).suffix.lower() in {'.docx', '.xlsx', '.pptx'}

    def decrypt(self, file_path, credential, job_id):
        if not self.detect(file_path):
            return {'success': False, 'error_code': 'UNSUPPORTED_ENCRYPTION', 'message': 'Office document encryption is not supported by the current processing engine.'}

        try:
            base_dir = Path(file_path).resolve().parent.parent / 'jobs' / job_id
            output_dir = base_dir / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)

            with pyzipper.AESZipFile(file_path, 'r', pwd=credential.encode()) as zf:
                zf.extractall(str(output_dir))

            return {'success': True, 'output_path': str(output_dir), 'job_id': job_id, 'message': 'Office package successfully extracted.'}
        except Exception:
            return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied credential is invalid or the Office package is not password-protected in a supported way.'}
