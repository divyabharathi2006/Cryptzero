import os
import re
from pathlib import Path


ALLOWED_EXTENSIONS = {'.zip', '.7z', '.pdf', '.docx', '.xlsx', '.pptx', '.gpg', '.asc', '.age', '.rar', '.tar', '.gz', '.bz2', '.xz'}


def sanitize_filename(filename):
    if not filename:
        return 'upload.bin'
    cleaned = os.path.basename(filename)
    cleaned = re.sub(r'[^A-Za-z0-9._-]', '_', cleaned)
    return cleaned or 'upload.bin'


def ensure_storage_dirs(app=None):
    base = Path(__file__).resolve().parent.parent.parent
    jobs_root = Path(getattr(app.config, 'get', lambda k, d=None: str(base / 'storage' / 'jobs'))('JOBS_ROOT', str(base / 'storage' / 'jobs')))
    quarantine_root = Path(getattr(app.config, 'get', lambda k, d=None: str(base / 'storage' / 'quarantine'))('QUARANTINE_ROOT', str(base / 'storage' / 'quarantine')))
    jobs_root.mkdir(parents=True, exist_ok=True)
    quarantine_root.mkdir(parents=True, exist_ok=True)


def validate_file_upload(file_storage, filename):
    if file_storage is None:
        return False, 'INVALID_FILE'
    content_length = getattr(file_storage, 'content_length', None)
    if content_length is not None and content_length > 100 * 1024 * 1024:
        return False, 'FILE_TOO_LARGE'
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, 'UNSUPPORTED_FORMAT'
    return True, 'ok'
