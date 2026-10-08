import os
from pathlib import Path

import pyzipper
import zipfile

from app.decryptors.base import FileDecryptor


class ZipDecryptor(FileDecryptor):
    name = 'zip'

    def detect(self, file_path):
        return zipfile.is_zipfile(file_path)

    def analyze(self, file_path):
        return {'success': True, 'name': 'ZIP', 'encrypted': True, 'requires_password': True}

    def decrypt(self, file_path, credential, job_id):
        if not file_path or not os.path.exists(file_path):
            return {'success': False, 'error_code': 'INVALID_FILE', 'message': 'Input file missing.'}

        try:
            base_dir = Path(file_path).resolve().parent.parent / 'jobs' / job_id
            output_dir = base_dir / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)

            with pyzipper.AESZipFile(file_path) as zf:
                zf.setpassword(credential.encode())
                zf.extractall(str(output_dir))

            if not any(output_dir.iterdir()):
                return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied ZIP password is incorrect.'}

            out_path = output_dir / Path(file_path).name
            return {'success': True, 'output_path': str(out_path), 'job_id': job_id, 'message': 'ZIP archive successfully extracted.'}
        except RuntimeError:
            return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied ZIP password is incorrect.'}
        except Exception as exc:
            return {'success': False, 'error_code': 'PROCESSING_ERROR', 'message': f'Unable to decrypt ZIP archive: {exc}'}

    def validate(self, output_path):
        return os.path.isdir(output_path) and len(os.listdir(output_path)) > 0
