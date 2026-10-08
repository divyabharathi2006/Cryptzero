import os
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.decryptors.base import FileDecryptor


class PdfDecryptor(FileDecryptor):
    name = 'pdf'

    def detect(self, file_path):
        return Path(file_path).suffix.lower() == '.pdf'

    def analyze(self, file_path):
        return {'success': True, 'name': 'PDF', 'encrypted': True, 'requires_password': True}

    def decrypt(self, file_path, credential, job_id):
        if not os.path.exists(file_path):
            return {'success': False, 'error_code': 'INVALID_FILE', 'message': 'Input file missing.'}

        try:
            reader = PdfReader(file_path)
            if not reader.is_encrypted:
                return {'success': False, 'error_code': 'NOT_ENCRYPTED', 'message': 'The PDF is not encrypted.'}

            if reader.decrypt(credential) == 0:
                return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'The supplied PDF password is incorrect.'}

            base_dir = Path(file_path).resolve().parent.parent / 'jobs' / job_id
            output_dir = base_dir / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)

            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            out_path = output_dir / f'{Path(file_path).stem}_unlocked.pdf'
            with open(out_path, 'wb') as fh:
                writer.write(fh)

            return {'success': True, 'output_path': str(out_path), 'job_id': job_id, 'message': 'PDF successfully decrypted.'}
        except Exception as exc:
            return {'success': False, 'error_code': 'PROCESSING_ERROR', 'message': f'Unable to process PDF: {exc}'}
