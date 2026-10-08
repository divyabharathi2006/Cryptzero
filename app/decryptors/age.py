import shutil
import subprocess
from pathlib import Path

from app.decryptors.base import FileDecryptor


class AgeDecryptor(FileDecryptor):
    name = 'age'

    def detect(self, file_path):
        return shutil.which('age') is not None

    def decrypt(self, file_path, credential, job_id):
        age_exec = shutil.which('age')
        if not age_exec:
            return {'success': False, 'error_code': 'MISSING_DEPENDENCY', 'message': 'The age utility is not installed on this machine.'}

        base_dir = Path(file_path).resolve().parent.parent / 'jobs' / job_id
        output_dir = base_dir / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / 'decrypted.age'

        try:
            result = subprocess.run(
                [age_exec, '-d', '-p', credential, '-o', str(out_path), file_path],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied age passphrase is invalid.'}
            return {'success': True, 'output_path': str(out_path), 'job_id': job_id, 'message': 'Age-encrypted file successfully decrypted.'}
        except Exception as exc:
            return {'success': False, 'error_code': 'PROCESSING_ERROR', 'message': f'Unable to process age file: {exc}'}
