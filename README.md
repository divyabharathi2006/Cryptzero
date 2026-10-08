# CRYPTZERO

CRYPTZERO is a local-first, security-focused file unlocking platform. It lets users upload files, detect the format and encryption container, provide a password/key, and run a real decryption flow when supported.

## Features
- ZIP and 7Z encrypted archive handling
- PDF password detection and decryption support when the installed library supports it
- Honest unsupported and dependency-aware handling
- Temporary job directories with automatic cleanup
- SQLite-based job metadata and admin dashboard
- Windows-friendly local setup on port 1630
- Docker support for web, worker, and Redis

## Quick start on Windows
1. Open PowerShell in the project folder.
2. Create a virtual environment:
   `python -m venv venv`
3. Activate it:
   `\.\venv\Scripts\Activate.ps1`
4. Install dependencies:
   `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and adjust values if needed.
6. Start the app:
   `python run.py`
7. Open http://127.0.0.1:1630

## Supported formats
- ZIP
- 7Z
- PDF password-protected documents (when supported by the library)
- Office ZIP-based documents when a compatible backend is present
- GPG/PGP and age detection when the required tool is installed
- Unsupported or unknown encrypted formats are reported honestly.

## Security model
- No passwords, keys, or decrypted content are stored in the database.
- Uploaded files are placed in isolated job folders.
- Temporary files are cleaned automatically.
- Path traversal and zip-slip safeguards are enforced.

## API
- POST /api/files/upload
- POST /api/files/analyze
- POST /api/files/unlock
- GET /api/jobs/<job_id>
- GET /api/jobs/<job_id>/progress
- GET /api/jobs/<job_id>/download
- DELETE /api/jobs/<job_id>
- GET /api/formats
- GET /api/health
- GET /api/capabilities

## Testing
Run:
`pytest`

## Docker
Run:
`docker-compose up --build`

## Production notes
This project is designed as a local-first secure application and can be served with Gunicorn in Linux or Waitress in Windows-based deployments. It does not use the Flask development server in production.
