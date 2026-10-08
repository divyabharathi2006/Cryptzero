import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    PORT = int(os.getenv('PORT', '1630'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 100 * 1024 * 1024))
    TEMP_EXPIRATION_MINUTES = int(os.getenv('TEMP_EXPIRATION_MINUTES', 15))
    STORAGE_ROOT = Path(os.getenv('STORAGE_ROOT', str(BASE_DIR / 'storage')))
    JOBS_ROOT = STORAGE_ROOT / 'jobs'
    QUARANTINE_ROOT = STORAGE_ROOT / 'quarantine'
    DB_PATH = BASE_DIR / 'cryptzero.db'
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 30))
    MAX_CONCURRENT_JOBS = int(os.getenv('MAX_CONCURRENT_JOBS', 5))
    MAX_EXTRACTION_SIZE = int(os.getenv('MAX_EXTRACTION_SIZE', 500 * 1024 * 1024))
    MAX_FILE_COUNT = int(os.getenv('MAX_FILE_COUNT', 2000))
    JSON_SORT_KEYS = False
