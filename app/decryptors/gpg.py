import shutil
import subprocess
from pathlib import Path

from app.decryptors.base import FileDecryptor


class GpgDecryptor(FileDecryptor):
    name = 'gpg'

    def detect(self, file_path):
        return shutil.which('gpg') is not None

    def decrypt(self, file_path, credential, job_id):
        gpg_exec = shutil.which('gpg')
        if not gpg_exec:
            return {'success': False, 'error_code': 'MISSING_DEPENDENCY', 'message': 'GPG is not installed on this machine.'}

        base_dir = Path(file_path).resolve().parent.parent / 'jobs' / job_id
        output_dir = base_dir / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / 'decrypted.gpg'

        try:
            result = subprocess.run(
                [
                    gpg_exec,
                    '--batch',
                    '--yes',
                    '--pinentry-mode',
                    'loopback',
                    '--passphrase',
                    credential,
                    '--decrypt',
                    file_path,
                    '-o',
                    str(out_path),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied GPG passphrase is invalid.'}
            return {'success': True, 'output_path': str(out_path), 'job_id': job_id, 'message': 'PGP file successfully decrypted.'}
        except Exception as exc:
            return {'success': False, 'error_code': 'PROCESSING_ERROR', 'message': f'Unable to process GPG file: {exc}'}
