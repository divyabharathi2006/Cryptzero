import os
from pathlib import Path

from app.decryptors.base import FileDecryptor

try:
    import rarfile
except Exception:  # pragma: no cover
    rarfile = None


class RarDecryptor(FileDecryptor):
    name = 'rar'

    def detect(self, file_path):
        path = Path(file_path)
        return path.suffix.lower() == '.rar' or (path.exists() and path.read_bytes()[:4] == b'Rar!')

    def analyze(self, file_path):
        return {'success': True, 'name': 'RAR', 'encrypted': True, 'requires_password': True}

    def decrypt(self, file_path, credential, job_id):
        if not file_path or not os.path.exists(file_path):
            return {'success': False, 'error_code': 'INVALID_FILE', 'message': 'Input file missing.'}
        if rarfile is None:
            return {'success': False, 'error_code': 'UNSUPPORTED_FORMAT', 'message': 'RAR support requires the rarfile dependency to be installed.'}

        try:
            base_dir = Path(file_path).resolve().parent.parent / 'jobs' / job_id
            output_dir = base_dir / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)

            with rarfile.RarFile(file_path) as rf:
                rf.setpassword(credential)
                rf.extractall(path=str(output_dir))

            if not any(output_dir.iterdir()):
                return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied RAR password is incorrect.'}

            return {'success': True, 'output_path': str(output_dir), 'job_id': job_id, 'message': 'RAR archive successfully extracted.'}
        except Exception as exc:
            message = str(exc).lower()
            if 'password' in message or 'wrong' in message or 'bad' in message:
                return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied RAR password is incorrect.'}
            return {'success': False, 'error_code': 'PROCESSING_ERROR', 'message': f'Unable to decrypt RAR archive: {exc}'}

    def validate(self, output_path):
        return os.path.isdir(output_path) and len(os.listdir(output_path)) > 0
